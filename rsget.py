#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright 2011 posativ <info@posativ.org>. All rights reserved.
# 
# terminal width aware: http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python/943921#943921
#
# rsget.py is a small python utility, to download (and verify) files from
# rapidshare.com as premium user.

import sys, os

from os.path import isfile, isdir, expanduser, join
from urllib import urlretrieve, urlopen, urlencode
from time import time
from collections import defaultdict
from hashlib import md5

# a quick and dirty hack to store values for progress bar
TD = defaultdict(int)

class ConnectionError(Exception): pass
class FileNotFound(Exception): pass
class InvalidURL(Exception): pass
class FileCorruptError(Exception): pass
class UnknownError(Exception): pass


def ppsize(num, fmt='%3.1f'):
    '''pretty-print filesize.
    http://blogmag.net/blog/read/38/Print_human_readable_file_size'''
    for x in ['B','KB','MB','GB','TB']:
        if num < 1024.0:
            return fmt % num + ' ' + x
        num /= 1024.0


def checkfiles(*links, **options):
    """check if a given bunch of links is online.  Refuses if request url is
    longer than 10000 bytes, we split them into parts, then."""
    
    def check(links):
        """check if bunch of links is online.  Returns True of everything's ok
        else False and print to stderr which link is offline.
        """
        response = urlopen('https://api.rapidshare.com/cgi-bin/rsapi.cgi?sub=checkfiles&' \
                   + urlencode({'files': ','.join([x[0] for x in links]), 
                                'filenames': ','.join([x[1] for x in links])})).read()
        if response.find('ERROR') > -1:
            raise UnknownError
            
        everythingok = True
        for line in response.split('\n'):
            if not line.strip():
                continue
            fileid, filename, size, spam = line.strip().split(',', 3)
            if int(size) == 0:
                print >> sys.stderr, '../' + fileid + '/' + filename, 'is offline'
                if everythingok:
                    everythingok = False
        return everythingok
    
    _links = [tuple(l.strip().rsplit('/', 2)[1:]) for l in links][::-1]
    bunch, length = [], 0
    isonline = True
    
    while True:
        fileid, filename = _links.pop()
        length += len(fileid) + len(filename)
        bunch.append((fileid, filename))
        if length > 7800 or not _links: # just to be safe, we have some overhead
            try:
                if not check(bunch):
                    isonline = False
            except UnknownError:
                if not options.get('ignore', False):
                    print >> sys.stderr, 'failed to check links'
                    sys.exit(1)
            if not _links:
                break
            bunch, length = [], 0
    
    return isonline


