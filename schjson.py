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
Loads KiCAD sch file (schematic file), parses it with sch.py, writes to json format.
"""


import re
import sys
import math
import numpy
import cgi
import urllib

import json

import sch

class schjson(sch.sch):
  def __init__(self):
    self.first = True

    self.json_file = ""
    self.json_prefix = "./"
    self.json_suffix = ".json"

    self.counter = 0

    self.bounding_box = [ [0,0], [0, 0] ]

    self.json_obj = {}
    self.json_obj["element"] = []
#    self.json_obj = {}
#    self.json_obj["line"] = []
#    self.json_obj["connection"] = []
#    self.json_obj["noconnect"] = []
#    self.json_obj["component"] = []
#    self.json_obj["header"] = None

    self.cur_component = {}

    sch.sch.__init__(self)

  def cb_END(self, args):

    print json.dumps( self.json_obj, indent=2 )


  def cb_descr_encoding(self, args):
    encoding_type = args
    self.json_obj["encoding"] = encoding_type

  def cb_comp(self, args):
    self.cur_component = {}
    self.cur_component["text"] = []
    self.cur_component["transform"] = [ [ 1, 0], [0, 1] ]
    self.cur_component["type"] = "component"

  def cb_comp_L(self, args):
    name, reference = args

    self.cur_component["name"]       = name
    self.cur_component["reference"]  = reference

  def cb_comp_U(self, args):
    nn, mm, ts = args
    self.cur_component["nn"] = nn
    self.cur_component["mm"] = mm
    self.cur_component["timestamp"] = ts


  def cb_comp_P(self, args):
    posx, posy = args
    self.cur_component["x"] = posx
    self.cur_component["y"] = posy

  def cb_comp_F(self, args):
    field_number, text, dummy, orientation, posx, posy, size, flags = args

    munged_text = text.strip()
    munged_text = re.sub( '^\"', '', munged_text )
    munged_text = re.sub( '\"$', '', munged_text )

    munged_flags = flags.strip()

    F = {}
    F["number"] = field_number;
    #F["text"] = text
    F["text"] = munged_text
    F["orientation"] = orientation
    F["x"] = posx
    F["y"] = posy
    F["size"] = size
    #F["flags"] = flags
    F["flags"] = munged_flags

    if munged_flags:
      F["visible"] = True
      if re.search("^0*1", munged_flags):
        F["visible"] = False

      g = re.search("([01])*\s*([LRCBT])\s*([LRCBT])([IN])?([BN])?", munged_flags);
      if g:
        F["hjustify"] = g.group(2)
        F["vjustify"] = g.group(3)

        F["italic"] = False
        F["bold"] = False

        if g.group(4) == "I":
          F["italic"] = True
        if g.group(5) == "B":
          F["bold"] = True

    self.cur_component["text"].append( F )

  def cb_comp_matrix(self, args):
    x00, x01, x10, x11 = args

    self.cur_component["transform"][0][0] = x00
    self.cur_component["transform"][0][1] = x01
    self.cur_component["transform"][1][0] = x10
    self.cur_component["transform"][1][1] = x11

  def cb_comp_end(self, args):
    #self.json_obj["component"].append( self.cur_component )
    self.json_obj["element"].append( self.cur_component )
    self.cur_component = {}


  def cb_noconn(self, args):
    posx, posy = args
    #self.json_obj["noconnect"].append( { "x" : posx, "y" : posy } )
    self.json_obj["element"].append( { "type" : "noconn", "x" : posx, "y" : posy } )

  def cb_connection(self, args):
    posx, posy = args
    #self.json_obj["connection"].append( { "x" : posx, "y" : posy } )
    self.json_obj["element"].append( { "type" : "connection", "x" : posx, "y" : posy } )

  def cb_wireline_segment(self, args):
    startx, starty, endx, endy = args
    #self.json_obj["line"].append( { "type" : "wireline", "startx" : startx, "starty" : starty, "endx" : endx, "endy" : endy } )
    self.json_obj["element"].append( { "type" : "wireline", "startx" : startx, "starty" : starty, "endx" : endx, "endy" : endy } )

  def cb_busline_segment(self, args):
    startx, starty, endx, endy = args
    #self.json_obj["line"].append( { "type" : "busline", "startx" : startx, "starty" : starty, "endx" : endx, "endy" : endy } )
    self.json_obj["element"].append( { "type" : "busline", "startx" : startx, "starty" : starty, "endx" : endx, "endy" : endy } )

  def cb_notesline_segment(self, args):
    startx, starty, endx, endy = args
    #self.json_obj["line"].append( { "type" : "notesline", "startx" : startx, "starty" : starty, "endx" : endx, "endy" : endy } )
    self.json_obj["element"].append( { "type" : "notesline", "startx" : startx, "starty" : starty, "endx" : endx, "endy" : endy } )

  def cb_wirebus_segment(self, args):
    startx, starty, endx, endy = args
    #self.json_obj["line"].append( { "type" : "wirebus", "startx" : startx, "starty" : starty, "endx" : endx, "endy" : endy } )
    self.json_obj["element"].append( { "type" : "wirebus", "startx" : startx, "starty" : starty, "endx" : endx, "endy" : endy } )

  def cb_busbus_segment(self, args):
    startx, starty, endx, endy = args
    #self.json_obj["line"].append( { "type" : "busbus", "startx" : startx, "starty" : starty, "endx" : endx, "endy" : endy } )
    self.json_obj["element"].append( { "type" : "busbus", "startx" : startx, "starty" : starty, "endx" : endx, "endy" : endy } )

  def cb_entrywirebus_segment(self, args):
    startx, starty, endx, endy = args
    #self.json_obj["line"].append( { "type" : "entrywirebus", "startx" : startx, "starty" : starty, "endx" : endx, "endy" : endy } )
    self.json_obj["element"].append( { "type" : "entrywirebus", "startx" : startx, "starty" : starty, "endx" : endx, "endy" : endy } )

  def cb_entrybusbus_segment(self, args):
    startx, starty, endx, endy = args
    #self.json_obj["line"].append( { "type" : "entrybusbus", "startx" : startx, "starty" : starty, "endx" : endx, "endy" : endy } )
    self.json_obj["element"].append( { "type" : "entrybusbus", "startx" : startx, "starty" : starty, "endx" : endx, "endy" : endy } )

  def cb_entrywireline_segment(self, args):
    startx, starty, endx, endy = args
    #self.json_obj["line"].append( { "type" : "entrywireline", "startx" : startx, "starty" : starty, "endx" : endx, "endy" : endy } )
    self.json_obj["element"].append( { "type" : "entrywireline", "startx" : startx, "starty" : starty, "endx" : endx, "endy" : endy } )




if __name__ == "__main__":

  infile = None
  outbase = None

  if len(sys.argv) >= 2:
    infile = sys.argv[1]

  if len(sys.argv) >= 3:
    outbase = sys.argv[2]


  if infile is None:
    print "provide infile"
    sys.exit(0)

  s = schjson()

  if outbase is not None:
    s.json_prefix = outbase

  s.parse_sch(infile)

