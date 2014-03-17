#!/usr/bin/python

import re
import os
from subprocess import check_call
import sys
import urllib

moddir = "modules"
#moddir = "thirdparty"

for mod_fn in os.listdir( moddir ):
  
  if re.search('\.mod$', mod_fn):
    print "converting:", mod_fn

    base = re.sub('\.mod', '', mod_fn)
    odn = urllib.quote( 'pcb/json/' + base + '/' )
    check_call( [ 'mkdir', '-p', odn ] )
    check_call( ['./modjson.py', moddir + '/' + mod_fn, odn] )

