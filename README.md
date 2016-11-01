# imagestrap

utility that wraps debootstrap and chroot

## Usage

```bash
$ ./imagestrap -h
usage: imagestrap.py [-h] [-s SIZE] [-f] [-c] dotimg

It puts the root into the filesystem. Or else hose.

positional arguments:
  dotimg                some_file.img, into which de boot will strap.

optional arguments:
  -h, --help            show this help message and exit
  -s SIZE, --size SIZE  Size of image to create in bytes. Suffices: K, M, G.
  -f, --force           Force overwrite.
  -c, --chroot          Chroot into img (might require root).
```
