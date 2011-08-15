#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright 2011 posativ <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses

import sys
sys.path.append('../')

import bottle
from bottle import route, run, post, request, response
#from jinja2 import Template

#bottle.debug(True)

import rsdf, dlc
from xml.etree.ElementTree import fromstring

tt = open('main.html').read()

@post('/decrypt/:container')
def decrypt(container=None):
    
    response.headers['Content-Type'] = 'text/plain'
    
    data = request.forms.get('data')
    if container == 'rsdf':
        return '\n'.join(rsdf.decrypt(data))
    elif container == 'dlc':
        try:
            data = dlc.decrypt(data)
        except TypeError:
            return 'unable to decrypt DLC'
        el = fromstring(''.join(dlc.Debase(data).result))
        return '\n'.join([item.find('url').text for item in el.iter('file')])

@route('/decrypt/')
def index():
    #tt = Template(open('main.html').read())
    return tt

run(host='localhost', port=8000)