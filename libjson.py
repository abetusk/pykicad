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
Loads KiCAD lib file (library file), parses it with lib.py, writes to json format.
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

class libjson(lib.lib):

  def __init__(self):
    self.first = True
    self.json_file = ""
    #self.json_prefix = "./json/"
    self.json_prefix = "./"
    self.json_suffix = ".json"

    self.counter = 0
    self.alias = []

    # bounding box is rough
    self.bounding_box = [ [0,0], [0, 0] ]

    self.json_obj = {}
    self.json_obj["text"] = []
    #self.json_obj["text"]["description"] = " horizontal and vertical justify - (C)entered (L)eft (R)ight (T)op, bold - (B)old (N)one, italic - (I)talic (N)one, orientation - (H)oriztonal (V)ertical" 
    self.json_obj["units"] = "deci-mils"

    self.json_obj["art"] = []
    self.json_obj["pin"] = []

    self.pixel_per_mil = 1
    self.line_width = 1

    lib.lib.__init__(self)

  def clear(self):
    self.json_obj = {}
    self.json_obj["text"] = []
    #self.json_obj["text"]["description"] = " horizontal and vertical justify - (C)entered (L)eft (R)ight (T)op, bold - (B)old (N)one, italic - (I)talic (N)one, orientation - (H)oriztonal (V)ertical" 

    self.json_obj["art"] = []
    self.json_obj["pin"] = []

    # bounding box is rough
    self.bounding_box = [ [0,0], [0, 0] ]


  def update_bounds(self, x, y):
    if x < self.bounding_box[0][0]:
      self.bounding_box[0][0] = x

    if x > self.bounding_box[1][0]:
      self.bounding_box[1][0] = x

    if y < self.bounding_box[0][1]:
      self.bounding_box[0][1] = y

    if y > self.bounding_box[1][1]:
      self.bounding_box[1][1] = y

  # TODO: be more intelligent about how we update these bounds
  def update_bounds_arc(self, x, y, r, start_angle_rad, end_angle_rad):
    self.update_bounds(x + r, y + r)
    self.update_bounds(x - r, y - r)
    pass

  def update_bounds_circle(self, x, y, r):
    self.update_bounds(x + r, y + r)
    self.update_bounds(x - r, y - r)


  def cb_header(self, arg):
    pass


  def cb_ALIAS(self, arg):
    s = arg[0].strip()

    self.alias = re.sub('  *', ' ', s).split(' ')


  def cb_DEF (self, arg):
    name,reference,unused,text_offset,draw_pinnumber,draw_pinname,unit_count,units_locked,option_flag = arg

    # replace '/' with '#' and url ecnode the rest of the string
    munged_name = re.sub('\/', '#', arg[0] )
    munged_name = urllib.quote( munged_name );

    self.json_file = self.json_prefix + munged_name + self.json_suffix 

    self.draw_pin_name = True
    if draw_pinname == "N":
      self.draw_pin_name = False

    self.draw_pin_num = True
    if draw_pinnumber == "N":
      self.draw_pin_num = False

    self.bounding_box = [ [0,0], [0, 0] ]
    self.name = name

    self.reference = reference
    self.text_offset = text_offset
    self.unit_count = int(unit_count)

    self.units_locked = 'F'
    if units_locked:
      self.units_locked = units_locked

    self.power_flag = 'N'
    if option_flag:
      self.power_flag = option_flag

    self.json_obj["name"] = self.name
    self.json_obj["reference"] = self.reference
    self.json_obj["unit_count"] = self.unit_count
    self.json_obj["units_locked"] = self.units_locked
    self.json_obj["power_flag"] = self.power_flag
    self.json_obj["text_offset"] = self.text_offset

    self.json_obj["draw_pin_name"] = self.draw_pin_name
    self.json_obj["draw_pin_number"] = self.draw_pin_num


  def cb_F0 (self, arg):
    reference, posx, posy, text_size, text_orient, visible, htext_justify, vtext_justify = arg

    if htext_justify:
      htext_justify = htext_justify.strip()
    if vtext_justify:
      vtext_justify = vtext_justify.strip()

    is_visible = True
    if visible == "I":
      is_visible = False

    reference = reference.strip('"')
    x,y = float(posx), float(posy)

    # KiCAD text position is centered 
    font_width_height_ratio = 0.6
    font_height = float(text_size)
    font_width = font_width_height_ratio * font_width_height_ratio 

    w = len(reference) * font_width 
    h = font_height

    angle_deg = 0
    if text_orient == "V" :
      angle_deg = -90

      h = w
      w = font_height

    self.update_bounds( x - w/2, y - h/2 )
    self.update_bounds( x + w/2, y + h/2 )

    htext_justify_token = 'C'
    vtext_justify_token = 'C'
    text_italic = 'N'
    text_bold = 'N'

    if vtext_justify:
      r = re.search("\s*([CLRT])([IN])([BN])", vtext_justify)
      if r:
        vtext_justify_token = r.group(1)
        text_italic = r.group(2)
        text_bold = r.group(3)

    if htext_justify:
      htext_justify_token = htext_justify


    f0 = {}
    f0["number"] = 0
    f0["reference"] = reference
    f0["x"] = posx
    f0["y"] = posy
    f0["size"] = text_size
    f0["orientation"] = text_orient
    f0["visible"] = is_visible
    f0["hjustify"] = htext_justify  # (C)enter, (L)eft, (R)ight, (T)op
    f0["vjustify"] = vtext_justify_token  # (C)enter, (L)eft, (R)ight, (T)op
    f0["italic"] = text_italic      # (I)italic, (N)one
    f0["bold"] = text_bold          # (B)old, (N)one

    #self.json_obj["text"]["F0"] = f0
    self.json_obj["text"].append(f0)

  def cb_F1 (self, arg):
    reference, posx, posy, text_size, text_orient, visible, htext_justify, vtext_justify = arg

    if vtext_justify:
      vtext_justify = vtext_justify.strip()
    if htext_justify:
      htext_justify = htext_justify.strip()

    is_visible = True
    if visible == "I":
      is_visible = False

    reference = reference.strip('"')
    x,y = float(posx), float(posy)

    # KiCAD text position is centered 
    font_width_height_ratio = 0.6
    font_height = float(text_size)
    font_width = font_width_height_ratio * font_width_height_ratio 

    w = len(reference) * font_width 
    h = font_height

    angle_deg = 0
    if text_orient == "V" :
      angle_deg = -90

      h = w
      w = font_height

    self.update_bounds( x - w/2, y - h/2 )
    self.update_bounds( x + w/2, y + h/2 )

    htext_justify_token = 'C'
    vtext_justify_token = 'C'
    text_italic = 'N'
    text_bold = 'N'

    if vtext_justify:
      r = re.search("\s*([CLRT])([IN])([BN])", vtext_justify)
      if r:
        if len(r.groups()) > 1:
          vtext_justify_token = r.group(1)
        if len(r.groups()) > 2:
          text_italic = r.group(2)
        if len(r.groups()) > 3:
          text_bold = r.group(3)

    if htext_justify:
      htext_justify_token = htext_justify

    f1 = {}
    f1["number"] = 1
    f1["reference"] = reference
    f1["x"] = posx
    f1["y"] = posy
    f1["size"] = text_size
    f1["orientation"] = text_orient
    f1["visible"] = is_visible
    f1["hjustify"] = htext_justify  # (C)enter, (L)eft, (R)ight, (T)op
    f1["vjustify"] = vtext_justify_token  # (C)enter, (L)eft, (R)ight, (T)op
    f1["italic"] = text_italic      # (I)italic, (N)one
    f1["bold"] = text_bold          # (B)old, (N)one

    #self.json_obj["text"]["F1"] = f1
    self.json_obj["text"].append(f1)


  def cb_Fn (self, arg): 
    num, text = arg

    fn = {}
    fn["number"] = num
    fn["text"] = text

    self.json_obj["text"].append(fn)


  def cb_ENDDEF(self, arg):


    munged_name = re.sub('\/', '#', self.json_obj["name"])
    json_base_fn = urllib.quote( munged_name ) + self.json_suffix 
    json_file = self.json_prefix + json_base_fn

    print json_file

    f = open( json_file, "w" )
    f.write( json.dumps( self.json_obj, indent=2 ) )
    f.close()

    # fails because we're creating duplicate symlinks.
    # this is an inconsistency in the .lib files, as two different parts
    # can have the same alias.  take it out for now.
