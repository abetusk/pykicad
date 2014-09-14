#!/usr/bin/python
#
# create the:
#
# (footprint|component)_(location|list_default).json
#
# files.


import os
import sys
import urllib
import json
import re

BASE_LIB = os.path.join( "eeschema", "json" )
BASE_MOD = os.path.join( "pcb", "json" )

component_location = {}
component_list_default = []

footprint_location = {}
footprint_list_default = []

def para_quote( s ):
  s = urllib.quote(s)
  s = re.sub( "/", "%2F", s )
  return urllib.quote(s)

def process_and_fill( hash_loc, list_menu, BASE, fn ):

  cur_ele = {}
  prev_parent = ""

  #f = open("base_lib.raw")
  f = open( fn )
  for line in f:
    line = line.rstrip()
    parent,raw_name = line.split( " " )

    if prev_parent != parent:
      if len(prev_parent) > 0:
        #component_list_default.append( cur_ele )
        list_menu.append( cur_ele )
      cur_ele = {}
      cur_ele["id"] = parent
      cur_ele["name"] = parent
      #cur_ele["data"] = os.path.join( BASE_LIB, parent )
      cur_ele["data"] = os.path.join( BASE, parent )
      cur_ele["type"] = "list"
      cur_ele["list"] = []

    enc_name = para_quote( raw_name )

    e = {}
    e["id"] = raw_name
    e["name"] = raw_name
    #e["data"] = os.path.join( BASE_LIB, parent, enc_name + ".json"  )
    e["data"] = os.path.join( BASE, parent, enc_name + ".json"  )
    e["type"] = "element"

    cur_ele["list"].append( e )

    #component_location[ raw_name ] = { "name" : raw_name, "location" : os.path.join( BASE_LIB, parent, enc_name + ".json" ) }
    hash_loc[ raw_name ] = { "name" : raw_name, "location" : os.path.join( BASE, parent, enc_name + ".json" ) }

    prev_parent = parent

  f.close()

process_and_fill( component_location, component_list_default, BASE_LIB, "base_lib.raw" )

fp = open( "component_location.json", "w" )
json.dump( component_location, fp, indent=2 )
fp.close()

fp = open( "component_list_default.json", "w" )
json.dump( component_list_default, fp, indent=2 )
fp.close()

process_and_fill( footprint_location, footprint_list_default, BASE_MOD, "base_mod.raw" )

fp = open( "footprint_location.json", "w" )
json.dump( footprint_location, fp, indent=2 )
fp.close()

fp = open( "footprint_list_default.json", "w" )
json.dump( footprint_list_default, fp, indent=2 )
fp.close()


