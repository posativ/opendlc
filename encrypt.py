#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright 2011 posativ <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses. see lilith.py
#
# Usage: python encrypt.py DLC-file
#
# Offene Implementierung einer DLC Decryption. DLC (Download Link Container)
# basiert auf einer server-seitigen Verschlüsselung, d.h. es ist unmgöglich,
# einen Container lokal zu entschlüsseln. Vom jDownloader-Team werden API-Keys
# an alternative Download-Manager ausgegeben, die notfalls geblacklistet
# werden können, sofern ein Missbrauch (massenhafte Entschlüsslung zum Melden
# von Links) vorliegt.
#
# Based on pyload/module/plugins/container/DLC_27.pyc –– using [uncompyle][1]
#
# [1]: https://github.com/sysfrog/uncompyle/
# 
# TODO: cleanup obfuscation

import sys; reload(sys); sys.setdefaultencoding('utf-8')

import base64, re
from Crypto.Cipher import AES
import urllib2

__name__ = 'DLC'

enc = [293, 492, 867, 1038, 162, 364, 802, 955, 145, 255, 116, 315, 327, 437, 562, 726, 721, 871, 566, 673, 763, 870, 560, 773, 863, 1014, 866, 1017, 698, 850, 659, 820, 978, 1177, 265, 436, 110, 264, 575, 683, 417, 522, 669, 868, 457, 610, 255, 467, 974, 1124, 225, 336, 671, 776, 708, 922, 469, 578, 531, 682, 922, 1032, 172, 327]
eurl = [524, 725, 932, 1097, 656, 824, 250, 486, 580, 813, 651, 807, 611, 842, 792, 988, 18, 129, 862, 1073, 907, 1051, 73, 238, 412, 577, 150, 319, 549, 716, 817, 973, 661, 859, 948, 1111, 981, 1147, 965, 1146, 828, 1063, 973, 1139, 363, 587, 508, 719, 578, 730, 978, 1187, 731, 929, 179, 382, 828, 992, 712, 890, 560, 718, 100, 264, 557, 754, 118, 270, 136, 299, 268, 447, 428, 664, 234, 385, 713, 942, 739, 944, 717, 878, 476, 685, 998, 1206, 779, 936, 511, 726, 623, 780, 409, 561, 54, 207, 846, 1044, 78, 244, 431, 597, 655, 889, 246, 409, 847, 982, 443, 673, 521, 739, 723, 890, 249, 471, 597, 797, 875, 1095, 372, 537, 856, 974, 960, 1112, 546, 710, 913, 1118, 90, 262, 750, 901, 886, 1112, 910, 1141, 56, 218, 662, 902, 970, 1105, 61, 226, 466, 676, 964, 1177, 3, 219, 338, 503, 471, 644, 342, 509, 457, 606, 184, 382, 67, 179]

api = 'http://service.jdownloader.org/dlcrypt/service.php?srcType=dlc&destType=pylo&data='

sab = 'drh75d5r476r456h'
sabsch = 'a34vu3wa5nawv944'

urlopen = urllib2.build_opener()
urlopen.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:5.0.1) Gecko/20100101 Firefox/5.0.1'),
                      ("Accept", "*/*"),
                      ("Accept-Language", "en-US,en"),
                      ("Accept-Charset", "ISO-8859-1,utf-8;q=0.7,*;q=0.7"),
                      ("Connection", "keep-alive"),
                      ("Keep-Alive", "300")]

def deobf(list1, keys):
    enc = list1
    t = 'r'
    rk = []
    es = []
    for c in enc:
        if t == 'r':
            rk.append(int(c))
            t = 's'
        else:
            es.append(int(c))
            t = 'r'

    ur = []
    for i in range(len(rk)):
        a = es[i] - rk[i]
        ur.append(a)

    d1 = []
    d2 = []
    t = 1
    key = 0
    f = int(len(ur) / len(keys)) + 1
    keys = keys * f
    for c in ur:
        k = ord(keys[key:(key + 1)])
        d = c - k
        d = chr(d)
        if t == 1:
            d1.append(d)
            t = 2
        else:
            d2.append(d)
            t = 1
        key += 1

    d1 = ''.join(d1)
    d2 = ''.join(d2)
    return (d1, d2)
    
def unbaseXML(data):

    data = re.sub('(<[^>]+>)(.+?)(</[^>]+>)',
            lambda x: x.group(1) + base64.standard_b64decode(x.group(2)) + x.group(3),
            data)
        
    return re.sub('([\w]+)="([^\"]+)"',
                 lambda x: x.group(1) + '="%s"' % base64.standard_b64decode(x.group(2)),
                 data)

if len(sys.argv) != 2:
    print 'usage: %s FILE' % sys.argv[0]
    sys.exit(1)

data = open(sys.argv[1], 'r').read().strip()

#print deobf(enc, sab)[0], deobf(enc, sab)[1]
obj = AES.new(deobf(enc, sab)[0], AES.MODE_CBC, deobf(enc, sab)[1])

dlckey = data[(-88):]
dlcdata = data[:(-88)]
dlcdata = base64.standard_b64decode(dlcdata)

#print ''.join(deobf(eurl, sabsch)) + dlckey
x = urlopen.open(''.join(deobf(eurl, sabsch)) + dlckey).read()
rc = re.search('<rc>(.+)</rc>', x).group(1)

rc = base64.standard_b64decode(rc)
dlckey = obj.decrypt(rc)
obj = AES.new(dlckey, AES.MODE_CBC, dlckey)
data = base64.standard_b64decode(obj.decrypt(dlcdata))

print unbaseXML(data)