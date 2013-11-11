#!/usr/bin/python
"""
Loads KiCAD mod file (version 1, not the new S-expression), parses it with mod,
writes to json.
"""

import re, sys, lib, math, numpy
import urllib
import math
import mod
import json

# text gray (192, 192, 192)
# text blue (0, 0, 192)
# part red (160, 0, 0)
# part green (0, 160, 0)
# art tiel (0, 160, 160)
# edge yellow (255, 255, 0)

class modjson(mod.mod):
  def __init__(self):
    self.json_file = ""
    self.json_prefix = "./"
    self.json_suffix = ".json"

    self.counter=0

    self.units = "deci-mils"

    self.buffer_pixel = 40

    self.bounding_box = [ [ 0, 0], [100, 100] ]

    self.line_width = 10

    self.json_obj = {}
    self.json_obj["art"] = []
    self.json_obj["units"] = "deci-mils"
    self.json_obj["text"] = []
    self.json_obj["pad"] = []

    self.line_width = 1

    mod.mod.__init__(self)

  def decithou(self, x):
    if self.units == "mm":
      return round( 10000.0 * float(x) / 25.4 )
    return float(x)

  def thou(self, x):
    if self.units == "mm":
      return  1000.0 * float(x) / 25.4 
    return x

  def mm(self, x):
    if self.units == "mm":
      return x
    return float(x)*25.4

  def clear(self):

    self.json_obj = {}
    self.json_obj[ "art" ] = []
    self.json_obj["units"] = "deci-mils"
    self.json_obj["text"] = []
    self.json_obj["pad"] = []



  def reset_bounds(self):
    self.bounding_box = [ [ 0, 0], [100, 100] ]

  def update_bounds(self, x, y):
    if x < self.bounding_box[0][0]:
      self.bounding_box[0][0] = x

    if x > self.bounding_box[1][0]:
      self.bounding_box[1][0] = x

    if y < self.bounding_box[0][1]:
      self.bounding_box[0][1] = y

    if y > self.bounding_box[1][1]:
      self.bounding_box[1][1] = y

  def inflate_bounds(self, px, py = None):
    dx = self.bounding_box[1][0] - self.bounding_box[0][0]
    dy = self.bounding_box[1][1] - self.bounding_box[0][1]

    if py is None:
      py = px

    ax = px * dx / 2.0
    ay = py * dy / 2.0

    self.update_bounds( self.bounding_box[0][0] - ax, self.bounding_box[0][1] - ay )
    self.update_bounds( self.bounding_box[1][0] + ax, self.bounding_box[1][1] + ay )

  def cb_header(self, arg):
    pass


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
    self.json_obj["units"] = self.units
    self.json_obj["name"] = clean_name

    self.json_file = self.json_prefix + str( munged_name ) + self.json_suffix


  ####

  def cb_MODULE_Po(self, arg):
    posx, posy, orientation, layer, timestamp, attribute0, attribute1 = arg

    self.json_obj["x"] = self.decithou(posx)
    self.json_obj["y"] = self.decithou(posy)

    self.json_obj["orientation"] = orientation

    rad_ang = math.radians( float(orientation)/10.0 )
    self.json_obj["angle"] = rad_ang


    self.json_obj["layer"] = layer
    self.json_obj["timestamp"] = timestamp
    self.json_obj["attribute1"] = attribute0
    self.json_obj["attribute2"] = attribute1


  def cb_MODULE_Li(self, arg):
    name = arg[0]

    tname = re.sub( '^\s*', '', name)
    tname = re.sub( '\s*$', '', tname)

    self.json_obj["library_name"] = tname
    pass

  def cb_MODULE_Cd(self, arg):
    text = arg
    self.json_obj["comment_description"] = text

  def cb_MODULE_Cd(self, arg):
    text = arg
    self.json_obj["keyword"] = text

  def cb_MODULE_Sc(self, arg):
    timestamp = arg[0]

    self.json_obj["timestamp_op"]  = timestamp

  def cb_MODULE_AR(self, arg):
    pass

  def cb_MODULE_Op(self, arg):
    rotation_cost_90, rotation_cost_180, unknown = arg

    self.json_obj["rotation_cost_90"] = rotation_cost_90
    self.json_obj["rotation_cost_180"] = rotation_cost_180
    self.json_obj["rotation_cost_misc"] = unknown

  def cb_MODULE_At(self, arg):
    attribute = arg
    self.json_obj["attribute"] = attribute
  
  def cb_MODULE_Tn(self, arg):
    #n, posx, posy, sizex, sizey, rotation, penwidth, flag, visible, layer, flag, name = arg
    n, posx, posy, sizex, sizey, rotation, penwidth, flag, visible, layer, name = arg

    text_field = {}
    text_field["number"] = n
    text_field["x"] = self.decithou(posx)
    text_field["y"] = self.decithou(posy)
    text_field["sizex"] = self.decithou(sizex)
    text_field["sizey"] = self.decithou(sizey)
    text_field["rotation"] = rotation
    text_field["penwidth"] = self.decithou(penwidth)
    text_field["flag"] = flag

    #text_field["visible"] = visible
    if visible == "V":
      text_field["visible"] = True
    else:
      text_field["visible"] = False


    text_field["layer"] = layer
    text_field["misc"] = name


    cleaned_name = re.sub( '^\s*N?\s*"?', '', name )
    cleaned_name = re.sub( '"?\s*$', '', cleaned_name )

    text_field["text"] = cleaned_name

    self.json_obj["text"].append( text_field )


  def cb_MODULE_DS(self, arg):
    startx,starty,endx,endy,stroke_width,layer = arg

    art_field = {}
    art_field["shape"] = "segment"
    art_field["startx"] = self.decithou(startx)
    art_field["starty"] = self.decithou(starty)

    art_field["endx"] = self.decithou(endx)
    art_field["endy"] = self.decithou(endy)

    art_field["line_width"] = self.decithou(stroke_width)
    art_field["layer"] = layer

    self.json_obj["art"].append( art_field )


  def cb_MODULE_DA(self, arg):
    centerx,centery,startx,starty,angle,stroke_width,layer = arg

    art_field = {}
    art_field["shape"] = "arc"

    cx = self.decithou( centerx )
    cy = self.decithou( centery )

    art_field["x"] = centerx
    art_field["y"] = centery

    sx = self.decithou( startx )
    sy = self.decithou( starty )
    dx = (cx - sx)
    dy = (cy - sy)
    dx2 = dx*dx
    dy2 = dy*dy
    r = math.sqrt( dx2 + dy2 )

    ang = math.radians(float(angle)/10.0)

    art_field["r"] = r
    art_field["angle"] = ang

    art_field["start_angle"] = math.atan2(dy, dx)
    art_field["line_width"] = self.decithou(stroke_width)
    art_field["layer"] = layer

    self.json_obj["art"].append( art_field )


  def cb_MODULE_DC(self, arg):
    centerx, centery, pointx, pointy, stroke_width, layer = arg

    art_field = {}
    art_field["shape"] = "circle"

    cx = self.decithou( centerx )
    cy = self.decithou( centery )

    art_field["x"] = cx
    art_field["y"] = cy

    px = self.decithou( pointx )
    py = self.decithou( pointy )
    dx = (cx - px)
    dy = (cy - py)
    dx2 = dx*dx
    dy2 = dy*dy
    r = math.sqrt( dx2 + dy2 )

    art_field["r"] = r

    art_field["line_width"] = self.decithou(stroke_width)
    art_field["layer"] = layer

    self.json_obj["art"].append( art_field )


  def cb_MODULE_end(self, arg):


    self.counter += 1
    if self.counter == 3:
      #sys.exit(0)
      pass

