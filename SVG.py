#!/usr/bin/env python
"""\
SVG.py - Construct/display SVG scenes.

The following code is a lightweight wrapper around SVG files. The metaphor
is to construct a scene, add objects to it, and then write it to a file
to display it.

This program uses ImageMagick to display the SVG files. ImageMagick also 
does a remarkable job of converting SVG files into other formats.

This is an enhanced Version of Rick Muller's Code from http://code.activestate.com/recipes/325823-draw-svg-images-in-python/

link:
http://code.activestate.com/recipes/578123-draw-svg-images-in-python-python-recipe-enhanced-v/

MIT license
"""

import os
display_prog = "display"

class Scene:
    def __init__(self,name="svg",height=400,width=400):
        self.name = name
        self.items = []
        self.height = height
        self.width = width
        self.transform = ""
        self.extra = ""
        self.background_rect = ""
        return

    def add(self,item): self.items.append(item)

    def strarray(self):
        var = ["<?xml version=\"1.0\"?>\n",
               "<svg height=\"%d\" width=\"%d\" %s >\n" % (self.height,self.width, self.extra),
               self.background_rect,
               " <g style=\"fill-opacity:1.0; stroke:black;\n",
               "  stroke-width:1;\"",
               " transform=\"" + self.transform + "\"",
               ">\n"]
        for item in self.items: var += item.strarray()            
        var += [" </g>\n</svg>\n"]
        return var

    def write_svg(self,filename=None):
        if filename:
            self.svgname = filename
        else:
            self.svgname = self.name + ".svg"
        file = open(self.svgname,'w')
        file.writelines(self.strarray())
        file.close()
        return

    def display(self,prog=display_prog):
        os.system("%s %s" % (prog,self.svgname))
        return        

class Line:
    def __init__(self,start,end,color,width,opacity = 1.0):
        self.start = start
        self.end = end
        self.color = color
        self.width = width
        self.opacity = opacity
        return

    def strarray(self):
#        return ["  <line x1=\"%d\" y1=\"%d\" x2=\"%d\" y2=\"%d\" style=\"stroke:%s;stroke-width:%d;stroke-opacity:%f\"/>\n" %\
        return ["  <line x1=\"%d\" y1=\"%d\" x2=\"%d\" y2=\"%d\" style=\"stroke:%s;stroke-width:%d;stroke-opacity:%f;stroke-linecap:round\"/>\n" %\
                (self.start[0],self.start[1],self.end[0],self.end[1],colorstr(self.color),self.width, self.opacity)]

class Circle:
    def __init__(self,center,radius,fill_color,line_color,line_width):
        self.center = center
        self.radius = radius
        self.fill_color = fill_color
        self.line_color = line_color
        self.line_width = line_width
        return

    def strarray(self):
#        r = float(self.radius)
#        return ["  <circle transform=\" translate(%d,%d) translate(%d,%d) rotate(%d) translate(%d,%d)\" r=\"%d\"\n" %\
#                (self.center[0],self.center[1], r/2.0, r/2.0, self.rot_deg, -r/2.0, -r/.20, r),
#                "    style=\"fill:%s;stroke:%s;stroke-width:%d\"  />\n" % (colorstr(self.fill_color),colorstr(self.line_color),self.line_width)]

        return ["  <circle cx=\"%d\" cy=\"%d\" r=\"%d\"\n" %\
                (self.center[0],self.center[1],self.radius),
                "    style=\"fill:%s;stroke:%s;stroke-width:%d\"  />\n" % (colorstr(self.fill_color),colorstr(self.line_color),self.line_width)]

class Ellipse:
    def __init__(self,center,radius_x,radius_y,fill_color,line_color,line_width):
        self.center = center
        self.radius_x = radius_x
        self.radius_y = radius_y
        self.fill_color = fill_color
        self.line_color = line_color
        self.line_width = line_width
    def strarray(self):
        return ["  <ellipse cx=\"%d\" cy=\"%d\" rx=\"%d\" ry=\"%d\"\n" %\
                (self.center[0],self.center[1],self.radius_x,self.radius_y),
                "    style=\"fill:%s;stroke:%s;stroke-width:%d\"/>\n" % (colorstr(self.fill_color),colorstr(self.line_color),self.line_width)]

class Arc:
    def __init__(self,center,radius_x,radius_y, rotation_x, large_arc_flag, sweep_flag, dest_x, dest_y, fill_color, line_color,line_width):
        self.center = center
        self.radius_x = radius_x
        self.radius_y = radius_y
        self.rotation_x = rotation_x
        self.large_arc_flag = large_arc_flag
        self.sweep_flag = sweep_flag
        self.dest_x = dest_x
        self.dest_y = dest_y
        self.fill_color = fill_color
        self.line_color = line_color
        self.line_width = line_width
    def strarray(self):
        return ["  <path d=\"M %d,%d A %d,%d %d %d,%d %d,%d \"\n" %\
                (self.center[0],self.center[1],self.radius_x,self.radius_y, self.rotation_x, self.large_arc_flag, self.sweep_flag, self.dest_x, self.dest_y ),
                "    style=\"fill:%s;stroke:%s;stroke-width:%d\"/>\n" % (colorstr(self.fill_color),colorstr(self.line_color),self.line_width)]

