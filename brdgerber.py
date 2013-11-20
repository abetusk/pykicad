#!/usr/bin/python
#
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
Loads KiCAD brd file (pcb(new?) file), parses it with brd.py, writes to gerber format.
"""

import re
import sys
import os
import lib
import math
import numpy
import cgi
import urllib

import json

import brd
import brdjson
import pygerber

class brdgerber(brdjson.brdjson):

  def __init__(self):
    brdjson.brdjson.__init__(self)
    self._apertureName = 10
    self._id = 1
    self.apertureIdMap = {}
    self.apertureTrack = {}

  def toUnit(self, v):
    return float(v) / 10000.0

  def genId(self):
    i  = self._id
    self._id+=1
    return i

  def genApertureName(self):
    an = self._apertureName
    self._apertureName += 1
    return str(an)


  def dump_json(self):
    print json.dumps( self.json_obj, indent=2 )


  def collect_apertures(self):

    width_set = {}
    for v in self.json_obj["element"]:

      if (v["type"] == "track") or (v["type"] == "drawsegment"):
        v["id"] = self.genId()
        width_key = "{0:011.5f}".format( float(v["width"]) )
        width_set[ width_key ] = float(v["width"])
      elif v["type"] == "module":

        for text in v["text"]:
          pass

        for art in v["art"]:
          if art["shape"] == "segment":
            pass
          elif art["shape"] == "circle":
            pass
          elif art["shape"] == "arc":
            pass
          elif art["shape"] == "polygon":
            pass

        for pad in v["pad"]:
          if pad["shape"] == "rectangle":
            pass
          elif pad["shape"] == "circle":
            pass
          elif pad["shape"] == "oblong":
            pass
          elif pad["shape"] == "trapeze":
            pass





    for width_key in width_set:
      an = self.genApertureName()
      ap = { "name" : an, "type" : "circle", "d" : self.toUnit(width_set[ width_key ])  }
      self.apertureTrack[ width_key ] = ap

  def dump_gerber(self):

    self.collect_apertures()

    grb = pygerber.pygerber()

    grb.mode( "IN" )
    grb.formatSpecification( 'L', 'A', 3, 4, 3, 4 )

    for width_key in self.apertureTrack:
      ap = self.apertureTrack[ width_key ]
      if ap["type"] == "circle":  grb.defineApertureCircle( ap["name"], ap["d"] )

    prev_x = None
    prev_y = None

    cur_x = None
    cur_y = None

    cur_ap = None

    for v in self.json_obj["element"]:
      if (v["type"] == "track") or (v["type"] == "drawsegment"):

        width_key = "{0:011.5f}".format( float(v["width"]) )

        ap_name = self.apertureTrack[ width_key ]["name"]

        if ap_name != cur_ap:
          cur_ap = ap_name
          grb.apertureSet( cur_ap )

        x = self.toUnit( v["x0"] )
        y = self.toUnit( v["y0"] )

        if (x != cur_x) or (y != cur_y):
          grb.moveTo( x, y )

        grb.lineTo( self.toUnit(v["x1"]), self.toUnit(v["y1"]) )
        cur_x = x
        cur_y = y

    grb.end()
    grb._print()


    #self.dump_json()

if __name__ == "__main__":

  infile = None

  if len(sys.argv) >= 2:
    infile = sys.argv[1]

  if infile is None:
    print "provide infile"
    sys.exit(0)

  b = brdgerber()

  b.parse_brd(infile)
  b.dump_gerber()

  #b.dump_json()


