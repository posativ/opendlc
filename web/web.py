#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright 2011 posativ <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses
#
# web.py is a webserver using bottle.py. It is intended, to use another
# webserver as proxy for this. lighttpd setup (using mod_proxy):
# $HTTP["url"] =~ "/decrypt/" {
#     proxy.server = ("" =>
#         (("host" => "127.0.0.1", "port" => 8000)))
# 
# }

import sys
sys.path.append('../')

from bottle import route, run, post, request, response

#import bottle
#bottle.debug(True)

from decrypt import rsdf, dlc, ccf
from xml.etree.ElementTree import fromstring

# the template file
tt = open('main.html').read()

# key file's layout: `APPKEY:IV:APPNAME` -> e.g. `acf...23f:2c...fd:jdsuck`
key, iv, name = [k.strip() for k in open('../keys').readline().split(':')]

@post('/decrypt/:container')
def decrypt(container=None):
    '''handles every supported decrypt/(.+) container'''
    
    response.headers['Content-Type'] = 'text/plain'
    
    data = request.files.get('file', None)
    if data != None:
        data.file.seek(0, 2)
        size = data.file.tell()
        if size > 2**20: # 1 MiB file limit
            return ''
        data.file.seek(0)
        data = data.file.read()
    else:
        data = request.forms.get('data', '')
    if container == 'rsdf':
        try:
            return '\n'.join(rsdf.decrypt(data))
        except TypeError:
            return 'unable to decrypt RSDF'
        
    elif container == 'dlc':
        try:
            data = dlc.decrypt(data, key, iv, name)
        except TypeError:
            return 'unable to decrypt DLC'
        el = fromstring(''.join(dlc.Debase(data).result))
        return '\n'.join([item.find('url').text for item in el.getiterator('file')])
    elif container == 'ccf':
        try:
            data = ccf.decrypt(data)
        except:
            # we fully rely on service.jdownloader.org, everything can happen...
            return 'service failure'
        data = dlc.decrypt(data, key, iv, name)
        el = fromstring(''.join(dlc.Debase(data).result))
        return '\n'.join([item.find('url').text for item in el.getiterator('file')])

@route('/decrypt/')
def index():
    return tt
    
if __name__ == '__main__':
    # starts bottle
    run(host='localhost', port=8000)