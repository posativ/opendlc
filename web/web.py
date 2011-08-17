#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright 2011 posativ <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses

import sys
sys.path.append('../')

import bottle
from bottle import route, run, post, request, response

bottle.debug(True)

from decrypt import rsdf, dlc, ccf
from xml.etree.ElementTree import fromstring

tt = open('main.html').read()
key, iv, name = [k.strip() for k in open('../keys').read().split(':')]

@post('/decrypt/:container')
def decrypt(container=None):
    
    response.headers['Content-Type'] = 'text/plain'
    
    data = request.files.get('file', None)
    if data != None:
        data.file.seek(0, 2)
        size = data.file.tell()
        if size > 2**20: # 1 MiB
            return ''
        data.file.seek(0)
        data = data.file.read()
    else:
        data = request.forms.get('data', '')
    
    if container == 'rsdf':
        return '\n'.join(rsdf.decrypt(data))
    elif container == 'dlc':
        try:
            data = dlc.decrypt(data, key, iv, name)
        except TypeError:
            return 'unable to decrypt DLC'
        el = fromstring(''.join(dlc.Debase(data).result))
        return '\n'.join([item.find('url').text for item in el.iter('file')])
    elif container == 'ccf':
        try:
            data = ccf.decrypt(data)
        except:
            return 'service failure'
        data = dlc.decrypt(data, key, iv, name)
        el = fromstring(''.join(dlc.Debase(data).result))
        return '\n'.join([item.find('url').text for item in el.iter('file')])

@route('/decrypt/')
def index():
    #tt = Template(open('main.html').read())
    return tt

run(host='localhost', port=8000)