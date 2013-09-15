#!/usr/bin/python

import os
import re
import sexpression

class kicad_pcb_node(object):

  name = None
  children_name = []
  children = []
  children_bp = {}
  parent = None

  def __init__(self):
    pass

  def __init__(self, name):
    self.name = name

  def __init__(self, name, children):
    self.name = name
    self.children = children

  def add_child(self, name, a):
    if name in self.children_bp:
      self.children_bp[name] = [ len(self.children) ]
    else:
      self.children_bp[name].append( len(self.children) ]
    self.children_name.append(name)
    self.children.append(a)

  def add_parent(self, parent_node):
    self.parent = parent_node


  def debug(self):
    print "name:", self.name
    print "children_name(len:", len(self.children_name), "):", self.children_name
    print "children(len:", len(self.children), "):", self.children
    print "children_bp(len:", len(self.children_bp), "):", self.children_bp
    print "parent:", self.parent
      

class kicad_pcb(sexpression.sexpression):

  parse_root = None
  parse_tree = None

  def __init__(self):
    pass

  def cb_begin(self, args):

    print "cb_begin:", args

    if self.parse_root is None:
      self.parse_root = kicad_pcb_node(args[0], [])
      self.parse_tree = self.parse_root
    else:
      self.parse_tree.add_child(args[0], [])

  def cb_end(self, args):
    print "cb_end:", args


fn = "example/osh_heart_v2.kicad_pcb"

kp = kicad_pcb()
kp.parse_file(fn)


