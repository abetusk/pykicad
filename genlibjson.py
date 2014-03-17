#!/usr/bin/python

import re
import os
from subprocess import check_call
import sys
import urllib

libdir = "library"
#libdir = "thirdparty"

for lib_fn in os.listdir( libdir ):

  if re.search('\.lib$', lib_fn):
    print "converting:", lib_fn

    base = re.sub('\.lib$', '', lib_fn)


    odn = urllib.quote( 'eeschema/json/' + base + '/' )

    check_call( ['mkdir', '-p', odn ] )
    check_call( ['./libjson.py', libdir + "/"  + lib_fn, odn ] )


