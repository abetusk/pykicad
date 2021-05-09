#!/usr/bin/python3
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import re
import sys
import getopt
import json
import copy

VERSION_STR = "0.1.0"

UNIT_SRC = "mm"
UNIT_DEST = "deci-mils"

UNIT_CONV_FACTOR = (10000.0/25.4)
SCALE_FACTOR = 1.0

ART_TYPE = 'polygon'

def toUnit(x):
  return (SCALE_FACTOR * UNIT_CONV_FACTOR * float(x))
  #return int(SCALE_FACTOR * UNIT_CONV_FACTOR * float(x))

art_polygon_template = {
  "rotation": 0,
  "x": 0,
  "y": 0,
  "layer": 27,
  "width": 0.0,
  "angle": 0,
  "shape":"polygon",
  "layer_name":"Eco2.User",
  "points": []
}

json_mod_template = {
  "attribute": [ " SMD" ], 
  "attr":"virtual",
  "library_name": "custom", 
  "layer": "15", 
  "layer_name": "F.Cu", 
  "attribute1": "00000000", 
  "art": [ ], 
  "name": "custom", 
  "keyword": [ " custom art " ], 
  "tags":"_art",
  "bounding_box":[[0,0],[100,100]],
  "descr": "custom art part",
  "tedit": "5FCCA526",
  "text": [
    {
      "layer": "21",
      "text": "ref", 
      "misc": " N \"REF\"",
      "sizex": 200.0, "sizey": 200.0, 
      "x": 0.0, "y": -400.0, 
      "angle": 0.0, 
      "number": "0", 
      "visible": True, 
      "flag": "N", 
      "rotation": "0", 
      "penwidth": 50.0
    }, 
    {
      "layer": "21", 
      "misc": " N \"VAL***\"", 
      "number": "1", 
      "sizex": 200.0, "sizey": 200.0, 
      "x": 0.0, "y": 400.0, 
      "angle": 0.0, 
      "visible": True, 
      "flag": "N", 
      "text": "val",
      "rotation": "0", 
      "penwidth": 50.0
    }
  ], 
  "timestamp_op": "0", 
  "rotation_cost_180": "0", 
  "attribute2": "~~", 
  "x": 0.0, 
  "y": 0.0, 
  "rotation_cost_misc": "0", 
  "pad": [ ],
  "timestamp": "4E16AFB4", 
  "units": "deci-mils", 
  "rotation_cost_90": "0", 
  "angle": 0.0, 
  "orientation": "0"
}


def version(fp):
  fp.write("kicad_mod2json v" + VERSION_STR + "\n")

def usage(fp):
  fp.write("\nusage:\n")
  fp.write("\n")
  fp.write("  gp2json_mod_art [-h] [-v] [-i ifn] [-s scale] [ifn]\n")
  fp.write("\n")
  fp.write("  [-s]          rescale factor\n")
  fp.write("  [--deci-thou] input in imperial deci-thou (\"deci-mils\")\n")
  fp.write("  [--mm]        input in mm (default)\n")
  fp.write("  [--simple]    create simple outline (segments only, no polygon)\n")
  fp.write("  [-h]          help\n")
  fp.write("  [-v]          version\n")
  fp.write("\n")

def main():
  global ART_TYPE
  global SCALE_FACTOR
  try:
    opts, args = getopt.getopt(sys.argv[1:], "hi:o:vs:", ["help", "version", "rescale=", "simple", "deci-thou", "mm"])
  except getopt.GetoptError as err:
    print(err)
    usage(sys.stderr)
    sys.exit(2)

  ifn = ""
  ofn = ""
  ofp = sys.stdout

  for o,a in opts:
    if o in ("-h", "--help"):
      usage(sys.stdout)
      sys.exit(0)
    elif o in ("-v", "--version"):
      version(sys.stdout)
      sys.exit(0)
    elif o == "-i":
      ifn = a
    elif o in ("-s", "--rescale"):
      SCALE_FACTOR = float(a)
    elif o in ("--simple"):
      ART_TYPE = 'segment'
    elif o in ("--deci-thou", "--deci-mils"):
      UNIT_CONV_FACTOR = 1.0
    elif o in ("--mm"):
      UNIT_CONV_FACTOR = 10000.0/25.4
    else:
      assert False, "option not found"

  if len(args) > 0:
    if len(ifn) != 0:
      sys.stderr.write("input file must be specified only once\n")
      usage(sys.stderr)
      sys.exit(2)
    ifn = args[0]

  if len(ifn)==0:
    sys.stderr.write("provide input file\n")
    usage(sys.stderr)
    sys.exit(2)

  if len(ofn) != 0:
    ofp = open(ofp, "w")

  weak_pgns = []
  pgn = []

  line_no = 0

  data = {}
  with open(ifn) as ifp:
    for line in ifp:
      line_no+=1
      line = line.strip()
      if len(line)==0:
        if len(pgn) > 0:
          weak_pgns.append(pgn)
          pgn = []
        continue
      if line[0] == '#': continue
      tok = line.split(" ")
      if len(tok) != 2:
        sys.stderr.write("input error on line " + str(line_no) +  ", expected 2 tokens (" + str(line) + ")\n")
        sys.exit(-1)
      x = toUnit(float(tok[0]))
      y = toUnit(float(tok[1]))

      pgn.append([x,y])

  json_mod = copy.copy(json_mod_template)

  art_entry = {}
  for pgn in weak_pgns:

    if ART_TYPE == 'polygon':
      art_entry = copy.deepcopy(art_polygon_template)
      for xy in pgn:
        art_entry["points"].append( { "x" : xy[0], "y": xy[1] } )
      json_mod["art"].append(art_entry)

    elif ART_TYPE == 'segment':
      first = True
      xy_prv = [0,0]
      for xy in pgn:
        #art_entry = copy.deepcopy(art_segment_template)
        if not first:
          json_mod["art"].append({"shape":"segment", "layer":"27", "startx":xy_prv[0], "starty":xy_prv[1], "endx":xy[0], "endy":xy[1], "line_width":50})
        xy_prv = [xy[0], xy[1]]
        first = False

  print(json.dumps(json_mod, indent=2))


if __name__ == "__main__":
  main()


