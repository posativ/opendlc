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

from os.path import isfile, expanduser
from urllib import urlretrieve, urlopen, urlencode
from time import time
from collections import defaultdict
from hashlib import md5

TD = defaultdict(int)

class ConnectionError(Exception): pass
class FileNotFound(Exception): pass
class InvalidURL(Exception): pass
class FileCorruptError(Exception): pass
#class NoSimultaneousDownloads(Exception): pass
#class DownloadLimit(Exception): pass
#class Timeout(Exception): pass
class UnknownError(Exception): pass


def ppsize(num):
    '''pretty-print filesize.
    http://blogmag.net/blog/read/38/Print_human_readable_file_size'''
    for x in ['B','KB','MB','GB','TB']:
        if num < 1024.0:
            return "%3i %s" % (num, x + '/sec')
        num /= 1024.0


def download(link, user, passwd, **kwargs):
    
    def progress(count, blocksize, length):
        """realtime urlretrieve progress bar.  """
        
        global TD
        TD['count'] += blocksize
        if TD['delta'] >= 0.5:
            # progress bar
            # [>] + 4 spaces + ppsize + 1 empty
            columns = int(os.popen('stty size', 'r').read().split()[1]) - 18
            p = int(round((1.0*(count*blocksize)/length)*columns))
            sys.stdout.write('\r[' + '='*p + '>' + ' '*(columns-p) + ']    ' + ppsize(TD['count']))
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
    urlretrieve(url, filename, reporthook=progress)
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
        make_option("-d",dest="dir", metavar="DIR", help="destination directory"),
        make_option("-u", dest="login", default=None,
                    help="rapidshare login as 'user:passwd'"),
        make_option("-s", "--save-login", dest="save", action='store_true',
                    help="save login data to ~/.rsget.py", default=False),
        make_option("-c", "--check-sum", dest="checksum", action='store_true',
                    help="check md5sum of downloads", default=False)
        ]
        
    parser = OptionParser(option_list=options, usage=usage)
    (options, args) = parser.parse_args()
    
    if options.login:
        user, passwd = options.login.split(':', 1)
        if options.save:
            open('%s/.rsget.py' % expanduser('~'), 'w').write(options.login)
    elif isfile('%s/.rsget.py' % expanduser('~')):
        user, passwd = open('%s/.rsget.py' % expanduser('~')).readline().split(':', 1)
    else:
        print >> sys.stderr, 'no login credentials commited, existing...'
        sys.exit(1)
    
    links = []
    for item in args:
        if isfile(item):
            links += [l.strip() for l in open(item).readlines()]
        else:
            links.append(item)
            
    for link in links:
        try:
            download(link, user, passwd, **{'checksum': options.checksum})
        except InvalidURL:
            print >> sys.stderr, "'%s' is no valid url, skipping..." % link
        except FileNotFound:
            print >> sys.stderr, "'%s' file not found, skipping..." % link.rsplit('/', 1)[-1]
        except FileCorruptError:
            try:
                download(link, user, passwd, **{'checksum': options.checksum})
            except FileCorruptError:
                print "\rchecksum mismatch of '%s', skipping..." % link.rsplit('/', 1)[-1][-32:]
        except UnknownError, e:
            print e
