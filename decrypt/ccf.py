#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright 2011 posativ <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses

import sys; reload(sys); sys.setdefaultencoding('utf-8')

import httplib
import mimetypes
import mimetools

def decrypt(ccf):
    
    ## {{{ http://code.activestate.com/recipes/146306-http-client-to-post-using-multipartform-data/#c3
    def post_multipart(host, selector, fields, files):
        content_type, body = encode_multipart_formdata(fields, files)
        h = httplib.HTTPConnection(host)
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': content_type
            }
        h.request('POST', selector, body, headers)
        res = h.getresponse()
        return res.status, res.reason, res.read()
    ## end of commented extension}}}

    ## {{{ http://code.activestate.com/recipes/146306/ (r1)
    def encode_multipart_formdata(fields, files):
        """
        fields is a sequence of (name, value) elements for regular form fields.
        files is a sequence of (name, filename, value) elements for data to be uploaded as files
        Return (content_type, body) ready for httplib.HTTP instance
        """
        BOUNDARY = mimetools.choose_boundary()
        CRLF = '\r\n'
        L = []
        for (key, value) in fields:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"' % key)
            L.append('')
            L.append(value)
        for (key, filename, value) in files:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            L.append('Content-Type: %s' % get_content_type(filename))
            L.append('')
            L.append(value)
        L.append('--' + BOUNDARY + '--')
        L.append('')
        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
        return content_type, body

    def get_content_type(filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    ## end of http://code.activestate.com/recipes/146306/ }}}

    host, uri = 'service.jdownloader.net', '/dlcrypt/getDLC.php'
    code, reason, data = post_multipart(host, uri,
            [('src', 'ccf'), ('filename', 'test.ccf')],
            [('upload', '../test/test.ccf', ccf)])
    x = data.find('<dlc>')
    return data[x+5:-6]
    
if __name__ == '__main__':
    
    from optparse import OptionParser, make_option
    
    options = [
        make_option('-d', '--decrypt', dest='decrypt', action='store_true',
                    help="decrypt resulting dlc", default=False),
        make_option('-k', '--key', dest='key', metavar='str',
                    help="-d application key"),
        make_option('-v', '--iv', dest='iv', metavar='str',
                    help="-d application's IV"),
        make_option('-n', '--name', dest='name', metavar='str',
                    help="-d application name, e.g. %s" % ', '.join(['pylo', 'load', 'rsdc'])),
    ]
    
    descr = ("ccf.py currently provides an interface to service.jdownload.org"
             ", allows you to decrypt CCF to DLC (crap to crap conversion)")
    
    parser = OptionParser(option_list=options, description=descr,
        usage="usage: %prog [options] FILE")
    options, args = parser.parse_args()
    
    if len(args) != 1:
        parser.print_usage()
        sys.exit(2)
        
    data = decrypt(ccf=open(args[0]).read())
        
    if not options.decrypt:
        print data
    else:
        if not (options.key or options.iv or options.name):
            print '-d only works with supplied DLC decryption args, see dlc.py'
            sys.exit(1)
        try:
            import dlc
        except ImportError:
            print 'error, dlc.py not found'
            sys.exit(1)
        
        from xml.etree.ElementTree import fromstring    
        data = dlc.decrypt(data, options.key, options.iv, options.name)
        el = fromstring(''.join(dlc.Debase(data).result))
        for item in el.getiterator('file'):
            print item.find('url').text