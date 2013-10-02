#!/usr/bin/python

import os
import re
import datetime

footprint = "smd_qfp"
footprint_opt = [ "sot23", "smd_sil", "smd_dil", "smd_qfp", "th_sil", "th_dil", "th_qp" ]
footprint_descr = [ 
  "sot23", 
  "smd sil", "smd dil", "smd qfp",
  "throughole sil", "throughhole dil", "throughole qp"
]

center_shape = "none"
center_shape_opt = [ "none", "circle", "rect" ]
center_shape_descr = [ "none", "circle", "rectangle" ]

pad_shape = "rect"
pad_shape_opt = [ "rect", "circle", "obround" ]
pad_shape_descr = [ "rectangle", "circle", "obround" ]

jitter_flag = False

g_layer_mask = "00888000"

def landing_pad_rect( name, posx, posy, xlen, ylen, orient = 0, drill_radius = 0, jitter_x = 0, jitter_y = 0  ):

  print "$PAD"
  print "Sh \"" + str(name) + "\"", "R", str(xlen), str(ylen), str(0), str(0), str(orient)
  print "Dr", str(drill_radius), int(jitter_x), int(jitter_y)
  if drill_radius > 0:
    print "At STD N", g_layer_mask
  else:
    print "At SMD N", g_layer_mask
  print "Ne 0 \"\""
  print "Po", str(posx), str(posy)
  print "$EndPAD"

def landing_pad_circle( name, posx, posy, radius, orient = 0, drill_radius = 0, jitter_x = 0, jitter_y = 0 ):

  print "$PAD"
  print "Sh \"" + str(name) + "\"", "C", str(xlen), str(ylen), str(0), str(0), str(orient)
  print "Dr", str(drill_radius), int(jitter_x), int(jitter_y)
  if drill_radius > 0:
    print "At STD N", g_layer_mask
  else:
    print "At SMD N", g_layer_mask
  print "Ne 0 \"\""
  print "Po", str(posx), str(posy)
  print "$EndPAD"

def landing_pad_obround( name, posx, posy, xlen, ylen, orient = 0, drill_radius = 0, jitter_x = 0, jitter_y = 0 ):

  print "$PAD"
  print "Sh \"" + str(name) + "\"", "O", str(xlen), str(ylen), str(0), str(0), str(orient)
  print "Dr", str(drill_radius), int(jitter_x), int(jitter_y)
  if drill_radius > 0:
    print "At STD N", g_layer_mask
  else:
    print "At SMD N", g_layer_mask
  print "Ne 0 \"\""
  print "Po", str(posx), str(posy)
  print "$EndPAD"


def sil_footprint_vertical( startx, starty, xlen, ylen, ds, n ):
  pass

def sil_footprint_horizontal( startx, starty, xlen, ylen, dy, n ):
  pass


def quad_footprint( startx, starty, x_pad_len, y_pad_len, width, height, n ):
  pass

n = 8
startx = 0
starty = 0
dx = 350
dy = 300

padx = 200
pady = 150

radius = 45

width = 1000
height = 710

g_module_name = "test_part"
g_layer = 15
g_hex_timestamp = "4E16AFB4" #???
g_pad_type_flag = "smd"


g_name_posx = 0
g_name_posy = 0

g_val_posx = 0
g_val_posy = 0

font_height = 200
font_buffer = 200

if footprint == "smd_sil" or footprint == "th_sil":

  h = (n-1)*dy
  g_name_posy = -h/2 - pady/2 - font_height - font_buffer
  g_val_posy  =  h/2 + pady/2 + font_height + font_buffer


elif footprint == "smd_dil" or footprint == "th_dil":

  n_left = int( (n+1) / 2 ) 
  h = (n_left - 1)*dy
  g_name_posy = -h/2 - pady/2 - font_height - font_buffer
  g_val_posy  =  h/2 + pady/2 + font_height + font_buffer


  #print "n_left", n_left, "h", h

elif footprint == "smd_qfp" or footprint == "th_qf":

  n_left = int( (n+3) / 4 ) 
  h = (n_left - 1)*dy
  g_name_posy = -h/2 - pady/2 - font_height/2
  g_val_posy  =  h/2 + pady/2 + font_height/2

print "PCBNEW-LibModule-V1 ", datetime.datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
print "# encoding utf-8"
#print "Units deci-mils"
print "$INDEX"
print g_module_name 
print "$EndINDEX"
print "$MODULE", g_module_name
print "Po 0 0 0", g_layer, g_hex_timestamp, "00000000", "~~"
print "Li", g_module_name
print "Cd", g_module_name, g_pad_type_flag.lower(), "package"
print "Kw", g_module_name, g_pad_type_flag.upper(), g_pad_type_flag.lower()
print "Sc 0"
print "AR"
print "Op 0 0 0"
print "At", g_pad_type_flag.upper()
print "T0", g_name_posx, g_name_posy, "200", "200", "0", "50", "V", "21", "N", "\"" + g_module_name + "\""
print "T1", g_val_posx, g_val_posy, "200", "200", "0", "50", "V", "21", "N", "\"VAL***\""



