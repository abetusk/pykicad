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

    self.pixel_per_mil = 150.0/1000.0

    self.buffer_pixel = 40

    self.bounding_box = [ [ 0, 0], [100, 100] ]

    self.line_width = 10
    self.svg_art = []
    self.units = "deci-mils"

    mod.mod.__init__(self)

  def decithou(self, x):
    if self.units == "mm":
      return 10000.0 * float(x) / 25.4
    return x

  def thou(self, x):
    if self.units == "mm":
      return 1000.0 * float(x) / 25.4
    return x

  def mm(self, x):
    if self.units == "mm":
      return x
    return float(x)*25.4

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

  def cb_MODULE(self, arg):


    name = arg[0]

    name = re.sub(' *', '', name)
    name = re.sub('\/', '#', name)

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

    px = self.decithou( float(posx) )
    py = self.decithou( float(posy) )

    name = re.sub('^\s*N\s*', '', name)
    name = re.sub('"', '', name)

    # what is happening with these fonts?
    font_size = self.decithou( float(sizex) ) / 0.6

    shift_x =  0.6 * font_size * float(len(name)-1) / 2.0
    shift_y = 0.6 * font_size / 2.0

    ang_deg = float(rotation)/10.0
    if rotation == "900":
      ang_deg = -90.0
    elif rotation == "1800":
      ang_deg = 0
    elif rotation == "2700":
      ang_deg = 90.0


    ca = math.cos( -math.radians(ang_deg) )
    sa = math.sin( -math.radians(ang_deg) )
    u = -shift_x
    v =  shift_y
    s_x =  ca*u + sa*v
    s_y = -sa*u + ca*v

    #self.svg_art.append( SVG.Text( (int(posx) - shift_x, int(posy) + shift_y), name, font_size, (192,192,192), int(rotation) ) )
    #self.svg_art.append( SVG.Text( (px - shift_x, py + shift_y), name, font_size, (192,192,192), ang_deg ) )
    self.svg_art.append( SVG.Text( (px + s_x, py + s_y), name, font_size, (192,192,192), ang_deg ) )

    self.update_bounds( px - shift_x, py - shift_y )
    self.update_bounds( px + shift_x, py + shift_y ) 


  def cb_MODULE_DS(self, arg):
    startx,starty,endx,endy,stroke_width,layer = arg

    sx,sy = self.decithou( float(startx) ), self.decithou( float(starty) )
    ex,ey = self.decithou( float(endx) ), self.decithou( float(endy) )

    opacity = 0.9
    color=(255,255,255)
    if int(layer) == 21:
      color = (0, 160, 160)

    #self.svg_scene.add( SVG.Line( (sx,sy), (ex,ey), color, int(stroke_width) ) )
    self.svg_art.append( SVG.Line( (sx,sy), (ex,ey), color, self.decithou( float(stroke_width) ), opacity ) )

    self.update_bounds( sx, sy )
    self.update_bounds( ex, ey )


  def cb_MODULE_DA(self, arg):
    centerx,centery,startx,starty,angle,stroke_width,layer = arg

    opacity = 0.9
    color=(255,255,255)
    if int(layer) == 21:
      color = (0, 160, 160)


    cx,cy = self.decithou( float(centerx) ), self.decithou( float(centery) )
    sx,sy = self.decithou( float(startx) ), self.decithou( float(starty) )
    a_rad = math.radians( float(angle)/10.0 )

    r = math.sqrt( (cx-sx)*(cx-sx) + (cy-sy)*(cy-sy) )
    #if r < 0.0001: return

    a_start_rad = math.atan2( sy - cy, sx - cx )

    # Can't SVG to render semi-circles properly (don't know what I'm doing wrong).
    # Interpolating instead
    prev_x, prev_y = None, None
    if a_rad > 0:

      for a in numpy.linspace(a_start_rad, a_start_rad + a_rad, 50):
        cur_x,cur_y = cx + r * math.cos(a), cy + r * math.sin(a)
        if prev_x is not None:
          self.svg_art.append( SVG.Line( (prev_x, prev_y), (cur_x, cur_y), color, self.decithou( float(stroke_width) ), opacity ) )
        prev_x, prev_y = cur_x, cur_y
        self.update_bounds( cur_x, cur_y )

    else:

      for a in numpy.linspace(a_start_rad, a_start_rad - a_rad, 50):
        cur_x,cur_y = cx + r * math.cos(a), cy + r * math.sin(a)
        if prev_x is not None:
          self.svg_art.append( SVG.Line( (prev_x, prev_y), (cur_x, cur_y), color, self.decithou( float(stroke_width) ), opacity ) )
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

    x0 = self.bounding_box[0][0]
    y0 = self.bounding_box[0][1]
    x1 = self.bounding_box[1][0]
    y1 = self.bounding_box[1][1]

    w = abs(self.bounding_box[1][0] - self.bounding_box[0][0])
    h = abs(self.bounding_box[1][1] - self.bounding_box[0][1])

    s_x = -x0
    s_y = -y0

    w *= self.pixel_per_mil
    h *= self.pixel_per_mil

    #self.svg_scene.add( SVG.Circle( (0, 0), 5, (128, 128, 128), None, 0) )

    s_x *= self.pixel_per_mil
    s_y *= self.pixel_per_mil

    s_x += self.buffer_pixel/2
    s_y += self.buffer_pixel/2

    w += self.buffer_pixel
    h += self.buffer_pixel


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
    self.pad.sizex = self.decithou( float(sizex) )
    self.pad.sizey = self.decithou( float(sizey) )
    self.pad.orientation = int(orientation)

  def cb_PAD_Dr(self, arg):
    pad_drill, offsetx, offsety = arg[0], arg[1], arg[2]

    hole_shape, pad_drill_x, pad_drill_y = None, None, None
    if len(arg) > 3 and arg[3] is not None:
      hole_shape = arg[3]
      self.pad.hole_shape = re.sub(' ', '', hole_shape)
    if len(arg) > 4 and arg[4] is not None:
      pad_drill_x = arg[4]
      self.pad.drill_hole_extra_x = self.decithou( float(pad_drill_x) )
    if len(arg) > 5 and arg[5] is not None:
      pad_drill_y = arg[5]
      self.pad.drill_hole_extra_y = self.decithou( float(pad_drill_y) )

    self.pad.drill_diam = self.decithou( float(pad_drill) )
    self.pad.drill_x = self.decithou( float(offsetx) )
    self.pad.drill_y = self.decithou( float(offsety) )


  def cb_PAD_At(self, arg):
    pad_type, n, layer_mask = arg

    if layer_mask is not None:
      self.pad.layer_mask = layer_mask

  def cb_PAD_Ne(self, arg):
    net_number, net_name = arg
    pass

  def cb_PAD_Po(self, arg):
    posx, posy = arg

    self.pad.posx = self.decithou( float(posx) )
    self.pad.posy = self.decithou( float(posy) )

  # units converted by thet ime we get here
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
      self.svg_scene.add( SVG.Rectangle( (p.posx - p.sizex/2, p.posy - p.sizey/2), p.sizey, p.sizex, color, None, 0, float(p.orientation)/10.0 ) )
    elif p.shape == "C":
      #self.svg_scene.add( SVG.Circle( (p.posx - p.sizex/2, p.posy - p.sizey/2), p.sizex, color, None, 0 ) )
      self.svg_scene.add( SVG.Circle( (p.posx, p.posy), p.sizex/2, color, None, 0 ) )
    elif p.shape == "O":  #obround

      self.svg_scene.add( SVG.Obround( (p.posx, p.posy), p.sizey, p.sizex, color, None, 0, float(p.orientation)/10.0 ) )

