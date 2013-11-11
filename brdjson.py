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
Loads KiCAD brd file (pcb(new?) file), parses it with brd.py, writes to json format.
"""

import re
import sys
import os
import lib
import math
import numpy
import cgi
import urllib

import brd

import json

class brdjson(brd.brd):

  def clear_mod(self):
    self.cur_pad = {}
    self.cur_mod = { "pad" : [], "text" : [], "art": [] }



  def clear(self):

    self.json_obj = {}

    self.json_obj["units"] = "deci-mils"
    self.json_obj["element"] = []

    # equipot maps internal net name to textual net name
    #

    self.clear_mod()
    self.cur_segment = {}
    self.cur_track = {}


  def __init__(self):
    self.clear()

    self.units = "deci-thou"

    brd.brd.__init__(self)
    
  def decithou(self, x):
    if self.units == "mm":
      return 10000.0 * float(x) / 25.4
    return x

  def thou(self, x):
    if self.units == "mm":
      return 1000.0 * float(x) / 25.4
    return x

  def mm(self, x):
    if self.units == "mm":
      return x
    return float(x)*25.4


  def cb_header(self, arg):
    self.json_obj["header"] = arg[0].strip()


  def cb_track(self, arg):
    pass

  def cb_track_po(self, arg):
    shape_code,x0,y0,x1,y1,width,extra = arg
    self.cur_track["shape_code"] = shape_code

    sc = int(shape_code)
    if  (sc == 0):
      self.cur_track["shape"] = "track"
    if  (sc == 1):
      self.cur_track["shape"] = "buried"
    if  (sc == 2):
      self.cur_track["shape"] = "blind"
    if  (sc == 3):
      self.cur_track["shape"] = "through"

    self.cur_track["x0"] = x0
    self.cur_track["y0"] = y0
    self.cur_track["x1"] = x1
    self.cur_track["y1"] = y1
    self.cur_track["width"] =  width
    self.cur_track["extra"] = extra

  def cb_track_de(self, arg):
    layer,track_type, netcode, timestamp, status = arg
    self.cur_track["layer"] = layer
    self.cur_track["track"] = track_type
    self.cur_track["netcode"] = netcode
    self.cur_track["timestamp"] = timestamp
    self.cur_track["status"] = status

    self.cur_track["type"] = "track"

    #self.json_obj["track"].append( self.cur_track )
    self.json_obj["element"].append( self.cur_track )

    self.cur_track = {}

  def cb_track_end(self, arg):
    pass


  def cb_drawsegment(self, arg):
    pass

  def cb_drawsegment_po(self, arg):
    shape, x0, y0, x1, y1, width = arg
    self.cur_segment["shape"] = shape
    self.cur_segment["x0"] = x0
    self.cur_segment["y0"] = y0
    self.cur_segment["x1"] = x1
    self.cur_segment["y1"] = y1
    self.cur_segment["width"] = width

  def cb_drawsegment_de(self, arg):
    layer,shape_code,angle,timestamp,status = arg
    self.cur_segment["layer"] = layer
    self.cur_segment["shape_code"] = shape_code

    sc = int(shape_code)
    if   (sc == 0):
      self.cur_segment["shape"] = "line"
    elif (sc == 1):
      self.cur_segment["shape"] = "circle"
    elif (sc == 2):
      self.cur_segment["shape"] = "arc"

    self.cur_segment["angle"] = angle
    self.cur_segment["timestamp"] = timestamp
    self.cur_segment["status"] = status

  def cb_drawsegment_end(self, arg):

    self.cur_segment["type"] = "drawsegment"
    self.json_obj["element"].append( self.cur_segment )

    #self.json_obj["segment"].append( self.cur_segment )
    self.cur_segment = {}



  def cb_UNITS(self, arg):
    self.units = arg[0]
    self.json_obj["units"] = self.units

  def cb_MODULE(self, arg):
    name = arg[0]

    clean_name = name.strip()

    munged_name = name
    munged_name = re.sub( '^\s*', '', munged_name )
    munged_name = re.sub( '\s*$', '', munged_name )
    munged_name = urllib.quote( munged_name )
    munged_name = re.sub( '\/', '%2F', munged_name )
    #self.cur_mod["units"] = self.units
    self.cur_mod["name"] = clean_name



  ####

  def cb_MODULE_Po(self, arg):
    posx, posy, orientation, layer, timestamp, attribute0, attribute1 = arg

    self.cur_mod["x"] = posx
    self.cur_mod["y"] = posy

    self.cur_mod["orientation"] = orientation

    rad_ang = math.radians( float(orientation)/10.0 )
    self.cur_mod["angle"] = rad_ang

    self.cur_mod["layer"] = layer
    self.cur_mod["timestamp"] = timestamp
    self.cur_mod["attribute1"] = attribute0
    self.cur_mod["attribute2"] = attribute1


  def cb_MODULE_Li(self, arg):
    name = arg[0]

    tname = re.sub( '^\s*', '', name)
    tname = re.sub( '\s*$', '', tname)

    self.cur_mod["library_name"] = tname
    pass

  def cb_MODULE_Cd(self, arg):
    text = arg
    self.cur_mod["comment_description"] = text

  def cb_MODULE_Cd(self, arg):
    text = arg
    self.cur_mod["keyword"] = text

  def cb_MODULE_Sc(self, arg):
    timestamp = arg[0]

    self.cur_mod["timestamp_op"]  = timestamp

  def cb_MODULE_AR(self, arg):
    pass

  def cb_MODULE_Op(self, arg):
    rotation_cost_90, rotation_cost_180, unknown = arg

    self.cur_mod["rotation_cost_90"] = rotation_cost_90
    self.cur_mod["rotation_cost_180"] = rotation_cost_180
    self.cur_mod["rotation_cost_misc"] = unknown

  def cb_MODULE_At(self, arg):
    attribute = arg
    self.json_obj["attribute"] = attribute
  
  def cb_MODULE_Tn(self, arg):
    #n, posx, posy, sizex, sizey, rotation, penwidth, flag, visible, layer, flag, name = arg
    n, posx, posy, sizex, sizey, rotation, penwidth, flag, visible, layer, name = arg

    text_field = {}
    text_field["number"] = n
    text_field["x"] = posx
    text_field["y"] = posy
    text_field["sizex"] = sizex
    text_field["sizey"] = sizey
    text_field["rotation"] = rotation
    text_field["penwidth"] = penwidth
    text_field["penwidth"] = penwidth
    text_field["flag"] = flag
    text_field["visible"] = visible
    text_field["layer"] = layer
    text_field["misc"] = name


    cleaned_name = re.sub( '^\s*N?\s*"?', '', name )
    cleaned_name = re.sub( '"?\s*$', '', cleaned_name )

    text_field["text"] = cleaned_name

    self.cur_mod["text"].append( text_field )


  def cb_MODULE_DS(self, arg):
    startx,starty,endx,endy,stroke_width,layer = arg

    art_field = {}
    art_field["shape"] = "segment"
    art_field["startx"] = startx
    art_field["starty"] = starty

    art_field["endx"] = endx
    art_field["endy"] = endy

    art_field["line_width"] = stroke_width
    art_field["layer"] = layer

    self.cur_mod["art"].append( art_field )


  def cb_MODULE_DA(self, arg):
    centerx,centery,startx,starty,angle,stroke_width,layer = arg

    art_field = {}
    art_field["shape"] = "arc"
    art_field["x"] = centerx
    art_field["y"] = centery

    cx = float(centerx)
    cy = float(centery)
    sx = float(startx)
    sy = float(starty)
    dx = (cx - sx)
    dy = (cy - sy)
    dx2 = dx*dx
    dy2 = dy*dy
    r = math.sqrt( dx2 + dy2 )

    ang = math.radians(float(angle)/10.0)

    art_field["r"] = r
    art_field["angle"] = ang

    art_field["start_angle"] = math.atan2(dy, dx)
    art_field["line_width"] = stroke_width
    art_field["layer"] = layer

    self.cur_mod["art"].append( art_field )


  def cb_MODULE_DC(self, arg):
    centerx, centery, pointx, pointy, stroke_width, layer = arg

    art_field = {}
    art_field["shape"] = "circle"
    art_field["x"] = centerx
    art_field["y"] = centery

    cx = float(centerx)
    cy = float(centery)
    px = float(pointx)
    py = float(pointy)
    dx = (cx - px)
    dy = (cy - py)
    dx2 = dx*dx
    dy2 = dy*dy
    r = math.sqrt( dx2 + dy2 )

    art_field["r"] = r

    art_field["line_width"] = stroke_width
    art_field["layer"] = layer

    self.cur_mod["art"].append( art_field )


  def cb_MODULE_end(self, arg):

    #self.json_obj["module"].append( self.cur_mod )

    self.cur_mod["type"] = "module"
    self.json_obj["element"].append( self.cur_mod )

    #f = open( self.json_file, "w" )
    #f.write( json.dumps( self.cur_mod, indent=2 ))
    #f.close();

    #self.reset_bounds()
    #self.first = False
    self.clear_mod()


  def cb_PAD(self, arg):
    self.cur_pad = {}

  def cb_PAD_Sh(self, arg):
    pad_name, shape, sizex, sizey, deltax, deltay, orientation = arg

    self.cur_pad["name"] = re.sub('"', '', pad_name)
    self.cur_pad["shape_code"] = shape

    shape_lookup = { "R" : "rectangle", "C" : "circle", "O" : "oblong", "T" : "trapeze" }

    self.cur_pad["shape"] = shape_lookup[ shape ]

    self.cur_pad["sizex"] = self.decithou( float(sizex) )
    self.cur_pad["sizey"] = self.decithou( float(sizey) )
    self.cur_pad["deltax"] = deltax
    self.cur_pad["deltay"] = deltay
    self.cur_pad["orientation"] = int(orientation)

    rad_ang = math.radians( float(orientation)/10.0 )

    self.cur_pad["angle"] = rad_ang

  def cb_PAD_Dr(self, arg):
    pad_drill, offsetx, offsety = arg[0], arg[1], arg[2]

    hole_shape, pad_drill_x, pad_drill_y = None, None, None
    if len(arg) > 3 and arg[3] is not None:
      hole_shape = arg[3]
      self.cur_pad["hole_shape"] = re.sub(' ', '', hole_shape)
    if len(arg) > 4 and arg[4] is not None:
      pad_drill_x = arg[4]
      self.cur_pad["drill_hole_extra_x"] = self.decithou( float(pad_drill_x) )
    if len(arg) > 5 and arg[5] is not None:
      pad_drill_y = arg[5]
      self.cur_pad["drill_hole_extra_y"] = self.decithou( float(pad_drill_y) )

    self.cur_pad["drill_diam"] = self.decithou( float(pad_drill) )
    self.cur_pad["drill_x"] = self.decithou( float(offsetx) )
    self.cur_pad["drill_y"] = self.decithou( float(offsety) )


  def cb_PAD_At(self, arg):
    pad_type, n, layer_mask = arg

    if layer_mask is not None:
      self.cur_pad["layer_mask"] = layer_mask

  def cb_PAD_Ne(self, arg):
    net_number, net_name = arg

    cleaned_net_name = re.sub( '^\s*N?\s*"?', '', net_name );
    cleaned_net_name = re.sub( '"?\s*$', '', cleaned_net_name );

    self.cur_pad["net_number"] = net_number
    self.cur_pad["net_name"] = cleaned_net_name

  def cb_PAD_Po(self, arg):
    posx, posy = arg

    self.cur_pad["posx"] = self.decithou( float(posx) )
    self.cur_pad["posy"] = self.decithou( float(posy) )

  # units converted by thet ime we get here
  def cb_PAD_end(self, arg):

    self.cur_mod["pad"].append( self.cur_pad )
    self.cur_pad = {}


  def cb_endboard(self, arg):
    print json.dumps( self.json_obj, indent=2 )


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

  b = brdjson()

  if outbase is not None:
    b.json_prefix = outbase

  b.parse_brd(infile)


