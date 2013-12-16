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
Parses KiCAD .sch files.
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

class sch(object):

  sch_file = ""
  sch = ""
  sch_lines = []

  parse_state = "header"

  parrot_flag = False

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
  #     =  - real number
  #
  op_descr = {
    "header" : [ "EESchema\s+Schematic", "*text" ],

    "LIB" : [ "LIBS:([^\s]+)" ],

    "EELAYER" : [ "EELAYER", "nn", "mm" ],
    "EELAYER_end" : [ "EELAYER\s+END" ],

    "descr" : [ "\$Descr", "sheet", "dimx", "dimy" ],
    "descr_encoding" : [ "encoding", "type" ],
    "descr_sheet" : [ "Sheet", "current_sheet_number", "total_sheet_number" ],
    "descr_title" : [ "Title", "\"title", "#dummy" ],
    "descr_date" : [ "Date", "\"date", "#dummy" ],
    "descr_rev" : [ "Rev", "\"revision", "#dummy" ],
    "descr_comp" : [ "Comp", "\"company", "#dummy" ],
    "descr_comment" : [ "Comment\d+", "\"comment" , "#dummy" ],
    "descr_end" : [ "\$EndDescr" ],

    "sheet" : [ "\$Sheet" ],
    "sheet_S" : [ "S", "posx", "posy", "dimx", "dimy" ],
    "sheet_Fn" : [ "F(\d+)", "\"text", "#dummy","#dummy",  "forms", "side", "posx", "posy", "dimension" ],
    "sheet_end" : [ "\$EndSheet" ],

    "comp" : [ "\$Comp" ],
    "comp_L" : [ "L", "name", "reference" ],
    "comp_U" : [ "U", "n", "mm", "timestamp" ],
    "comp_P" : [ "P", "posx", "posy" ],
    "comp_F" : [ "F", "field_number", "\"text", "#dummy", "orientation", "posx", "posy", "size", "*flags" ],
    #"comp_redundant" : [ "", "1", "posx", "posy" ],
    "comp_redundant" : [ "1", "=posx", "=posy" ],
    #"comp_matrix" : [ "", "A", "B", "C", "D" ],
    "comp_matrix" : [ "", "=A", "=B", "=C", "=D" ],
    "comp_end" : [ "\$EndComp" ],

    # a note on theboard
    "textnote" : [ "Text\s+Notes", "posx", "posy", "orientation", "dimension", "~", "?zero" ],
    "textnote_text" : [ "" , "_text" ],                                                             # _ all line, potentially at start

    "label" : [ "Text\s+Label", "posx", "posy", "orientation", "dimension", "shape", "~" ],
    "label_text" : [ "", "*label" ],                                                                # ^ potentially at start of line

    "heirarchicallabel" : [ "Text\s+HLabel", "posx", "posy", "orientation", "dimension", "shape", "*cruft" ],
    "heirarchicallabel_text" : [ "", "^label" ],

    #"globallabel" : [ "Text\s+GLabel", "posx", "posy", "orientation", "dimension", "shape", "text" ],
    "globallabel" : [ "Text\s+GLabel", "posx", "posy", "orientation", "dimension", "shape", "*cruft" ],
    "globallabel_text" : [ "", "^label" ],


    "noconn" : [ "NoConn\s+~", "posx", "posy" ],
    "connection" : [ "Connection\s+~", "posx", "posy" ],

    # wire line
    "wireline" : [ "Wire\s+Wire\s+Line" ],
    "wireline_segment" : [ "", "^startx", "starty", "endx", "endy" ],

    # bus line
    "busline" : [ "Wire\s+Bus\s+Line" ],
    "busline_segment" : [ "", "^startx", "starty", "endx", "endy" ],

    # graphic line
    "notesline" : [ "Wire\s+Notes\s+Line" ],
    "notesline_segment" : [ "" , "^startx", "starty", "endx", "endy" ],

    # wire to bus line
    "wirebus" : [ "Wire\s+Wire\s+Bus" ],
    "wirebus_segment" : [ "", "^startx", "starty", "endx", "endy" ],

    # bus to bus line
    "busbus" : [ "Wire\s+Bus\s+Bus" ],
    "busbus_segment" : [ "", "^startx", "starty", "endx", "endy" ],


    ## entry?
    "entrybusline" : [ "Entry\s+Bus\s+Line" ],
    "entrybusline_segment" : [ "", "startx", "starty", "endx", "endy" ],

    "entrywirebus" : [ "Entry\s+Wire\s+Bus" ],
    "entrywirebus_segment" : [ "", "startx", "starty", "endx", "endy" ],

    "entrywireline" : [ "Entry\s+Wire\s+Line" ],
    "entrywireline_segment" : [ "", "startx", "starty", "endx", "endy" ],

    "entrybusbus" : [ "Entry\s+Bus\s+Bus" ],
    "entrybusbus_segment" : [ "", "startx", "starty", "endx", "endy" ],

    "END" : [ "\$EndSCHEMATI?C" ]

  }

  # A arc
  # C circle
  # P polyline
  # S rectangle
  # T text
  # X pin

  def cb_header(self, arg):
    if self.parrot_flag:
      print "cb_header", arg
    pass

  def cb_LIB(self, arg):
    if self.parrot_flag:
      print "cb_LIB", arg
    pass

  def cb_EELAYER(self, arg):
    if self.parrot_flag:
      print "cb_EELAYER", arg
    pass

  def cb_EELAYER_end(self, arg):
    if self.parrot_flag:
      print "cb_EELAYER_end", arg
    pass

  def cb_descr(self, arg):
    if self.parrot_flag:
      print "cb_descr", arg
    pass

  def cb_descr_encoding(self, arg):
    if self.parrot_flag:
      print "cb_descr_encoding", arg
    pass

  def cb_descr_sheet(self, arg):
    if self.parrot_flag:
      print "cb_descr_sheet", arg
    pass

  def cb_descr_title(self, arg):
    if self.parrot_flag:
      print "cb_descr_title", arg
    pass

  def cb_descr_date(self, arg):
    if self.parrot_flag:
      print "cb_descr_date", arg
    pass

  def cb_descr_rev(self, arg):
    if self.parrot_flag:
      print "cb_descr_rev", arg
    pass

  def cb_descr_comp(self, arg):
    if self.parrot_flag:
      print "cb_descr_comp", arg
    pass

  def cb_descr_comment(self, arg):
    if self.parrot_flag:
      print "cb_descr_comment", arg
    pass

  def cb_descr_end(self, arg):
    if self.parrot_flag:
      print "cb_descr_end", arg
    pass

  def cb_sheet(self, arg):
    if self.parrot_flag:
      print "cb_sheet", arg
    pass

  def cb_sheet_S(self, arg):
    if self.parrot_flag:
      print "cb_sheet_S", arg
    pass

  def cb_sheet_Fn(self, arg):
    if self.parrot_flag:
      print "cb_sheet_Fn", arg
    pass

  def cb_comp(self, arg):
    if self.parrot_flag:
      print "cb_comp", arg
    pass

  def cb_comp_L(self, arg):
    if self.parrot_flag:
      print "cb_comp_L", arg
    pass

  def cb_comp_U(self, arg):
    if self.parrot_flag:
      print "cb_comp_U", arg
    pass

  def cb_comp_P(self, arg):
    if self.parrot_flag:
      print "cb_comp_P", arg
    pass

  def cb_comp_F(self, arg):
    if self.parrot_flag:
      print "cb_comp_F", arg
    pass

  def cb_comp_redundant(self, arg):
    if self.parrot_flag:
      print "cb_comp_redundant", arg
    pass

  def cb_comp_matrix(self, arg):
    if self.parrot_flag:
      print "cb_comp_matrix", arg
    pass

  def cb_comp_end(self, arg):
    if self.parrot_flag:
      print "cb_comp_end", arg
    pass



  def cb_textnote(self, arg):
    if self.parrot_flag:
      print "cb_textnote", arg
    pass

  def cb_textnote_text(self, arg):
    if self.parrot_flag:
      print "cb_textnote_text", arg
    pass

  def cb_label(self, arg):
    if self.parrot_flag:
      print "cb_label", arg
    pass

  def cb_label_text(self, arg):
    if self.parrot_flag:
      print "cb_label_text", arg
    pass

  def cb_heirarchicallabel(self, arg):
    if self.parrot_flag:
      print "cb_heirarchicallabel", arg
    pass

  def cb_heirarchicallabel_text(self, arg):
    if self.parrot_flag:
      print "cb_heirarchicallabel_text", arg
    pass

  def cb_globallabel(self, arg):
    if self.parrot_flag:
      print "cb_globallabel", arg
    pass

  def cb_globallabel_text(self, arg):
    if self.parrot_flag:
      print "cb_globallabel_text", arg
    pass

  def cb_noconn(self, arg):
    if self.parrot_flag:
      print "cb_noconn", arg
    pass

  def cb_connection(self, arg):
    if self.parrot_flag:
      print "cb_connection", arg
    pass

  def cb_wireline(self, arg):
    if self.parrot_flag:
      print "cb_wireline", arg
    pass

  def cb_wireline_segment(self, arg):
    if self.parrot_flag:
      print "cb_wireline_segment", arg
    pass

  def cb_busline(self, arg):
    if self.parrot_flag:
      print "cb_busline", arg
    pass

  def cb_busline_segment(self, arg):
    if self.parrot_flag:
      print "cb_busline_segment", arg
    pass

  def cb_notesline(self, arg):
    if self.parrot_flag:
      print "cb_notesline", arg
    pass

  def cb_notesline_segment(self, arg):
    if self.parrot_flag:
      print "cb_notesline_segment", arg
    pass

  def cb_wirebus(self, arg):
    if self.parrot_flag:
      print "cb_wirebus", arg
    pass

  def cb_wirebus_segment(self, arg):
    if self.parrot_flag:
      print "cb_wirebus_segment", arg
    pass

  def cb_busbus(self, arg):
    if self.parrot_flag:
      print "cb_busbus", arg
    pass

  def cb_busbus_segment(self, arg):
    if self.parrot_flag:
      print "cb_busbus_segment", arg
    pass

  def cb_entrywirebus(self, arg):
    if self.parrot_flag:
      print "cb_entrywirebus", arg
    pass

  def cb_entrywirebus_segment(self, arg):
    if self.parrot_flag:
      print "cb_entrywirebus_segment", arg
    pass

  def cb_entrybusbus(self, arg):
    if self.parrot_flag:
      print "cb_entrybusbus", arg
    pass

  def cb_entrybusbus_segment(self, arg):
    if self.parrot_flag:
      print "cb_entrybusbus_segment", arg
    pass

  def cb_entrywireline(self, arg):
    if self.parrot_flag:
      print "cb_entrywireline", arg
    pass

  def cb_entrywireline_segment(self, arg):
    if self.parrot_flag:
      print "cb_entrywireline_segment", arg
    pass


  def cb_END(self, arg):
    if self.parrot_flag:
      print "cb_END", arg
    pass



  op_callback = {}


  # Key entry is the state name.
  # Value is hash with name from op_descr as the key and the state to transition to.
  #    Transition  name is the name that appears in this hash.
  op_state_transition = {

    "header" : { "header" : "main" },

    "main" :  { "LIB" : "main",
                "EELAYER" : "eelayer_state",

                "descr" : "descr_state",

                "sheet" : "sheet_state",

                "comp" : "comp_state",

                "textnote" : "textnote_state",
                "label" : "label_state",
                "heirarchicallabel" : "heirlabel_state",
                "globallabel" : "globlabel_state",
                "noconn" : "main",
                "connection" : "main",
                "wireline" : "wireline_state",
                "busline" : "busline_state",
                "notesline" : "notesline_state",
                "wirebus" : "wirebus_state",
                "busbus" : "busbus_state",
                "entrywirebus" : "entrywirebus_state",
                "entrybusbus" : "entrybusbus_state",
                "entrywireline" : "entrywireline_state",

                "END" : "header" },




    "eelayer_state" : { "EELAYER_end" : "main" },

    "descr_state" : { "descr_encoding" : "descr_state",
                      "descr_sheet" : "descr_state",
                      "descr_title" : "descr_state",
                      "descr_date" : "descr_state",
                      "descr_rev" : "descr_state",
                      "descr_comp" : "descr_state",
                      "descr_comment" : "descr_state",
                      "descr_end" : "main" },

    "sheet_state" : { "sheet_S" : "sheet_state",
                      "sheet_Fn" : "sheet_state",
                      "sheet_end" : "main" },

    "comp_state" : { "comp_L" : "comp_state",
                     "comp_U" : "comp_state",
                     "comp_P" : "comp_state",
                     "comp_F" : "comp_state",
                     "comp_redundant" : "comp_state",
                     "comp_matrix" : "comp_state",
                     "comp_end" : "main" },

    "textnote_state" : { "textnote_text" : "main" },
    "label_state" : { "label_text" : "main" },
    "heirlabel_state" : { "heirarchicallabel_text" : "main" },
    "globlabel_state" : { "globallabel_text" : "main" },
    "wireline_state" : { "wireline_segment" : "main" },
    "busline_state" : { "busline_segment" : "main" },
    "notesline_state" : { "notesline_segment" : "main" },
    "wirebus_state" : { "wirebus_segment" : "main" },
    "busbus_state" : { "busbus_segment" : "main" },
    "entrywirebus_state" : { "entrywirebus_segment" : "main" },
    "entrybusbus_state" : { "entrybusbus_segment" : "main" },
    "entrywireline_state" : { "entrywireline_segment" : "main" }




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
      elif re.match('^"', descr): op_re_search += re_prefix + '("(\\"|[^"])*")'
      elif re.match('^\*', descr): op_re_search += "(.*)"
      #elif re.match('^=', descr): op_re_search += re_prefix + "(-?\s*\d+\.|-?\s*\d+(\.\d+)?|-?\s*\.\d+)"
      elif re.match('^=', descr): op_re_search += re_prefix + "(-?\s*\d+\.\d+|-?\s*\d+\.|-?\s*\.\d+|-?\s*\d+)"
      else: op_re_search += re_prefix + "(\S+)"
      re_prefix = '\s+'
    op_re_search += "\s*$"
    op_re[kw] = op_re_search

  def __init__(self):
    self.op_callback = {

      "header" : self.cb_header,
      "LIB" : self.cb_LIB,
      "EELAYER" : self.cb_EELAYER,
      "EELAYER_end" : self.cb_EELAYER_end,
      "descr" : self.cb_descr,
      "descr_encoding" : self.cb_descr_encoding,
      "descr_sheet" : self.cb_descr_sheet,
      "descr_title" : self.cb_descr_title,
      "descr_date" : self.cb_descr_date,
      "descr_rev" : self.cb_descr_rev,
      "descr_comp" : self.cb_descr_comp,
      "descr_comment" : self.cb_descr_comment,
      "descr_end" : self.cb_descr_end,
      "sheet" : self.cb_sheet,
      "sheet_S" : self.cb_sheet_S,
      "sheet_Fn" : self.cb_sheet_Fn,
      "comp" : self.cb_comp,
      "comp_L" : self.cb_comp_L,
      "comp_U" : self.cb_comp_U,
      "comp_P" : self.cb_comp_P,
      "comp_F" : self.cb_comp_F,
      "comp_redundant" : self.cb_comp_redundant,
      "comp_matrix" : self.cb_comp_matrix,
      "comp_end" : self.cb_comp_end,
      "textnote" : self.cb_textnote,
      "textnote_text" : self.cb_textnote_text,
      "label" : self.cb_label,
      "label_text" : self.cb_label_text,
      "heirarchicallabel" : self.cb_heirarchicallabel,
      "heirarchicallabel_text" : self.cb_heirarchicallabel_text,
      "globallabel" : self.cb_globallabel,
      "globallabel_text" : self.cb_globallabel_text,
      "noconn" : self.cb_noconn,
      "connection" : self.cb_connection,
      "wireline" : self.cb_wireline,
      "wireline_segment" : self.cb_wireline_segment,
      "busline" : self.cb_busline,
      "busline_segment" : self.cb_busline_segment,
      "notesline" : self.cb_notesline,
      "notesline_segment" : self.cb_notesline_segment,
      "wirebus" : self.cb_wirebus,
      "wirebus_segment" : self.cb_wirebus_segment,
      "busbus" : self.cb_busbus,
      "busbus_segment" : self.cb_busbus_segment,
      "entrywirebus" : self.cb_entrywirebus,
      "entrywirebus_segment" : self.cb_entrywirebus_segment,
      "entrybusbus" : self.cb_entrybusbus,
      "entrybusbus_segment" : self.cb_entrybusbus_segment,
      "entrywireline" : self.cb_entrywireline,
      "entrywireline_segment" : self.cb_entrywireline_segment,
      "END" : self.cb_END

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


  def read_sch(self, fn):

    self.sch_file = fn

    f = open( fn, "r" )
    self.sch = f.read()
    f.close()

    f = open( fn, "r" )
    self.sch_lines = f.readlines()
    f.close()


  def parse_sch(self, fn):

    self.read_sch(fn)
    line_no = 0

    for l in self.sch_lines:
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
        raise parse_exception("ERROR, couldn't match line '" + str(l) + "', line_no: " +  str(line_no) + " (parse_state:" + str(self.parse_state) + ")" )

      self.op_callback[ op ]( matched_arg )

if __name__ == "__main__":
  if (len(sys.argv) < 2):
    print "provide schematic"
    sys.exit(0)
  s = sch()
  s.parrot_flag = True
  #s.read_sch(sys.argv[1])
  s.parse_sch(sys.argv[1])
