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

VERSION="( brdgerber.py v0.1 2014-03-12 )"

# TODO: 
#  - contours and regions (somewhat done, needs to be more inteligent about how it splits
#       up regions so nasty strands don't leave trails)
#  - art for modules (arc, polygon )
#  - arcs for segments
#  - text
#  - trapeze (if ever)

import re
import sys
import os
import lib
import math
import numpy
import cgi
import urllib

import datetime
import time

import json

import brd
import brdjson
import pygerber

import math
import numpy as np
import json

class brdgerber(brdjson.brdjson):

  def __init__(self, fontFile = None):
    brdjson.brdjson.__init__(self)
    self._apertureName = 10
    self._id = 1
    self.apertureIdMap = {}
    self.apertureTrack = {}

    self.aperture = {}
    self.invertY = False
    #self.invertY = True

    self.grb = pygerber.pygerber()
    self.grb.invertY = self.invertY

    self.islands = []
    self.island_layer = []

    self.layer = 0


    self.font_file = "./aux/hershey_ascii.json"
    if fontFile is not None:
      self.font_file = fontFile

    f = open( self.font_file, "r")
    s = ""
    for l in f:
      s += l
    f.close()
    self.hershey_font_json = json.loads(s)
    #print json.dumps(self.hershey_font_json, indent = 2)

    self.hershey_scale_factor = float( self.hershey_font_json["scale_factor"] )


  def _font_string_width(self, text, sizex):
    w = 0
    sf = float(self.hershey_font_json["scale_factor"])
    for i in range(len(text)):
      ch_ord = str(ord(text[i]))
      if ch_ord not in self.hershey_font_json : continue
      f = self.hershey_font_json[ch_ord]
      w += sf * (float(f["xsto"]) - float(f["xsta"])) * float(sizex)
    return w


  def toUnit(self, v):
    return float(v) / 10000.0

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



  def _find_czone_islands_r( self, islands, pnts, start_pos, end_pos , layer, width, ap_key ):

    island = []

    cur_pos = start_pos + 1
    while cur_pos <= end_pos:

      pnt = pnts[cur_pos]

      if pnt["skip_pos"] >= 0:
        self._find_czone_islands_r( islands, pnts, cur_pos, pnt["skip_pos"], layer, width, ap_key )
        cur_pos = pnt["skip_pos"]
      else:
        island.append( { "x" : pnt["x0"], "y" : pnt["y0"] } )

      cur_pos += 1


    # reject duplicate points
    if len(island) == 2:
      #print "#ERROR, got length 2 for subregion"
      #print island
      #sys.exit(0)
      pass
    elif len(island) > 1:
      islands.append( { "island":island, "layer": layer, "width": width, "aperture_key": ap_key  } )


  def _find_czone_islands( self, islands, czone, ap_key ):
    cur_list = []
    pos_dict = {}

    scalar = 10000.0
    #scalar = 10000000.0
    pos = 0

    orig_pnts = czone["polyscorners"]

    prev_pnt = { "x": 0, "y": 0 }
    pnts = []
    for i, pnt in enumerate(orig_pnts):
      if i==0:
        pnts.append(pnt)
        continue
      if ( (int(prev_pnt["x"]) == int(pnt["x0"])) and
           (int(prev_pnt["y"]) == int(pnt["y0"])) ):
        continue
      prev_pnt["x"] = int(pnt["x0"])
      prev_pnt["y"] = int(pnt["y0"])

      pnts.append( pnt )


    for pnt in pnts:
      key_x = int( scalar * float(pnt["x0"]) + 0.5 )
      key_y = int( scalar * float(pnt["y0"]) + 0.5 )

      x = float(pnt["x0"])
      y = float(pnt["y0"])

      key = str(key_x) + ":" + str(key_y)
      cur_list.append( { "x" : x, "y" : y } )

      pnt["skip_pos"] = -1

      if key in pos_dict:
        pnts[ pos_dict[key] ]["skip_pos"]  = pos
      else:
        pos_dict[key] = pos

      pos += 1

    #for i, p in enumerate(pnts):
    #  print "[" + str(i) + "]", p

    self._find_czone_islands_r( islands, pnts, 0, len(pnts)-1, czone["layer"], czone["min_thickness"], ap_key )


  def first_pass(self):

    aperture_set = {}

    for v in self.json_obj["element"]:

      if (v["type"] == "track") or (v["type"] == "drawsegment"):
        key = "circle:" + "{0:011.5f}".format( self.toUnit(v["width"]) )

        if v["type"] == "drawsegment":
          shape = v["shape"]
          if shape == "line":
            v["y0"] = -float(v["y0"])
            v["y1"] = -float(v["y1"])
          elif shape == "circle" :
            v["y"] = -float(v["y"])
          elif shape == "arc":
            v["y"] = -float(v["y"])
            v["start_angle"] = -float(v["start_angle"])
            v["angle"] = -float(v["angle"])

        else:
          v["y0"] = -float(v["y0"])
          v["y1"] = -float(v["y1"])



        if key in aperture_set:
          ap_name = aperture_set[key]["aperture_name"]
        else:
          aperture_set[ key ] = { \
              "type" : "circle",  \
              "d" : self.toUnit(v["width"] ),  \
              "aperture_name" : self.genApertureName() \
              }

        v["aperture_name"] = ap_name
        v["aperture_key"] = key

      elif v["type"] == "text":

        key = "circle:" + "{0:011.5f}".format( self.toUnit(v["width"]) )

        v["angle"] = -float(v["angle"])

        if key in aperture_set:
          ap_name = aperture_set[key]["aperture_name"]
        else:
          aperture_set[ key ] = { \
              "type" : "circle",  \
              "d" : self.toUnit(v["width"] ),  \
              "aperture_name" : self.genApertureName() \
              }

        v["aperture_name"] = ap_name
        v["aperture_key"] = key


        v["y"] = -float(v["y"])
        pass

      elif v["type"] == "czone":

        key = "circle:" +  "{0:011.5f}".format( self.toUnit(v["min_thickness"]) )

        if key in aperture_set:
          ap_name = aperture_set[key]["aperture_name"]
        else:
          aperture_set[ key ] = { \
            "type" : "circle",  \
            "d" : self.toUnit(v["min_thickness"] ),  \
            "aperture_name" : self.genApertureName() \
          }

        v["aperture_name"] = ap_name
        v["aperture_key"] = key


        poly = v["polyscorners"]
        for pc in poly:
          pc["y0"] = -float(pc["y0"])



        self._find_czone_islands( self.islands, v, key)


      elif v["type"] == "module":

        v["y"] = -float(v["y"])

        for text in v["text"]:

          text["y"] = -float(text["y"])

          width = self.toUnit( text["penwidth"] )
          key = "circle:" + "{0:011.5f}".format(width)
          if key not in aperture_set:
            aperture_set[key] = { "type" : "circle", "d" : width, "aperture_name" : self.genApertureName() }
            
          ap_name = aperture_set[key]["aperture_name"]
          text["aperture_name"] = ap_name
          text["aperture_key"] = key


        for art in v["art"]:
          shape = art["shape"]

          if (shape == "segment"):
            art["starty"] = -float(art["starty"])
            art["endy"] = -float(art["endy"])

          if (shape == "circle") or (shape == "arc") or (shape == "polygon"):
            art["y"] = -float(art["y"])

            if shape == "arc":
              art["start_angle"] = -float(art["start_angle"])
              art["angle"] = -float(art["angle"])

          if (shape == "segment") or (shape == "circle") or (shape == "arc") or (shape == "polygon"):
            d = self.toUnit( art["line_width"] )
            key = "circle:" + "{0:011.5f}".format(d) 
            if key not in aperture_set:
              aperture_set[key] = { "type" : "circle", "d" : d, "aperture_name" : self.genApertureName() }
            
            ap_name = aperture_set[key]["aperture_name"]
            art["aperture_name"] = ap_name
            art["aperture_key"] = key

        for pad in v["pad"]:

          pad["posy"] = -float(pad["posy"])
          pad["drill_y"] = -float(pad["drill_y"])
          pad["deltay"] = -float(pad["deltay"])


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
    #a = float( pad["angle"] )

    v = self._rot( mod_a, [ x, y ] )
    #v = self._rot( a, [ x, y ] )

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

    sx = self.toUnit( pad["sizex"] )
    sy = self.toUnit( pad["sizey"] )

    a = float( pad["angle"] )

    #v = self._rot( mod_a, [ x, y ] )
    v = self._rot( a, [ x, y ] )

    if "aperture_key" in pad:

      key = pad["aperture_key"]
      ap = self.aperture[key]

      self.grb.apertureSet( ap["aperture_name"] )
      self.grb.flash( v[0,0] + mod_x , v[0,1] + mod_y )
    else:
      dx = sx/2
      dy = sy/2

      p0 = self._rot( a, [ x - dx, y - dy ] )
      p1 = self._rot( a, [ x + dx, y - dy ] )
      p2 = self._rot (a, [ x + dx, y + dy ] )
      p3 = self._rot (a, [ x - dx, y + dy ] )

      self.grb.regionStart()
      self.grb.moveTo( p0[0,0] + mod_x , p0[0,1] + mod_y )
      self.grb.lineTo( p1[0,0] + mod_x , p1[0,1] + mod_y )
      self.grb.lineTo( p2[0,0] + mod_x , p2[0,1] + mod_y )
      self.grb.lineTo( p3[0,0] + mod_x , p3[0,1] + mod_y )
      self.grb.lineTo( p0[0,0] + mod_x , p0[0,1] + mod_y )
      self.grb.regionEnd()


  def pad_oblong(self, mod, pad):

    mod_x = self.toUnit( mod["x"] )
    mod_y = self.toUnit( mod["y"] )
    mod_a = float( mod["angle"] )

    x = self.toUnit( pad["posx"] )
    y = self.toUnit( pad["posy"] )
    a = float( pad["angle"] )

    sx = self.toUnit( pad["sizex"] )
    sy = self.toUnit( pad["sizey"] )

    if sx > sy:
      obR = sy
      obS = sx - sy
      dx = obS
      dy = 0
    else:
      obR = sx
      obS = sy - sx
      dx = 0
      dy = obS

    da = a - mod_a

    u = self._rot( a, [ x, y ] )
    v = self._rot( a, [ x, y ] )

    if "aperture_key" in pad:
      key = pad["aperture_key"]
      ap = self.aperture[key]

      self.grb.apertureSet( ap["aperture_name"] )
      self.grb.moveTo( u[0,0], u[0,1] )
      self.grb.lineTo( v[0,0], v[0,1] )
    else:
      print "# WARNING, no aperture for pad_oblong:", pad


  def pad_trapeze(self, mod, pad):
    print "# WARNIGN: pad_trapeze not implemented"


  def track_line(self, track):

    x0 = self.toUnit( track["x0"] )
    y0 = self.toUnit( track["y0"] )

    x1 = self.toUnit( track["x1"] )
    y1 = self.toUnit( track["y1"] )

    if "aperture_key" in track:
      key = track["aperture_key"]
      ap = self.aperture[key]

      self.grb.apertureSet( ap["aperture_name"] )
      self.grb.moveTo( x0, y0 )
      self.grb.lineTo( x1, y1 )
    else:
      print "# WARNING: no aperture for track: ", track


  def drawsegment_line(self, segment):

    x0 = self.toUnit( segment["x0"] )
    y0 = self.toUnit( segment["y0"] )

    x1 = self.toUnit( segment["x1"] )
    y1 = self.toUnit( segment["y1"] )

    if "aperture_key" in segment:
      key = segment["aperture_key"]
      ap = self.aperture[key]

      self.grb.apertureSet( ap["aperture_name"] )
      self.grb.moveTo( x0, y0 )
      self.grb.lineTo( x1, y1 )
    else:
      print "# WARNING: no aperture for segment: ", segment

  def drawsegment_circle(self, segment):
    x = self.toUnit( segment["x"] )
    y = self.toUnit( segment["y"] )
    r = self.toUnit( segment["r"] )

    n = 128

    if "aperture_key" in segment:
      key = segment["aperture_key"]
      ap = self.aperture[key]
      self.grb.apertureSet( ap["aperture_name"] )
      self.grb.moveTo( x + r, y )

      # It's just easier to linearize
      #
      for i in range(n+1):
        ang = (2.0 * math.pi * float(i)/float(n))
        self.grb.lineTo( x + r * math.cos(ang) , y + r * math.sin(ang) )


  def drawsegment_arc(self, segment):
    x = self.toUnit( segment["x"] )
    y = self.toUnit( segment["y"] )
    r = self.toUnit( segment["r"] )

    sa = float( segment["start_angle"] )
    a = float( segment["angle"] )

    ccw = segment["counterclockwise_flag"]

    s = 1.0
    if ccw: s = -1.0

    n = 128

    if "aperture_key" in segment:
      key = segment["aperture_key"]
      ap = self.aperture[key]
      self.grb.apertureSet( ap["aperture_name"] )

      self.grb.moveTo( x + r*math.cos(sa), y + r*math.sin(sa)  )


      # It's just easier to linearize
      #
      for i in range(n+1):
        ang = sa + (s*a*float(i)/float(n))
        self.grb.lineTo( x + r * math.cos(ang) , y + r * math.sin(ang) )


  def czone(self, czone):
    first = True

    polyscorners = czone["polyscorners"]
    for pc in polyscorners:

      x = self.toUnit( pc["x0"] )
      y = self.toUnit( pc["y0"] )

      if first:
        self.grb.regionStart()
        self.grb.moveTo( x, y )
        first = False

      else:
        self.grb.lineTo( x, y )

    if not first:
      self.grb.regionEnd()


  def track_via(self, via):
    x0 = self.toUnit( via["x0"] )
    y0 = self.toUnit( via["y0"] )

    if "aperture_key" in via:
      key = via["aperture_key"]
      ap = self.aperture[key]

      self.grb.apertureSet( ap["aperture_name"] )
      self.grb.flash( x0, y0 )
    else:
      print "# WARNING: no aperture for via: ", via


  def art_segment(self, mod, art):

    mod_x = self.toUnit( mod["x"] )
    mod_y = self.toUnit( mod["y"] )
    mod_a = float( mod["angle"] )

    sx = self.toUnit( art["startx"] )
    sy = self.toUnit( art["starty"] )

    ex = self.toUnit( art["endx"] )
    ey = self.toUnit( art["endy"] )

    u = self._rot( mod_a, [ sx , sy ] )
    x0 = u[0,0] + mod_x
    y0 = u[0,1] + mod_y

    v = self._rot( mod_a, [ ex , ey ] )
    x1 = v[0,0] + mod_x
    y1 = v[0,1] + mod_y

    if "aperture_key" in art:
      key = art["aperture_key"]
      ap = self.aperture[key]

      self.grb.apertureSet( ap["aperture_name"] )
      self.grb.moveTo( x0, y0 )
      self.grb.lineTo( x1, y1 )
    else:
      print "# WARNING: no aperture for art_segment: ", art


  def art_circle(self, mod, art):
    mod_x = self.toUnit( mod["x"] )
    mod_y = self.toUnit( mod["y"] )
    mod_a = float( mod["angle"] )

    cx = self.toUnit( art["x"] )
    cy = self.toUnit( art["y"] )
    r = self.toUnit( art["r"] )

    u = self._rot( mod_a, [ cx , cy ] )
    x = u[0,0] + mod_x
    y = u[0,1] + mod_y

    if "aperture_key" in art:
      key = art["aperture_key"]
      ap = self.aperture[key]

      self.grb.apertureSet( ap["aperture_name"] )
      self.grb.moveTo( x + r, y )

      n = 256
      for i in range(n+1):
        ang = 2.0 * math.pi * float(i)/float(n)
        self.grb.lineTo( x + r * math.cos(ang), y + r * math.sin(ang) )

      #self.grb.arcTo(x + r, y, -r, 0  )
    else:
      print "# WARNING: no aperture for art_circle: ", art


  # We should come back and review all of our angle assumptions
  # are correct.
  #
  def art_arc(self, mod, art):
    mod_x = self.toUnit( mod["x"] )
    mod_y = self.toUnit( mod["y"] )
    mod_a = float( mod["angle"] )

    cx = self.toUnit( art["x"] )
    cy = self.toUnit( art["y"] )
    r = self.toUnit( art["r"] )

    sa = float( art["start_angle"] )
    a = float( art["angle"] )

    if a > 2.0 * math.pi:
      a -= 2.0 * math.pi
    elif a <= -2.0 * math.pi:
      a += 2.0 * math.pi

    sa = -sa - mod_a
    s = 1.0

    u = self._rot( mod_a, [ cx, cy ] )

    x0 = u[0,0] + mod_x
    y0 = u[0,1] + mod_y

    if "aperture_key" in art:
      key = art["aperture_key"]
      ap = self.aperture[key]

      self.grb.apertureSet( ap["aperture_name"] )

      n = 64
      for i in range(n+1):
        ang = sa + (s*a*float(i)/float(n))

        if i==0:
          self.grb.moveTo( x0 + r * math.cos(ang), y0 + r * math.sin(ang) )
        else:
          self.grb.lineTo( x0 + r * math.cos(ang), y0 + r * math.sin(ang) )


    else:
      print "# WARNING: no aperture for art_circle: ", art


  def art_polygon(self, mod, art):
    pass


  # first apply the rotation in ang radians, then apply the trnslation [x,y]
  #
  def _draw_hershey_char( self, ap, font_entry, ang, x, y, sizex, sizey, flip_flag = False ):

    sf = float( self.hershey_font_json["scale_factor"] )
    xsto = float(font_entry["xsto"])
    xsta = float(font_entry["xsta"])

    dx = sf * (xsto - xsta) * float(sizex)

    for pnts in font_entry["art"]:
      first = True
      for pnt in pnts:

        f_x = pnt["x"]
        f_y = pnt["y"]

        a = f_x * sizex
        b = f_y * sizey

        a *= self.hershey_scale_factor
        b *= self.hershey_scale_factor

        if flip_flag:
          a *= -1

        u = self._rot( ang, [a,b] )

        u[0,0] += x
        u[0,1] += y

        a = self.toUnit( u[0,0] )
        b = self.toUnit( u[0,1] )
        

        if first:
          self.grb.apertureSet( ap["aperture_name"] )
          self.grb.moveTo(a,b)
        else:
          self.grb.lineTo(a,b)

        first = False

    return dx

  def _feq(self, a, b):
    return abs(float(a)-float(b)) < 0.001

  def _deg_mod(self, ang):
    q = int( float(ang) / 360 )
    deg = float(ang) - float(q) * 360.0

    if (deg >= 180.0 ): return deg - 360
    if (deg < -180.0 ): return deg + 360
    return deg

  def _find_footprint_text_angle( self, loc_deg_ang, glob_deg_ang):
    loc_deg_ang = self._deg_mod( loc_deg_ang )
    glob_deg_ang = self._deg_mod( glob_deg_ang )

    if (self._feq(loc_deg_ang, 90) or 
        self._feq(loc_deg_ang, -90)):
      loc_deg_ang = -90.0
    elif (self._feq(loc_deg_ang, 180) or
          self._feq(loc_deg_ang, -180)):
      loc_deg_ang = 0.0
    elif loc_deg_ang > 90:
      loc_deg_ang -= 180
    elif loc_deg_ang < -90:
      loc_deg_ang += 180

    loc_deg_ang -= glob_deg_ang

    if loc_deg_ang >  180: loc_deg_ang -= 360
    if loc_deg_ang < -180: loc_deg_ang += 360

    return loc_deg_ang


  def text_module(self, mod, text_obj, flip_flag = False):

    #flip_flag = True
    #flip_flag = False
    if "flag" in text_obj:
      if re.search( 'M', text_obj["flag"]):
        flip_flag = True

    visible_flag = text_obj["visible"]
    if not visible_flag: return

    mod_x = float(mod["x"])
    mod_y = float(mod["y"])
    mod_a = float(mod["angle"])

    x = float(text_obj["x"])
    y = float(text_obj["y"])

    ang = float(text_obj["angle"])

    width = float(text_obj["penwidth"])
    text_code = text_obj["flag"]
    text = text_obj["text"]

    key = text_obj["aperture_key"]
    ap = self.aperture[key]
    aperture_name = ap["aperture_name"]

    sizex = float(text_obj["sizex"])
    sizey = float(text_obj["sizey"])

    text_width = self._font_string_width( text, sizex )
    text_height = sizey

    dx = sizex
    dy = 0

    if flip_flag:
      dx *= -1

    dv = self._rot( ang, [ dx, dy ] )

    deg_ang = math.degrees(ang)
    deg_ang = -self._find_footprint_text_angle( -deg_ang, 0 )
    rad_ang = math.radians(deg_ang)

    d_off = [ - text_width/2, - text_height/2 ]
    if flip_flag:
      d_off[0] *= -1.0
    td_off = self._rot( rad_ang, d_off )

    ds = [ x, y ]
    tds = self._rot( ang, ds )
    cur_u = [ tds[0,0] + td_off[0,0], tds[0,1] + td_off[0,1] ]

    for ch in text:
      c = ord(ch) 
      c_str = str(c)
      font = self.hershey_font_json[c_str]

      dx = self._draw_hershey_char( ap, font, rad_ang, mod_x + cur_u[0], mod_y + cur_u[1], sizex, sizey, flip_flag )

      if flip_flag:
        dx *= -1

      dv = self._rot( rad_ang, [ dx, 0 ] )

      cur_u[0] += dv[0,0]
      cur_u[1] += dv[0,1]


  def text_element(self, text_obj, flip_flag = False):

    #flip_flag = True
    #flip_flag = False
    if "mirror_code" in text_obj:
      if int(text_obj["mirror_code"]) == 0:
        flip_flag = True

    visible_flag = text_obj["visible"]
    if not visible_flag: return

    x = float(text_obj["x"])
    y = float(text_obj["y"])

    ang = float(text_obj["angle"])

    width = float(text_obj["width"])
    #text_code = text_obj["flag"]
    #texts = text_obj["text"]

    key = text_obj["aperture_key"]
    ap = self.aperture[key]
    aperture_name = ap["aperture_name"]

    sizex = float(text_obj["sizex"])
    sizey = float(text_obj["sizey"])

    s = text_obj["text"]
    texts = s.split( "\n" )

    dh = -int(float(sizey)/0.6)
    curh = 0

    for text in texts:

      #text_width = len(text) * sizex
      text_width = self._font_string_width( text, sizex )
      text_height = sizey

      dx = sizex
      dy = 0

      tv = self._rot( ang, [ 0, curh ])
      h_offset = [ tv[0,0], tv[0,1] ]
      curh += dh

      if flip_flag:
        dx *= -1

      dv = self._rot( ang, [ dx, dy ] )


      start_x = - text_width/2
      if flip_flag:
        start_x = + text_width/2

      start_y = - text_height/2
      su = self._rot( ang , [ start_x, start_y ] )

      cur_u = [ su[0,0], su[0,1] ]

      for ch in text:
        c = ord(ch) 
        c_str = str(c)

        if c_str not in self.hershey_font_json:
          c_str = str(ord('.'))


        font = self.hershey_font_json[c_str]
        dx = self._draw_hershey_char( ap, font, ang, \
            x + cur_u[0] + h_offset[0], \
            y + cur_u[1] + h_offset[1], \
            sizex, sizey, flip_flag )

        if flip_flag: dx *= -1
        dv = self._rot( ang, [ dx, 0 ] )

        cur_u[0] += dv[0,0]
        cur_u[1] += dv[0,1]



  def second_pass(self):

    for v in self.json_obj["element"]:


      ele_type = v["type"]

      if ele_type == "module":

        for art in v["art"]:

          if int(art["layer"]) != self.layer: continue

          shape = art["shape"]
          if shape == "segment":      self.art_segment(v, art)
          if shape == "circle":       self.art_circle(v, art)
          if shape == "arc":          self.art_arc(v, art)
          if shape == "polygon":      self.art_polygon(v, art)

        for pad in v["pad"]:

          pad_layer_mask = int(pad["layer_mask"], 16)
          if not (pad_layer_mask & (1<<self.layer)): continue

          shape = pad["shape"]
          if   shape == "circle":     self.pad_circle(v, pad)
          elif shape == "rectangle":  self.pad_rectangle(v, pad)
          elif shape == "oblong":     self.pad_oblong(v, pad)
          elif shape == "trapeze":    self.pad_trapeze(v, pad)

        for text in v["text"]:
          if int(text["layer"]) != self.layer: continue
          self.text_module(v, text)

      elif ele_type == "text":

        if int(v["layer"]) != self.layer: continue

        self.text_element(v)

        pass


      elif ele_type == "track":


        shape = v["shape"]

        if (shape == "track") and (self.layer != int(v["layer"])): continue
        else:
          a_layer = int(v["layer"]) & 0xf
          b_layer = (int(v["layer"]) & 0xf0) >> 4
          start_layer = min(a_layer, b_layer)
          end_layer = max(a_layer, b_layer)
          if ( self.layer < start_layer ) or ( self.layer > end_layer ) : continue

        if   shape == "track":      self.track_line(v)
        elif shape == "through":    self.track_via(v)
        elif shape == "blind":      self.track_via(v)

      elif ele_type == "drawsegment":

        if self.layer != int(v["layer"]): continue

        shape = v["shape"]

        if shape == "line":         self.drawsegment_line(v)
        elif shape == "circle":     self.drawsegment_circle(v)
        elif shape == "arc":        self.drawsegment_arc(v)
      #elif ele_type == "czone": self.czone(v)

      elif ele_type == "czone":

        if self.layer != int(v["layer"]): continue

        if len(v["polyscorners"]) < 3: continue

        pnts = v["polyscorners"]
        for i,p in enumerate(pnts):
          if i==0:
            self.grb.regionStart()
            self.grb.moveTo( self.toUnit(p["x0"]), self.toUnit(p["y0"]) )
            continue
          self.grb.lineTo( self.toUnit(p["x0"]), self.toUnit(p["y0"]) )
        self.grb.lineTo( self.toUnit(pnts[0]["x0"]), self.toUnit(pnts[0]["y0"]) )
        self.grb.regionEnd();



