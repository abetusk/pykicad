#!/usr/bin/python
"""
Parses KiCAD .brd files.
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

class brd(object):

  brd_file = ""
  brd = ""
  brd_lines = []

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
  #     "  - quoted string
  #
  op_descr = {
    "header" : [ "PCBNEW-BOARD", "*text" ],

    "general" : [ "\$GENERAL" ],
    "general_encoding" : [ "encoding", "encoding" ],
    "general_units" : [ "Units", "units" ],
    "general_layercount" : [ "LayerCount", "layer_count" ],
    "general_ly" : [ "Ly", "ly" ],
    "general_enabledlayers" : [ "EnabledLayers", "enabled_layers" ],
    "general_links" : [ "Links", "links" ],
    "general_noconn" : [ "NoConn", "noconn_count" ],
    "general_di" : [ "Di", "x0", "y0", "x1", "y1" ],
    "general_ndraw" : [ "Ndraw", "ndraw" ],
    "general_ntrack" : [ "Ntrack", "n" ],
    "general_nzone" : [ "Nzone", "n" ],
    "general_nmodule" : [ "Nmodule", "n" ],
    "general_boardthickness" : [ "BoardThickness", "board_thickness" ],
    "general_nnets" : [ "Nnets", "nnets" ],
    "general_end" : [ "\$EndGENERAL" ],

    "sheetdescr" : [ "\$SHEETDESCR" ],
    "sheetdescr_sheet" : [  "Sheet", "sheet_type", "width", "height" ],
    "sheetdescr_title" : [  "Title", "\"title", "#dummy"  ],
    "sheetdescr_date" : [  "Date", "\"date", "#dummy"  ],
    "sheetdescr_rev" : [  "Rev", "\"rev", "#dummy" ],
    "sheetdescr_comp" : [  "Comp", "\"comp", "#dummy"  ],
    "sheetdescr_commentN" : [  "Comment(\d+)", "\"comment", "#dummy" ],
    "sheetdescr_end" : [ "\$EndSHEETDESCR" ],

    "setup"                     : [ "\$SETUP" ],
    "setup_internalunit"        : [ "InternalUnit", "value", "units" ], # e.g. 0.000100 INCH
    "setup_layers"              : [ "Layers", "layers" ],
    "setup_layerN"              : [ "Layer\[(\d+)\]", "name", "type" ],
    "setup_trackwidth"          : [ "TrackWidth", "width" ],
    "setup_trackclearence"      : [ "TrackClearence", "clearence" ],
    "setup_zoneclearence"       : [ "ZoneClearence", "clearence" ],
    "setup_zone45only"          : [ "Zone_45_Only", "value" ],
    "setup_trackminwidth"       : [ "TrackMinWidth", "width" ],
    "setup_drawsegmwidth"       : [ "DrawSegmWidth", "width" ],
    "setup_edgesegmwidth"       : [ "EdgeSegmWidth", "width" ],
    "setup_viasize"             : [ "ViaSize", "size" ],
    "setup_viadrill"            : [ "ViaDrill", "size" ],
    "setup_viaminsize"          : [ "ViaMinSize", "size"],
    "setup_viamindrill"         : [ "ViaMinDrill", "size"],
    "setup_microviasize"        : [ "MicroViaSize", "size"],
    "setup_microviadrill"       : [ "MicroViaDrill", "size"],
    "setup_microviasallowed"    : [ "MicroViasAllowed", "size"],
    "setup_microviaminsize"     : [ "MicroViaMinSize", "size"],
    "setup_microviamindrill"    : [ "MicroViaMinDrill", "size"],
    "setup_textpcbwidth"        : [ "TextPcbWidth", "size"],
    "setup_textpcbsize"         : [ "TextPcbSize", "size",  "size"],
    "setup_edgemodwidth"        : [ "EdgeModWidth", "size"],
    "setup_textmodsize"         : [ "TextModSize", "size",  "size"],
    "setup_textmodwidth"        : [ "TextModWidth", "size"],
    "setup_padsize"             : [ "PadSize", "size",  "size"],
    "setup_paddrill"            : [ "PadDrill", "size"],
    "setup_pad2maskclearance"   : [ "Pad2MaskClearance", "size"],
    "setup_soldermaskminwidth"  : [ "SolderMaskMinWidth", "width"],
    "setup_visibleelements"     : [ "VisibleElements", "mask"],
    "setup_auxiliaryaxisorg"    : [ "AuxiliaryAxisOrg", "size",  "size" ],
    "setup_pcbplotparams"       : [ "PcbPlotParams", "*text" ],
    "setup_end"                 : [ "\$EndSETUP" ],

    "equipot" : [ "\$EQUIPOT" ],
    "equipot_na" : [ "Na", "net_number", "\"net_name", "#dummy" ],
    "equipot_st" : [ "St", "st" ],
    "equipot_end" : [ "\$EndEQUIPOT" ],

    "nclass" : [ "\$NCLASS" ],
    "nclass_name" : [ "Name", "\"name", "#dummy" ],
    "nclass_desc" : [ "Desc", "\"descr", "#dummy" ],
    "nclass_clearance" : [ "Clearance", "size" ],
    "nclass_trackwidth" : [ "TrackWidth", "size" ],
    "nclass_viadia" : [ "ViaDia", "size" ],
    "nclass_viadrill" : [ "ViaDrill", "size"],
    "nclass_uviadia" : [ "uViaDia", "size" ],
    "nclass_uviadrill" : [ "uViaDrill", "size" ],
    "nclass_addnet" : [ "AddNet", "\"net", "#dummy" ],
    "nclass_end" : [ "\$EndNCLASS" ],

    "MODULE" : [ "\$MODULE", "*name" ],
    "MODULE_Po" : [ "Po", "posx", "posy", "orientation", "layer", "timestamp", "attribute", "attribute" ], # position?
    "MODULE_Li" : [ "Li", "*name" ], # module name lib
    "MODULE_Sc" : [ "Sc", "timestamp" ], # timestamp
    "MODULE_AR" : [ "AR", "?name"  ], # ??
    "MODULE_Op" : [ "Op", "rotation_cost_90", "rotation_cost_180", "unknown" ], # rotation cost?
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

    "drawsegment" : [ "\$DRAWSEGMENT" ],
    "drawsegment_po" : [ "Po", "shape", "x0", "y0", "x1", "y1", "width"  ],
    "drawsegment_de" : [ "De", "layer", "type", "angle", "timestamp", "status" ],
    "drawsegment_end" : [ "\$EndDRAWSEGMENT" ],

    "textpcb" : [ "\$TEXTPCB" ],
    "textpcb_te" : [ "Te", "\"string", "#dummy" ],
    "textpcb_nl" : [ "nl", "\"string", "#dummy" ],
    "textpcb_po" : [ "Po", "x0", "y0", "x1", "y1", "width", "rotation" ],
    #"textpcb_de" : [ "De", "layer", "normal_flag", "timestamp", "style" ],
    "textpcb_de" : [ "De", "layer", "normal_flag", "timestamp", "style", "?extra" ],
    "textpcb_end" : [ "\$EndTEXTPCB" ],

    "mirepcb" : [ "\$MIREPCB" ],
    "mirepcb_po" : [ "Po", "shape", "x", "y", "size", "width", "timestamp" ],
    "mirepcb_end" : [ "\$EndMIREPCB" ],

    "cotation" : [ "\$COTATION" ],
    "cotation_ge" : [ "Ge", "shape", "layer", "timestamp" ],
    "cotation_te" : [ "Te", "\"string", "#dummy" ],
    "cotation_po" : [ "Po", "x", "y", "xsize", "ysize", "width", "orient", "normal" ],
    "cotation_sb" : [ "Sb", ";x y", "#dummy" ],
    "cotation_sd" : [ "Sd", ";x y", "#dummy"  ],
    "cotation_sg" : [ "Sg", ";x y", "#dummy"  ],
    "cotation_sN" : [ "S(\d+)" ],
    "cotation_end" : [ "\$EndCOTATION" ],

    "track" : [ "\$TRACK" ],
    "track_po" : [ "Po", "shape", "x0", "y0", "x1", "y1", "width", "*wat" ],
    "track_de" : [ "De", "layer", "type", "netcode", "timestamp", "status" ],
    "track_end" : [ "\$EndTRACK" ],

    "zone" : [ "\$ZONE" ],
    "zone_po" : [ "Po", "shape", "x0", "y0", "x1", "y1", "width" ],
    "zone_de" : [ "De", "layer", "type", "netcode", "timestamp", "status" ],
    "zone_end" : [ "\$EndZONE" ],

    "czone" : [ "\$CZONE_OUTLINE" ],
    "czone_zinfo" : [ "ZInfo", "timestamp", "netcode", "\"name", "#dummy" ],
    "czone_zlayer" : [ "ZLayer", "layer" ],
    "czone_zaux" : [ "ZAux", "corner_count", "hatching_option" ],
    "czone_clearance" : [ "ZClearance", "clearance", "pad_option" ],
    "czone_zminthickness" : [ "ZMinThickness", "thickness" ],
    "czone_zoptions" : [ "ZOptions", "fill", "arc", "F", "antipad_thickness", "thermal_stub_width" ],
    "czone_zcorner" : [ "ZCorner", "x", "y", "end_flag" ],
    "czone_zsmoothing" : [ "ZSmoothing", "x", "y" ],
    "czone_end" : [ "\$[Ee]ndCZONE_OUTLINE" ],

    "polyscorners" : [ "\$POLYSCORNERS" ],
    "polyscorners_corner" : [ "", "x0", "y0", "x1", "y1" ],
    "polyscorners_end" : [ "\$[Ee]ndPOLYSCORNERS" ],

    "endboard" : [ "\$EndBOARD" ]

  }

  # A arc
  # C circle
  # P polyline
  # S rectangle
  # T text
  # X pin

  def cb_header(self, arg):
    if self.parrot_flag:
      print("cb_header",arg)
    pass


  def cb_general(self, arg):
    if self.parrot_flag:
      print("cb_general",arg)
    pass

  def cb_general_encoding(self, arg):
    if self.parrot_flag:
      print("cb_general_encoding",arg)
    pass

  def cb_general_units(self, arg):
    if self.parrot_flag:
      print("cb_general_units",arg)
    pass

  def cb_general_layercount(self, arg):
    if self.parrot_flag:
      print("cb_general_layercount",arg)
    pass

  def cb_general_ly(self, arg):
    if self.parrot_flag:
      print("cb_general_ly",arg)
    pass

  def cb_general_enabledlayers(self, arg):
    if self.parrot_flag:
      print("cb_general_enabledlayers",arg)
    pass

  def cb_general_links(self, arg):
    if self.parrot_flag:
      print("cb_general_links",arg)
    pass

  def cb_general_noconn(self, arg):
    if self.parrot_flag:
      print("cb_general_noconn",arg)
    pass

  def cb_general_di(self, arg):
    if self.parrot_flag:
      print("cb_general_di",arg)
    pass

  def cb_general_ndraw(self, arg):
    if self.parrot_flag:
      print("cb_general_ndraw",arg)
    pass

  def cb_general_ntrack(self, arg):
    if self.parrot_flag:
      print("cb_general_ntrack",arg)
    pass

  def cb_general_nzone(self, arg):
    if self.parrot_flag:
      print("cb_general_nzone",arg)
    pass

  def cb_general_nmodule(self, arg):
    if self.parrot_flag:
      print("cb_general_nmodule",arg)
    pass


  def cb_general_boardthickness(self, arg):
    if self.parrot_flag:
      print("cb_general_boardthickness",arg)
    pass

  def cb_general_nnets(self, arg):
    if self.parrot_flag:
      print("cb_general_nnets",arg)
    pass

  def cb_general_end(self, arg):
    if self.parrot_flag:
      print("cb_general_end",arg)
    pass


  def cb_sheetdescr(self, arg):
    if self.parrot_flag:
      print("cb_sheetdescr",arg)
    pass

  def cb_sheetdescr_sheet(self, arg):
    if self.parrot_flag:
      print("cb_sheetdescr_sheet",arg)
    pass

  def cb_sheetdescr_title(self, arg):
    if self.parrot_flag:
      print("cb_sheetdescr_title",arg)
    pass

  def cb_sheetdescr_date(self, arg):
    if self.parrot_flag:
      print("cb_sheetdescr_date",arg)
    pass

  def cb_sheetdescr_rev(self, arg):
    if self.parrot_flag:
      print("cb_sheetdescr_rev",arg)
    pass

  def cb_sheetdescr_comp(self, arg):
    if self.parrot_flag:
      print("cb_sheetdescr_comp",arg)
    pass

  def cb_sheetdescr_commentN(self, arg):
    if self.parrot_flag:
      print("cb_sheetdescr_commentN",arg)
    pass

  def cb_sheetdescr_end(self, arg):
    if self.parrot_flag:
      print("cb_sheetdescr_end",arg)
    pass


  def cb_setup(self, arg):
    if self.parrot_flag:
      print("cb_setup",arg)
    pass

  def cb_setup_internalunit(self, arg):
    if self.parrot_flag:
      print("cb_setup_internalunit",arg)
    pass

  def cb_setup_layers(self, arg):
    if self.parrot_flag:
      print("cb_setup_layers",arg)
    pass

  def cb_setup_layerN(self, arg):
    if self.parrot_flag:
      print("cb_setup_layerN",arg)
    pass

  def cb_setup_trackwidth(self, arg):
    if self.parrot_flag:
      print("cb_setup_trackwidth",arg)
    pass

  def cb_setup_trackclearence(self, arg):
    if self.parrot_flag:
      print("cb_setup_trackclearence",arg)
    pass

  def cb_setup_zoneclearence(self, arg):
    if self.parrot_flag:
      print("cb_setup_zoneclearence",arg)
    pass

  def cb_setup_zone45only(self, arg):
    if self.parrot_flag:
      print("cb_setup_zone45only",arg)
    pass

  def cb_setup_trackminwidth(self, arg):
    if self.parrot_flag:
      print("cb_setup_trackminwidth",arg)
    pass

  def cb_setup_drawsegmwidth(self, arg):
    if self.parrot_flag:
      print("cb_setup_drawsegmwidth",arg)
    pass

  def cb_setup_edgesegmwidth(self, arg):
    if self.parrot_flag:
      print("cb_setup_edgesegmwidth",arg)
    pass

  def cb_setup_viasize(self, arg):
    if self.parrot_flag:
      print("cb_setup_viasize",arg)
    pass

  def cb_setup_viadrill(self, arg):
    if self.parrot_flag:
      print("cb_setup_viadrill",arg)
    pass

  def cb_setup_viaminsize(self, arg):
    if self.parrot_flag:
      print("cb_setup_viaminsize",arg)
    pass

  def cb_setup_viamindrill(self, arg):
    if self.parrot_flag:
      print("cb_setup_viamindrill",arg)
    pass

  def cb_setup_microviasize(self, arg):
    if self.parrot_flag:
      print("cb_setup_microviasize",arg)
    pass

  def cb_setup_microviadrill(self, arg):
    if self.parrot_flag:
      print("cb_setup_microviadrill",arg)
    pass

  def cb_setup_microviasallowed(self, arg):
    if self.parrot_flag:
      print("cb_setup_microviasallowed",arg)
    pass

  def cb_setup_microviaminsize(self, arg):
    if self.parrot_flag:
      print("cb_setup_microviaminsize",arg)
    pass

  def cb_setup_microviamindrill(self, arg):
    if self.parrot_flag:
      print("cb_setup_microviamindrill",arg)
    pass

  def cb_setup_textpcbwidth(self, arg):
    if self.parrot_flag:
      print("cb_setup_textpcbwidth",arg)
    pass

  def cb_setup_textpcbsize(self, arg):
    if self.parrot_flag:
      print("cb_setup_textpcbsize",arg)
    pass

  def cb_setup_edgemodwidth(self, arg):
    if self.parrot_flag:
      print("cb_setup_edgemodwidth",arg)
    pass

  def cb_setup_textmodsize(self, arg):
    if self.parrot_flag:
      print("cb_setup_textmodsize",arg)
    pass

  def cb_setup_textmodwidth(self, arg):
    if self.parrot_flag:
      print("cb_setup_textmodwidth",arg)
    pass

  def cb_setup_padsize(self, arg):
    if self.parrot_flag:
      print("cb_setup_padsize",arg)
    pass

  def cb_setup_paddrill(self, arg):
    if self.parrot_flag:
      print("cb_setup_paddrill",arg)
    pass

  def cb_setup_pad2maskclearance(self, arg):
    if self.parrot_flag:
      print("cb_setup_pad2maskclearance",arg)
    pass

  def cb_setup_soldermaskminwidth(self, arg):
    if self.parrot_flag:
      print("cb_setup_soldermaskminwidth",arg)
    pass

  def cb_setup_visibleelements(self, arg):
    if self.parrot_flag:
      print("cb_setup_visibleelements",arg)
    pass

  def cb_setup_auxiliaryaxisorg(self, arg):
    if self.parrot_flag:
      print("cb_setup_auxiliaryaxisorg",arg)
    pass

  def cb_setup_pcbplotparams(self, arg):
    if self.parrot_flag:
      print("cb_setup_pcbplotparams",arg)
    pass

  def cb_setup_end(self, arg):
    if self.parrot_flag:
      print("cb_setup_end",arg)
    pass


  def cb_equipot(self, arg):
    if self.parrot_flag:
      print("cb_equipot",arg)
    pass

  def cb_equipot_na(self, arg):
    if self.parrot_flag:
      print("cb_equipot_na",arg)
    pass

  def cb_equipot_st(self, arg):
    if self.parrot_flag:
      print("cb_equipot_st",arg)
    pass

  def cb_equipot_end(self, arg):
    if self.parrot_flag:
      print("cb_equipot_end",arg)
    pass


  def cb_nclass(self, arg):
    if self.parrot_flag:
      print("cb_nclass",arg)
    pass

  def cb_nclass_name(self, arg):
    if self.parrot_flag:
      print("cb_nclass_name",arg)
    pass

  def cb_nclass_desc(self, arg):
    if self.parrot_flag:
      print("cb_nclass_desc",arg)
    pass

  def cb_nclass_clearance(self, arg):
    if self.parrot_flag:
      print("cb_nclass_clearance",arg)
    pass

  def cb_nclass_trackwidth(self, arg):
    if self.parrot_flag:
      print("cb_nclass_trackwidth",arg)
    pass

  def cb_nclass_viadia(self, arg):
    if self.parrot_flag:
      print("cb_nclass_viadia",arg)
    pass

  def cb_nclass_viadrill(self, arg):
    if self.parrot_flag:
      print("cb_nclass_viadrill",arg)
    pass

  def cb_nclass_uviadia(self, arg):
    if self.parrot_flag:
      print("cb_nclass_uviadia",arg)
    pass

  def cb_nclass_uviadrill(self, arg):
    if self.parrot_flag:
      print("cb_nclass_uviadrill",arg)
    pass

  def cb_nclass_addnet(self, arg):
    if self.parrot_flag:
      print("cb_nclass_addnet",arg)
    pass

  def cb_nclass_end(self, arg):
    if self.parrot_flag:
      print("cb_nclass_end",arg)
    pass


  def cb_MODULE(self, arg):
    if self.parrot_flag:
      print("cb_MODULE",arg)
    pass

  def cb_MODULE_Po(self, arg):
    if self.parrot_flag:
      print("cb_MODULE_Po",arg)
    pass

  def cb_MODULE_Li(self, arg):
    if self.parrot_flag:
      print("cb_MODULE_Li",arg)
    pass

  def cb_MODULE_Sc(self, arg):
    if self.parrot_flag:
      print("cb_MODULE_Sc",arg)
    pass

  def cb_MODULE_AR(self, arg):
    if self.parrot_flag:
      print("cb_MODULE_AR",arg)
    pass

  def cb_MODULE_Op(self, arg):
    if self.parrot_flag:
      print("cb_MODULE_Op",arg)
    pass

  def cb_MODULE_Tn(self, arg):
    if self.parrot_flag:
      print("cb_MODULE_Tn",arg)
    pass

  def cb_MODULE_Cd(self, arg):
    if self.parrot_flag:
      print("cb_MODULE_Cd",arg)
    pass

  def cb_MODULE_Kw(self, arg):
    if self.parrot_flag:
      print("cb_MODULE_Kw",arg)
    pass

  def cb_MODULE_At(self, arg):
    if self.parrot_flag:
      print("cb_MODULE_At",arg)
    pass

  def cb_MODULE_DS(self, arg):
    if self.parrot_flag:
      print("cb_MODULE_DS",arg)
    pass

  def cb_MODULE_DC(self, arg):
    if self.parrot_flag:
      print("cb_MODULE_DC",arg)
    pass

  def cb_MODULE_DA(self, arg):
    if self.parrot_flag:
      print("cb_MODULE_DA",arg)
    pass

  def cb_MODULE_DP(self, arg):
    if self.parrot_flag:
      print("cb_MODULE_DP",arg)
    pass

  def cb_MODULE_DI(self, arg):
    if self.parrot_flag:
      print("cb_MODULE_DI",arg)
    pass

  def cb_MODULE_SolderMask(self, arg):
    if self.parrot_flag:
      print("cb_MODULE_SolderMask",arg)
    pass

  def cb_MODULE_SolderPaste(self, arg):
    if self.parrot_flag:
      print("cb_MODULE_SolderPaste",arg)
    pass

  def cb_MODULE_SolderPasteRatio(self, arg):
    if self.parrot_flag:
      print("cb_MODULE_SolderPasteRatio",arg)
    pass

  def cb_MODULE_end(self, arg):
    if self.parrot_flag:
      print("cb_MODULE_end",arg)
    pass


  def cb_SHAPE3D(self, arg):
    if self.parrot_flag:
      print("cb_SHAPE3D",arg)
    pass

  def cb_SHAPE3D_Na(self, arg):
    if self.parrot_flag:
      print("cb_SHAPE3D_Na",arg)
    pass

  def cb_SHAPE3D_Sc(self, arg):
    if self.parrot_flag:
      print("cb_SHAPE3D_Sc",arg)
    pass

  def cb_SHAPE3D_Of(self, arg):
    if self.parrot_flag:
      print("cb_SHAPE3D_Of",arg)
    pass

  def cb_SHAPE3D_Ro(self, arg):
    if self.parrot_flag:
      print("cb_SHAPE3D_Ro",arg)
    pass

  def cb_SHAPE3D_end(self, arg):
    if self.parrot_flag:
      print("cb_SHAPE3D_end",arg)
    pass


  def cb_PAD(self, arg):
    if self.parrot_flag:
      print("cb_PAD",arg)
    pass

  def cb_PAD_Sh(self, arg):
    if self.parrot_flag:
      print("cb_PAD_Sh",arg)
    pass

  def cb_PAD_Dr(self, arg):
    if self.parrot_flag:
      print("cb_PAD_Dr",arg)
    pass

  def cb_PAD_At(self, arg):
    if self.parrot_flag:
      print("cb_PAD_At",arg)
    pass

  def cb_PAD_Ne(self, arg):
    if self.parrot_flag:
      print("cb_PAD_Ne",arg)
    pass

  def cb_PAD_Po(self, arg):
    if self.parrot_flag:
      print("cb_PAD_Po",arg)
    pass

  def cb_PAD_SolderMask(self, arg):
    if self.parrot_flag:
      print("cb_PAD_SolderMask",arg)
    pass

  def cb_PAD_end(self, arg):
    if self.parrot_flag:
      print("cb_PAD_end",arg)
    pass


  def cb_drawsegment(self, arg):
    if self.parrot_flag:
      print("cb_drawsegment",arg)
    pass

  def cb_drawsegment_po(self, arg):
    if self.parrot_flag:
      print("cb_drawsegment_po",arg)
    pass

  def cb_drawsegment_de(self, arg):
    if self.parrot_flag:
      print("cb_drawsegment_de",arg)
    pass

  def cb_drawsegment_end(self, arg):
    if self.parrot_flag:
      print("cb_drawsegment_end",arg)
    pass


  def cb_textpcb(self, arg):
    if self.parrot_flag:
      print("cb_textpcb",arg)
    pass

  def cb_textpcb_te(self, arg):
    if self.parrot_flag:
      print("cb_textpcb_te",arg)
    pass

  def cb_textpcb_nl(self, arg):
    if self.parrot_flag:
      print("cb_textpcb_nl",arg)
    pass

  def cb_textpcb_po(self, arg):
    if self.parrot_flag:
      print("cb_textpcb_po",arg)
    pass

  def cb_textpcb_de(self, arg):
    if self.parrot_flag:
      print("cb_textpcb_de",arg)
    pass

  def cb_textpcb_end(self, arg):
    if self.parrot_flag:
      print("cb_textpcb_end",arg)
    pass


  def cb_mirepcb(self, arg):
    if self.parrot_flag:
      print("cb_mirepcb",arg)
    pass

  def cb_mirepcb_po(self, arg):
    if self.parrot_flag:
      print("cb_mirepcb_po",arg)
    pass

  def cb_mirepcb_end(self, arg):
    if self.parrot_flag:
      print("cb_mirepcb_end",arg)
    pass


  def cb_cotation(self, arg):
    if self.parrot_flag:
      print("cb_cotation",arg)
    pass

  def cb_cotation_ge(self, arg):
    if self.parrot_flag:
      print("cb_cotation_ge",arg)
    pass

  def cb_cotation_te(self, arg):
    if self.parrot_flag:
      print("cb_cotation_te",arg)
    pass

  def cb_cotation_po(self, arg):
    if self.parrot_flag:
      print("cb_cotation_po",arg)
    pass

  def cb_cotation_sb(self, arg):
    if self.parrot_flag:
      print("cb_cotation_sb",arg)
    pass

  def cb_cotation_sd(self, arg):
    if self.parrot_flag:
      print("cb_cotation_sd",arg)
    pass

  def cb_cotation_sg(self, arg):
    if self.parrot_flag:
      print("cb_cotation_sg",arg)
    pass

  def cb_cotation_sN(self, arg):
    if self.parrot_flag:
      print("cb_cotation_sN",arg)
    pass

  def cb_cotation_end(self, arg):
    if self.parrot_flag:
      print("cb_cotation_end",arg)
    pass


  def cb_track(self, arg):
    if self.parrot_flag:
      print("cb_track",arg)
    pass

  def cb_track_po(self, arg):
    if self.parrot_flag:
      print("cb_track_po",arg)
    pass

  def cb_track_de(self, arg):
    if self.parrot_flag:
      print("cb_track_de",arg)
    pass

  def cb_track_end(self, arg):
    if self.parrot_flag:
      print("cb_track_end",arg)
    pass


  def cb_zone(self, arg):
    if self.parrot_flag:
      print("cb_zone",arg)
    pass

  def cb_zone_po(self, arg):
    if self.parrot_flag:
      print("cb_zone_po",arg)
    pass

  def cb_zone_de(self, arg):
    if self.parrot_flag:
      print("cb_zone_de",arg)
    pass

  def cb_zone_end(self, arg):
    if self.parrot_flag:
      print("cb_zone_end",arg)
    pass


  def cb_czone(self, arg):
    if self.parrot_flag:
      print("cb_czone",arg)
    pass

  def cb_czone_zinfo(self, arg):
    if self.parrot_flag:
      print("cb_czone_zinfo",arg)
    pass

  def cb_czone_zlayer(self, arg):
    if self.parrot_flag:
      print("cb_czone_zlayer",arg)
    pass

  def cb_czone_zaux(self, arg):
    if self.parrot_flag:
      print("cb_czone_zaux",arg)
    pass

  def cb_czone_clearance(self, arg):
    if self.parrot_flag:
      print("cb_czone_clearance",arg)
    pass

  def cb_czone_zminthickness(self, arg):
    if self.parrot_flag:
      print("cb_czone_zminthickness",arg)
    pass

  def cb_czone_zoptions(self, arg):
    if self.parrot_flag:
      print("cb_czone_zoptions",arg)
    pass

  def cb_czone_zcorner(self, arg):
    if self.parrot_flag:
      print("cb_czone_zcorner",arg)
    pass

  def cb_czone_zsmoothing(self, arg):
    if self.parrot_flag:
      print("cb_czone_zsmoothing",arg)
    pass

  def cb_czone_end(self, arg):
    if self.parrot_flag:
      print("cb_czone_end",arg)
    pass


  def cb_polyscorners(self, arg):
    if self.parrot_flag:
      print("cb_polyscorners",arg)
    pass

  def cb_polyscorners_corner(self, arg):
    if self.parrot_flag:
      print("cb_polyscorners_corner",arg)
    pass

  def cb_polyscorners_end(self, arg):
    if self.parrot_flag:
      print("cb_polyscorners_end",arg)
    pass


  def cb_endboard(self, arg):
    if self.parrot_flag:
      print("cb_endboard",arg)
    pass




  op_callback = {}


  # Key entry is the state name.
  # Value is hash with name from op_descr as the key and the state to transition to.
  #    Transition  name is the name that appears in this hash.
  op_state_transition = {

    "header" : { "header" : "main" },

    "main" :  { "general" : "general",
                "sheetdescr" : "sheetdescr",
                "setup" : "setup",
                "equipot" : "equipot",
                "nclass" : "nclass",

                 "MODULE" : "module",

                "drawsegment" : "drawsegment",

                "textpcb" : "textpcb",
                "mirepcb" : "mirepcb",
                "cotation" : "cotation",
                "track" : "track",
                "zone" : "zone",
                "czone" : "czone",

                "endboard" : "header" },


    "general" : { "general_end" : "main",
                  "general_encoding"        : "general",
                  "general_units"           : "general",
                  "general_layercount"      : "general",
                  "general_ly"              : "general",
                  "general_enabledlayers"   : "general",
                  "general_links"           : "general",
                  "general_noconn"          : "general",
                  "general_di"              : "general",
                  "general_ndraw"           : "general",
                  "general_ntrack"          : "general",
                  "general_nzone"           : "general",
                  "general_nmodule"         : "general",
                  "general_boardthickness"  : "general",
                  "general_nnets"           : "general" },


    "sheetdescr" : { "sheetdescr_sheet" : "sheetdescr",
                    "sheetdescr_title" : "sheetdescr",
                    "sheetdescr_date" : "sheetdescr",
                    "sheetdescr_rev" : "sheetdescr",
                    "sheetdescr_comp" : "sheetdescr",
                    "sheetdescr_commentN" : "sheetdescr",
                    "sheetdescr_end" : "main" },

    "setup" : { "setup_internalunit"        : "setup",
                "setup_layers"              : "setup",
                "setup_layerN"              : "setup",
                "setup_trackwidth"          : "setup",
                "setup_trackclearence"      : "setup",
                "setup_zoneclearence"       : "setup",
                "setup_zone45only"          : "setup",
                "setup_trackminwidth"       : "setup",
                "setup_drawsegmwidth"       : "setup",
                "setup_edgesegmwidth"       : "setup",
                "setup_viasize"             : "setup",
                "setup_viadrill"            : "setup",
                "setup_viaminsize"          : "setup",
                "setup_viamindrill"         : "setup",
                "setup_microviasize"        : "setup",
                "setup_microviadrill"       : "setup",
                "setup_microviasallowed"    : "setup",
                "setup_microviaminsize"     : "setup",
                "setup_microviamindrill"    : "setup",
                "setup_textpcbwidth"        : "setup",
                "setup_textpcbsize"         : "setup",
                "setup_edgemodwidth"        : "setup",
                "setup_textmodsize"         : "setup",
                "setup_textmodwidth"        : "setup",
                "setup_padsize"             : "setup",
                "setup_paddrill"            : "setup",
                "setup_pad2maskclearance"   : "setup",
                "setup_soldermaskminwidth"  : "setup",
                "setup_visibleelements"     : "setup",
                "setup_auxiliaryaxisorg"    : "setup",
                "setup_pcbplotparams"       : "setup",
                "setup_end"                 : "main" },

    "equipot" : { "equipot_na" : "equipot",
                  "equipot_st" : "equipot",
                  "equipot_end" : "main" },

    "nclass" : { "nclass_name" : "nclass",
                 "nclass_desc" : "nclass",
                 "nclass_clearance" : "nclass",
                 "nclass_trackwidth" : "nclass",
                 "nclass_viadia" : "nclass",
                 "nclass_viadrill" : "nclass",
                 "nclass_uviadia" : "nclass",
                 "nclass_uviadrill" : "nclass",
                 "nclass_addnet" : "nclass",
                 "nclass_end" : "main" },


    "module" : {
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

                 "MODULE_SolderMask"        : "module",
                 "MODULE_SolderPaste"       : "module",
                 "MODULE_SolderPasteRatio"  : "module",

                 "MODULE_end" : "main",

                 "SHAPE3D" : "shape3d",

                 "PAD" : "pad" },

    "shape3d" : { "SHAPE3D_Na" : "shape3d",
                  "SHAPE3D_Sc" : "shape3d",
                  "SHAPE3D_Of" : "shape3d",
                  "SHAPE3D_Ro" : "shape3d",

                  "SHAPE3D_end" : "module" },

    "pad" : { "PAD"    : "pad",
              "PAD_Sh" : "pad",
              "PAD_Dr" : "pad",
              "PAD_At" : "pad",
              "PAD_Ne" : "pad",
              "PAD_Po" : "pad",
              "PAD_SolderMask" : "pad",

              "PAD_end" : "module" },


    "drawsegment" : { "drawsegment_po" : "drawsegment",
                      "drawsegment_de" : "drawsegment",
                      "drawsegment_end" : "main" },

    "textpcb" : { "textpcb_te" : "textpcb",
                  "textpcb_nl" : "textpcb",
                  "textpcb_po" : "textpcb",
                  "textpcb_de" : "textpcb",
                  "textpcb_end" : "main" }, 

    "mirepcb" : { "mirepcb_po" : "mirepcb",
                  "mirepcb_end" : "main" }, 

    "cotation" : { "cotation_ge" : "cotation",
                   "cotation_te" : "cotation",
                   "cotation_po" : "cotation",
                   "cotation_sb" : "cotation",
                   "cotation_sd" : "cotation",
                   "cotation_sg" : "cotation",
                   "cotation_sN" : "cotation",
                   "cotation_end" : "main" },

    "track" : { "track_po" : "track",
                "track_de" : "track",
                "track_end" : "main" },

    "zone" : { "zone_po" : "zone",
               "zone_de" : "zone",
               "zone_end" : "main" },

    "czone" : { "czone_zinfo" : "czone",
                "czone_zlayer" : "czone",
                "czone_zaux" : "czone",
                "czone_clearance" : "czone",
                "czone_zminthickness" : "czone",
                "czone_zoptions" : "czone",
                "czone_zcorner" : "czone",
                "czone_zsmoothing" : "czone",
                "polyscorners" : "polyscorners",
                "czone_end" : "main" },
 
    "polyscorners" : { "polyscorners_corner" : "polyscorners",
                       "polyscorners_end" : "czone" }


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

    "header" :  self.cb_header,

    "general" :  self.cb_general,
    "general_encoding" :  self.cb_general_encoding,
    "general_units" :  self.cb_general_units,
    "general_layercount" :  self.cb_general_layercount,
    "general_ly" :  self.cb_general_ly,
    "general_enabledlayers" :  self.cb_general_enabledlayers,
    "general_links" :  self.cb_general_links,
    "general_noconn" :  self.cb_general_noconn,
    "general_di" :  self.cb_general_di,
    "general_ndraw" :  self.cb_general_ndraw,
    "general_ntrack" :  self.cb_general_ntrack,
    "general_nzone" :  self.cb_general_nzone,
    "general_nmodule" :  self.cb_general_nmodule,
    "general_boardthickness" :  self.cb_general_boardthickness,
    "general_nnets" :  self.cb_general_nnets,
    "general_end" :  self.cb_general_end,

    "sheetdescr" :  self.cb_sheetdescr,
    "sheetdescr_sheet" :  self.cb_sheetdescr_sheet,
    "sheetdescr_title" :  self.cb_sheetdescr_title,
    "sheetdescr_date" :  self.cb_sheetdescr_date,
    "sheetdescr_rev" :  self.cb_sheetdescr_rev,
    "sheetdescr_comp" :  self.cb_sheetdescr_comp,
    "sheetdescr_commentN" :  self.cb_sheetdescr_commentN,
    "sheetdescr_end" :  self.cb_sheetdescr_end,

    "setup" :  self.cb_setup,
    "setup_internalunit" :  self.cb_setup_internalunit,
    "setup_layers" :  self.cb_setup_layers,
    "setup_layerN" :  self.cb_setup_layerN,
    "setup_trackwidth" :  self.cb_setup_trackwidth,
    "setup_trackclearence" :  self.cb_setup_trackclearence,
    "setup_zoneclearence" :  self.cb_setup_zoneclearence,
    "setup_zone45only" :  self.cb_setup_zone45only,
    "setup_trackminwidth" :  self.cb_setup_trackminwidth,
    "setup_drawsegmwidth" :  self.cb_setup_drawsegmwidth,
    "setup_edgesegmwidth" :  self.cb_setup_edgesegmwidth,
    "setup_viasize" :  self.cb_setup_viasize,
    "setup_viadrill" :  self.cb_setup_viadrill,
    "setup_viaminsize" :  self.cb_setup_viaminsize,
    "setup_viamindrill" :  self.cb_setup_viamindrill,
    "setup_microviasize" :  self.cb_setup_microviasize,
    "setup_microviadrill" :  self.cb_setup_microviadrill,
    "setup_microviasallowed" :  self.cb_setup_microviasallowed,
    "setup_microviaminsize" :  self.cb_setup_microviaminsize,
    "setup_microviamindrill" :  self.cb_setup_microviamindrill,
    "setup_textpcbwidth" :  self.cb_setup_textpcbwidth,
    "setup_textpcbsize" :  self.cb_setup_textpcbsize,
    "setup_edgemodwidth" :  self.cb_setup_edgemodwidth,
    "setup_textmodsize" :  self.cb_setup_textmodsize,
    "setup_textmodwidth" :  self.cb_setup_textmodwidth,
    "setup_padsize" :  self.cb_setup_padsize,
    "setup_paddrill" :  self.cb_setup_paddrill,
    "setup_pad2maskclearance" :  self.cb_setup_pad2maskclearance,
    "setup_soldermaskminwidth" :  self.cb_setup_soldermaskminwidth,
    "setup_visibleelements" :  self.cb_setup_visibleelements,
    "setup_auxiliaryaxisorg" :  self.cb_setup_auxiliaryaxisorg,
    "setup_pcbplotparams" :  self.cb_setup_pcbplotparams,
    "setup_end" :  self.cb_setup_end,

    "equipot" :  self.cb_equipot,
    "equipot_na" :  self.cb_equipot_na,
    "equipot_st" :  self.cb_equipot_st,
    "equipot_end" :  self.cb_equipot_end,

    "nclass" :  self.cb_nclass,
    "nclass_name" :  self.cb_nclass_name,
    "nclass_desc" :  self.cb_nclass_desc,
    "nclass_clearance" :  self.cb_nclass_clearance,
    "nclass_trackwidth" :  self.cb_nclass_trackwidth,
    "nclass_viadia" :  self.cb_nclass_viadia,
    "nclass_viadrill" :  self.cb_nclass_viadrill,
    "nclass_uviadia" :  self.cb_nclass_uviadia,
    "nclass_uviadrill" :  self.cb_nclass_uviadrill,
    "nclass_addnet" :  self.cb_nclass_addnet,
    "nclass_end" :  self.cb_nclass_end,

    "MODULE" :  self.cb_MODULE,
    "MODULE_Po" :  self.cb_MODULE_Po,
    "MODULE_Li" :  self.cb_MODULE_Li,
    "MODULE_Sc" :  self.cb_MODULE_Sc,
    "MODULE_AR" :  self.cb_MODULE_AR,
    "MODULE_Op" :  self.cb_MODULE_Op,
    "MODULE_Tn" :  self.cb_MODULE_Tn,
    "MODULE_Cd" :  self.cb_MODULE_Cd,
    "MODULE_Kw" :  self.cb_MODULE_Kw,
    "MODULE_At" :  self.cb_MODULE_At,
    "MODULE_DS" :  self.cb_MODULE_DS,
    "MODULE_DC" :  self.cb_MODULE_DC,
    "MODULE_DA" :  self.cb_MODULE_DA,
    "MODULE_DP" :  self.cb_MODULE_DP,
    "MODULE_DI" :  self.cb_MODULE_DI,
    "MODULE_SolderMask" :  self.cb_MODULE_SolderMask,
    "MODULE_SolderPaste" :  self.cb_MODULE_SolderPaste,
    "MODULE_SolderPasteRatio" :  self.cb_MODULE_SolderPasteRatio,
    "MODULE_end" :  self.cb_MODULE_end,

    "SHAPE3D" :  self.cb_SHAPE3D,
    "SHAPE3D_Na" :  self.cb_SHAPE3D_Na,
    "SHAPE3D_Sc" :  self.cb_SHAPE3D_Sc,
    "SHAPE3D_Of" :  self.cb_SHAPE3D_Of,
    "SHAPE3D_Ro" :  self.cb_SHAPE3D_Ro,
    "SHAPE3D_end" :  self.cb_SHAPE3D_end,

    "PAD" :  self.cb_PAD,
    "PAD_Sh" :  self.cb_PAD_Sh,
    "PAD_Dr" :  self.cb_PAD_Dr,
    "PAD_At" :  self.cb_PAD_At,
    "PAD_Ne" :  self.cb_PAD_Ne,
    "PAD_Po" :  self.cb_PAD_Po,
    "PAD_SolderMask" :  self.cb_PAD_SolderMask,
    "PAD_end" :  self.cb_PAD_end,

    "drawsegment" :  self.cb_drawsegment,
    "drawsegment_po" :  self.cb_drawsegment_po,
    "drawsegment_de" :  self.cb_drawsegment_de,
    "drawsegment_end" :  self.cb_drawsegment_end,

    "textpcb" :  self.cb_textpcb,
    "textpcb_te" :  self.cb_textpcb_te,
    "textpcb_nl" :  self.cb_textpcb_nl,
    "textpcb_po" :  self.cb_textpcb_po,
    "textpcb_de" :  self.cb_textpcb_de,
    "textpcb_end" :  self.cb_textpcb_end,

    "mirepcb" :  self.cb_mirepcb,
    "mirepcb_po" :  self.cb_mirepcb_po,
    "mirepcb_end" :  self.cb_mirepcb_end,

    "cotation" :  self.cb_cotation,
    "cotation_ge" :  self.cb_cotation_ge,
    "cotation_te" :  self.cb_cotation_te,
    "cotation_po" :  self.cb_cotation_po,
    "cotation_sb" :  self.cb_cotation_sb,
    "cotation_sd" :  self.cb_cotation_sd,
    "cotation_sg" :  self.cb_cotation_sg,
    "cotation_sN" :  self.cb_cotation_sN,
    "cotation_end" :  self.cb_cotation_end,

    "track" :  self.cb_track,
    "track_po" :  self.cb_track_po,
    "track_de" :  self.cb_track_de,
    "track_end" :  self.cb_track_end,

    "zone" :  self.cb_zone,
    "zone_po" :  self.cb_zone_po,
    "zone_de" :  self.cb_zone_de,
    "zone_end" :  self.cb_zone_end,

    "czone" :  self.cb_czone,
    "czone_zinfo" :  self.cb_czone_zinfo,
    "czone_zlayer" :  self.cb_czone_zlayer,
    "czone_zaux" :  self.cb_czone_zaux,
    "czone_clearance" :  self.cb_czone_clearance,
    "czone_zminthickness" :  self.cb_czone_zminthickness,
    "czone_zoptions" :  self.cb_czone_zoptions,
    "czone_zcorner" :  self.cb_czone_zcorner,
    "czone_zsmoothing" :  self.cb_czone_zsmoothing,
    "czone_end" :  self.cb_czone_end,

    "polyscorners" :  self.cb_polyscorners,
    "polyscorners_corner" :  self.cb_polyscorners_corner,
    "polyscorners_end" :  self.cb_polyscorners_end,

    "endboard" :  self.cb_endboard

    }

  def debug(self):
    print("op_descr:")
    for op in self.op_descr:
      print(op, self.op_descr[op])

    print("\nop_state_transition:")
    for s in self.op_state_transition:
      for op  in self.op_state_transition[s]:
        print("state:", s, " op:", op, " transition:", self.op_state_transition[s][op])

    print("\nop_re:")
    for op in self.op_re:
      print("op:", op, "op_re:", self.op_re[op])


  def read_brd(self, fn):

    self.brd_file = fn

    if fn != "-":
      f = open( fn, "r" )
      self.brd = f.read()
      f.close()

      f = open( fn, "r" )
      self.brd_lines = f.readlines()
      f.close()
    else:
      self.brd_lines = sys.stdin.readlines()
      self.brd = "\n".join( self.brd_lines )


  def parse_brd(self, fn):

    self.read_brd(fn)
    line_no = 0

    for l in self.brd_lines:
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
        extra = str( self.parse_state )
        raise parse_exception("ERROR, couldn't match line '" + str(l) + "', line_no: " +  str(line_no) + " (parse_state:" + str(self.parse_state) + ")" +", state: " + extra )

      self.op_callback[ op ]( matched_arg )

if __name__ == "__main__":
  if (len(sys.argv) < 2):
    print("provide board file")
    sys.exit(0)
  s = brd()
  s.parrot_flag = True
  #s.read_brd(sys.argv[1])
  s.parse_brd(sys.argv[1])