#      if p.sizex > p.sizey:
#        dx = p.sizex/2
#        ry = p.sizey/2
#        self.svg_scene.add( SVG.Circle( (p.posx + dx - ry, p.posy), ry, color, None, 0) )
#        self.svg_scene.add( SVG.Circle( (p.posx - dx + ry, p.posy), ry, color, None, 0) )
#        self.svg_scene.add( SVG.Rectangle( (p.posx - dx + ry, p.posy - ry), 2*ry, 2*(dx-ry), color, None, 0, float(p.orientation)/10.0 ) )
#      elif p.sizey > p.sizex:
#        dy = p.sizey/2
#        rx = p.sizex/2
#        self.svg_scene.add( SVG.Circle( (p.posx, p.posy + dy - rx), rx, color, None, 0) )
#        self.svg_scene.add( SVG.Circle( (p.posx, p.posy - dy + rx), rx, color, None, 0) )
#        self.svg_scene.add( SVG.Rectangle( (p.posx - rx, p.posy - dy + rx), 2*(dy-rx), 2*rx, color, None, 0, float(p.orientation)/10.0 ) )


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

    name_s_x = -name_shiftx
    name_s_y = font_size/2

    angle_deg = float(p.orientation)/10.0

    text_view_angle_deg = angle_deg
    other_ang = 0
    if p.orientation == 900:
      text_view_angle_deg = -90.0
      other_ang = 90.0
    elif p.orientation == 1800:
      text_view_angle_deg = 0
    elif p.orientation == 2700:
      other_ang = 90.0

    ca = math.cos(math.radians(other_ang))
    sa = math.sin(math.radians(other_ang))

    a = -name_shiftx
    b = font_size/2

    name_s_x =  ca * a + sa * b
    name_s_y = -sa * a + ca * b


#    if p.orientation == 900:
#      name_s_y = name_shiftx
#      name_s_x = font_size/2
#    elif p.orientation == 2700:
#      name_s_y = name_shiftx
#      name_s_x = font_size/2


    #self.svg_scene.add( SVG.Text( (p.posx - name_shiftx, p.posy + font_size/2), p.name, p.sizex/2, (255,255,255), text_view_angle_deg ) )
    self.svg_scene.add( SVG.Text( (p.posx + name_s_x, p.posy + name_s_y), p.name, p.sizex/2, (255,255,255), text_view_angle_deg ) )


    #self.update_bounds( p.posx - p.sizex/2, p.posy - p.sizey/2 )
    #self.update_bounds( p.posx + p.sizex/2, p.posy + p.sizey/2 )

    self.update_bounds( p.posx - p.sizex, p.posy - p.sizey )
    self.update_bounds( p.posx + p.sizex, p.posy + p.sizey )


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