# grahpics if we want them
#print "DS", sx, sy, ex, ey, pw, lyr

name_map = []
for i in range(n):
  name_map.append(i+1)
  #name_map[i] = i+1

if footprint == "smd_sil" or footprint == "th_sil":

  drill_rad = 0
  if footprint == "th_sil":
    drill_rad = 50
    g_layer_mask = "8880008888"


  for k in range(n):
    px = startx
    py = starty + dy * k

    name = name_map[k]

    if pad_shape == "rect":
      landing_pad_rect( k, px, py, padx, pady, 900, drill_rad )
    elif pad_shape == "circle":
      landing_pad_circle( k, px, py, radius, drill_rad )
    elif pad_shape == "obround":
      landing_pad_obround( k, px, py, padx, pady, 900, drill_rad )

elif footprint == "smd_dil" or footprint == "th_dil":

  n_left = int( (n+1) / 2 )
  n_right = n - n_left

  h_shift = int(float((n_left-1)*dy)/2.0)

  drill_rad = 0
  if footprint == "th_dil":
    drill_rad = 50
    g_layer_mask = "8880008888"


  for k in range(n_left):
    px = startx - width/2
    py = starty + dy * k - h_shift

    name = name_map[k]

    if pad_shape == "rect":
      landing_pad_rect( name, px, py, padx, pady, 900, drill_rad )
    elif pad_shape == "circle":
      landing_pad_circle( name, px, py, radius, drill_rad )
    elif pad_shape == "obround":
      landing_pad_obround( name, px, py, padx, pady, 900, drill_rad )

  for k in range(n_right):
    px = startx + width/2
    py = starty + dy * k - h_shift

    name = name_map[k + n_left]

    if pad_shape == "rect":
      landing_pad_rect( name, px, py, padx, pady, 2700, drill_rad )
    elif pad_shape == "circle":
      landing_pad_circle( name, px, py, radius, drill_rad )
    elif pad_shape == "obround":
      landing_pad_obround( name, px, py, padx, pady, 2700, drill_rad )

elif footprint == "smd_qfp" or footprint == "th_qp":

  n_left  = int( (n+3) / 4 )
  n_bot   = int( (n+2) / 4 )
  n_right = int( (n+1) / 4 )
  n_top   = int( (n)   / 4 )

  h_shift = int( float((n_left-1)*dy) / 2.0 )
  w_shift = int( float((n_bot -1)*dx) / 2.0 )

  drill_rad = 0
  if footprint == "th_qp":
    drill_rad = 50
    g_layer_mask = "8880008888"

  offset = 0


  for k in range(n_left):
    name = name_map[k]

    px = startx - width/2
    py = starty - h_shift + dy * k

    if pad_shape == "rect":
      landing_pad_rect( name, px, py, padx, pady, 900, drill_rad )
    elif pad_shape == "circle":
      landing_pad_circle( name, px, py, radius, drill_rad )
    elif pad_shape == "obround":
      landing_pad_obround( name, px, py, padx, pady, 900, drill_rad )

  offset += n_left

  for k in range(n_bot):
    name = name_map[k + offset]

    px = startx - w_shift  + dx * k
    py = starty + height/2 

    if pad_shape == "rect":
      landing_pad_rect( name, px, py, padx, pady, 0, drill_rad )
    elif pad_shape == "circle":
      landing_pad_circle( name, px, py, radius , drill_rad )
    elif pad_shape == "obround":
      landing_pad_obround( name, px, py, padx, pady, 0, drill_rad )

  offset += n_bot

  for k in range(n_right):
    name = name_map[k + offset]

    px = startx + width/2
    py = starty - h_shift + dy * k

    if pad_shape == "rect":
      landing_pad_rect( name, px, py, padx, pady, 1800, drill_rad )
    elif pad_shape == "circle":
      landing_pad_circle( name, px, py, radius , drill_rad )
    elif pad_shape == "obround":
      landing_pad_obround( name, px, py, padx, pady, 1800 , drill_rad )

  offset += n_right

  for k in range(n_top):
    name = name_map[k + offset]

    px = startx - w_shift + dx * k
    py = starty - height/2 

    if pad_shape == "rect":
      landing_pad_rect( name, px, py, padx, pady, 2700, drill_rad )
    elif pad_shape == "circle":
      landing_pad_circle( name, px, py, radius , drill_rad )
    elif pad_shape == "obround":
      landing_pad_obround( name, px, py, padx, pady, 2700, drill_rad )


print "$EndMODULE", g_module_name