class Polygon:
    def __init__(self,points,fill_color,line_color,line_width):
        self.points = points
        self.fill_color = fill_color
        self.line_color = line_color
        self.line_width = line_width
    def strarray(self):
        polygon="<polygon points=\""
        for point in self.points:
            polygon+=" %d,%d" % (point[0],point[1])
        return [polygon,\
               "\" \nstyle=\"fill:%s;stroke:%s;stroke-width:%d\"/>\n" %\
               (colorstr(self.fill_color),colorstr(self.line_color),self.line_width)]

class Obround:
    def __init__(self, origin, height, width, fill_color, line_color, line_width, rot_deg = 0):
        self.origin = origin
        self.height = height
        self.width = width
        self.fill_color = fill_color
        self.line_color = line_color
        self.line_width = line_width
        self.t_x = 0
        self.t_y = 0
        self.rot_deg = rot_deg
        return

#        return ["  <circle cx=\"%d\" cy=\"%d\" r=\"%d\"\n" %\
#                (self.center[0],self.center[1],self.radius),
#                "    style=\"fill:%s;stroke:%s;stroke-width:%d\"  />\n" % (colorstr(self.fill_color),colorstr(self.line_color),self.line_width)]

    def strarray(self):
        w = float(self.width)
        h = float(self.height)
        x = float(self.origin[0])
        y = float(self.origin[1])
        rot_deg = float(self.rot_deg)

        if w > h:
        #if False:
          dx = w/2
          r = h/2

          rect_w = w - 2*r
          rect_h = h

          c0  = "<circle transform=\" translate(%d,%d) rotate(%d) translate(%d,%d)\" r=\"%d\"\n" %\
              ( x, y, self.rot_deg, - dx + r, 0, r)
          c0 += "    style=\"fill:%s;stroke:%s;stroke-width:%d\"  />\n" % (colorstr(self.fill_color),colorstr(self.line_color),self.line_width)

          rect  = "  <rect transform=\" translate(%d,%d) rotate(%d) translate(%d,%d)\" height=\"%d\"\n" %\
              ( x, y, rot_deg, -rect_w/2, -rect_h/2, rect_h)
          rect += "    width=\"%d\" style=\"fill:%s;stroke:%s;stroke-width:%d\" /> \n" %\
                (rect_w ,colorstr(self.fill_color),colorstr(self.line_color),self.line_width)

          c1  = "<circle transform=\" translate(%d,%d) rotate(%d) translate(%d,%d)\" r=\"%d\"\n" %\
              ( x, y, rot_deg, + dx - r, 0, r)
          c1 += "    style=\"fill:%s;stroke:%s;stroke-width:%d\"  />\n" % (colorstr(self.fill_color),colorstr(self.line_color),self.line_width)

        else:
          dy = h/2
          r = w/2

          rect_w = w
          rect_h = h - 2*r

          c0  = "<circle transform=\" translate(%d,%d) rotate(%d) translate(%d,%d)\" r=\"%d\"\n" %\
              ( x, y, rot_deg, 0, - dy + r, r)
          c0 += "    style=\"fill:%s;stroke:%s;stroke-width:%d\"  />\n" % (colorstr(self.fill_color),colorstr(self.line_color),self.line_width)

          rect  = "  <rect transform=\" translate(%d,%d) rotate(%d) translate(%d,%d)\" height=\"%d\"\n" %\
              ( x, y, rot_deg, -rect_w/2, -rect_h/2, rect_h)
          rect += "    width=\"%d\" style=\"fill:%s;stroke:%s;stroke-width:%d\" /> \n" %\
                (rect_w ,colorstr(self.fill_color),colorstr(self.line_color),self.line_width)

          c1  = "<circle transform=\" translate(%d,%d) rotate(%d) translate(%d,%d)\" r=\"%d\"\n" %\
              ( x, y, rot_deg, 0, dy - r, r)
          c1 += "    style=\"fill:%s;stroke:%s;stroke-width:%d\"  />\n" % (colorstr(self.fill_color),colorstr(self.line_color),self.line_width)

        return [ c0, rect, c1 ]

#        return ["  <rect transform=\" translate(%d,%d) translate(%d,%d) rotate(%d) translate(%d,%d)\" height=\"%d\"\n" %\
#                ( self.origin[0], self.origin[1], float(self.width)/2, float(self.height)/2, self.rot_deg, -float(self.width)/2, -float(self.height)/2, self.height),
#                "    width=\"%d\" style=\"fill:%s;stroke:%s;stroke-width:%d\" /> \n" %\
#                (self.width,colorstr(self.fill_color),colorstr(self.line_color),self.line_width)]




