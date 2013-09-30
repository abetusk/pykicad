#!/usr/bin/python

import re
import os
from subprocess import check_call
import sys

for mod_fn in os.listdir('modules'):
  if re.search('\.mod$', mod_fn):
    print "converting:", mod_fn

    base = re.sub('\.mod$', '', mod_fn)

    check_call( ['mkdir', '-p', 'pcbnew/svg/' + base ] )
    check_call( ['mkdir', '-p', 'pcbnew/jpg/' + base ] )
    check_call( ['./modsvg.py', 'modules/' + mod_fn, 'pcbnew/svg/' + base + '/' ] )

    for svg_fn in os.listdir('pcbnew/svg/' + base + '/'):
      jpeg_fn = re.sub('\.svg$', '.jpg', svg_fn)
      check_call( ['convert', 'pcbnew/svg/' + base + '/' + svg_fn, 'pcbnew/jpg/' + base + '/' + jpeg_fn ] )

for mod_fn in os.listdir('modules/contrib'):
  if re.search('\.mod$', mod_fn):
    print "converting contrib:", mod_fn

    base = re.sub('\.mod$', '', mod_fn)

    check_call( ['mkdir', '-p', 'pcbnew/svg/contrib/' + base ] )
    check_call( ['mkdir', '-p', 'pcbnew/jpg/contrib/' + base ] )
    check_call( ['./modsvg.py', 'modules/contrib/' + mod_fn, 'pcbnew/svg/contrib/' + base + '/' ] )

    for svg_fn in os.listdir('pcbnew/svg/contrib/' + base + '/'):
      jpeg_fn = re.sub('\.svg$', '.jpg', svg_fn)
      check_call( ['convert', 'pcbnew/svg/contrib/' + base + '/' + svg_fn, 'pcbnew/jpg/contrib/' + base + '/' + jpeg_fn ] )

