#!/usr/bin/python

import sys
import re
import argparse

package_type = "DIP"
n_pin = None

parser = argparse.ArgumentParser( description = "Generate SIL/DIP/QFP KiCAD schematic files" )

parser.add_argument("-t", "--type", help="Type of outline ( (SIL?|DIP?|QF?P), defaults to DIP)", nargs=1, default=[package_type] )
parser.add_argument("-n", "--n_pin", help="Number of pins", nargs=1, default=[n_pin], type=int, required=True)
parser.add_argument("-v", "--verbose", help='Set verbose mode', default=False, action="store_true")

args = parser.parse_args()
v_args = vars(parser.parse_args())

print v_args

if len(sys.argv)==1:
  parser.print_help()
  sys.exit(0)

if hasattr(args, "type"):
  print "package type:", args.type[0]

if hasattr(args, "n_pin"):
  print "n_pin", args.n_pin[0]
