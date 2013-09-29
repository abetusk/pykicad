#!/usr/bin/python

import re
import os
from subprocess import check_call
import sys

for lib_fn in os.listdir('library'):
  if re.search('\.lib$', lib_fn):
    print "converting:", lib_fn

    base = re.sub('\.lib$', '', lib_fn)

    check_call( ['mkdir', '-p', 'eeschema/svg/' + base ] )
    check_call( ['mkdir', '-p', 'eeschema/jpg/' + base ] )
    check_call( ['./libsvg.py', 'library/' + lib_fn, 'eeschema/svg/' + base + "/" ] )

    for svg_fn in os.listdir('eeschema/svg/' + base + '/'):
      jpeg_fn = re.sub('\.svg$', '.jpg', svg_fn)
      check_call( ['convert', 'eeschema/svg/' + base + '/' + svg_fn, 'eeschema/jpg/' + base + '/' + jpeg_fn ] )