#    for comp in self.alias:
#      fn = self.json_prefix + urllib.quote( re.sub('\/', '#', comp) ) + self.json_suffix
#      if fn == json_file:
#        continue
#      print "base:", json_base_fn, " sym:", fn
#      os.symlink( json_base_fn , fn )

    self.first = False
    self.clear()


  def cb_EOF(self, arg):
    #print "}"
    pass


  def cb_A(self, arg):
    posx,posy,radius,start_angle,end_angle,unit,convert,thickness,fill,startx,starty,endx,endy = arg

    sa = math.radians( float(start_angle)/10.0 )
    ea = math.radians( float(end_angle)/10.0 )

    ccw = True
    if abs(ea - sa) > (math.pi/2.0):
      ccw = False

    arc_obj = {}
    arc_obj["shape"] = "arc"
    arc_obj["x"] = float(posx)
    arc_obj["y"] = float(posy)
    arc_obj["r"] = float(radius)
    arc_obj["start_angle"] = math.radians( float(start_angle)/10.0 )
    arc_obj["end_angle"] = math.radians( float(end_angle)/10.0 )
    arc_obj["unit"] = unit
    arc_obj["de_morgan_alternate_shape"] = convert
    arc_obj["line_width"] = int(thickness)

    fill_opt = "N"
    if fill is not None:
      fill_opt = fill.strip()
    arc_obj["fill"] = fill_opt

    arc_obj["counterclockwise"] = ccw

    self.json_obj["art"].append( arc_obj )

  def cb_C(self, arg):
    posx, posy, radius, unit, convert, thickness, fill = arg
    x,y,r = float(posx), float(posy), float(radius)

    circle_obj = {}
    circle_obj["shape"] = "circle"
    circle_obj["x"] = x
    circle_obj["y"] = y
    circle_obj["r"] = r

    circle_obj["unit"] = unit
    circle_obj["de_morgan_alternate_shape"] = convert
    circle_obj["line_width"] = thickness

    fill_opt = "N"
    if fill is not None:
      fill_opt = fill.strip()
    circle_obj["fill"] = fill_opt

    self.json_obj["art"].append( circle_obj )

  def cb_P(self, arg):
    point_count,unit,convert,thickness,str_pnts,dummy,fill_opt = int(arg[0]),arg[1],arg[2],arg[3],arg[4],arg[5],arg[6]

    path_obj = {}
    path_obj["shape"] = "path"
    path_obj["count"] = int(point_count)
    path_obj["unit"] = unit
    path_obj["convert"] = convert
    path_obj["line_width"] = thickness
    path_obj["de_morgan_alternate_shape"] = convert

    fill_opt_flag = "N"
    if fill_opt is not None:
      fill_opt_flag = fill_opt.replace(" ", "")

    path_obj["fill"] = fill_opt_flag

    str_pnts = str_pnts.strip()
    str_pnts = re.sub(' +', ' ', str_pnts)
    pnts = str_pnts.split(' ')

    prev_x,prev_y =  float(pnts[0]), float(pnts[1])
    self.update_bounds( float(prev_x), float(prev_y) )

    f_pnts = [ [ float(pnts[0]), float(pnts[1]) ] ]
    pos = 2
    while pos < len(pnts):
      x,y = float(pnts[pos]), float(pnts[pos+1])
      f_pnts.append( [ x, y ] )

      self.update_bounds( float(x), float(y) )
      pos += 2

    path_obj["path"] = f_pnts

    self.json_obj["art"].append( path_obj )


  def cb_S(self, arg):
    startx, starty, endx, endy, unit, convert, thickness, fill = arg


    sx = int(startx)
    sy = int(starty)

    ex = int(endx)
    ey = int(endy)

    self.update_bounds( float(sx), float(sy) )
    self.update_bounds( float(ex), float(ey) )

    height = abs( float(ey-sy) )
    width  = abs( float(ex-sx) )

    px = min(sx, ex)
    py = min(sy, ey)

    rect_obj = {}
    rect_obj["shape"] = "rectangle"
    rect_obj["x"] = float(startx)
    rect_obj["y"] = float(starty)
    rect_obj["width"] = width
    rect_obj["height"] = height
    rect_obj["unit"] = unit
    rect_obj["de_morgan_alternate_shape"] = convert

    fill_opt = "N"
    if fill is not None:
      fill_opt = fill.strip()
    rect_obj["fill"] = fill_opt

    rect_obj["line_width"] = thickness

    self.json_obj["art"].append( rect_obj )


  def cb_T(self, arg):
    direction, posx, posy, text_size, text_type, unit, convert, text = arg

    x,y = float(posx), float(posy)

    font_width_height_ratio = 0.6
    font_height = float(text_size)
    font_width = font_width_height_ratio * font_height


    text_obj = {}
    text_obj["shape"] = "text"
    text_obj["x"] = x
    text_obj["y"] = y
    text_obj["size"] = text_size
    text_obj["type"] = text_type
    text_obj["unit"] = unit
    text_obj["de_morgan_alternate_shape"] = convert
    text_obj["direction_unit"] = "deci-degrees"
    text_obj["direction"] = direction

    self.json_obj["art"].append( text_obj )

    text = text.strip()
    atext = text.split(' ')
    atext[0] = re.sub('~', ' ', atext[0])

    text_obj["text"] = str(atext[0])


  # WARNING!  num_text_size and name_text_size look to be reversed
  # TODO: render pin properly with DEF text_offset 
  def cb_X(self, arg):
    #name, num, posx, posy, length, direction, name_text_size, num_text_size, unit, convert, electrical_type, pin_type = arg
    name, num, posx, posy, length, direction, num_text_size, name_text_size, unit, convert, electrical_type, pin_type = arg


    pin_obj = {}
    #pin_obj["field_description"] = "direction - (U)p (D)own (L)eft (R)ight"
    #pin_obj["field_description"] += ", electrical_type - (O)output (B)idirectional (T)ristate (P)assive (C)ollector (E)mitter (N)otconnected (U)nspecified (W)powerinput (w)poweroutput"
    #pin_obj["field_description"] += ", shape - (null)line (I)nverted (C)lock (L)owinput (V)lowoutput (N)invisible"
    pin_obj["name"] = name
    pin_obj["number"] = num
    pin_obj["x"] = posx
    pin_obj["y"] = posy

    pin_obj["length"] = length
    pin_obj["direction"] = direction
    pin_obj["text_size_number"] = num_text_size
    pin_obj["text_size_name"]   = name_text_size
    pin_obj["unit"] = unit
    pin_obj["de_morgan_alternate_shape"] = convert
    pin_obj["electrical_type"] = electrical_type

    visible_flag = True
    if pin_type:
      if re.search( "^ *N", pin_type):
        visible_flag = False

    pin_obj["shape"] = pin_type
    pin_obj["visible"] = visible_flag


    self.json_obj["pin"].append( pin_obj )


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

  s = libjson()

  if outbase is not None:
    s.json_prefix = outbase

  s.parse_lib(infile)


