#!/usr/bin/python

import re
import os
from subprocess import check_call

for lib_fn in os.listdir('library'):
  if re.search('\.lib$', lib_fn):
    print "converting:", lib_fn

    base = re.sub('\.lib$', '', lib_fn)

    check_call( ['mkdir', '-p', 'svg/' + base ] )
    check_call( ['mkdir', '-p', 'jpg/' + base ] )
    check_call( ['./libsvg.py', 'library/' + lib_fn, 'svg/' + base + "/" ] )

    for svg_fn in os.listdir('svg/' + base + '/'):
      jpeg_fn = re.sub('\.svg$', '.jpg', svg_fn)
      check_call( ['convert', 'svg/' + base + '/' + svg_fn, 'jpg/' + base + '/' + jpeg_fn ] )




