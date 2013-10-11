#!/usr/bin/python

import re
import os
from subprocess import check_call
import sys
import urllib

for lib_fn in os.listdir('library'):

  print lib_fn

  if re.search('\.lib$', lib_fn):
    print "converting:", lib_fn

    base = re.sub('\.lib$', '', lib_fn)

    odn = urllib.quote( 'eeschema/json/' + base + '/' )

    check_call( ['mkdir', '-p', odn ] )
    check_call( ['./libjson.py', 'library/' + lib_fn, odn ] )


