#!/usr/bin/env python2.7

from argparse import ArgumentParser
from tempfile import mkdtemp
from os import rmdir, stat
from contextlib import contextmanager
import subprocess
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def shell(*args):
    logging.debug(list(args))
    return subprocess.Popen(args, stdout=subprocess.PIPE)

def shell_through(*args):
    p = shell(*args)
    return p.wait(), p.stdout.read()

def make_chunk(filename, size_in_bytes):
    return shell_through("truncate", "-s", str(size_in_bytes), filename)

@contextmanager
def mount(src, mountpoint=None, extras=None):
    m = mountpoint or mkdtemp()
    args = ["mount"] + (extras or []) + [src, m]
    shell_through(*args)
    try:
        yield m
    finally:
        shell_through("umount", m)
        if mountpoint is None:
            rmdir(m)

def mkfs(img, mkfs_="mkfs.ext4"):
    return shell_through(mkfs_, img)

def debootstrap(rootdir, release, variant="minbase", includes=None):
    opts = [
        ("--include=" + ",".join(includes)) if includes else "",
        "--variant=" + variant
    ]
    args = ["debootstrap"] + opts + [release, rootdir]
    p = shell(*args)
    for line in p.stdout.read(256):
        logger.info(line)
    return p.wait()

def create_root_img(img, size_in_bytes, release, includes=None):
    make_chunk(img, size_in_bytes)
    mkfs(img)
    with mount(img) as mountpoint:
        logger.info("Including packages: %s" % includes)
        debootstrap(mountpoint, release, includes=includes)

def parse_size(maybesuffix):
    BI = {
        "K": 1024,
        "M": 1024 ** 2,
        "G": 1024 ** 3,
    }
    mult = 1
    while maybesuffix[-1] in BI:
        mult = mult * BI[maybesuffix[-1]]
        maybesuffix = maybesuffix[:-1]
    return mult * int(maybesuffix)

def chroot(img):
    with mount(args.dotimg) as mp:
        with \
            mount("proc", mp + "/proc", extras="-t proc".split()), \
            mount("sysfs", mp + "/sys", extras="-t sysfs".split()), \
            mount("devtmpfs", mp + "/dev", extras="-t devtmpfs".split()), \
            mount("devpts", mp + "/dev/pts", extras="-t devpts".split()):

            # should block till shell exits
            subprocess.Popen(["chroot " + mp], shell=True).wait()

definc = "sudo aptitude pump ifupdown less vim-tiny openssh-server".split() + \
         "iputils-ping iproute2 linux-image-amd64 linux-tools".split() + \
         "binutils-dev sysvinit-core".split()

opts = ArgumentParser(description=("It puts the root into the filesystem. " +
                                   "Or else hose."))
opts.add_argument("dotimg",
                  help="some_file.img, into which de boot will strap.")
opts.add_argument("-s", "--size", default="2G",
                  help="Size of image to create in bytes. Suffices: K, M, G.")
opts.add_argument("-f", "--force", action="store_true", help="Force overwrite.")
opts.add_argument("-c", "--chroot", action="store_true",
                  help="Chroot into img (might require root).")
opts.add_argument("--inc", default=None,
                  help="Optional list of packages to include.")

if __name__ == "__main__":
    args = opts.parse_args()
    if args.chroot:
        chroot(args.dotimg)
    else:
        try:
            stat(args.dotimg)
        except OSError:
            pass
        else:
            if not args.force:
                print "File or dir exists:", args.dotimg
                exit(-1)
        incs = definc if args.inc is None else args.inc.split()
        create_root_img(args.dotimg, parse_size(args.size), "testing",
                        includes=incs)
