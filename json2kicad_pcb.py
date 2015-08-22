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
converts from bleepsix JSON KiCAD format to kicad_pcb format
"""

import re
import sys
import math
import numpy
import json
import time
import datetime

VERSION="pykicad json2kicad_pcb.py 2015-08-10"
SRC_UNIT = "deci-thou"
DST_UNIT = "mm"

FP_TEXT_LOOKUP = { 0 : "reference", 1:"value", 2:"user", "0":"reference", "1":"value", "2":"user" }

PAD_TYPE_LOOKUP = { "STD" : "thru_hole", "HOLE" : "np_thru_hole", "SMD" : "smd", "CONN" : "connect" }
PAD_SHAPE_LOOKUP = { "rectangle" : "rect", "circle" : "circle", "oblong" : "oval", "trapeze" : "trapezoid" }

LAYERS = [ (0, "B.Cu", "signal"),
      (1, "Inner1.Cu", "signal"),
      (2, "Inner2.Cu", "signal"),
      (15, "F.Cu", "signal"),
      (20, "B.SilkS", "user"),
      (21, "F.SilkS", "user"),
      (22, "B.Paste", "user"),
      (23, "F.Paste", "user"),
      (24, "Dwgs.User", "user"),
      (25, "Cmts.User", "user"),
      (26, "Eco1.User", "user"),
      (27, "Eco2.User", "user"),
      (28, "Edge.Cuts", "user"),
      (31, "B.Cu", "signal"),
      (32, "B.Adhes", "user"),
      (33, "F.Adhes", "user"),
      (34, "B.Paste", "user"),
      (35, "F.Paste", "user"),
      (36, "B.SilkS", "user"),
      (37, "F.SilkS", "user"),
      (38, "B.Mask", "user"),
      (39, "F.Mask", "user"),
      (40, "Dwgs.User", "user"),
      (41, "Cmts.User", "user"),
      (42, "Eco1.User", "user"),
      (43, "Eco2.User", "user"),
      (44, "Edge.Cuts", "user") ]

SETUP = """(last_trace_width 0.254)
    (trace_clearance 0.254)
    (zone_clearance 0.508)
    (zone_45_only no)
    (trace_min 0.254)
    (segment_width 0.2)
    (edge_width 0.1)
    (via_size 1.19888)
    (via_drill 0.635)
    (via_min_size 0.889)
    (via_min_drill 0.508)
    (uvia_size 0.508)
    (uvia_drill 0.127)
    (uvias_allowed no)
    (uvia_min_size 0.508)
    (uvia_min_drill 0.127)
    (pcb_text_width 0.3)
    (pcb_text_size 1.5 1.5)
    (mod_edge_width 0.15)
    (mod_text_size 1 1)
    (mod_text_width 0.15)
    (pad_size 1.5 1.5)
    (pad_drill 0.6)
    (pad_to_mask_clearance 0)
    (aux_axis_origin 0 0)
    (visible_elements 7FFFFFFF)
    (pcbplotparams
      (layerselection 0x00030_80000001)
      (usegerberextensions true)
      (excludeedgelayer true)
      (linewidth 0.150000)
      (plotframeref false)
      (viasonmask false)
      (mode 1)
      (useauxorigin false)
      (hpglpennumber 1)
      (hpglpenspeed 20)
      (hpglpendiameter 15)
      (hpglpenoverlay 2)
      (psnegative false)
      (psa4output false)
      (plotreference true)
      (plotvalue true)
      (plotinvisibletext false)
      (padsonsilk false)
      (subtractmaskfromsilk false)
      (outputformat 1)
      (mirror false)
      (drillshape 1)
      (scaleselection 1)
      (outputdirectory \"\"))"""

def ac_r(ang):
  return "{:.2f}".format(math.degrees(ang))

def layer_mask_to_namelist(mask_str):
  rlist = []
  mask = int(mask_str, 16)
  for lll in LAYERS:
    layer_name = lll[1]
    layer_num = lll[0]
    if (mask & (1<<layer_num)):
      rlist.append(layer_name)
  return rlist

def layer_num_to_name(layer_num):
  for lll in LAYERS:
    if lll[0] == int(layer_num):
      return lll[1]

  print "ERROR: could not find layer_num:", layer_num
  return ""

def update_bounds(area_bouds, pnt):
  if area_bounds[0][0] > float(pnt[0]):
    area_bounds[0][0] = pnt[0]
  if area_bounds[0][1] > float(pnt[1]):
    area_bounds[0][1] = pnt[1]

  if area_bounds[1][0] < float(pnt[0]):
    area_bounds[1][0] = pnt[0]
  if area_bounds[1][1] < float(pnt[1]):
    area_bounds[1][1] = pnt[1]

class json2kicad_pcb:
  def __init__(self):
    pass

# unit convert
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

  if infile != "-":
    with open(infile) as fp:
      #s = fp.readlines()
      for line in fp:
        s += line
  else:
    s = sys.stdin.readlines()

  json_data = json.loads(s)

  SRC_UNIT = "mm"
  if "units" in json_data:
    SRC_UNIT = json_data["units"]
  DST_UNIT = "mm"

  dt = datetime.datetime.now()
  str_dt = dt.strftime("%Y-%m-%d %H:%M:%S")
  tz = time.strftime("%Z", time.gmtime())
  human_str_dt = dt.strftime("%a %d %b %Y %I:%M:%S") + " " + tz

  brd_info = { "n_zone" : 0, "n_module":0, "n_net":0, "n_track":0 }
  area_bounds = [ [0,0], [0,0] ]
  first_pass = True
  for ele in json_data["element"]:
    if "type" not in ele: continue
    typ = ele["type"]

    if typ == "drawsegment" or typ == "track":
      if typ == "track": brd_info["n_track"] += 1
      if first_pass:
        area_bounds[0][0] = float(ele["x0"])
        area_bounds[0][1] = float(ele["y0"])
        area_bounds[1][0] = float(ele["x0"])
        area_bounds[1][1] = float(ele["y0"])
      update_bounds(area_bounds, [ float(ele["x0"]), float(ele["y0"]) ] )
      update_bounds(area_bounds, [ float(ele["x1"]), float(ele["y1"]) ] )
      first_pass = False
    elif typ == "czone":
      brd_info["n_zone"]+=1

      for zc in ele["zcorner"]:
        if first_pass:
          area_bounds[0][0] = float(zc["x"])
          area_bounds[0][1] = float(zc["y"])
          area_bounds[1][0] = float(zc["x"])
          area_bounds[1][1] = float(zc["y"])
        update_bounds(area_bounds, [ float(zc["x"]), float(zc["y"]) ] )
        first_pass = False
      for pc in ele["polyscorners"]:
        if first_pass:
          area_bounds[0][0] = float(pc["x0"])
          area_bounds[0][1] = float(pc["y0"])
          area_bounds[1][0] = float(pc["x0"])
          area_bounds[1][1] = float(pc["y0"])
        update_bounds(area_bounds, [ float(pc["x0"]), float(pc["y0"]) ] )
        first_pass = False
    elif typ == "module":
      brd_info["n_module"] += 1
      if "text" in ele:
        for txt_ele in ele["text"]:
          if first_pass:
            area_bounds[0][0] = float(txt_ele["x"])
            area_bounds[0][1] = float(txt_ele["y"])
            area_bounds[1][0] = float(txt_ele["x"])
            area_bounds[1][1] = float(txt_ele["y"])
          update_bounds(area_bounds, [ float(txt_ele["x"]), float(txt_ele["y"]) ] )
          first_pass = False
      if "art" in ele:
        for art_ele in ele["art"]:
          if "shape" in art_ele and art_ele["shape"] == "segment":

            if first_pass:
              area_bounds[0][0] = float(art_ele["startx"])
              area_bounds[0][1] = float(art_ele["starty"])
              area_bounds[1][0] = float(art_ele["startx"])
              area_bounds[1][1] = float(art_ele["starty"])
            update_bounds(area_bounds, [ float(art_ele["startx"]), float(art_ele["starty"]) ] )
            update_bounds(area_bounds, [ float(art_ele["endx"]), float(art_ele["endy"]) ] )
            first_pass = False

          elif "shape" in art_ele and art_ele["shape"] == "arc":
            if first_pass:
              area_bounds[0][0] = float(art_ele["x"])
              area_bounds[0][1] = float(art_ele["y"])
              area_bounds[1][0] = float(art_ele["x"])
              area_bounds[1][1] = float(art_ele["y"])
            update_bounds(area_bounds, [ float(art_ele["x"]), float(art_ele["y"]) ] )
            first_pass = False
      if "pad" in ele:
        for pad_ele in ele["pad"]:
          if first_pass:
            area_bounds[0][0] = float(pad_ele["posx"])
            area_bounds[0][1] = float(pad_ele["posy"])
            area_bounds[1][0] = float(pad_ele["posx"])
            area_bounds[1][1] = float(pad_ele["posy"])
          update_bounds(area_bounds, [ float(pad_ele["posx"]), float(pad_ele["posy"]) ] )
          first_pass = False

  for v in json_data["equipot"]:
    brd_info["n_net"] += 1

  board_thickness = 630

  print "(kicad_pcb (version 4) (host json2kicad_pcb \"" + str_dt + "\")"
  print ""
  print "  (general"
  print "    (links 0)"
  print "    (no_connects 0)"
  print "    (area " + " ".join(map(str, map(uc, [ item for sublist in area_bounds for item in sublist ]))) + ")"
  print "    (thickness " + str(uc(board_thickness)) + ")"
  #print "    (thickness 1.6)"
  print "    (drawings 0)"
  print "    (tracks " + str(brd_info["n_track"]) + ")"
  print "    (zones " + str(brd_info["n_zone"]) + ")"
  print "    (modules " + str(brd_info["n_module"]) + ")"
  print "    (nets " + str(brd_info["n_net"]) + ")"
  print "  )"
  print ""
  print "  (page A3)"
  print "  (title_block"
  print "    (date \"30 dec 2015\")"
  print "  )"
  print ""
  print "  (layers"
  for v in LAYERS:
    print "  (" + str(v[0]) + " " + str(v[1]) + " " + str(v[2]) + ")"
  print "  )"
  print ""
  print "  (setup"
  print SETUP
  print "  )"
  print ""

  NET_LOOKUP = {}

  for v in json_data["equipot"]:
    print "  (net", v["net_number"], "\"" + v["net_name"] + "\")"
    NET_LOOKUP[str(v["net_number"])] = v["net_name"]
    NET_LOOKUP[int(v["net_number"])] = v["net_name"]
  print ""

  for net_class_name in json_data["net_class"]:

    valid_net_kw = { "clearance" : "clearance", "via_diameter":"via_dia", "via_drill_diameter": "via_drill",
                  "uvia_diameter" : "uvia_dia", "uvia_drill_diameter" : "uvia_drill", "track_width" : "trace_width" }

    ele = json_data["net_class"][net_class_name]

    print "  (net_class " + str(ele["name"]) + " \"" + str(ele["description"]) + "\""
    for ke in ele:
      if ke not in valid_net_kw: continue
      field = valid_net_kw[ke]
      if type(ele[ke]) == type("") or type(ele[ke]) == unicode:
        #print "    (" + str(ke) + " \"" + str(ele[ke]) + "\")"
        print "    (" + str(field) + " \"" + str(ele[ke]) + "\")"
      elif type(ele[ke]) == type(1.25) or type(ele[ke]) == type(1):
        #print "    (" + str(ke) + " " + str(uc(ele[ke])) + ")"
        print "    (" + str(field) + " " + str(uc(ele[ke])) + ")"
      else:
        #print "    (" + str(ke) + " " + str(ele[ke]) + ")"
        print "    (" + str(field) + " " + str(ele[ke]) + ")"
    for net in NET_LOOKUP:
      print "    (add_net \"" + str(NET_LOOKUP[net]) + "\")"
    print "  )"

  for ele in json_data["element"]:
    if "type" in ele and ele["type"] == "drawsegment":
      t = "  "
      t += "(gr_line"
      t += " (start " + str(uc(ele["x0"])) + " " + str(uc(ele["y0"])) + ")" 
      t += " (end " + str(uc(ele["x1"])) + " " + str(uc(ele["y1"])) + ")" 
      t += " (angle " + ac_r(float(ele["angle"])) + ")"
      t += " (width " + str(uc(ele["width"])) + ")"
      t += " (layer " + str(layer_num_to_name(ele["layer"])) + ")"
      t += ")"
      print t
    elif "type" in ele and ele["type"] == "track":
      t = "  "
      t += "(segment"
      t += " (start " + str(uc(ele["x0"])) + " " + str(uc(ele["y0"])) + ")" 
      t += " (end " + str(uc(ele["x1"])) + " " + str(uc(ele["y1"])) + ")" 
      t += " (width " + str(uc(ele["width"])) + ")"

      layer_name = layer_num_to_name(ele["layer"])

      t += " (layer " + str(layer_name) + ")"
      t += " (net " + str(ele["netcode"]) + ")"
      t += ")"
      print t
    elif "type" in ele and ele["type"] == "czone":
      t = "  "
      t += "(zone"
      t += " (net " + str(ele["netcode"]) + ")"

      net_name = NET_LOOKUP[ele["netcode"]]
      t += " (net_name " + str(net_name) + ")"

      layer_name = layer_num_to_name(ele["layer"])

      t += " (layer " + str(layer_name) + ")"
      t += " (tstamp 0)"
      t += " (hatch edge " + str(uc(200)) + ")"
      t += "\n   "
      t += " (connect_pads (clearance " + str(uc(ele["clearance"])) + "))"
      t += " (min_thickness " + str(uc(ele["min_thickness"])) + ")"
      t += " (fill (arc_segments 16) (thermal_gap " + str(uc(ele["thermal_stub_width"])) + ")"
      t += "  (thermal_bridge_width " + str(uc(ele["antipad_thickness"])) + "))"
      t += "\n   "

      t += " (polygon"
      t += " (pts\n"
      for zc in ele["zcorner"]:
        t += "      (xy " + str(uc(zc["x"])) + " " + str(uc(zc["y"])) + ")\n"
      t += "    ))"

      
      t += "\n"
      t += "    (filled_polygon"
      t += " (pts\n"
      for pc in ele["polyscorners"]:
        t += "      (xy " + str(uc(pc["x0"])) + " " + str(uc(pc["y0"])) + ")\n"
      t += "    ))\n"
      t += "  )"
      print t
    elif "type" in ele and ele["type"] == "module":
      print "  (module \"" + ele["name"] + "\""

      layer_name = layer_num_to_name(ele["layer"])
      print "    (layer \"" + str(layer_name) + "\")"
      print "    (tedit 0)"
      print "    (tstamp 0)"
      print "    (at " + str(uc(ele["x"])) + " " + str(uc(ele["y"])) + " " + ac_r(float(ele["angle"])) + ")"

      # todo:
      # * layer to text layer conversion (lookup)
      # * angle to degree from radians
      # * rpelace ?? with correct value (reference, value, user)
      #
      if "text" in ele:
        for txt_ele in ele["text"]:

          fp_txt = "user"
          if int(txt_ele["number"])<2:
            fp_txt = FP_TEXT_LOOKUP[txt_ele["number"]]
          if fp_txt == "": fp_txt = "user"

          print "    (fp_text " + fp_txt + " \"" + txt_ele["text"] + "\""
          print "      (at " + str(uc(txt_ele["x"])) + " " + str(uc(txt_ele["y"])) + " " + ac_r(float(txt_ele["angle"])) + ")"

          layer_name = layer_num_to_name(txt_ele["layer"])

          print "      (layer " + str(layer_name) + ")"
          print "      (effects (font (size " + str(uc(txt_ele["sizex"])) + " " + str(uc(txt_ele["sizey"])) + ")"
          print "        (thickness " + str(uc(txt_ele["penwidth"])) + ")))"
          print "    )"

      if "art" in ele:
        for art_ele in ele["art"]:
          if "shape" in art_ele and art_ele["shape"] == "segment":
            t = "    "
            t += "(fp_line"
            t += " (start " + str(uc(art_ele["startx"])) + " " + str(uc(art_ele["starty"])) + ")"
            t += " (end " + str(uc(art_ele["endx"])) + " " + str(uc(art_ele["endy"])) + ")"

            layer_name = layer_num_to_name(art_ele["layer"])

            t += " (layer " + str(layer_name) + ")"
            t += " (width " + str(uc(art_ele["line_width"])) + ")"
            t += ")"
            print t
          elif "shape" in art_ele and art_ele["shape"] == "arc":
            t = "    "
            t += "(fp_arc"

            x = float(art_ele["x"])
            y = float(art_ele["y"])
            #x = float(art_ele["start_x"])
            #y = float(art_ele["start_y"])
            a = float(art_ele["angle"])
            sa = float(art_ele["start_angle"])
            r = float(art_ele["r"])

            sx = x
            sy = y
            ex = math.cos(sa)*r + x
            ey = math.sin(sa)*r + y
            #sx =  math.sin(sa)*r + math.cos(sa)*r
            #sy = -math.cos(sa)*r + math.sin(sa)*r
            #ex =  math.sin(sa+a)*r + math.cos(sa+a)*r
            #ey = -math.cos(sa+a)*r + math.sin(sa+a)*r

            #t += " (start " + str(uc(art_ele["x"])) + " " + str(uc(art_ele["y"])) + ")"
            t += " (start " + str(uc(sx)) + " " + str(uc(sy)) + ")"
            t += " (end "   + str(uc(ex)) + " " + str(uc(ey)) + ")"

            t += " (angle " + ac_r(float(art_ele["angle"])) + ")"

            layer_name = layer_num_to_name(art_ele["layer"])

            t += " (layer " + str(layer_name) + ")"
            t += " (width " + str(uc(art_ele["line_width"])) + ")"
            t += ")"
            print t

      if "pad" in ele:
        for pad_ele in ele["pad"]:
          if "name" not in pad_ele or pad_ele["name"] == "": continue
          t = "    "
          t += "(pad"
          t += " " + str(pad_ele["name"])
          t += " " + PAD_TYPE_LOOKUP[str(pad_ele["type"])]
          t += " " + PAD_SHAPE_LOOKUP[str(pad_ele["shape"])]
          t += " (at " + str(uc(pad_ele["posx"])) + " " + str(uc(pad_ele["posy"])) + " " + ac_r(float(pad_ele["angle"])) + ")"
          t += " (size " + str(uc(pad_ele["sizex"])) + " " + str(uc(pad_ele["sizey"])) + ")"
          t += " (drill " + str(uc(pad_ele["drill_diam"])) + ")"

          layer_name_array = layer_mask_to_namelist(pad_ele["layer_mask"])
          layer_names = '"' + '" "'.join(layer_name_array) + '"'

          t += " (layers " + str(layer_names) + ")"

          net_num = 0
          if "net_number" in pad_ele: net_num = pad_ele["net_number"]
          net_name = "\"\""

          if "net_name" in pad_ele:
            net_name = pad_ele["net_name"]
          elif net_num in NET_LOOKUP:
            net_name = NET_LOOKUP[net_num]
          if net_name == "":
            net_name = "\"\""
            if net_num in NET_LOOKUP: net_name = NET_LOOKUP[net_num]
          t += " (net " + str(net_num) + " " + str(net_name) + ")"

          t += ")"
          print t
          pass

      print "  )"
      print ""


  print ")"

