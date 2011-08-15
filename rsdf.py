#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# via http://wiki.ubuntuusers.de/Tuxload -> http://board.gulli.com/thread/865191-ccd-und-rsdf-files-unter-mac/#25
# License: BSD Style, 2 clauses

import sys; reload(sys); sys.setdefaultencoding('utf-8')

import binascii
import base64
from Crypto.Cipher import AES

def decrypt(rsdf):

    key = binascii.unhexlify('8C35192D964DC3182C6F84F3252239EB4A320D2500000000')

    iv = binascii.unhexlify('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')
    IV_Cipher = AES.new(key, AES.MODE_ECB)
    iv = IV_Cipher.encrypt(iv)
    
    aes = AES.new(key, AES.MODE_CFB, iv)
    
    data = binascii.unhexlify(''.join(rsdf.split())).splitlines()
    
    urls = []
    
    for link in data:
        link = base64.b64decode(link)
        link = aes.decrypt(link)
        link = link.replace('CCF: ','')
        urls.append(link)
        
    return urls
    
if __name__ == '__main__':
    
    if len(sys.argv) != 2:
        print 'usage: python %s FILE'
        sys.exit(2)
    
    for link in decrypt(open(sys.argv[1]).read()):
        print link