def download(link, user, passwd, **kwargs):
    """downloads a link using rapidshare premium account and displaying
    a neat progress bar."""
    
    def progress(count, blocksize, length):
        """realtime urlretrieve progress bar.  Something like this
        [=============134.7/247.8 MB=>           ] 137 kb/sec"""
    
        global TD
        TD['count'] += blocksize
        if TD['delta'] >= 0.5:
            columns = int(os.popen('stty size', 'r').read().split()[1]) - 18
            if columns % 2 == 1:
                columns -= 1
            p = int(round((1.0*(count*blocksize)/length)*columns))

            def f(p):
                '''indicator before counting information'''
                if p < (columns/2 - 7):
                    return ' '
                elif p == (columns/2 - 7) or p == (columns/2 + 7):
                    return '>'
                else:
                    return '='
        
            g = lambda p: '=' if p == columns else '>'
        
            line = [
                '\r[',
                ('='*p + g(p)).ljust(columns/2 - 7) if p < (columns/2 - 7) else '='*(columns/2 - 7),
                ppsize(count*blocksize)[:-3].rjust(5, f(p)) + '/' + ppsize(length).ljust(8, f(p)),
                ' '*(columns/2 - 7) if p <= (columns/2 + 7) else ('='*(p-(columns/2+7)-1)+g(p)).ljust(columns/2 - 7),
                ']',
                ' '*6 + ppsize(2*TD['count'], '%3i').ljust(3) + '/sec'
            ]
        
            sys.stdout.write(''.join(line))
            sys.stdout.flush()
            TD['delta'] = 0
            TD['count'] = 0
    
        TD['delta'] += time() - TD['time']
        TD['time'] = time()    
    
    if not link.startswith('http'):
        raise InvalidURL
    
    try:
        spam, fileid, filename = link.strip().rsplit('/', 2)
    except ValueError:
        raise InvalidURL
    
    # something like DL:rs916tl4.rapidshare.com,0,0,5FC2DB0E02A42FC54ECA5C9392AFCDC0
    status = urlopen('https://api.rapidshare.com/cgi-bin/rsapi.cgi?sub=download&' \
                + urlencode({'fileid': fileid, 'filename': filename, 'login': user, 'password': passwd})).read()
    if status.find('File not found') > -1:
        raise FileNotFound
    elif status.find('ERROR') > -1:
        raise UnknownError(status)
    
    host, auth, countdown, md5sum = status[3:].split(',')
    url = 'https://' + host + '/cgi-bin/rsapi.cgi?sub=download&' \
          + urlencode({'fileid': fileid, 'filename': filename, 'login': user, 'password': passwd})
    timestamp = time() # get time spend on downloading each link
    urlretrieve(url, join(options.dir, filename), reporthook=progress)
    sys.stdout.write('\r' + ' '*int(os.popen('stty size', 'r').read().split()[1]))
    
    if kwargs.get('checksum', False):
        f = open(filename)
        h = md5()
        while True:
            chunks = f.read(2048)
            if chunks:
                h.update(chunks)
            else:
                break
        if h.hexdigest() != md5sum.lower():
            raise FileCorruptError
    
    sys.stdout.write("\rdownloaded '%s' in %2.1f secs\n" % (filename[-32:], (time() - timestamp)))


if __name__ == '__main__':
    
    from optparse import OptionParser, make_option
    
    usage = '%prog [options] LINK LINKLIST ...'
    
    options = [
        make_option("-d",dest="dir", metavar="DIR", help="destination directory",
                    default=''),
        make_option("-u", dest="login", default=None,
                    help="rapidshare login as 'user:passwd'"),
        make_option("-s", "--save-login", dest="save", action='store_true',
                    help="save login data to ~/.rsget.py", default=False),
        make_option("-c", "--check-sum", dest="checksum", action='store_true',
                    help="check md5sum of downloads", default=False),
        make_option("-i", "--ignore", dest="ignore", action='store_true',
                    help="ignore errors on checkfiles", default=False)
        ]
        
    parser = OptionParser(option_list=options, usage=usage)
    (options, args) = parser.parse_args()
    
    if options.login:
        user, passwd = options.login.split(':', 1)
        if options.save:
            open(expanduser('~/.rsget.py'), 'w').write(options.login)
    elif isfile(expanduser('~/.rsget.py')):
        user, passwd = open(expanduser('~/.rsget.py')).readline().split(':', 1)
    else:
        print >> sys.stderr, 'no login credentials commited, existing...'
        sys.exit(1)
    
    if options.dir:
        options.dir = expanduser(options.dir)
        if not isdir(options.dir):
            print >> sys.stderr, "'%s' is no valid directory" % options.dir
    
    links = []
    for item in args:
        if isfile(item):
            links += [l.strip() for l in open(item).readlines()]
        else:
            links.append(item)
    
    if not links:
        parser.print_usage()
        sys.exit(1)
            
    if not checkfiles(*links, ignore=options.ignore) and not options.ignore:
        query = raw_input('continue [y/n]? ') == 'n'
        if query == 'n':
            sys.exit(0)
            
    for link in links:
        try:
            download(link, user, passwd, **{'checksum': options.checksum,
                        'dir': options.dir})
        except InvalidURL:
            print >> sys.stderr, "'%s' is no valid url, skipping..." % link
        except FileNotFound:
            print >> sys.stderr, "'%s' file not found, skipping..." % link.rsplit('/', 1)[-1]
        except FileCorruptError:
            try:
                download(link, user, passwd, **{'checksum': options.checksum,
                        'dir': options.dir})
            except FileCorruptError:
                print "\rchecksum mismatch of '%s', skipping..." % link.rsplit('/', 1)[-1][-32:]
        except UnknownError, e:
            print e
