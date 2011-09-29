# rapidshare toolchain in python

This is a collection of small, commandline based scripts for acting with
filehoster like rapidshare and others. It focuses on full transparency and
let the user decide, how to download a file.

### rsget.py

rsget.py is a small script to download links from rapidshare.com. It features
a really nice progress bar.

    Usage: rsget.py [options] LINK LINKLIST ...

    Options:
      -d DIR            destination directory
      -u LOGIN          rapidshare login as 'user:passwd'
      -s, --save-login  save login data to ~/.rsget.py
      -c, --check-sum   check md5sum of downloads
      -h, --help        show this help message and exit