class Rectangle:
    def __init__(self,origin,height,width,fill_color,line_color,line_width,rot_deg = 0):
        self.origin = origin
        self.height = height
        self.width = width
        self.fill_color = fill_color
        self.line_color = line_color
        self.line_width = line_width
        self.t_x = 0
        self.t_y = 0
        self.rot_deg = rot_deg
        return

    def strarray(self):
        return ["  <rect transform=\" translate(%d,%d) translate(%d,%d) rotate(%d) translate(%d,%d)\" height=\"%d\"\n" %\
                ( self.origin[0], self.origin[1], float(self.width)/2, float(self.height)/2, self.rot_deg, -float(self.width)/2, -float(self.height)/2, self.height),
                "    width=\"%d\" style=\"fill:%s;stroke:%s;stroke-width:%d\" /> \n" %\
                (self.width,colorstr(self.fill_color),colorstr(self.line_color),self.line_width)]

#        return ["  <g transform=\"translate(%d,%d) rotate(%d)\"> <rect x=\"%d\" y=\"%d\" height=\"%d\"\n" %\
#                (self.t_x, self.t_y, self.rot_deg,  self.origin[0],self.origin[1],self.height),
#                "    width=\"%d\" style=\"fill:%s;stroke:%s;stroke-width:%d\" /> </g>\n" %\
#                (self.width,colorstr(self.fill_color),colorstr(self.line_color),self.line_width)]

class Text:
    def __init__(self,origin,text,size,color,angle_deg = 0):
        self.origin = origin
        self.text = text
        self.size = size
        self.color = color
        self.angle_deg = angle_deg
        return

    def strarray(self):
    #    return ["  <text x=\"%d\" y=\"%d\" font-size=\"%d\" fill=\"%s\">\n" %\
    #    return ["  <text x=\"%d\" y=\"%d\" font-size=\"%s\" fill=\"%s\" font-family=\"Courier\" >\n" %\
    #    return ["  <text x=\"%d\" y=\"%d\" font-size=\"%s\" fill=\"%s\" font-family=\"Simplex monospace\" >\n" %\
#        return ["  <text x=\"%d\" y=\"%d\" font-size=\"%s\" fill=\"%s\" font-family=\"monospace\"  >\n" %\
#                (self.origin[0],self.origin[1],self.size,colorstr(self.color)),
#                "   %s\n" % self.text,
#                "  </text>\n"]

#        return ["  <g transform=\"translate(%d,%d) rotate(%d)\" > <text font-size=\"%s\" fill=\"%s\" font-family=\"monospace\" style=\"text-decoration: overline;\" >\n" %\
        return ["  <g transform=\"translate(%d,%d) rotate(%d)\" > <text font-size=\"%s\" fill=\"%s\" font-family=\"monospace\"  >\n" %\
                (self.origin[0],self.origin[1],self.angle_deg,self.size,colorstr(self.color)),
#                " <tspan text-decoration=\"underline\"> ",
                "   %s\n" % self.text,
#                " </tspan>",
                "  </text> </g> \n"]

def colorstr(rgb): 
  if rgb is None:
    return "none"
  if rgb == "none":
    return "none"
  return "#%x%x%x" % (rgb[0]/16,rgb[1]/16,rgb[2]/16)

def test():
    scene = Scene("test")
    scene.add(Rectangle((100,100),200,200,(0,255,255),(0,0,0),1))
    scene.add(Line((200,200),(200,300),(0,0,0),1))
    scene.add(Line((200,200),(300,200),(0,0,0),2))
    scene.add(Line((200,200),(100,200),(0,0,0),3))
    scene.add(Line((200,200),(200,100),(0,0,0),4))
    scene.add(Circle((200,200),30,(0,0,255),(0,0,0),1))
    scene.add(Circle((200,300),30,(0,255,0),(0,0,0),1))
    scene.add(Circle((300,200),30,(255,0,0),(0,0,0),1))
    scene.add(Circle((100,200),30,(255,255,0),(0,0,0),1))
    scene.add(Circle((200,100),30,(255,0,255),(0,0,0),1))

    scene.add(Circle((10,10),30,None,(0,0,0),1))
    scene.add(Circle((20,20),10,"none",(255,0,0),1))

    scene.add(Ellipse((150,150),30,40,(255,0,255),(0,0,0),1))
    scene.add(Arc((250,150),50,60,10,0,1,10,60, "none", (128,0,255),1))
    scene.add(Text((50,50),"Testing SVG",24,(0,0,0)))
    scene.write_svg()
    scene.display()
    return

if __name__ == "__main__": test()