#    print json.dumps( self.json_obj, indent=2 )

#    munged_name = self.json_obj["name"]
#    munged_name = urllib.quote( munged_name )
#    munged_name = re.sub('\/', '%2F', self.json_obj["name"])
#
#    json_base_fn = munged_name + self.json_suffix
#    json_file = self.json_prefix + json_base_fn

    #print "### file:", self.json_file

    f = open( self.json_file, "w" )
    f.write( json.dumps( self.json_obj, indent=2 ))
    f.close();

    self.reset_bounds()
    self.first = False
    self.clear()


  def cb_PAD(self, arg):
    self.pad = {}

  def cb_PAD_Sh(self, arg):
    pad_name, shape, sizex, sizey, deltax, deltay, orientation = arg

    self.pad["name"] = re.sub('"', '', pad_name)
    self.pad["shape_code"] = shape

    shape_lookup = { "R" : "rectangle", "C" : "circle", "O" : "oblong", "T" : "trapeze" }

    self.pad["shape"] = shape_lookup[ shape ]

    self.pad["sizex"] = self.decithou( sizex )
    self.pad["sizey"] = self.decithou( sizey )
    self.pad["deltax"] = self.decithou( deltax )
    self.pad["deltay"] = self.decithou( deltay )
    self.pad["orientation"] = int(orientation)

    rad_ang = math.radians( float(orientation)/10.0 )
    self.pad["angle"] = rad_ang


  def cb_PAD_Dr(self, arg):
    pad_drill, offsetx, offsety = arg[0], arg[1], arg[2]

    hole_shape, pad_drill_x, pad_drill_y = None, None, None
    if len(arg) > 3 and arg[3] is not None:
      hole_shape = arg[3]
      self.pad["hole_shape"] = re.sub(' ', '', hole_shape)
    if len(arg) > 4 and arg[4] is not None:
      pad_drill_x = arg[4]
      self.pad["drill_hole_extra_x"] = self.decithou( pad_drill_x )
    if len(arg) > 5 and arg[5] is not None:
      pad_drill_y = arg[5]
      self.pad["drill_hole_extra_y"] = self.decithou( pad_drill_y )

    self.pad["drill_diam"] = self.decithou( pad_drill )
    self.pad["drill_x"] = self.decithou( offsetx )
    self.pad["drill_y"] = self.decithou( offsety )


  def cb_PAD_At(self, arg):
    pad_type, n, layer_mask = arg

    if layer_mask is not None:
      self.pad["layer_mask"] = layer_mask

  def cb_PAD_Ne(self, arg):
    net_number, net_name = arg

    cleaned_net_name = re.sub( '^\s*N?\s*"?', '', net_name );
    cleaned_net_name = re.sub( '"?\s*$', '', cleaned_net_name );

    self.pad["net_number"] = net_number
    self.pad["net_name"] = cleaned_net_name

  def cb_PAD_Po(self, arg):
    posx, posy = arg

    self.pad["posx"] = self.decithou( posx )
    self.pad["posy"] = self.decithou( posy )

  # units converted by thet ime we get here
  def cb_PAD_end(self, arg):

    self.json_obj["pad"].append( self.pad )
    self.pad = {}


  def cb_LIBRARY_end(self, arg):
    pass


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

  s = modjson()

  if outbase is not None:
    s.json_prefix = outbase

  s.parse_mod(infile)


