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

try:
  from urllib  import quote
except ImportError:
  from urllib.parse import quote



import brd

import json

class brdjson(brd.brd):

  def clear_mod(self):
    self.cur_pad = {}
    self.cur_mod = { "pad" : [], "text" : [], "art": [] }



  def clear(self):

    self.json_obj = {}

    self.json_obj["units"] = "deci-thou"
    self.json_obj["element"] = []
    self.json_obj["equipot"] = []
    #self.json_obj["net_class"] = []
    self.json_obj["net_class"] = {}


    self.destination_units = "deci-thou"

    # equipot maps internal net name to textual net name
    #

    self.clear_mod()
    self.cur_segment = {}
    self.cur_track = {}


  def __init__(self):
    self.clear()

    self.units = "deci-thou"
    self.destination_units = "deci-thou"

    brd.brd.__init__(self)

    self.cur_net_class = {}
    
  def decithou(self, x):
    if self.units == "mm":
      return round( 10000.0 * float(x) / 25.4 )
    return float(x)

  def thou(self, x):
    if self.units == "mm":
      return 1000.0 * float(x) / 25.4
    return float(x)

  def mm(self, x):
    if self.units == "mm":
      return x
    return float(x)*25.4


  def cb_header(self, arg):
    self.json_obj["header"] = arg[0].strip()


  def cb_track(self, arg):
    pass

  def cb_general_units(self, arg):
    units = arg[0]
    self.json_obj["units"] = str(units)


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

    self.cur_track["x0"] = self.decithou( float(x0) )
    self.cur_track["y0"] = self.decithou( float(y0) )
    self.cur_track["x1"] = self.decithou( float(x1) )
    self.cur_track["y1"] = self.decithou( float(y1) )
    self.cur_track["width"] = self.decithou( float( width) )

    self.cur_track["extra"] = extra

  def cb_track_de(self, arg):
    layer,track_type, netcode, timestamp, status = arg
    self.cur_track["layer"] = layer
    self.cur_track["track"] = track_type
    self.cur_track["netcode"] = netcode
    self.cur_track["timestamp"] = timestamp
    self.cur_track["status"] = status

    self.cur_track["type"] = "track"

    self.json_obj["element"].append( self.cur_track )

    self.cur_track = {}

  def cb_track_end(self, arg):
    pass


  def cb_nclass(self, arg):
    self.cur_net_class = {}
    self.cur_net_class_name = "Default"
    #self.cur_net_class["Default"] = {}

  def cb_nclass_name(self, arg):
    name,dummy = arg
    name = re.sub('"', '', name)
    #self.cur_net_class["name"] = name
    self.cur_net_class["name"] = name
    self.cur_net_class_name = name

  def cb_nclass_desc(self,arg):
    desc,dummy = arg
    desc = re.sub('"', '', desc)
    #self.cur_net_class["description"] = desc
    self.cur_net_class["description"] = desc

  def cb_nclass_clearance(self,arg):
    sz = arg[0]
    #self.cur_net_class["clearance"] = self.decithou(float(sz))
    self.cur_net_class["clearance"]  = self.decithou(float(sz))

  def cb_nclass_trackwidth(self,arg):
    tw = arg[0]
    #self.cur_net_class["track_width"] = self.decithou(float(tw))
    self.cur_net_class["track_width"]   = self.decithou(float(tw))

  def cb_nclass_viadia(self,arg):
    viadia = arg[0]
    #self.cur_net_class["via_diameter"] = self.decithou(float(viadia))
    self.cur_net_class["via_diameter"] = self.decithou(float(viadia))

  def cb_nclass_viadrill(self,arg):
    viadrill = arg[0]
    #self.cur_net_class["via_drill_diameter"] = self.decithou(float(viadrill))
    self.cur_net_class["via_drill_diameter"] = self.decithou(float(viadrill))

  def cb_nclass_uviadia(self,arg):
    uviadia = arg[0]
    #self.cur_net_class["uvia_diameter"] = self.decithou(float(uviadia))
    self.cur_net_class["uvia_diameter"] = self.decithou(float(uviadia))

  def cb_nclass_uviadrill(self,arg):
    uviadrill = arg[0]
    #self.cur_net_class["uvia_drill_diameter"] = self.decithou(float(uviadrill))
    self.cur_net_class["uvia_drill_diameter"] = self.decithou(float(uviadrill))

  def cb_nclass_addnet(self,arg):
    net_name,dummy = arg
    if "net" not in self.cur_net_class:
      self.cur_net_class["net"] = []
    #self.cur_net_class["net"].append(net_name)
    self.cur_net_class["net"].append(net_name)

  def cb_nclass_end(self,arg):
    #self.json_obj["net_class"].append(self.cur_net_class)
    self.json_obj["net_class"][self.cur_net_class_name] = self.cur_net_class
    self.cur_net_class = {}
    pass



  def cb_drawsegment(self, arg):
    pass

  def cb_drawsegment_po(self, arg):
    shape_code, x0, y0, x1, y1, width = arg

    self.cur_segment["shape_code"] = shape_code

    tx0 = self.decithou( float(x0) )
    ty0 = self.decithou( float(y0) )
    tx1 = self.decithou( float(x1) )
    ty1 = self.decithou( float(y1) )

    sc = int(shape_code)

    if   (sc == 0):
      self.cur_segment["shape"] = "line"
    # Either the documentation is wrong or KiCAD is wrong..
    # 2 appears to be arc, 3 appears to be circle
    # ( as opposed to 2 being arc, 1 being circle )
    #elif (sc == 1) or (sc == 2):
    elif (sc == 2) or (sc == 3):

      if   (sc == 3):
        self.cur_segment["shape"] = "circle"
      elif (sc == 2):
        self.cur_segment["shape"] = "arc"

      r = math.sqrt( (tx0-tx1)*(tx0-tx1) + (ty0-ty1)*(ty0-ty1) )

      self.cur_segment["x"] = tx0
      self.cur_segment["y"] = ty0
      self.cur_segment["r"] = r

      # also, documentation is defintely lying about
      # point interpreationg.  For arcs, x0,y0 are center,
      # x1,y1 are start point, 90 degree clockwise.
      if (sc == 2):
        dx = tx1 - tx0
        dy = ty1 - ty0

        # start angle is clockwise, going counter clocwise from
        # start angle
        self.cur_segment["start_angle"] = math.atan2(dy,dx)
        self.cur_segment["angle"] = math.pi / 2.0
        self.cur_segment["counterclockwise_flag"] = False


    self.cur_segment["x0"] = self.decithou( float(x0) )
    self.cur_segment["y0"] = self.decithou( float(y0) )
    self.cur_segment["x1"] = self.decithou( float(x1) )
    self.cur_segment["y1"] = self.decithou( float(y1) )
    self.cur_segment["width"] = self.decithou( float(width) )

  def cb_drawsegment_de(self, arg):
    layer,type_code,angle,timestamp,status = arg

    self.cur_segment["type_code"] = type_code
    self.cur_segment["layer"] = layer

    self.cur_segment["rotation"] = angle
    self.cur_segment["angle"] = math.radians( float(angle)/10.0 )
    self.cur_segment["timestamp"] = timestamp
    self.cur_segment["status"] = status

  def cb_drawsegment_end(self, arg):

    self.cur_segment["type"] = "drawsegment"
    self.json_obj["element"].append( self.cur_segment )

    self.cur_segment = {}


  def cb_general_units(self, arg):
    self.units = arg[0]
    #self.json_obj["units"] = self.units
    self.json_obj["units"] = self.destination_units


  def cb_UNITS(self, arg):
    self.units = arg[0]
    #self.json_obj["units"] = self.units
    self.json_obj["units"] = self.destination_units

  def cb_MODULE(self, arg):
    name = arg[0]

    clean_name = name.strip()

    munged_name = name
    munged_name = re.sub( '^\s*', '', munged_name )
    munged_name = re.sub( '\s*$', '', munged_name )
    #munged_name = urllib.quote( munged_name )
    munged_name = quote( munged_name )
    munged_name = re.sub( '\/', '%2F', munged_name )
    self.cur_mod["name"] = clean_name



  ####

  def cb_MODULE_Po(self, arg):
    posx, posy, orientation, layer, timestamp, attribute0, attribute1 = arg

    self.cur_mod["x"] = self.decithou( float(posx) )
    self.cur_mod["y"] = self.decithou( float(posy) )

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
  
  # EITHER THE DOCUMENTATION IS WRONG OR THERE'S A BUG IN KiCAD
  # KiCAD clearly renders what the documentation says as sizex as sizey
  # and sizey as sizex.  I'm switching it here to be consistent with
  # KiCAD....
  # 
  def cb_MODULE_Tn(self, arg):
    #n, posx, posy, sizex, sizey, rotation, penwidth, flag, visible, layer, flag, name = arg
    n, posx, posy, sizey, sizex, rotation, penwidth, flag, visible, layer, name = arg

    text_field = {}
    text_field["number"] = n

    text_field["x"] = self.decithou( float(posx) )
    text_field["y"] = self.decithou( float(posy) )
    text_field["sizex"] = self.decithou( float(sizex) )
    text_field["sizey"] = self.decithou( float(sizey) )

    text_field["rotation"] = rotation

    text_field["angle"] = float(rotation) * math.pi / 1800.0

    text_field["penwidth"] = self.decithou( float(penwidth) )

    text_field["flag"] = flag

    if (visible == "V"):
      text_field["visible"] = True
    else:
      text_field["visible"] = False

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

    art_field["startx"] = self.decithou( float(startx) )
    art_field["starty"] = self.decithou( float(starty) )

    art_field["endx"] = self.decithou( float(endx) )
    art_field["endy"] = self.decithou( float(endy) )

    art_field["line_width"] = self.decithou( float(stroke_width) )
    art_field["layer"] = layer

    self.cur_mod["art"].append( art_field )


  def cb_MODULE_DA(self, arg):
    centerx,centery,startx,starty,angle,stroke_width,layer = arg

    art_field = {}
    art_field["shape"] = "arc"

    art_field["x"] = self.decithou( float(centerx) )
    art_field["y"] = self.decithou( float(centery) )

    cx = self.decithou( float(centerx) )
    cy = self.decithou( float(centery) )
    sx = self.decithou( float(startx) )
    sy = self.decithou( float(starty) )
    dx = (sx - cx)
    dy = (cy - sy)
    dx2 = dx*dx
    dy2 = dy*dy
    r = math.sqrt( dx2 + dy2 )

    ang = math.radians(float(angle)/10.0)

    art_field["r"] = r
    art_field["angle"] = ang

    art_field["start_angle"] = math.atan2(dy, dx)
    art_field["line_width"] = self.decithou( float(stroke_width) )
    art_field["layer"] = layer

    self.cur_mod["art"].append( art_field )


  def cb_MODULE_DC(self, arg):
    centerx, centery, pointx, pointy, stroke_width, layer = arg

    art_field = {}
    art_field["shape"] = "circle"

    art_field["x"] = self.decithou( float(centerx) )
    art_field["y"] = self.decithou( float(centery) )

    cx = self.decithou( float(centerx) )
    cy = self.decithou( float(centery) )
    px = self.decithou( float(pointx) )
    py = self.decithou( float(pointy) )
    dx = (cx - px)
    dy = (cy - py)
    dx2 = dx*dx
    dy2 = dy*dy
    r = math.sqrt( dx2 + dy2 )

    art_field["r"] = r

    art_field["line_width"] = self.decithou( float(stroke_width) )
    art_field["layer"] = layer

    self.cur_mod["art"].append( art_field )


  def cb_MODULE_end(self, arg):

    self.cur_mod["type"] = "module"
    self.json_obj["element"].append( self.cur_mod )

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
    self.cur_pad["deltax"] = self.decithou( float(deltax) )
    self.cur_pad["deltay"] = self.decithou( float(deltay) )
    self.cur_pad["orientation"] = int(float(orientation))

    rad_ang = math.radians( float(orientation)/10.0 )

    self.cur_pad["angle"] = rad_ang

  def cb_PAD_Dr(self, arg):
    pad_drill, offsetx, offsety = arg[0], arg[1], arg[2]

    self.cur_pad["drill_shape"] = 'circle'

    drill_hole_shape, pad_drill_x, pad_drill_y = None, None, None
    if len(arg) > 3 and arg[3] is not None:
      drill_hole_shape = arg[3].strip()
      self.cur_pad["drill_shape_code"] = re.sub(' ', '', drill_hole_shape)

      if (drill_hole_shape == 'O'):
        self.cur_pad["drill_shape"] = 'oblong'

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

    self.cur_pad["type"] = pad_type
    if layer_mask is not None:
      self.cur_pad["layer_mask"] = layer_mask

  def cb_PAD_Ne(self, arg):
    net_number, net_name = arg

    cleaned_net_name = re.sub( '^\s*N?\s*"?', '', net_name )
    cleaned_net_name = re.sub( '"?\s*$', '', cleaned_net_name )

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

  def cb_equipot(self, arg):
    pass
 
  def cb_equipot_na(self, arg):
    netcode, netname, dummy = arg

    netname = re.sub('"', '', netname)

    netcode = int(netcode)
    self.json_obj["equipot"].append( { "net_number": netcode, "net_name": netname } )

  def cb_equipot_st(self, arg):
    pass

  def cb_equipot_end(self, arg):
    pass





  def cb_czone(self, arg):
    self.cur_czone = { "zcorner" : [], "polyscorners" : [], "type" : "czone" }

  def cb_czone_zinfo(self, arg):
    timestamp, netcode, name, dummy = arg

    name = re.sub( '"', '', name );

    self.cur_czone["timestamp"] = timestamp
    self.cur_czone["netcode"] = netcode
    self.cur_czone["name"] = name

  def cb_czone_zaux(self, arg):
    corner_count, hatching_option = arg

    self.cur_czone["corner_count"] = corner_count
    self.cur_czone["hatching_option"] = hatching_option

  def cb_czone_clearance(self, arg):
    clearance, pad_option = arg

    self.cur_czone["clearance"] = self.decithou( clearance )
    self.cur_czone["pad_option"] = pad_option

  def cb_czone_zminthickness(self, arg):
    min_thickness = arg[0]

    self.cur_czone["min_thickness"] = self.decithou( min_thickness )

  def cb_czone_zoptions(self, arg):
    fill, arc, f, antipad_thickness, thermal_stub_width = arg

    self.cur_czone["fill"] = fill
    self.cur_czone["arc"] = arc
    self.cur_czone["F"] = f
    self.cur_czone["antipad_thickness"] = self.decithou( antipad_thickness )
    self.cur_czone["thermal_stub_width"] = self.decithou( thermal_stub_width )

  def cb_czone_zsmoothing(self, arg):
    x, y = arg

    self.cur_czone["zsmoothing_x"] = self.decithou( x )
    self.cur_czone["zsmoothing_y"] = self.decithou( y )


  def cb_czone_zcorner(self, arg):
    x, y, flag = arg

    p = { }
    p["x"] = self.decithou( x );
    p["y"] = self.decithou( y );

    self.cur_czone["zcorner"].append( p )

  def cb_polyscorners(self, arg):
    pass

  def cb_polyscorners_corner(self, arg):
    x0, y0, x1, y1 = arg

    p = {}
    p["x0"] = self.decithou( x0 );
    p["y0"] = self.decithou( y0 );
    p["x1"] = self.decithou( x1 );
    p["y1"] = self.decithou( y1 );

    self.cur_czone["polyscorners"].append(p)

  def cb_czone_zlayer(self, arg):
    zlayer = arg[0]

    self.cur_czone["layer"] = zlayer

  def cb_czone_end(self, arg):
    self.json_obj["element"].append( self.cur_czone );


  def cb_textpcb(self, arg):
    self.cur_text = { "type" : "text", "visible" : True }

  def cb_textpcb_te(self, arg):
    text = arg[0]
    text = re.sub( '^"|"$', '', text )
    self.cur_text["text"] = text;

  def cb_textpcb_po(self, arg):
    x, y, sizex, sizey, width, rotation = arg
    self.cur_text["x"] = self.decithou( x )
    self.cur_text["y"] = self.decithou( y )
    self.cur_text["sizex"] = self.decithou( sizex )
    self.cur_text["sizey"] = self.decithou( sizey )
    self.cur_text["width"] = self.decithou( width )
    self.cur_text["rotation"] = rotation
    self.cur_text["angle"] = math.radians( -float(rotation)/10.0 )

  def cb_textpcb_de(self, arg):
    #layer, mirror_code, ts, style = arg
    layer, mirror_code, ts, style, extra = arg

    self.cur_text["layer"] = layer
    self.cur_text["mirror_code"] = mirror_code
    self.cur_text["timestamp"] = ts
    self.cur_text["style"] = style

  def cb_textpcb_nl(self, arg):
    text = arg[0]
    text = re.sub( '^"|"$', '', text )
    self.cur_text["text"] += "\n" + str(text)

  def cb_textpcb_end(self, arg):
    self.json_obj["element"].append( self.cur_text )


  def cb_endboard(self, arg):
    #print(json.dumps( self.json_obj, indent=2 )
    pass


if __name__ == "__main__":

  infile = None
  outfile = None

  if len(sys.argv) >= 2:
    infile = sys.argv[1]

  if len(sys.argv) >= 3:
    outfile = sys.argv[2]

  if infile is None:
    print("provide infile")
    sys.exit(0)

  b = brdjson()

  b.parse_brd(infile)

  if outfile is None:
    print(json.dumps( b.json_obj, indent = 2 ))