#    # print pours
#    #
#    for ele in self.islands:
#      first = True
#      island = ele["island"]
#      layer = int(ele["layer"])
#
#      if int(self.layer) != int(layer): continue
#
#      for pnt in island:
#        if first:
#          self.grb.regionStart()
#          self.grb.moveTo( self.toUnit(pnt["x"]), self.toUnit(pnt["y"]) )
#          first = False
#        else:
#          self.grb.lineTo( self.toUnit(pnt["x"]), self.toUnit(pnt["y"]) )
#      if not first:
#        self.grb.lineTo( self.toUnit(island[0]["x"]), self.toUnit(island[0]["y"]) )
#        self.grb.regionEnd()

    # print pour outlines
    #
    for ele in self.islands:
      island = ele["island"]
      width = ele["width"]
      key = ele["aperture_key"]

      layer = int(ele["layer"])

      if int(self.layer) != int(layer): continue

      ap = self.aperture[key]
      self.grb.apertureSet( ap["aperture_name"] )

      if len(island) < 3: continue

      self.grb.moveTo( self.toUnit(island[0]["x"]), self.toUnit(island[0]["y"]) )
      for pnt in island:
        self.grb.lineTo( self.toUnit(pnt["x"]), self.toUnit(pnt["y"]) )
      self.grb.lineTo( self.toUnit(island[0]["x"]), self.toUnit(island[0]["y"]) )


  def dump_gerber(self):

    # first pass to get apertures that are used
    #
    self.first_pass()

    self.grb.mode("IN")
    self.grb.formatSpecification( 'L', 'A', 3, 4, 3, 4 )


    self.grb.addCommand( "G01*" )  # linear interpolation
    self.grb.addCommand( "G70*" )  # deprecated set inches
    self.grb.addCommand( "G90*" )  # deprecated set aboslute

    self.grb.comment("APERTURE LIST")

    # define apertures
    #
    dummy_aperture_name = None
    for key in self.aperture:
      ap = self.aperture[key]
      typ = ap["type"] 
      nam = ap["aperture_name"]
      if typ == "rect":     self.grb.defineApertureRectangle( nam, ap["x"], ap["y"] )
      elif typ == "circle": self.grb.defineApertureCircle( nam, ap["d"] )

      if dummy_aperture_name is None:
        dummy_aperture_name = nam

    self.grb.comment("APERTURE END LIST")

    self.grb.addCommand( "G54D" + dummy_aperture_name + "*" )  # deprecated set aperture

    # second pass to push to render
    #
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

####
# Code taken from question by Daniel Goldberg :
# http://stackoverflow.com/questions/354038/how-do-i-check-if-a-string-is-a-number-in-python 
#
def is_num(s):
  try:
    float(s)
    return True
  except ValueError:
    return False
#
###

if __name__ == "__main__":

  infile = None
  layer = 0
  font_file = None

  if len(sys.argv) >= 2:
    infile = sys.argv[1]
    if len(sys.argv) >= 3:
      layer = int(sys.argv[2])
      if len(sys.argv) >= 4:
        font_file = sys.argv[3]

  if infile is None:
    print "provide infile"
    sys.exit(0)


  b = brdgerber(font_file)

  b.layer = layer

  str_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  str_date += " " + time.strftime("%Z")
  b.grb.comment("( created by brdgerber.py " + VERSION + " ) date " + str_date )
  b.grb.comment("Gerber Fmt 3.4, Leading zero omitted, Abs format")

  b.parse_brd(infile)

  b.dump_gerber()



