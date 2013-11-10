#!/usr/bin/python
"""
Parses KiCAD .mod files.
Access state by callbacks.
"""

import sys
import os
import re

class parse_exception(Exception):
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return repr(self.value)

class mod(object):

  mod_file = ""
  mod = ""
  mod_lines = []

  parse_state = "header"

  # don't get confused, key is just a name
  # first entry of value array is literal RE that will match
  # all other entries are the description of the field and will be used as an indicator when
  #   building the regex op match to match non-whitespace text 
  #   _except_ when the first character is '?', '*', ';' or '#':
  #     ?  - match non-whitespace conditionsally (that is, '(\S+)?')
  #     *  - blanket match text (that is, '(.*)')
  #     ;  - match non-whitespace 2-tuples (that is, '((\s*\S+\s+\S+)*)').
  #          note that this must be followed by a '#' field to get rid of extraneous RE match
  #     #  - ignore (that is, "")
  #
  op_descr = {
    "header" : [ "PCBNEW-LibModule-V1", "*text" ],

    "dollar_hash" : [ "\$#", "*text" ],

    "UNITS" : [ "Units", "unit" ],

    "INDEX" : [ "\$INDEX" ],
    "INDEX_item" : [ "", "name" ],
    "INDEX_end" : [ "\$EndINDEX" ],

    "MODULE" : [ "\$MODULE", "*name" ],
    "MODULE_Po" : [ "Po", "posx", "posy", "orientation", "layer", "timestamp", "attribute", "attribute" ], # position?
    "MODULE_Li" : [ "Li", "*name" ], # module name lib
    "MODULE_Sc" : [ "Sc", "timestamp" ], # timestamp
    "MODULE_AR" : [ "AR", "?name"  ], # ??
    "MODULE_Op" : [ "Op", "rotation_cost_90", "rotation_cost_180", "unknown" ], # rotation cost?
    #"MODULE_Tn" : [ "T(\d+)", "posx", "posy", "sizex", "sizey", "rotation", "penwidth", "flag", "visible", "layer", "flag", "\"name" ], # text
    "MODULE_Tn" : [ "T(\d+)", "posx", "posy", "sizex", "sizey", "rotation", "penwidth", "flag", "visible", "layer", "*name" ], # text
    "MODULE_Cd" : [ "Cd", "*text" ], # comment description
    "MODULE_Kw" : [ "Kw", "*text" ], # key words
    "MODULE_At" : [ "At", "*text" ], # key words

    "MODULE_DS" : [ "DS", "startx", "starty", "endx", "endy", "width", "layer" ], # draw segment
    "MODULE_DC" : [ "DC", "posx", "posy", "pointx", "pointy", "width", "layer" ], # draw circle
    "MODULE_DA" : [ "DA", "centerx", "centery", "startx", "starty", "angle", "width", "layer" ], # draw arc
    "MODULE_DP" : [ "DP", "zero", "zero", "zero", "zero", "corners_count", "width", "layer" ], # draw polygon
    "MODULE_DI" : [ "DI", "cornerx", "cornery" ], # polygon point 

    "MODULE_SolderMask" : [ "\.SolderMask", "layer" ],
    "MODULE_SolderPaste" : [ "\.SolderPaste", "layer" ],
    "MODULE_SolderPasteRatio" : [ "\.SolderPasteRatio", "layer" ],

    "MODULE_end" : [ "\$EndMODULE", "*name" ],

    "SHAPE3D" : [ "\$SHAPE3D" ],
    "SHAPE3D_Na" : [ "Na", "\"filename" ],
    "SHAPE3D_Sc" : [ "Sc", "scalex", "scaley", "scalez" ],
    "SHAPE3D_Of" : [ "Of", "offsetx", "offsety", "offsetz" ],
    "SHAPE3D_Ro" : [ "Ro", "rotx", "roty", "rotz" ],
    "SHAPE3D_end" : [ "\$EndSHAPE3D" ],



    "PAD" : [ "\$PAD" ],
    "PAD_Sh" : [ "Sh", "pad_name", "shape", "sizex", "sizey", "deltax", "deltay", "orientation" ], # shape
    "PAD_Dr" : [ "Dr", "pad_drill", "offsetx", "offsety", "?hole_shape", "?pad_drill_x", "?pad_drill_y" ], # drill
    "PAD_At" : [ "At", "pad_type", "n", "layer_mask" ], # attribute
    "PAD_Ne" : [ "Ne", "net_number", "net_name" ], # net
    "PAD_Po" : [ "Po", "posx", "posy" ], # position

    "PAD_SolderMask" : [ "\.SolderMask", "layer" ],

    "PAD_end" : [ "\$EndPAD" ],

    "LIBRARY_end" : [ "\$EndLIBRARY" ]

  }

  # CROT
  # C - Circle
  # R - Rectangle
  # O - Oblong
  # T - Trapeze (Trapezoid?)

  def cb_header(self, arg): 
    if self.parrot_flag:
      print "cb_header",arg
    pass


  def cb_dollar_hash(self, arg):
    if self.parrot_flag:
      print "cb_dollar_hash",arg
    pass


  def cb_UNITS(self, arg): 
    if self.parrot_flag:
      print "cb_UNITS",arg
    pass


  def cb_INDEX(self, arg): 
    if self.parrot_flag:
      print "cb_INDEX",arg
    pass


  def cb_INDEX_item(self, arg): 
    if self.parrot_flag:
      print "cb_INDEX_item",arg
    pass


  def cb_INDEX_end(self, arg): 
    if self.parrot_flag:
      print "cb_INDEX_end",arg
    pass


  def cb_MODULE(self, arg): 
    if self.parrot_flag:
      print "cb_MODULE",arg
    pass


  def cb_MODULE_Po(self, arg): 
    if self.parrot_flag:
      print "cb_MODULE_Po",arg
    pass


  def cb_MODULE_Li(self, arg): 
    if self.parrot_flag:
      print "cb_MODULE_Li",arg
    pass


  def cb_MODULE_Sc(self, arg): 
    if self.parrot_flag:
      print "cb_MODULE_Sc",arg
    pass


  def cb_MODULE_AR(self, arg): 
    if self.parrot_flag:
      print "cb_MODULE_AR",arg
    pass


  def cb_MODULE_Op(self, arg): 
    if self.parrot_flag:
      print "cb_MODULE_Op",arg
    pass


  def cb_MODULE_Tn(self, arg): 
    if self.parrot_flag:
      print "cb_MODULE_Tn",arg
    pass


  def cb_MODULE_Kw(self, arg): 
    if self.parrot_flag:
      print "cb_MODULE_Kw",arg
    pass


  def cb_MODULE_Cd(self, arg): 
    if self.parrot_flag:
      print "cb_MODULE_Cd",arg
    pass


  def cb_MODULE_At(self, arg): 
    if self.parrot_flag:
      print "cb_MODULE_At",arg
    pass


  def cb_MODULE_DS(self, arg): 
    if self.parrot_flag:
      print "cb_MODULE_DS",arg
    pass


  def cb_MODULE_DC(self, arg): 
    if self.parrot_flag:
      print "cb_MODULE_DC",arg
    pass


  def cb_MODULE_DA(self, arg): 
    if self.parrot_flag:
      print "cb_MODULE_DA",arg
    pass


  def cb_MODULE_DP(self, arg): 
    if self.parrot_flag:
      print "cb_MODULE_DP",arg
    pass


  def cb_MODULE_DI(self, arg): 
    if self.parrot_flag:
      print "cb_MODULE_DI",arg
    pass


  def cb_MODULE_SolderMask(self, arg): 
    if self.parrot_flag:
      print "cb_MODULE_SolderMask",arg
    pass


  def cb_MODULE_SolderPaste(self, arg): 
    if self.parrot_flag:
      print "cb_MODULE_SolderPaste",arg
    pass


  def cb_MODULE_SolderPasteRatio(self, arg): 
    if self.parrot_flag:
      print "cb_MODULE_SolderPasteRatio",arg
    pass


  def cb_MODULE_end(self, arg): 
    if self.parrot_flag:
      print "cb_MODULE_end",arg
    pass


  def cb_SHAPE3D(self,arg): 
    if self.parrot_flag:
      print "cb_SHAPE3D",arg
    pass


  def cb_SHAPE3D_Na(self,arg): 
    if self.parrot_flag:
      print "cb_SHAPE3D_Na",arg
    pass


  def cb_SHAPE3D_Sc(self,arg): 
    if self.parrot_flag:
      print "cb_SHAPE3D_Sc",arg
    pass


  def cb_SHAPE3D_Of(self,arg): 
    if self.parrot_flag:
      print "cb_SHAPE3D_Of",arg
    pass


  def cb_SHAPE3D_Ro(self,arg): 
    if self.parrot_flag:
      print "cb_SHAPE3D_Ro",arg
    pass


  def cb_SHAPE3D_end(self,arg): 
    if self.parrot_flag:
      print "cb_SHAPE3D_end",arg
    pass


  def cb_PAD(self, arg): 
    if self.parrot_flag:
      print "cb_PAD",arg
    pass


  def cb_PAD_Sh(self, arg): 
    if self.parrot_flag:
      print "cb_PAD_Sh",arg
    pass


  def cb_PAD_Dr(self, arg): 
    if self.parrot_flag:
      print "cb_PAD_Dr",arg
    pass


  def cb_PAD_At(self, arg): 
    if self.parrot_flag:
      print "cb_PAD_At",arg
    pass


  def cb_PAD_Ne(self, arg): 
    if self.parrot_flag:
      print "cb_PAD_Ne",arg
    pass


  def cb_PAD_Po(self, arg): 
    if self.parrot_flag:
      print "cb_PAD_Po",arg
    pass


  def cb_PAD_SolderMask(self, arg): 
    if self.parrot_flag:
      print "cb_PAD_SolderMask",arg
    pass


  def cb_PAD_end(self, arg): 
    if self.parrot_flag:
      print "cb_PAD_end",arg
    pass


  def cb_LIBRARY_end(self, arg): 
    if self.parrot_flag:
      print "cb_LIBRARY_end",arg
    pass


  op_callback = {}


  # Key entry is the state name.
  # Value is hash with name from op_descr as the key and the state to transition to.
  #    Transition  name is the name that appears in this hash.
  op_state_transition = {

    "header" : { "header" : "start" },

    "start" : { "INDEX" : "index" ,
                "MODULE" : "module",
                "LIBRARY_end" : "header",
                "UNITS" : "start" ,
                "dollar_hash" : "start" },

    "index" : { "INDEX_item" : "index",
                "INDEX_end" : "start" },

    "module" : { "MODULE" : "module", 
                 "MODULE_Po" : "module", 
                 "MODULE_Li" : "module", 
                 "MODULE_Sc" : "module", 
                 "MODULE_AR" : "module", 
                 "MODULE_Op" : "module", 
                 "MODULE_Tn" : "module", 
                 "MODULE_Kw" : "module", 
                 "MODULE_Cd" : "module", 
                 "MODULE_At" : "module", 

                 "MODULE_DS"  : "module",
                 "MODULE_DC"  : "module",
                 "MODULE_DA"  : "module",
                 "MODULE_DP"  : "module",
                 "MODULE_DI"  : "module",

                 "MODULE_SolderMask"  : "module",
                 "MODULE_SolderPaste"  : "module",
                 "MODULE_SolderPasteRatio"  : "module",

                 "MODULE_end" : "start",

                 "SHAPE3D" : "shape3d",

                 "PAD" : "pad" },
 
    "shape3d" : { "SHAPE3D_Na" : "shape3d",
                  "SHAPE3D_Sc" : "shape3d",
                  "SHAPE3D_Of" : "shape3d", 
                  "SHAPE3D_Ro" : "shape3d", 
                  "SHAPE3D_end" : "module" },

    "pad" : { "PAD" : "pad", 
              "PAD_Sh" : "pad", 
              "PAD_Dr" : "pad", 
              "PAD_At" : "pad", 
              "PAD_Ne" : "pad", 
              "PAD_Po" : "pad", 
              "PAD_SolderMask" : "pad", 
              "PAD_end" : "module" }
  }

  # Build the RE from the op_descr hash as described above.
  op_re = {}
  for kw in op_descr:
    op_re_search = "^\s*" + op_descr[kw][0];

    re_prefix = '\s*'
    for descr in op_descr[kw][1:]:
      if re.match('^#', descr): continue
      if   re.match('^\?', descr): op_re_search += '(' + re_prefix + '\S+)?'
      elif re.match('^;', descr):  op_re_search += "((" + re_prefix + "\S+\s+\S+)+)"
      elif re.match('^\*', descr): op_re_search += "(.*)"
      else: op_re_search += re_prefix + "(\S+)"
      re_prefix = '\s+'
    op_re_search += "\s*$"
    op_re[kw] = op_re_search

  def __init__(self):

    self.parrot_flag = False

    self.op_callback = {
      "header"  : self.cb_header,
      "dollar_hash"  : self.cb_dollar_hash,

      "UNITS" : self.cb_UNITS,

      "INDEX" : self.cb_INDEX,
      "INDEX_item" : self.cb_INDEX_item,
      "INDEX_end" : self.cb_INDEX_end,

      "MODULE" : self.cb_MODULE,
      "MODULE_Po" : self.cb_MODULE_Po,
      "MODULE_Li" : self.cb_MODULE_Li,
      "MODULE_Sc" : self.cb_MODULE_Sc,
      "MODULE_AR" : self.cb_MODULE_AR,
      "MODULE_Op" : self.cb_MODULE_Op,
      "MODULE_Tn" : self.cb_MODULE_Tn,
      "MODULE_Cd" : self.cb_MODULE_Cd,
      "MODULE_Kw" : self.cb_MODULE_Kw,
      "MODULE_At" : self.cb_MODULE_At,

      "MODULE_DS" : self.cb_MODULE_DS,
      "MODULE_DC" : self.cb_MODULE_DC,
      "MODULE_DA" : self.cb_MODULE_DA,
      "MODULE_DP" : self.cb_MODULE_DP,
      "MODULE_DI" : self.cb_MODULE_DI,
      "MODULE_SolderMask" : self.cb_MODULE_SolderMask,
      "MODULE_SolderPaste" : self.cb_MODULE_SolderPaste,
      "MODULE_SolderPasteRatio" : self.cb_MODULE_SolderPasteRatio,

      "MODULE_end" : self.cb_MODULE_end,

      "SHAPE3D" : self.cb_SHAPE3D,
      "SHAPE3D_Na" : self.cb_SHAPE3D_Na,
      "SHAPE3D_Sc" : self.cb_SHAPE3D_Sc,
      "SHAPE3D_Of" : self.cb_SHAPE3D_Of,
      "SHAPE3D_Ro" : self.cb_SHAPE3D_Ro,
      "SHAPE3D_end" : self.cb_SHAPE3D_end,

      "PAD" : self.cb_PAD,
      "PAD_Sh" : self.cb_PAD_Sh,
      "PAD_Dr" : self.cb_PAD_Dr,
      "PAD_At" : self.cb_PAD_At,
      "PAD_Ne" : self.cb_PAD_Ne,
      "PAD_Po" : self.cb_PAD_Po,
      "PAD_SolderMask" : self.cb_PAD_SolderMask ,
      "PAD_end" : self.cb_PAD_end,

      "LIBRARY_end" : self.cb_LIBRARY_end

    }

  def debug(self):
    print "op_descr:"
    for op in self.op_descr:
      print op, self.op_descr[op]

    print "\nop_state_transition:"
    for s in self.op_state_transition:
      for op  in self.op_state_transition[s]:
        print "state:", s, " op:", op, " transition:", self.op_state_transition[s][op]

    print "\nop_re:"
    for op in self.op_re:
      print "op:", op, "op_re:", self.op_re[op]


  def read_mod(self, fn):

    self.mod_file = fn

    f = open( fn, "r" )
    self.mod = f.read()
    f.close()

    f = open( fn, "r" )
    self.mod_lines = f.readlines()
    f.close()


  def parse_mod(self, fn):

    self.read_mod(fn)
    #line_no = 0

    self.parse_mod_lines()

  def parse_mod_lines(self):

    line_no = 0

    for l in self.mod_lines:
      line_no += 1

      l = l.strip()

      if re.search('^\s*#', l): continue
      if re.search('^\s*$', l): continue

      found_match = False
      matched_op = None
      matched_arg = []

      state_transition = self.op_state_transition[self.parse_state]
      for op in state_transition:
        m = re.search( self.op_re[op], l )
        if m:
          self.parse_state = state_transition[op]
          found_match = True
          matched_op = op

          matched_arg = m.groups()
          break

      if not found_match:
        raise parse_exception("ERROR, couldn't match line '" + str(l) + "', line_no: " +  str(line_no) + " (op:" + str(self.parse_state) + ")" )

      self.op_callback[ op ]( matched_arg )


#fn = "example/cr1216_onboard.mod"
#fn = "example/led.mod"

#m = mod()
#m.parse_mod(fn)
if __name__ == "__main__":
  if (len(sys.argv) < 2):
    print "provide board file"
    sys.exit(0)
  m = mod()
  m.parrot_flag = True

  m.parse_mod(sys.argv[1])

  def cb_header(self, arg):
    if self.header:
      print "header",arg
    pass


