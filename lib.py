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
Parses KiCAD .lib files.
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

class lib(object):

  lib_file = ""
  lib = ""
  lib_lines = []

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
#    "header" : [ "", "*text" ],
    "header" : [ "EES[cC][hH][eE][mM][aA]-LIB(RARY)?", "#dummy", "*text" ],
    "DEF" : [ "DEF", "name", "reference", "unused", "text_offset", "draw_pinnumber", "draw_pinname", "unit_count", "units_locked", "option_flag" ], 
    "ENDDEF" : [ "ENDDEF" ],
    "F0" : [ "F0", "reference", "posx", "posy", "text_size", "text_orient", "visible", "?htext_justify", "?vtext_justify" ],
    "F1" : [ "F1", "name", "posx", "posy", "text_size", "text_orient", "visible", "?htext_justify", "?vtext_justify" ],
    #"F2" : [ "F2", "*text" ],
    #"F3" : [ "F3", "*text" ],
    #"F4" : [ "F4", "*text" ],
    #"F5" : [ "F5", "*text" ],
    "Fn" : [ "F(\d+)", "#dummy", "*text" ],
    "DRAW" : [ "DRAW" ] ,
    "ENDDRAW" : [ "ENDDRAW" ] ,
    "ALIAS" : [ "ALIAS", "*name" ],
    "FPLIST" : [ "\$FPLIST" ],
    "FPLIST_item" : [ "", "text" ],
    "ENDFPLIST" : [ "\$ENDFPLIST" ],
    "A" : [ "A", "posx", "posy", "radius", "start_angle", "end_angle", "unit", "convert", "thickness", "?fill", "?startx", "?starty", "?endx", "?endy" ],
    "C" : [ "C", "posx", "posy", "radius", "unit", "convert", "thickness", "fill" ],
    "P" : [ "P", "point_count", "unit", "convert", "thickness", ";posx posy", "#dummy", "?fill" ],  # ';' produces extra match in RE, need to have '#dummy' to ignore extra match
    "S" : [ "S", "startx", "starty", "endx", "endy", "unit", "convert", "thickness", "?fill" ],
    "T" : [ "T", "direction", "posx", "posy", "text_size", "text_type", "unit", "convert", "*text" ],

    #### NOTE: though the reference says 'name_text_size' comes before 'num_text_size', I think they might actually be reversed
    "X" : [ "X", "name", "num", "posx", "posy", "length", "direction", "name_text_size", "num_text_size", "unit", "convert", "electrical_type", "?pin_type" ],

    "EOF" : [ "EOF" ]
  }

  # A arc
  # C circle
  # P polyline
  # S rectangle
  # T text
  # X pin

  def cb_header(self, arg): 
    pass

  def cb_DEF (self, arg): 
    pass

  def cb_ENDDEF(self, arg): 
    pass

  def cb_F0(self, arg): 
    pass

  def cb_F1(self, arg): 
    pass

  #def cb_F2(self, arg): 
  #  pass

  #def cb_F3(self, arg): 
  #  pass

  #def cb_F4(self, arg): 
  #  pass

  #def cb_F5(self, arg): 
  #  pass

  def cb_Fn(self, arg): 
    pass

  def cb_DRAW(self, arg): 
    pass

  def cb_ENDDRAW(self, arg): 
    pass

  def cb_ALIAS(self, arg): 
    pass

  def cb_FPLIST(self, arg): 
    pass

  def cb_FPLIST_item(self, arg): 
    pass

  def cb_ENDFPLIST(self, arg): 
    pass

  def cb_A(self, arg): 
    pass

  def cb_C(self, arg): 
    pass

  def cb_P(self, arg): 
    pass

  def cb_S(self, arg): 
    pass

  def cb_T(self, arg): 
    pass

  def cb_X(self, arg): 
    pass

  def cb_EOF(self, arg):
    pass

  op_callback = {}


  # Key entry is the state name.
  # Value is hash with name from op_descr as the key and the state to transition to.
  #    Transition  name is the name that appears in this hash.
  op_state_transition = {
    "header" : { "header" : "start" },
    "start" : { "DEF" : "def" },
    "def" :  { "ENDDEF" : "start" , 
               "F0" : "def" , 
               "F1" : "def", 
               #"F2" : "def", 
               #"F3" : "def",
               #"F4" : "def",
               #"F5" : "def",
               "Fn" : "def",
               "ALIAS" : "def",
               "DRAW" : "def.draw", 

               # be a little more fogiving if we see an endrawy without a beginning draw
               #
               "ENDDRAW" : "def",

               "FPLIST" : "def.fplist" },
    "def.fplist" : { "ENDFPLIST" : "def", 
                     "FPLIST_item" : "def.fplist"  },
    "def.draw" : { "ENDDRAW" : "def", 
                   "A" : "def.draw", 
                   "C" : "def.draw", 
                   "P" : "def.draw", 
                   "S" : "def.draw", 
                   "T" : "def.draw", 
                   "X" : "def.draw" },
    "eof" : { "EOF" : "eof" }
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
    self.op_callback = {
      "header"  : self.cb_header,
      "DEF"  : self.cb_DEF, 
      "ENDDEF"  : self.cb_ENDDEF,
      "F0"  : self.cb_F0,
      "F1"  : self.cb_F1,
      #"F2"  : self.cb_F2,
      #"F3"  : self.cb_F3,
      #"F4"  : self.cb_F4,
      #"F5"  : self.cb_F5,
      "Fn"  : self.cb_Fn,
      "DRAW"  : self.cb_DRAW,
      "ENDDRAW"  : self.cb_ENDDRAW,
      "ALIAS"  : self.cb_ALIAS,
      "FPLIST"  : self.cb_FPLIST,
      "FPLIST_item"  : self.cb_FPLIST_item,
      "ENDFPLIST"  : self.cb_ENDFPLIST,
      "A"  : self.cb_A,
      "C"  : self.cb_C,
      "P"  : self.cb_P,
      "S"  : self.cb_S,
      "T"  : self.cb_T,
      "X"  : self.cb_X,
      "EOF" : self.cb_EOF
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


  def read_lib(self, fn):

    self.lib_file = fn

    f = open( fn, "r" )
    self.lib = f.read()
    f.close()

    f = open( fn, "r" )
    self.lib_lines = f.readlines()
    f.close()


  def parse_lib(self, fn):

    self.read_lib(fn)
    line_no = 0

    #for l in self.lib_lines:
    for latin_line in self.lib_lines:
      l = latin_line.decode('latin1').encode('utf-8')
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

    self.op_callback[ "EOF" ]( "" )

