#!/usr/bin/python

import re
import os
from subprocess import check_call
import sys

for dirname, dirnames, filenames in os.walk('modules'):

  for f in filenames:

    if not re.search('\.mod$', f) :
      continue 

    mod_fn = dirname + "/" + f

    print "converting:", mod_fn


    base = re.sub('\.mod$', '', mod_fn)
    base = re.sub('^modules\/?', '', base)

    check_call( ['mkdir', '-p', 'pcbnew/svg/' + base ] )
    check_call( ['mkdir', '-p', 'pcbnew/jpg/' + base ] )
    check_call( ['./modsvg.py', mod_fn, 'pcbnew/svg/' + base + '/' ] )

    for svg_fn in os.listdir('pcbnew/svg/' + base + '/'):
      jpeg_fn = re.sub('\.svg$', '.jpg', svg_fn)
      check_call( ['convert', 'pcbnew/svg/' + base + '/' + svg_fn, 'pcbnew/jpg/' + base + '/' + jpeg_fn ] )


