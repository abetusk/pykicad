#!/usr/bin/python

import os
import sys
import re


class sexpression(object):

  _debug_flag = False

  parse_state = None
  stack = []

  filename = None
  file_raw = None
  file_lines = None

  re_lparan = '^\('
  re_rparan = '^\)'

  re_name = '^(\w+)'
  re_int = '^(-?\d+)$'
  re_real = '^(-?\d+(\.\d+)?|-?\.\d+)'
  re_string = '^("(\\"|[^"])*")'
  re_val = '^([0-9a-zA-Z_\.\\\/\-]+)'

  _debug_depth = 0

  def cb_begin(self, arg):

    if self._debug_flag:
      print "."*self._debug_depth + "begin:", arg
      self._debug_depth += 1
    pass

  def cb_end(self, arg):

    if self._debug_flag:
      self._debug_depth -= 1
      print "."*self._debug_depth + "end:", arg
    pass

  def __init__(self):
    pass

  def read_file(self, fn):
    self.filename = fn

    f = open(fn, "r")
    self.file_raw = f.read()
    f.close()

    f = open(fn, "r")
    self.file_lines = f.readlines()
    f.close()

  def parse_file(self, fn):

    self.read_file(fn)

    self.parse_state = "normal"

    line_no = 0
    for l in self.file_lines:
      line_no += 1

      while len(l) > 0:

        if self.parse_state == "normal":
          l = l.lstrip()

          #print "l:'" + l + "'"

          if len(l) == 0:
            continue
          
          if re.search( self.re_lparan, l ):

            # take of leading paran
            l = l[1:]

            m = re.search( self.re_name, l )
            if m is None:
              print "PARSE ERROR", line_no
              sys.exit(0)

            kw = m.group(0)
            self.stack.append( [ kw ] )

            self.cb_begin( self.stack[ len(self.stack) - 1 ] )

            #print " "*len(self.stack),"pushed:", kw

            # munch off matched word
            l = l[m.end(0):]

          elif re.search( self.re_rparan, l ):
            m =  re.search( self.re_rparan, l )
            l = l[1:]

            v = self.stack.pop()

            #print " "*len(self.stack), "popped", v

            self.cb_end( v )

          elif re.search( self.re_string, l ):

            m = re.search(self.re_string, l )

            v = m.group(0)
            l = l[ m.end(0):]

            #print " "*len(self.stack),"re_string:", v

            self.stack[ len(self.stack)-1 ].append( v )

          elif re.search( self.re_real, l ):
            m_real = re.search(self.re_real, l)

            s = l[0:m_real.end(0)]
            l = l[ m_real.end(0):]

            m_int = re.search(self.re_int, s)

            if m_int:
              v = m_int.group(0)

              #print " "*len(self.stack),"re_int:", v

              self.stack[ len(self.stack)-1 ].append( v )

            else:

              v = m_real.group(0)

              #print " "*len(self.stack),"re_real:", v

              self.stack[ len(self.stack)-1 ].append( v )

          elif re.search( self.re_val, l ):

            m = re.search(self.re_val, l )
            v = m.group(0)
            l = l[ m.end(0):]

            #print " "*len(self.stack), "re_val:", v

            self.stack[ len(self.stack)-1 ].append( v )

          else:

            print "PARSE ERROR, couldn't find any re"
            sys.exit(0)






#fn = "example/osh_heart_v2.kicad_pcb"

#s = sexpression()
#s.parse_file(fn)
