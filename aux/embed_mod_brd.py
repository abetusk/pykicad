#!/usr/bin/python3

import json
import sys

brd_template = {
  "units" : "deci-mils",
  "equipot": [{"net_name":"", "net_number":0}],
  "net_class": [{
    "name":"Default",
    "via_diameter": 472,
    "via_drill_diameter": 250,
    "uvia_drill_diameter": 50,
    "track_width": 100,
    "uvia_diameter": 200,
    "clearance": 100,
    "net": [],
    "unit": "deci-thou",
    "description": "This is the default net class."
  }],
  "element":[],
  "net_code_map": { "0": "" },
  "net_name_map": { "": 0 },
  "brd_to_sch_net_map": {},
  "sch_to_brd_net_map": {},
  "sch_pin_id_net_map": {},
  "net_code_airwire_map": {}
}

_mod_json = {}
with open(sys.argv[1]) as fp:
  _mod_json = json.loads(fp.read())


brd_template["element"].append(_mod_json)
brd_template["element"][0]["type"] = "module"

print(json.dumps(brd_template, indent=2))


