#!/usr/bin/python
"""
Loads KiCAD mod file (old version, not the new S-expression), parses it with mod,
writes to svg and displays.
"""

import re, sys, lib, math, numpy
import mod
import SVG

# text gray (192, 192, 192)
# text blue (0, 0, 192)
# part red (160, 0, 0)
# part green (0, 160, 0)
# art tiel (0, 160, 160)
# edge yellow (255, 255, 0)

class pad:
  def __init__(self):
    self.name = None
    self.shape = None
    self.sizex = None
    self.sizey = None
    self.posx = None
    self.posy = None
    self.mask = None

    self.drill_type = None
    self.drill_x = None
    self.drill_y = None

    self.hole_shape = None
    self.drill_hole_extra_x = None
    self.drill_hole_extra_y = None

    self.layer_mask = None

class modsvg(mod.mod):
  def __init__(self):
    self.svg_file = ""
    self.svg_prefix = "./svg/"
    self.svg_suffix = ".svg"
    self.svg_scene = None

    self.counter=0

    self.pixel_per_mil = 150/1000.0

    self.buffer_pixel = 40

    self.bounding_box = [ [ 0, 0], [100, 100] ]
    #self.bounding_box = [ [ 0, 0], [5000, 1000] ]

    self.line_width = 10

    self.svg_art = []

    mod.mod.__init__(self)



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



  def cb_MODULE(self, arg):


    name = arg[0]

    self.svg_file = self.svg_prefix + str( name ) + self.svg_suffix
    self.svg_scene = SVG.Scene( self.svg_file )


  def cb_MODULE_Po(self, arg):
    posx, posy, orientation, layer, timestamp, attribute0, attribute1 = arg
    pass

  def cb_MODULE_Li(self, arg):
    name = arg[0]
    pass

  def cb_MODULE_Sc(self, arg):
    timestamp = arg[0]
    pass

  def cb_MODULE_AR(self, arg):
    pass

  def cb_MODULE_Op(self, arg):
    rotation_cost_90, rotation_cost_180, unknown = arg
    pass

  def cb_MODULE_Tn(self, arg):
    #n, posx, posy, sizex, sizey, rotation, penwidth, flag, visible, layer, flag, name = arg
    n, posx, posy, sizex, sizey, rotation, penwidth, flag, visible, layer, name = arg

    name = re.sub('^\s*N\s*', '', name)
    name = re.sub('"', '', name)

    font_size = float(sizex)/0.6

    shift_x = 0.6 * font_size * len(name) / 2
    #shift_x = font_size * len(name) / 2
    shift_y = 0.6 * font_size / 2
    #shift_y = font_size / 2

    sx = int(posx)
    sy = int(posy)

    self.svg_art.append( SVG.Text( (int(posx) - shift_x, int(posy) + shift_y), name, font_size, (192,192,192), int(rotation) ) )

    self.update_bounds( sx - shift_x, sy - shift_y )
    #self.update_bounds( sx + 2*shift_x, sy + shift_y ) 
    self.update_bounds( sx + shift_x, sy + shift_y ) 


  def cb_MODULE_DS(self, arg):
    startx,starty,endx,endy,stroke_width,layer = arg

    sx,sy = int(startx),int(starty)
    ex,ey = int(endx),int(endy)

    opacity = 0.9
    color=(255,255,255)
    if int(layer) == 21:
      color = (0, 160, 160)

    #self.svg_scene.add( SVG.Line( (sx,sy), (ex,ey), color, int(stroke_width) ) )
    self.svg_art.append( SVG.Line( (sx,sy), (ex,ey), color, int(stroke_width), opacity ) )


    self.update_bounds( sx, sy )
    self.update_bounds( ex, ey )


  def cb_MODULE_DA(self, arg):
    centerx,centery,startx,starty,angle,stroke_width,layer = arg

    opacity = 0.9
    color=(255,255,255)
    if int(layer) == 21:
      color = (0, 160, 160)


    cx,cy = int(centerx),int(centery)
    sx,sy = int(startx),int(starty)
    a_rad = math.radians( float(angle)/10.0 )

    r = math.sqrt( (cx-sx)*(cx-sx) + (cy-sy)*(cy-sy) )
    #if r < 0.0001: return

    a_start_rad = math.atan2( sy - cy, sx - cx )

    prev_x, prev_y = None, None
    if a_rad > 0:

      for a in numpy.linspace(a_start_rad, a_start_rad + a_rad, 50):
        cur_x,cur_y = cx + r * math.cos(a), cy + r * math.sin(a)
        if prev_x is not None:
          self.svg_art.append( SVG.Line( (prev_x, prev_y), (cur_x, cur_y), color, int(stroke_width), opacity ) )
        prev_x, prev_y = cur_x, cur_y
        self.update_bounds( cur_x, cur_y )

    else:

      for a in numpy.linspace(a_start_rad, a_start_rad - a_rad, 50):
        cur_x,cur_y = cx + r * math.cos(a), cy + r * math.sin(a)
        if prev_x is not None:
          self.svg_art.append( SVG.Line( (prev_x, prev_y), (cur_x, cur_y), color, int(stroke_width), opacity ) )
        prev_x, prev_y = cur_x, cur_y
        self.update_bounds( cur_x, cur_y )

    #r = math.sqrt( (cx-sx)*(cx-sx) + (cy-sy)*(cy-sy) )
    #if r < 0.0001: return





  def cb_MODULE_DC(self, arg):
    pass


  def cb_MODULE_end(self, arg):

    for a in self.svg_art:
      self.svg_scene.add( a )

    self.inflate_bounds(0.1, 0.1)

    self.svg_art = []

    w = abs(self.bounding_box[1][0] - self.bounding_box[0][0])
    h = abs(self.bounding_box[1][1] - self.bounding_box[0][1])

    w *= self.pixel_per_mil
    h *= self.pixel_per_mil

    #s_x = (self.bounding_box[1][0] - self.bounding_box[0][0]) / 2.0
    #s_y = (self.bounding_box[1][1] - self.bounding_box[0][1]) / 2.0
    #s_x += self.bounding_box[0][0]
    #s_y -= self.bounding_box[0][1]

    s_x = -self.bounding_box[0][0]
    s_y = -self.bounding_box[0][1]

    s_x *= self.pixel_per_mil
    s_y *= self.pixel_per_mil

    w += self.buffer_pixel
    h += self.buffer_pixel

    #s_x += self.buffer_pixel/2
    #s_y += self.buffer_pixel/2


    self.svg_scene.height = h
    self.svg_scene.width = w

    self.svg_scene.transform = " translate( {0},{1} ) scale( {2},{3} )".format( s_x, s_y, self.pixel_per_mil, self.pixel_per_mil )
    self.svg_scene.extra = " viewport-fill=\"black\" ";
    self.svg_scene.background_rect = ' <rect x="0" y="0" height="' + str(h) + '" width="' + str(w) + '" />'

    self.svg_scene.write_svg( self.svg_file )

    self.reset_bounds()

    self.counter += 1
    if self.counter == 15:
    #  sys.exit(0)
      pass


  def cb_PAD(self, arg):
    self.pad = pad()

  def cb_PAD_Sh(self, arg):
    pad_name, shape, sizex, sizey, deltax, delta, orientation = arg

    self.pad.name = re.sub('"', '', pad_name)
    self.pad.shape = shape
    self.pad.sizex = int(sizex)
    self.pad.sizey = int(sizey)
    self.pad.orientation = int(orientation)

  def cb_PAD_Dr(self, arg):

    pad_drill, offsetx, offsety = arg[0], arg[1], arg[2]
    hole_shape, pad_drill_x, pad_drill_y = None, None, None
    if len(arg) > 3 and arg[3] is not None:
      hole_shape = arg[3]
      self.pad.hole_shape = re.sub(' ', '', hole_shape)
    if len(arg) > 4 and arg[4] is not None:
      pad_drill_x = arg[4]
      self.pad.drill_hole_extra_x = int(pad_drill_x)
    if len(arg) > 5 and arg[5] is not None:
      pad_drill_y = arg[5]
      self.pad.drill_hole_extra_y = int(pad_drill_y)

    self.pad.drill_diam = int(pad_drill)
    self.pad.drill_x = int(offsetx)
    self.pad.drill_y = int(offsety)


  def cb_PAD_At(self, arg):
    pad_type, n, layer_mask = arg

    if layer_mask is not None:
      self.pad.layer_mask = layer_mask

  def cb_PAD_Ne(self, arg):
    net_number, net_name = arg
    pass

  def cb_PAD_Po(self, arg):
    posx, posy = arg

    self.pad.posx = int(posx)
    self.pad.posy = int(posy)

  def cb_PAD_end(self, arg):
    p = self.pad

    color = ( 160, 0, 0)
    if p.layer_mask is not None:
      mask = int( p.layer_mask, 16)

      if (mask & (1<<15)) and (mask & 1):
        color = (128, 128, 0)
      elif (mask & (1<<15)):
        color = (160, 0, 0)
      elif (mask & 1):
        color = (0, 160, 0)

    font_size = 0.6 * p.sizex/2
    name_shiftx = len(p.name)*font_size/2

    if p.shape == "R":
      self.svg_scene.add( SVG.Rectangle( (p.posx - p.sizex/2, p.posy - p.sizey/2), p.sizey, p.sizex, color, None, 0 ) )
    elif p.shape == "C":
      #self.svg_scene.add( SVG.Circle( (p.posx - p.sizex/2, p.posy - p.sizey/2), p.sizex, color, None, 0 ) )
      self.svg_scene.add( SVG.Circle( (p.posx, p.posy), p.sizex/2, color, None, 0 ) )
    elif p.shape == "O":
      if p.sizex > p.sizey:
        dx = p.sizex/2
        ry = p.sizey/2
        self.svg_scene.add( SVG.Circle( (p.posx + dx - ry, p.posy), ry, color, None, 0) )
        self.svg_scene.add( SVG.Circle( (p.posx - dx + ry, p.posy), ry, color, None, 0) )
        self.svg_scene.add( SVG.Rectangle( (p.posx - dx + ry, p.posy - ry), 2*ry, 2*(dx-ry), color, None, 0 ) )
      elif p.sizey > p.sizex:
        dy = p.sizey/2
        rx = p.sizex/2
        self.svg_scene.add( SVG.Circle( (p.posx, p.posy + dy - rx), rx, color, None, 0) )
        self.svg_scene.add( SVG.Circle( (p.posx, p.posy - dy + rx), rx, color, None, 0) )
        self.svg_scene.add( SVG.Rectangle( (p.posx - rx, p.posy - dy + rx), 2*(dy-rx), 2*rx, color, None, 0 ) )


    if p.drill_diam:

      if p.hole_shape == "O":

        dcx,dcy = p.posx + p.drill_x, p.posy + p.drill_y

        if p.drill_hole_extra_x > p.drill_hole_extra_y:
          dx = p.drill_hole_extra_x/2
          ry = p.drill_hole_extra_y/2

          ofx = dx - ry
          ofy = ry

          self.svg_scene.add( SVG.Circle( (dcx - ofx, dcy ), ry, (0,0,0), None, 0) )
          self.svg_scene.add( SVG.Circle( (dcx + ofx, dcy ), ry, (0,0,0), None, 0) )
          self.svg_scene.add( SVG.Rectangle( ( dcx - ofx, dcy - ofy ), 2*ofy, 2*ofx, (0,0,0), None, 0 ) )

        elif p.drill_hole_extra_x < p.drill_hole_extra_y:
          dy = p.drill_hole_extra_y/2
          rx = p.drill_hole_extra_x/2

          ofx = rx
          ofy = dy - rx

          self.svg_scene.add( SVG.Circle( (dcx, dcy - ofy), rx, (0,0,0), None, 0) )
          self.svg_scene.add( SVG.Circle( (dcx, dcy + ofy), rx, (0,0,0), None, 0) )
          self.svg_scene.add( SVG.Rectangle( ( dcx - ofx, dcy - ofy ), 2*ofy, 2*ofx, (0,0,0), None, 0 ) )

      else:
        self.svg_scene.add( SVG.Circle( (p.posx + p.drill_x, p.posy + p.drill_y), p.drill_diam/2, (0,0,0), None, 0) )

    self.svg_scene.add( SVG.Text( (p.posx - name_shiftx, p.posy + font_size/2), p.name, p.sizex/2, (255,255,255) ) )


    self.update_bounds( p.posx - p.sizex/2, p.posy - p.sizey/2 )
    self.update_bounds( p.posx + p.sizex/2, p.posy + p.sizey/2 )


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

  s = modsvg()

  if outbase is not None:
    s.svg_prefix = outbase

  s.parse_mod(infile)

#fn = "example/led.mod"
#fn = "modules/display.mod"
#fn = "modules/led.mod"
#fn = "modules/contrib/Transistor_TO-220_RevA.mod"
#fn = "modules/sockets.mod"
#fn = "modules/dip_sockets.mod"
#fn = "modules/sockets.mod"

#m = modsvg()
#m.parse_mod(fn)
