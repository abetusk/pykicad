#!/usr/bin/python

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
converts from bleepsix JSON KiCAD format to EESchema KiCAD format (V1?  V2?)
"""

import re
import sys
import math
import numpy
import json

class jsonsch:
  def __init__(self):
    pass


if __name__ == "__main__":

  infile = None
  outbase = None

  if len(sys.argv) >= 2:
    infile = sys.argv[1]

  if len(sys.argv) >= 3:
    outfile = sys.argv[2]


  if infile is None:
    print "provide infile"
    sys.exit(1)

  s = ""

  f = open( infile, "r" )
  for line in f:
    s += line
  f.close()

  json_data = json.loads(s)

  #print json_data

  libs = [ "power", "device", "transistors", "conn", "linear", "regul", "74xx", "cmos4000", "adc-dac", "memory", "xilinx", "special", "microcontrollers", "dsp", "microchip", "analog_switches", "motorola", "texas", "intel", "audio", "interface", "digital-audio", "philips", "display", "cypress", "siliconi", "opto", "atmel", "contrib", "valves", "net_test-cache" ]
  print "EESchema Schematic File Version 2"
  for lib in libs:
    print "LIBS:" + lib
  
  print "EELAYER 27 0"
  print "EELAYER END"

  print "$Descr A4 11693 8268"
  print "encoding utf-8"
  print "Sheet 1 1"
  print "Title \"\""
  print "Date \"30 nov 2013\""
  print "Rev \"\""
  print "Comp \"\""
  print "Comment1 \"\""
  print "Comment2 \"\""
  print "Comment3 \"\""
  print "Comment4 \"\""
  print "$EndDescr"

  eles = json_data["element"]
  for ele in eles:
    ele_type = ele["type"]
    if ele_type == "component":
      print "$Comp"
      print "L", ele["name"], ele["reference"]
      print "U", ele["nn"], ele["mm"], ele["timestamp"]
      print "P", ele["x"], ele["y"]

      for text in ele["text"]:
        print "F", text["number"], "\"" + text["text"] + "\"", text["orientation"], text["x"], text["y"], text["size"], text["flags"] 
      transform = ele["transform"]
      print "       ", str(1).ljust(4), str(ele["x"]).ljust(4), str(ele["y"]).ljust(4)
      print "       ", str(transform[0][0]).ljust(4), str(transform[0][1]).ljust(4), str(transform[1][0]).ljust(4), str(transform[1][1]).ljust(4)
      print "$EndComp"

    elif ele_type == "wireline":
      print "Wire Wire Line"
      print "       ", ele["startx"], ele["starty"], ele["endx"], ele["endy"]
    elif ele_type == "connection":
      print "Connection ~", ele["x"], ele["y"]
    elif ele_type == "noconn":
      print "NoConn ~", ele["x"], ele["y"]

  print "$EndSCHEMATIC"


