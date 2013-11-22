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

import math
import numpy as np

class brdgerber(brdjson.brdjson):

  def __init__(self):
    brdjson.brdjson.__init__(self)
    self._apertureName = 10
    self._id = 1
    self.apertureIdMap = {}
    self.apertureTrack = {}

    self.aperture = {}

    self.grb = pygerber.pygerber()

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

  def addAperture(self, ap_type, x, y ):

    x = float(x)
    y = float(y)

    ap_name = None

    if ap_type == "circle":
      pass

  def _R(self, rad_ang):
    return np.matrix( [ [ math.cos(rad_ang), -math.sin(rad_ang) ], [ math.sin(rad_ang), math.cos(rad_ang) ] ] )

  def _Rt(self, rad_ang):
    return np.matrix( [ [ math.cos(rad_ang), math.sin(rad_ang) ], [ -math.sin(rad_ang), math.cos(rad_ang) ] ] )


  def _rot(self, theta, u):
    return np.dot( self._R(theta), u )


  def dump_json(self):
    print json.dumps( self.json_obj, indent=2 )


  def first_pass(self):

    aperture_set = {}

    for v in self.json_obj["element"]:

      if (v["type"] == "track") or (v["type"] == "drawsegment"):
        v["id"] = self.genId()
        key = "circle:" + "{0:011.5f}".format( self.toUnit(v["width"]) )

        if key in aperture_set:
          ap_name = aperture_set[key]["aperture_name"]
          v["aperture_name"] = ap_name
          v["aperture_key"] = key
        else:
          aperture_set[ key ] = { "type" : "circle", "d" : self.toUnit(v["width"] ), "aperture_name" : self.genApertureName() }

      elif v["type"] == "module":


        for text in v["text"]:
          pass

        for art in v["art"]:
          if art["shape"] == "segment": pass
          elif art["shape"] == "circle": pass
          elif art["shape"] == "arc": pass
          elif art["shape"] == "polygon": pass
        for pad in v["pad"]:
          pad["id"] = self.genId()


          if   pad["shape"] == "rectangle":

            sx = self.toUnit( pad["sizex"] )
            sy = self.toUnit( pad["sizey"] )
            a = float( pad["angle"] )
            deg = int( round( math.degrees(a) ) )

            if (deg % 90) == 0:
              if (deg % 180) == 0:
                key = "rect:" + "{0:011.5f}".format(sx) + ":" + "{0:011.5f}".format(sy)

                if key not in aperture_set:
                  aperture_set[key] = { "type" : "rect", "x" : sx , "y" : sy, "aperture_name" : self.genApertureName() }
                ap_name = aperture_set[key]["aperture_name"]
                pad["aperture_name"] = ap_name
                pad["aperture_key"] = key

              else:
                key = "rect:" + "{0:011.5f}".format(sy) + ":" + "{0:011.5f}".format(sx)

                if key not in aperture_set:
                  aperture_set[key] = { "type" : "rect", "x" : sy , "y" : sx, "aperture_name" : self.genApertureName() }

                ap_name = aperture_set[key]["aperture_name"]
                pad["aperture_name"] = ap_name
                pad["aperture_key"] = key

            else:
              pass

          elif pad["shape"] == "circle":
            d = self.toUnit(pad["sizex"])
            key = "circle:" + "{0:011.5f}".format( d )

            if key not in aperture_set:
              aperture_set[key] = { "type" : "circle" , "d" : d, "aperture_name" : self.genApertureName() }

            ap_name = aperture_set[key]["aperture_name"]
            pad["aperture_name"] = ap_name
            pad["aperture_key"] = key

          elif pad["shape"] == "oblong":

            sx = self.toUnit( pad["sizex"] )
            sy = self.toUnit( pad["sizey"] )

            if sx > sy: d = sy
            else: d = sx

            key = "circle:" + "{0:011.5f}".format( d )

            if key not in aperture_set:
              aperture_set[key] = { "type" : "circle" , "d" : d, "aperture_name" : self.genApertureName() }

            ap_name = aperture_set[key]["aperture_name"]
            pad["aperture_name"] = ap_name
            pad["aperture_key"] = key

          elif pad["shape"] == "trapeze":
            pass

    ## end for json_obj
    self.aperture = aperture_set

    #for key in self.aperture:
    #  print key, self.aperture[key]


  def pad_circle(self, mod, pad):

    mod_x = self.toUnit( mod["x"] )
    mod_y = self.toUnit( mod["y"] )
    mod_a = float( mod["angle"] )

    x = self.toUnit( pad["posx"] )
    y = self.toUnit( pad["posy"] )

    v = self._rot( mod_a, [ x, y ] )

    key = pad["aperture_key"]
    ap = self.aperture[key]

    self.grb.apertureSet( ap["aperture_name"] )
    self.grb.flash( v[0,0] + mod_x , v[0,1] + mod_y )

  def pad_rectangle(self, mod, pad):

    mod_x = self.toUnit( mod["x"] )
    mod_y = self.toUnit( mod["y"] )
    mod_a = float( mod["angle"] )

    x = self.toUnit( pad["posx"] )
    y = self.toUnit( pad["posy"] )
    a = float( pad["angle"] )

    v = self._rot( mod_a, [ x, y ] )

    if "aperture_key" in pad:
      key = pad["aperture_key"]
      ap = self.aperture[key]

      self.grb.apertureSet( ap["aperture_name"] )
      self.grb.flash( v[0,0] + mod_x , v[0,1] + mod_y )

    else:

      pass


  def pad_oblong(self, pad):
    pass

  def pad_trapeze(self, pad):
    pass

  def second_pass(self):

    for v in self.json_obj["element"]:


      ele_type = v["type"]

      if ele_type == "module":

        for pad in v["pad"]:


          shape = pad["shape"]

          if shape == "circle": self.pad_circle(v, pad)
          elif shape == "rectangle": self.pad_rectangle(v, pad)
          elif shape == "oblong": self.pad_oblong(pad)
          elif shape == "trapeze": self.pad_trapeze(pad)





          shape = pad["shape"]

          if shape == "circle":
            pass





  def dump_gerber(self):

    self.first_pass()

    self.grb.mode("IN")
    self.grb.formatSpecification( 'L', 'A', 3, 4, 3, 4 )

    # define apertures
    for key in self.aperture:
      ap = self.aperture[key]
      typ = ap["type"] 
      nam = ap["aperture_name"]
      if typ == "rect":     self.grb.defineApertureRectangle( nam, ap["x"], ap["y"] )
      elif typ == "circle": self.grb.defineApertureCircle( nam, ap["d"] )


    self.second_pass()

    
    self.grb.end()
    self.grb._print()

    sys.exit(0)

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

        width_key = "{0:011.5f}".format( self.toUnit(v["width"]) )

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


