#!/usr/bin/python
"""
Loads KiCAD lib file, parses it with lib, writes to svg and displays.
Things are still hard coded
"""

import re
import sys
import lib
import math
import numpy
import cgi
import urllib

import SVG

class libsvg(lib.lib):

  def __init__(self):
    self.svg_file = ""
    #self.svg_prefix = "./svg/"
    self.svg_prefix = "./"
    self.svg_suffix = ".svg"
    self.svg_scene = None

    self.counter = 0

    #self.pixel_per_mil = 72.0 / 1000.0
    self.pixel_per_mil = 150.0 / 1000.0
    #self.pixel_per_mil = 300.0 / 1000.0

    self.buffer_pixel = 20

    # bounding box is rough
    self.bounding_box = [ [0,0], [100, 100] ]

    #self.line_width = self.pixel_per_mil * 200.0
    #self.line_width = self.pixel_per_mil * 20.0
    self.line_width = 10

    lib.lib.__init__(self)

  def update_bounds(self, x, y):
    if x < self.bounding_box[0][0]:
      self.bounding_box[0][0] = x

    if x > self.bounding_box[1][0]:
      self.bounding_box[1][0] = x

    if y < self.bounding_box[0][1]:
      self.bounding_box[0][1] = y

    if y > self.bounding_box[1][1]:
      self.bounding_box[1][1] = y

  def cb_header(self, arg):
    pass

  def cb_DEF (self, arg):
    name,reference,unused,text_offset,draw_pinnumber,draw_pinname,unit_count,units_locked,option_flag = arg


    munged_name = re.sub('\/', '#', arg[0] )
    #munged_name = re.sub('\/', 'whack', str(arg[0]) )
    munged_name = urllib.quote( munged_name );

    print "  making:", arg[0], "->", munged_name

    #self.svg_file = self.svg_prefix + str(arg[0]) + self.svg_suffix 
    self.svg_file = self.svg_prefix + munged_name + self.svg_suffix 
    self.svg_scene = SVG.Scene( self.svg_file )

    self.draw_pin_name = True
    if draw_pinname == "N":
      self.draw_pin_name = False

    self.draw_pin_num = True
    if draw_pinnumber == "N":
      self.draw_pin_num = False

    self.bounding_box = [ [0,0], [100, 100] ]

    self.unit_count = int(unit_count)


  def cb_F0 (self, arg):
    reference, posx, posy, text_size, text_orient, visible, htext_justify, vtext_justify = arg

    if visible == "I":
      return

    reference = reference.strip('"')
    x,y = float(posx),-float(posy)

    font_width_height_ratio = 0.6
    font_aspect_ratio = 0.6
    font_size   = float(text_size) / font_aspect_ratio

    font_height = float(text_size)
    font_width = font_size * font_width_height_ratio 

    y += font_height / 2.0
    x -= font_width * len(str(reference)) / 2.0


    angle_deg = 0
    if text_orient == "V" :
      angle_deg = -90

    self.update_bounds( x, y )
    self.update_bounds( x + font_size * len(reference) , y  - font_size * len(reference))

    self.svg_scene.add( SVG.Text( (x, y), cgi.escape(reference), font_size, (0,136,136), angle_deg )  )

  def cb_F1 (self, arg):
    name, posx, posy, text_size, text_orient, visible, htext_justify, vtext_justify = arg

    if visible == "I":
      return

    name = name.strip('"')
    x,y = float(posx),-float(posy)

    font_width_height_ratio = 0.6
    font_aspect_ratio = 0.6

    font_size   = float(text_size) / font_aspect_ratio

    font_height = float(text_size)
    font_width = font_size * font_width_height_ratio 

    ## TODO:
    if vtext_justify:
      if re.search('T', vtext_justify):
        pass
      elif re.search('B', vtext_justify):
        pass
      else:
        y += font_height / 2.0

    ## TODO:
    if htext_justify:
      if htext_justify == "L":
        pass
      else:
        x -= font_width * len(str(name)) / 2.0

    angle_deg = 0
    if text_orient == "V" :
      angle_deg = -90

    self.update_bounds( x, y )
    self.update_bounds( x + font_size * len(name) , y  + font_size * len(name))
    self.svg_scene.add( SVG.Text( (x, y), cgi.escape(name), font_size, (0,136,136), angle_deg )  )


  def cb_F2 (self, arg): pass

  def cb_F3 (self, arg): pass

  def cb_F4 (self, arg): pass
  def cb_F5 (self, arg): pass
  def cb_Fn (self, arg): pass

  def cb_ENDDEF(self, arg):

    w = abs(self.bounding_box[1][0] - self.bounding_box[0][0])
    h = abs(self.bounding_box[1][1] - self.bounding_box[0][1])

    w *= self.pixel_per_mil
    h *= self.pixel_per_mil

    s_x = (self.bounding_box[1][0] - self.bounding_box[0][0]) / 2.0
    s_y = (self.bounding_box[1][1] - self.bounding_box[0][1]) / 2.0

    s_x *= self.pixel_per_mil
    s_y *= self.pixel_per_mil

    w += self.buffer_pixel
    h += self.buffer_pixel

    s_x += self.buffer_pixel/2
    s_y += self.buffer_pixel/2

    self.svg_scene.height = h 
    self.svg_scene.width = w 
    #self.svg_scene.transform = " translate( {0},{1} ) scale( {2},{3} )".format( s_x, s_y, self.pixel_per_mil, -self.pixel_per_mil )
    self.svg_scene.transform = " translate( {0},{1} ) scale( {2},{3} )".format( s_x, s_y, self.pixel_per_mil, self.pixel_per_mil )
    #self.svg_scene.transform = " translate(" + str(s_x) + "," + str(s_y) + ") scale(" + str(self.pixel_per_mil) + ",-" + str(self.pixel_per_mil) + ") "
    self.svg_scene.write_svg( self.svg_file )


  def cb_A(self, arg):
    posx,posy,radius,start_angle,end_angle,unit,convert,thickness,fill,startx,starty,endx,endy = arg

    if int(unit) >= 2:
      return


    if int(unit) >= self.unit_count:
      return

    if convert == "2":
      return

    #x,y,r = float(posx),float(posy),float(radius)
    x,y,r = float(posx),-float(posy),float(radius)

    if startx: sx = float(startx)
    if starty: sy = float(starty)
    if endx: ex = float(endx)
    if endy: ey = float(endy)
    #sx,sy,ex,ey = float(startx),float(starty),float(endx),float(endy)

    # I really don't know what KiCAD is doing.  Taking the minor arc?
    # angles based on center to end points?  I'm being lazy
    # and using angle

    sa = float(start_angle)/10.0
    ea = float(end_angle)/10.0

    
    if ea > sa:
      deg_se = ea - sa
      deg_es = 360 - deg_se
    else:
      deg_es = sa - ea
      deg_se = 360 - deg_es

    if deg_se < deg_es:
      sa_rad = math.radians(sa)
      ea_rad = math.radians(ea)
    else:
      sa_rad = math.radians(ea)
      ea_rad = math.radians(sa)

    prev_x, prev_y = None, None
    if sa_rad > ea_rad:

      for a in numpy.linspace(sa_rad, math.pi, 20):
        #cur_x,cur_y = x + r * math.cos(a), y + r * math.sin(a)
        cur_x,cur_y = x + r * math.cos(-a), y + r * math.sin(-a)
        if prev_x is not None:
          self.svg_scene.add( SVG.Line( (prev_x, prev_y), (cur_x, cur_y), (136,0,0), self.line_width) )
        prev_x,prev_y = cur_x,cur_y

      for a in numpy.linspace(-math.pi, ea_rad, 20):
        #cur_x,cur_y = x + r * math.cos(a), y + r * math.sin(a)
        cur_x,cur_y = x + r * math.cos(-a), y + r * math.sin(-a)
        if prev_x is not None:
          self.svg_scene.add( SVG.Line( (prev_x, prev_y), (cur_x, cur_y), (136,0,0), self.line_width) )
        prev_x,prev_y = cur_x,cur_y

    else:

      for a in numpy.linspace(sa_rad, ea_rad, 20):
        #cur_x,cur_y = x + r * math.cos(a), y + r * math.sin(a)
        cur_x,cur_y = x + r * math.cos(-a), y + r * math.sin(-a)
        if prev_x is not None:
          self.svg_scene.add( SVG.Line( (prev_x, prev_y), (cur_x, cur_y), (136,0,0), self.line_width) )
        prev_x,prev_y = cur_x,cur_y

    return

    #start_arc_x = x + r * math.cos(sa_rad)
    #start_arc_y = y + r * math.sin(sa_rad)
    #end_arc_x = x + r * math.cos(ea_rad)
    #end_arc_y = y + r * math.sin(ea_rad)


    ## SVG not rendering properly?
    #self.svg_scene.add( SVG.Arc( (start_arc_x,start_arc_y), r,r, 0, 0,1 , end_arc_x,end_arc_y , None, (136,0,0), self.line_width ) )


  def cb_C(self, arg):
    posx, posy, radius, unit, convert, thickness, fill = arg
    #x,y,r = float(posx), -float(posy), float(radius)
    x,y,r = float(posx), -float(posy), float(radius)

    fill_color = None
    if fill is not None:
      if fill == "F":
        fill_color = (136,0,0)
      elif fill == "f":
        fill_color = (255,255,136)

    self.svg_scene.add( SVG.Circle( (x, y), r, fill_color, (136,0,0), self.line_width) )

  def cb_P(self, arg):
    point_count,unit,convert,thickness,str_pnts,dummy,fill_opt = int(arg[0]),arg[1],arg[2],arg[3],arg[4],arg[5],arg[6]

    if int(unit) >= 2:
      return

    #if int(unit) >= self.unit_count: return

    if int(convert) == 2:
      return

    if fill_opt is not None:
      fill_opt = fill_opt.replace(" ", "")

    if convert == "2":
      return

    str_pnts = str_pnts.strip()
    str_pnts = re.sub(' +', ' ', str_pnts)
    pnts = str_pnts.split(' ')

    
    prev_x,prev_y =  float(pnts[0]), -float(pnts[1])
    self.update_bounds( float(prev_x), float(prev_y) )

    f_pnts = [ [ float(pnts[0]), -float(pnts[1]) ] ]
    pos = 2
    while pos < len(pnts):
      x,y = float(pnts[pos]), -float(pnts[pos+1])

      if fill_opt:
        if fill_opt != "F" and fill_opt != "f":
          self.svg_scene.add( SVG.Line( (prev_x, prev_y), (x, y), (136,0,0), self.line_width) )
      pos += 2

      f_pnts.append( [ x, y ] )

      prev_x, prev_y = x,y
      self.update_bounds( float(x), float(y) )

    fill_color = None
    if fill_opt:

      if fill_opt == "F":

        fill_color = (136,0,0)
        self.svg_scene.add( SVG.Polygon( f_pnts, fill_color, (136,0,0), self.line_width) )
      if fill_opt == "f":

        fill_color = (255,255,136)
        self.svg_scene.add( SVG.Polygon( f_pnts, fill_color, (136,0,0), self.line_width) )
    else:
      self.svg_scene.add( SVG.Polygon( f_pnts, None, (136, 0, 0), self.line_width ) )


  def cb_S(self, arg):
    startx, starty, endx, endy, unit, convert, thickness, fill = arg

    sx =  int(startx)
    sy = -int(starty)

    ex =  int(endx)
    ey = -int(endy)

    self.update_bounds( float(sx), float(sy) )
    self.update_bounds( float(ex), float(ey) )

    height = abs( float(ey-sy) )
    width  = abs( float(ex-sx) )

    px = min(sx, ex)
    py = min(sy, ey)

    line_width = self.line_width
    self.svg_scene.add( SVG.Rectangle( (px, py), height, width,  "none", (136,0,0), line_width ) )


  def cb_T(self, arg):
    direction,posx,posy,text_size,text_type,unit,convert,text = arg

    x,y = float(posx),-float(posy)

    font_width_height_ratio = 0.6
    font_aspect_ratio = 0.6
    font_size  = float(text_size) / font_aspect_ratio
    font_height = float(text_size)
    font_width = font_size * font_width_height_ratio 


    rot_deg = 0
    if direction == "900":
      rot_deg = -90

    text = text.strip()
    atext = text.split(' ')
    atext[0] = re.sub('~', ' ', atext[0])

    dx,dy = 0,0

    text_type = "C"

    if re.search("C", text_type):
      dx -= font_width * len(atext[0]) / 2
      dy += font_height / 2

    self.svg_scene.add( SVG.Text( (x + dx,y + dy), cgi.escape(str(atext[0])), font_size, (136,0,0), rot_deg ) )



  # WARNING!  num_text_size and name_text_size look to be reversed
  # BUGS:  PGA4311 in audio.lib isn't rendering properly.  Pin numbers are rendered undernath the pin
  #  and pin names are rendered above the pins in Kicad.  I see no way to get those rendering hints
  #  from the pin data or any other of the DEF, F0, F1 or other properties, so PGA4311 is rendered just
  #  like all the other parts, with pin number over the line and name rendered next to the line.
  #  Also looks like AD620 from linear.lib isn't being rendered properly.  How does KiCAD know that it
  #  needs to do this?  Does it see that the text is getting jumbled?
  #
  #  UPDATE 2013-09-29: OK, it looks like it's the text_offset field in the DEF.  Right now I ignore it
  #  (I think), but it should be used.  When it's non-zero, the text is in the format I'm rendering it now
  #  (with the extra text_offset added maybe?) and when it's 0, it's rendered in the other format of
  #  name on top, pin underneath.  
  #
  # TODO: render pin properly with DEF text_offset
  def cb_X(self, arg):
    #name, num, posx, posy, length, direction, name_text_size, num_text_size, unit, convert, electrical_type, pin_type = arg
    name, num, posx, posy, length, direction, num_text_size, name_text_size, unit, convert, electrical_type, pin_type = arg

    if unit == "0" and convert == "0":
      pass
    elif unit == "0" and convert == "1":
      pass
    elif unit == "1" and convert == "0":
      pass
    elif unit == "1" and convert == "1":
      pass
    elif unit != "1" or convert != "1":
      return

    name = name.strip()
    num = num.strip()

    font_width_height_ratio = 0.6
    font_aspect_ratio = 0.6
    num_font_size   = float(num_text_size) / font_aspect_ratio
    name_font_size  = float(name_text_size) / font_aspect_ratio

    name_font_height = float(name_text_size)
    name_font_width = name_font_size * font_width_height_ratio 

    sx, sy = float(posx), -float(posy)
    ex, ey = sx, sy

    self.update_bounds( sx, sy )

    l = float(length)

    pin_num_pos = [ sx - (num_font_size * float(len(num)) / 2 ), sy ]
    num_rot_deg = 0
    if   direction == "R": 
      pin_num_pos[0] += (l / 2) + (len(str(num)) * self.pixel_per_mil * num_font_size / 2.0)
      pin_num_pos[1] -= 40 * self.pixel_per_mil
      ex += l
    elif direction == "D": 
      num_rot_deg = -90
      pin_num_pos = [ sx - (num_font_size * self.pixel_per_mil), sy + (num_font_size * float(len(num)) * self.pixel_per_mil) ]
      pin_num_pos[1] += (l/2)
      ey += l
    elif direction == "L": 
      pin_num_pos[0] -= (l / 2) - (len(str(num)) * self.pixel_per_mil * num_font_size / 2.0)
      pin_num_pos[1] -= 40 * self.pixel_per_mil
      ex -= l
    elif direction == "U": 
      num_rot_deg = -90
      pin_num_pos = [ sx - (num_font_size * self.pixel_per_mil), sy + (num_font_size * float(len(num)) * self.pixel_per_mil) ]
      pin_num_pos[1] -= (l/2)
      ey -= l


    pin_name_pos = []
    name_rot_deg = 0
    if   direction == "R": 
      pin_name_pos = [ ex + self.pixel_per_mil * 120, ey + name_font_height/2.0 + 10  ]
    elif direction == "D": 
      name_rot_deg = -90
      pin_name_pos = [ ex + (self.pixel_per_mil * name_font_size / 2.0),  ey + (name_font_width * float(len(name)) ) + name_font_size/2 ]
      pass
    elif direction == "L": 
      pin_name_pos = [ ex - (name_font_width * len(str(name)) + 40 ), ey + name_font_height/2.0 + 10]
    elif direction == "U": 
      name_rot_deg = -90
      pin_name_pos = [ ex + (self.pixel_per_mil * name_font_size / 2.0),  ey - name_font_size/2 ]
      pass

    line_width = self.line_width

    num_color = (136,0,0)
    name_color = (0, 136,136)
    if (length == "0"):
      num_color = (136,136,136)
      name_color = (136,136,136)
    elif pin_type:

      if re.search("C", pin_type):
        clock_width = 40
        clock_height = 80

        if direction == "R":
          self.svg_scene.add( SVG.Line( (ex + clock_width, ey), (ex, ey + clock_height / 2 ), (136,0,0), self.line_width ) )
          self.svg_scene.add( SVG.Line( (ex, ey + clock_height / 2 ), (ex, ey - clock_height / 2 ), (136,0,0), self.line_width ) )
          self.svg_scene.add( SVG.Line( (ex, ey - clock_height / 2 ), (ex + clock_width, ey ), (136,0,0), self.line_width ) )

        elif direction == "L":
          self.svg_scene.add( SVG.Line( (ex - clock_width, ey), (ex, ey + clock_height / 2 ), (136,0,0), self.line_width ) )
          self.svg_scene.add( SVG.Line( (ex, ey + clock_height / 2 ), (ex, ey - clock_height / 2 ), (136,0,0), self.line_width ) )
          self.svg_scene.add( SVG.Line( (ex, ey - clock_height / 2 ), (ex - clock_width, ey ), (136,0,0), self.line_width ) )

        # untested !
        elif direction == "U":
          self.svg_scene.add( SVG.Line( (ex, ey - clock_width), (ex + clock_height / 2, ey ), (136,0,0), self.line_width ) )
          self.svg_scene.add( SVG.Line( (ex + clock_height / 2, ey ), (ey - clock_height / 2, ey ), (136,0,0), self.line_width ) )
          self.svg_scene.add( SVG.Line( (ex - clock_height / 2, ey ), (ex, ey - clock_width ), (136,0,0), self.line_width ) )

        # untested !
        elif direction == "D":
          self.svg_scene.add( SVG.Line( (ex, ey + clock_width), (ex + clock_height / 2, ey ), (136,0,0), self.line_width ) )
          self.svg_scene.add( SVG.Line( (ex + clock_height / 2, ey ), (ey - clock_height / 2, ey ), (136,0,0), self.line_width ) )
          self.svg_scene.add( SVG.Line( (ex - clock_height / 2, ey ), (ex, ey + clock_width ), (136,0,0), self.line_width ) )

      if re.search("L", pin_type):

        low_in_height = 40
        low_in_width = 80

        if direction == "R":
          self.svg_scene.add( SVG.Line( (ex - low_in_width, ey ), (ex - low_in_width, ey - low_in_height), (136,0,0), self.line_width) )
          self.svg_scene.add( SVG.Line( (ex - low_in_width, ey - low_in_height ), (ex, ey), (136,0,0), self.line_width) )

        elif direction == "L":
          self.svg_scene.add( SVG.Line( (ex + low_in_width, ey ), (ex + low_in_width, ey - low_in_height), (136,0,0), self.line_width) )
          self.svg_scene.add( SVG.Line( (ex + low_in_width, ey - low_in_height ), (ex, ey), (136,0,0), self.line_width) )

        # todo: up and down?

      if re.search("V", pin_type):
        low_out_height = 40
        low_out_width = 80

        if direction == "R":
          self.svg_scene.add( SVG.Line( (ex - low_out_width, ey ), (ex , ey - low_out_height), (136,0,0), self.line_width) )
          self.svg_scene.add( SVG.Line( (ex, ey - low_out_height ), (ex, ey), (136,0,0), self.line_width) )

        elif direction == "L":
          self.svg_scene.add( SVG.Line( (ex + low_out_width, ey ), (ex, ey - low_out_height), (136,0,0), self.line_width) )
          self.svg_scene.add( SVG.Line( (ex, ey - low_out_height ), (ex, ey), (136,0,0), self.line_width) )

        # todo: up and down?

      if re.search("I", pin_type):
        hollow_circle_diam = 70
        cx,cy = ex,ey

        if direction == "R":
          cx -= hollow_circle_diam / 2
          ex -= hollow_circle_diam
        elif direction == "L":
          cx += hollow_circle_diam / 2
          ex += hollow_circle_diam
        elif direction == "U":
          cy += hollow_circle_diam / 2
          ey += hollow_circle_diam
        elif direction == "D":
          cy -= hollow_circle_diam / 2
          ey -= hollow_circle_diam
        self.svg_scene.add( SVG.Line( (sx,sy), (ex,ey), (136,0,0), line_width ) )
        self.svg_scene.add( SVG.Circle( (cx,cy), hollow_circle_diam / 2, None, (136,0,0) , self.line_width) )
      else:
        self.svg_scene.add( SVG.Line( (sx,sy), (ex,ey), (136,0,0), line_width ) )
    else:
      self.svg_scene.add( SVG.Line( (sx,sy), (ex,ey), (136,0,0), line_width ) )

    if self.draw_pin_num:
      if num != "~":
        self.svg_scene.add( SVG.Text( pin_num_pos, cgi.escape(str(num)), num_font_size, num_color, num_rot_deg ) )
      else:
        #print "# NOT drawing pin num...", arg
        pass

    if (name != "~") :
      #if electrical_type is not None and re.search("P", electrical_type):
      #  print "# NOT drawing pin name type 'P'...", arg
      #  pass
      #elif self.draw_pin_name:
      if self.draw_pin_name:
        self.svg_scene.add( SVG.Text( pin_name_pos, cgi.escape(str(name)), name_font_size, name_color, name_rot_deg ) )
      else:
        #print "# NOT drawing pin name...", arg
        pass

    self.svg_scene.add( SVG.Circle( (sx,sy), 10, "none", num_color, 2) )

    ds = max( num_font_size * float(len(num)), num_font_size * float(len(name)) )

    min_val = min(sx, sy, ex, ey, float(pin_num_pos[0]), float(pin_num_pos[1]), float(pin_name_pos[0]), float(pin_name_pos[1]) )
    min_val -= ds

    max_val = max(sx, sy, ex, ey, float(pin_num_pos[0]), float(pin_num_pos[1]), float(pin_name_pos[0]), float(pin_name_pos[1]) )
    max_val += ds


    self.update_bounds( min_val, min_val )
    self.update_bounds( max_val, max_val )


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

  s = libsvg()

  if outbase is not None:
    s.svg_prefix = outbase

  s.parse_lib(infile)


