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
import time
import datetime

VERSION="pykicad jsonbrd.py 2014-03-05"
SRC_UNIT = "deci-thou"
DST_UNIT = "mm"


class jsonbrd:
  def __init__(self):
    pass


# unic convert
# only hanldes deci-thou and mm
#
def uc( src ):
  s = float(src)
  f = 1.0

  if SRC_UNIT == DST_UNIT:
    return s

  if   (SRC_UNIT == "mm") and (DST_UNIT == "deci-thou"):
    f = 10000.0/25.4
  elif (SRC_UNIT == "mm") and (DST_UNIT == "deci-mils"):
    f = 10000.0/25.4
  elif (SRC_UNIT == "mm") and (DST_UNIT == "deci-mil"):
    f = 10000.0/25.4

  elif (SRC_UNIT == "deci-thou") and (DST_UNIT == "mm"):
    f = 25.4/10000.0
  elif (SRC_UNIT == "deci-mils") and (DST_UNIT == "mm"):
    f = 25.4/10000.0
  elif (SRC_UNIT == "deci-mil")  and (DST_UNIT == "mm"):
    f = 25.4/10000.0


  return f*s

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

  SRC_UNIT = "mm"
  if "units" in json_data:
    SRC_UNIT = json_data["units"]
  DST_UNIT = "mm"

  dt = datetime.datetime.now()
  str_dt = dt.strftime("%Y-%m-%d %H:%M:%S")
  tz = time.strftime("%Z", time.gmtime())
  human_str_dt = dt.strftime("%a %d %b %Y %I:%M:%S") + " " + tz

  print "PCBNEW-BOARD Version 2 date", human_str_dt
  print 

  print "# Created by", VERSION
  print

  print "$GENERAL"
  print "encoding utf-8"
  print "Units", DST_UNIT
  print "LayerCount 2"
  print "EnabledLayers 1FFF8001"
  print "Links 36"
  print "NoConn 4"
  print "Di 47.249999 24.273 111.027001 100.650001"
  print "Ndraw 7"
  print "Ntrack 168"
  print "Nzone 0"
  print "BoardThickness 1.6"
  print "Nmodule 8"
  print "Nnets 8"
  print "$EndGENERAL"
  print 

  print "$SHEETDESCR"
  print "Sheet A3 16535 11693"
  print "Title \"\""
  print "Date \"30 nov 2013\""
  print "Rev \"\""
  print "Comp \"\""
  print "Comment1 \"\""
  print "Comment2 \"\""
  print "Comment3 \"\""
  print "Comment4 \"\""
  print "$EndSHEETDESCR"
  print

  print "$SETUP"
  print "Layers 2"
  print "Layer[0] B.Cu signal"
  print "Layer[15] F.Cu signal"
  print "TrackWidth 0.254"
  print "TrackClearence 0.254"
  print "ZoneClearence 0.508"
  print "Zone_45_Only 0"
  print "TrackMinWidth 0.254"
  print "DrawSegmWidth 0.2"
  print "EdgeSegmWidth 0.1"
  print "ViaSize 0.889"
  print "ViaDrill 0.635"
  print "ViaMinSize 0.889"
  print "ViaMinDrill 0.508"
  print "MicroViaSize 0.508"
  print "MicroViaDrill 0.127"
  print "MicroViasAllowed 0"
  print "MicroViaMinSize 0.508"
  print "MicroViaMinDrill 0.127"
  print "TextPcbWidth 0.3"
  print "TextPcbSize 1.5 1.5"
  print "EdgeModWidth 0.15"
  print "TextModSize 1 1"
  print "TextModWidth 0.15"
  print "PadSize 1.5 1.5"
  print "PadDrill 0.6"
  print "Pad2MaskClearance 0"
  print "SolderMaskMinWidth 0"
  print "AuxiliaryAxisOrg 0 0"
  print "VisibleElements 7FFFFFFF"
  print "PcbPlotParams (pcbplotparams (layerselection 3178497) (usegerberextensions true) (excludeedgelayer true) (linewidth 0.150000) (plotframeref false) (viasonmask false) (mode 1) (useauxorigin false) (hpglpennumber 1) (hpglpenspeed 20) (hpglpendiameter 15) (hpglpenoverlay 2) (psnegative false) (psa4output false) (plotreference true) (plotvalue true) (plotothertext true) (plotinvisibletext false) (padsonsilk false) (subtractmaskfromsilk false) (outputformat 1) (mirror false) (drillshape 1) (scaleselection 1) (outputdirectory \"\"))"
  print "$EndSETUP"
  print 

  eqpot = json_data["equipot"]
  for ep in eqpot:
    name = ep["net_name"]
    number = ep["net_number"]

    print "$EQUIPOT"
    print "Na", number, "\"" + name + "\""
    print "St ~"
    print "$EndEQUIPOT"

  if len(eqpot) > 0:
    print "$NCLASS"
    print "Name \"Default\""
    print "Desc \"This is the default net class.\""
    print "Clearance 0.254"
    print "TrackWidth 0.254"
    print "ViaDia 0.889"
    print "ViaDrill 0.635"
    print "uViaDia 0.508"
    print "uViaDrill 0.127"

    for eq in eqpot:
      name = ep["net_name"]
      print "AddNet \"" + name + "\""
    print "$EndNCLASS"

  tracks = []


  eles = json_data["element"]
  for ele in eles:
    ele_type = ele["type"]
    if ele_type == "module":
      name = ele["library_name"]
      x = uc(ele["x"])
      y = uc(ele["y"])
      layer = ele["layer"]
      orientation = ele["orientation"]
      timestamp = ele["timestamp"]
      timestamp_op = ele["timestamp_op"]

      attr1 = ele["attribute1"]
      attr2 = ele["attribute2"]

      print "$MODULE", name
      print "Po", x, y, orientation, layer, timestamp, attr1, attr2
      print "Li", name
      print "Sc", timestamp_op
      #print "Ar /" + timestamp_op
      print "Op 0 0 0"

      text = ele["text"]
      for t in text:
        num = t["number"]
        x = uc(t["x"])
        y = uc(t["y"])
        #sizex = uc(t["sizex"])
        #sizey = uc(t["sizey"])
        sizex = uc(t["sizey"])
        sizey = uc(t["sizex"])
        rot = t["rotation"]
        w = uc(t["penwidth"])
        flag = t["flag"]
        visible = "I"
        if t["visible"]:
          visible = "V"
        layer = t["layer"]
        misc = t["misc"]

        print "T" + str(num), x, y, sizex, sizey, rot, w, flag, visible, layer, misc

      art = ele["art"]
      for a in art:
        shape = a["shape"]
        
        if shape == "arc":
          x = uc(a["x"])
          y = uc(a["y"])
          r = uc(a["r"])
          da_rad = float(a["angle"])
          sa_rad = float(a["start_angle"])
          da = math.degrees( da_rad )*10
          sa = math.degrees( sa_rad )*10
          layer = a["layer"]
          w = uc(a["line_width"])

          px = x + r*math.cos(sa_rad)
          py = y + r*math.sin(sa_rad)

          print "DA", x, y, px, py, da, w, layer

        elif shape == "segment":
          sx = uc(a["startx"])
          sy = uc(a["starty"])
          ex = uc(a["endx"])
          ey = uc(a["endy"])
          layer = a["layer"]
          w = uc(a["line_width"])

          print "DS", sx, sy, ex, ey, w, layer

        elif shape == "circle":
          x = uc(a["x"])
          y = uc(a["y"])
          r = uc(a["r"])
          layer = a["layer"]
          w = uc(a["line_width"])

          print "DC", x, y, x+r, y, w, layer

      if "pad" in ele:
        pad = ele["pad"]
        for p in pad:
          x = uc(p["posx"])
          y = uc(p["posy"])

          #pad_type = "SMD"
          pad_type = "STD"
          if "type" in pad:
            pad_type = pad["type"]

          print "$PAD"
          print "Sh", "\"" + str(p["name"]) + "\"", p["shape_code"], uc(p["sizex"]), uc(p["sizey"]), \
              uc(p["deltax"]), uc(p["deltay"]), p["orientation"]
          print "Dr", uc(p["drill_diam"]), uc(p["drill_x"]), uc(p["drill_y"])
          print "At", pad_type, "N", p["layer_mask"]
          print "Ne", p["net_number"], "\"" + str(p["net_name"]) + "\""
          print "Po", uc(p["posx"]), uc(p["posy"])
          print "$EndPAD"


      print "$EndMODULE"

    elif ele_type == "drawsegment":
      seg_shape = ele["shape"]
      print "$DRAWSEGMENT"

      if seg_shape == "line":
        print "Po", ele["shape_code"], uc(ele["x0"]), uc(ele["y0"]), uc(ele["x1"]), uc(ele["y1"]), uc(ele["width"])
        print "De", ele["layer"], 0, ele["angle"], 0, 0

      elif seg_shape == "arc":
        x = uc(ele["x"])
        y = uc(ele["y"])
        r = uc(ele["r"])

        sa = float(ele["start_angle"])
        a = float(ele["angle"])

        deg_a = math.degrees(a)

        # Come back to this later, not sure why this works
        #
        s = -1.0
        if ele["counterclockwise_flag"]:
          s = 1.0

        x1 = x + r*math.cos(s*sa)
        y1 = y + r*math.sin(s*sa)

        print "Po", ele["shape_code"], uc(ele["x"]), uc(ele["y"]), x1, y1, uc(ele["width"])
        print "De", ele["layer"], 0, int(s*deg_a*10.0), 0, 0

      elif seg_shape == "circle":
        x = uc(ele["x"])
        y = uc(ele["y"])
        r = uc(ele["r"])

        print "Po", ele["shape_code"], uc(ele["x"]), uc(ele["y"]), x+r, y, uc(ele["width"])
        print "De", ele["layer"], 0, ele["angle"], 0, 0

      print "$EndDRAWSEGMENT"

    elif ele_type == "text":
      print "$TEXTPCB"

      texts = ele["text"].split("\n")
      for i, t in enumerate(texts):
        if i==0:
          print "Te \"" + texts[i] + "\""
        else:
          print "nl \"" + texts[i] + "\""
      print "Po", uc(ele["x"]), uc(ele["y"]), uc(ele["sizex"]), \
          uc(ele["sizey"]), uc(ele["width"]), ele["rotation"]
      print "De", ele["layer"], ele["mirror_code"], ele["timestamp"], ele["style"]
      print "$EndTEXTPCB"

    elif ele_type == "track":
      s = "Po"
      s += " " + str(ele["shape_code"])
      s += " " + str(uc(ele["x0"]))
      s += " " + str(uc(ele["y0"]))
      s += " " + str(uc(ele["x1"]))
      s += " " + str(uc(ele["y1"]))
      s += " " + str(uc(ele["width"]))

      tracks.append( s )

      s = "De " + str(ele["layer"])
      if  ele["type"] == "via": s += " 1"
      else: s += " 0"
      s += " " + str(ele["netcode"])
      s += " " + str(ele["timestamp"])
      s += " " + str(ele["status"])

      tracks.append( s )

  print "$TRACK"
  for t in tracks:
    print t

  print "$EndTRACK"

  print "$ZONE"
  print "$EndZONE"

  for ele in eles:
    ele_type = ele["type"]

    if ele_type == "czone":
      print "$CZONE_OUTLINE"

      nc = int( ele["netcode"] )
      print "ZInfo", ele["timestamp"], ele["netcode"], "\"" + eqpot[ nc ]["net_name"] + "\""
      print "ZLayer", ele["layer"]
      print "ZAux", len( ele["zcorner"] ), ele["hatching_option"]
      print "ZClearance", uc(ele["clearance"]), ele["pad_option"]
      print "ZMinThickness", uc(ele["min_thickness"])
      print "ZOptions", ele["fill"], ele["arc"], "F", uc(ele["antipad_thickness"]), uc(ele["thermal_stub_width"])
      print "ZSmoothing", uc(ele["zsmoothing_x"]), uc(ele["zsmoothing_y"])

      for i, z in enumerate(ele["zcorner"]):
        k = 0
        if i == len(ele["zcorner"])-1: k = 1
        print "ZCorner", uc(z["x"]), uc(z["y"]), k

      print "$POLYSCORNERS"
      for i, pc in enumerate(ele["polyscorners"]):
        if i == (len(ele["polyscorners"]) - 1):
          print uc(pc["x0"]), uc(pc["y0"]), 1, 0
        else:
          print uc(pc["x0"]), uc(pc["y0"]), uc(pc["x1"]), uc(pc["y1"])


      print "$EndPOLYSCORNERS"
      print "$EndCZONE_OUTLINE"

  print "$EndBOARD"
