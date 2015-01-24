#!/usr/bin/python
#
"""
Helper library to genreate gerber files
"""


import sys, os, re



class pygerber(object):

  def __init__(self):
    self.state = "init"
    self._command = []
    self._aperture = []
    self._apertureMacro = []

    self.Xdig  = 2
    self.Xfrac = 6
    self.Ydig  = 2
    self.Yfrac = 6

    self.Xmax = 0
    self.Ymax = 0

    self.invertY = False

    self.leading_zero_flag = "L"  # 'L' omit leading zeros, 'T' omit trailing
    self.coordinate_code = "A"  # 'A' absolute, 'I' incremental
    self.unit = "IN" # 'IN' inches, 'MM' mm
    self.image_polarity = "POS" # 'POS', 'NEG'
    self.level_polarity = 'C' # 'C' clear, 'D' dark

    self._updateXFormat( self.Xdig, self.Xfrac )
    self._updateYFormat( self.Ydig, self.Yfrac )


  def _updateXFormat( self, dig, frac ):
    self.Xmax = int( "9"*dig + "9"*frac )

  def _updateYFormat( self, dig, frac ):
    self.Ymax = int( "9"*dig + "9"*frac )

  def _fmt( self, n, n_frac, val ):
    fval = float(val)
    afval = abs( fval )

    lead_char = ''
    if (fval < 0): 
      n+=1
      lead_char = '-'

    #print "_fmt:", fval, afval, lead_char, n

    s = "{0:0" + str(n) + "." + str(n_frac) + "f}"

    #print "_fmt:", fval, afval, lead_char, n, s

    v = s.format( afval )
    v = v.strip()


    #print "_fmt:", s, v

    if (self.leading_zero_flag == 'L'):
      v = re.sub('^0*', '', v )
      v = re.sub('^\.', '0.', v )
      v = re.sub( '\.', '', v )

    elif (self.leading_zero_flag == 'T'):
      v = re.sub('0*$', '', v )
      v = re.sub( '\.', '', v )

    #print "_fmt...:", v

    return lead_char + v

  def _Ifmt (self, x ):
    n = self.Xdig + self.Xfrac + 1

    if (self.Xdig == 0): n -= 1
    if (self.Xfrac == 0): n -= 1

    if n<=0: return

    return "I" + self._fmt(n, self.Xfrac, x)

  def _Jfmt (self, x ):
    n = self.Ydig + self.Yfrac + 1

    if (self.Ydig == 0): n -= 1
    if (self.Yfrac == 0): n -= 1

    if n<=0: return

    if self.invertY:
      return "J" + self._fmt(n, self.Yfrac, -float(x) )
    else:
      return "J" + self._fmt(n, self.Yfrac, x)


  def _Xfmt( self, x ):
    n = self.Xdig + self.Xfrac + 1

    if (self.Xdig == 0): n -= 1
    if (self.Xfrac == 0): n -= 1

    if n<=0: return

    return "X" + self._fmt(n, self.Xfrac, x)

  def _Yfmt( self, y ):
    n = self.Ydig + self.Yfrac + 1

    if (self.Ydig == 0): n -= 1
    if (self.Yfrac == 0): n -= 1

    if n<=0: return

    #print "_Yfmt:", y, n, self.Yfrac

    if self.invertY:
      return "Y" + self._fmt(n, self.Yfrac, -float(y) )
    else:
      return "Y" + self._fmt(n, self.Yfrac, y)



  def defineApertureCircle(self, name, r, hole_a = None, hole_b = None ):
    extra = ""
    if hole_a is not None: extra += "X" + str(hole_a) 
    if hole_b is not None: extra += "X" + str(hole_b)

    self._aperture.append( "%ADD" + str(name) + "C," + "{:0.4f}".format(r) + extra + "*%" )
    self._command.append( "%ADD" + str(name) + "C," + "{:0.4f}".format(r) + extra + "*%" )

  def defineApertureRectangle(self, name, x, y, hole_a = None, hole_b = None ):
    extra = ""
    if hole_a is not None: extra += "X" + str(hole_a) 
    if hole_b is not None: extra += "X" + str(hole_b)

    self._aperture.append( "%ADD" + str(name) + "R," + "{:0.4f}".format(x) + "X" + "{:0.4f}".format(y) + "*%" )
    self._command.append( "%ADD" + str(name) + "R," + "{:0.4f}".format(x) + "X" + "{:0.4f}".format(y) + "*%" )

  def defineApertureObround(self, name, x, y, hole_a = None, hole_b = None ):
    extra = ""
    if hole_a is not None: extra += "X" + str(hole_a) 
    if hole_b is not None: extra += "X" + str(hole_b)

    self._aperture.append( "%ADD" + str(name) + "O," + "{:10.4f}".format(x) + "X" + "{:10.4f}".format(y) + "*%" )
    self._command.append( "%ADD" + str(name) + "O," + "{:10.4f}".format(x) + "X" + "{:10.4f}".format(y) + "*%" )

  def defineAperturePolygon(self, name, r, n, rot_deg = None, hole_a = None, hole_b = None ):
    extra = ""
    if rot_deg is not None: extra += "X" + str(rot_deg)
    if hole_a is not None: extra += "X" + str(hole_a) 
    if hole_b is not None: extra += "X" + str(hole_b)

    self._aperture.append( "%ADD" + str(name) + "P," + "{:10.4f}".format(r) + "X" + str(n) + "*%" )
    self._command.append( "%ADD" + str(name) + "P," + "{:10.4f}".format(r) + "X" + str(n) + "*%" )


  def apertureSet(self,  name ):
    self._command.append("D" + str(name) + "*")


  def defineApertureMacroStart(self, name):
    self._apertureMacro.append( "%AM" + name + "*" )
    self._command.append( "%AM" + name + "*" )

  def defineApertureMacroComment(self, comment ):
    self._apertureMacro.append( "0 " + comment + "*" )
    self._command.append( "0 " + comment + "*" )

  def defineApertureMacroCircle(self, exposure, x, y, diam ):
    self._apertureMacro.append( "1," + str(exposure) + "," + str(diam) + "," + str(x) + "," + str(y) + "*" )
    self._command.append( "1," + str(exposure) + "," + str(diam) + "," + str(x) + "," + str(y) + "*" )

  def defineApertureMacroLine(self, exposure, x0, y0, x1, y1, width, rot_deg = 0 ):
    # also could be 2...
    self._apertureMacro.append( "20," + str(exposure) + "," + str(width) + "," + str(x0) + "," + str(y0) + "," + str(x1) + "," + str(y1) + "," + str(rot_deg) + "*" )
    self._command.append( "20," + str(exposure) + "," + str(width) + "," + str(x0) + "," + str(y0) + "," + str(x1) + "," + str(y1) + "," + str(rot_deg) + "*" )

  def defineApertureMacroLineCenter(self, exposure, x0, y0, x1, y1, width, rot_deg = 0 ):
    self._apertureMacro.append( "21," + str(exposure) + "," + str(width) + "," + str(x0) + "," + str(y0) + "," + str(x1) + "," + str(y1) + "," + str(rot_deg) + "*" )
    self._command.append( "21," + str(exposure) + "," + str(width) + "," + str(x0) + "," + str(y0) + "," + str(x1) + "," + str(y1) + "," + str(rot_deg) + "*" )

  def defineApertureMacroLineLowerLeft(self, exposure, x0, y0, x1, y1, width, rot_deg = 0 ):
    self._apertureMacro.append( "22," + str(exposure) + "," + str(width) + "," + str(x0) + "," + str(y0) + "," + str(x1) + "," + str(y1) + "," + str(rot_deg) + "*" )
    self._command.append( "22," + str(exposure) + "," + str(width) + "," + str(x0) + "," + str(y0) + "," + str(x1) + "," + str(y1) + "," + str(rot_deg) + "*" )

  def defineApertureMacroOutline(self, exposure, pnts, rot_deg = 0):
    self._apertureMacro.append( "4," + str(exposure) + "," + str(len(pnts) + 1) + "," + str(width) + "," + ",".join( map( lambda a: str(a[0]) + "," + str(a[1]) + "\n", pnts ) ) + "," + str(rot_deg) + "*" )
    self._command.append( "4," + str(exposure) + "," + str(len(pnts) + 1) + "," + str(width) + "," + ",".join( map( lambda a: str(a[0]) + "," + str(a[1]) + "\n", pnts ) ) + "," + str(rot_deg) + "*" )

  def defineApertureMacroPolygon(self, exposure, n, x, y, diam, rot_deg = 0 ):
    self._apertureMacro.append( "5," + str(exposure) + "," + str(n) + "," + str(x) + "," + str(y) + "," + str(diam) + "," + str(rot_deg) +   "*" )
    self._command.append( "5," + str(exposure) + "," + str(n) + "," + str(x) + "," + str(y) + "," + str(diam) + "," + str(rot_deg) +   "*" )

  def defineApertureMacroMoire(self, x, y, outer_diam, gap, max_ring, xhair_thickness, xhair_length, rot_deg = 0 ):
    self._apertureMacro.append( "6," + str(x) + "," + str(y) + "," + str(outer_diam) + "," + str(gap) + "," + str(max_ring) + "," + str(xhair_thickness) + "," + str(xhair_length) + "," + str(rot_deg) +   "*" )
    self._command.append( "6," + str(x) + "," + str(y) + "," + str(outer_diam) + "," + str(gap) + "," + str(max_ring) + "," + str(xhair_thickness) + "," + str(xhair_length) + "," + str(rot_deg) +   "*" )

  def defineApertureMacroThermal(self, x, y, outer_diam, inner_diam, gap, rot_deg = 0 ):
    self._apertureMacro.append( "6," + str(x) + "," + str(y) + "," + str(outer_diam) + "," + str(inner_diam) + "," + str(gap) + "," + str(rot_deg) +   "*" )
    self._command.append( "6," + str(x) + "," + str(y) + "," + str(outer_diam) + "," + str(inner_diam) + "," + str(gap) + "," + str(rot_deg) +   "*" )

  def defineApertureMacroVariableDef(self, varname, varexpr):
    self._apertureMacro.append( "$" + str(varname) + "=" + str(varexpr) + "*" )
    self._command.append( "$" + str(varname) + "=" + str(varexpr) + "*" )

  def defineApertureMacroEnd(self):
    self._apertureMacro.append("%")
    self._command.append("%")



  def stepRepeat(self, x_rep, y_rep, i_stp, j_stp ):
    self._command.append( "%SRX" + str(x_rep) + "Y" + str(y_rep) + "I" + i_stp + "J" + j_stp + "*%" )

  def levelPolarity(sefl, dark_clear):
    self._command.append( "%LP" + dark_clear + "*%" );
    self.level_polarity = dark_clear


  def formatSpecification(self, leading_zero_code, coordinate_code, xdig, xfrac, ydig, yfrac):
    self._command.append( "%FS" + leading_zero_code + coordinate_code + "X" + str(xdig)  + str(xfrac) + "Y" + str(ydig) + str(yfrac) + "*%" )

    self.leading_zero_code = leading_zero_code
    self.coordinate_code = coordinate_code

    self.Xdig = xdig
    self.Xfrac = xfrac

    self.Ydig = ydig
    self.Yfrac = yfrac



  def comment(self, comment):
    self._command.append("G04 " + comment + "*" )

#  def coordinateFormat(self, lead_x, deci_x, lead_y, deci_y ):
#    self._command.append( "%FSLAX" + str(lead_x) + str(deci_x) + "Y" + str(lead_y) + str(deci_y) + "*%" )

  def mode(self, unit):
    self._command.append( "%MO" + unit  + "*%" )
    self.unit = unit

  def imagePolarity(self, NEG_POS):
    self._command.append( "%IP" + NEG_POS + "%" )
    self.image_polarity = NEG_POS

  def selectAperture(self, aperture_name):
    self._command.append( "D" + aperture_name + "*" )


  def move(self, x, y, move_type):
    #self._command.append( " " + self._Xfmt(x) + " " + self._Yfmt(y) + " " + "D" + str(move_type) + "*" )
    self._command.append( self._Xfmt(x) + self._Yfmt(y) + "D" + str(move_type) + "*" )


  def moveLightsOn(self, x, y):
    self.move(x,y,"01")

  def moveLightsOff(self, x, y):
    self.move(x,y,"02")

  def flash(self, x, y ):
    self.move(x,y,"03")


  def regionStart(self):
    self._command.append( "G36*" )
  
  def regionEnd(self):
    self._command.append( "G37*" )
  

  def quadrantSingle( self ):
    self._command.append( "G74" )

  def quadrantMulti( self ):
    self._command.append( "G75" )


  def lineTo( self, x, y, move_type = "01"  ):
    self._command.append( "G01" + self._Xfmt(x) + self._Yfmt(y) + "D" + str(move_type) + "*" )

  def moveTo( self, x, y,  ):
    self.lineTo(x,y,"02")


  def arcTo( self, x, y, I, J, cw_flag = True, move_type = "01" ):
    code = "02"
    if (not cw_flag): code = "03"
    self._command.append( "G" + code + self._Xfmt(x) + self._Yfmt(y) + self._Ifmt(I) + self._Jfmt(J) + "D" + str(move_type) + "*" )

  def quickSetup(self):
    self.formatSpecification( 'L', 'A', 2, 4, 2, 4)
    self.mode("IN")

  # if you just need to bypass the helper functions
  #
  def addCommand(self, cmd):
    self._command.append( cmd )

  def end(self):
    self._command.append( "M02*" )

  def _print(self, outfile=""):

    if len(outfile)==0 or outfile == "-":
      for l in self._command:
        print l
    else:
      fp = open( outfile, "w" )
      for l in self._command:
        fp.write(l)
        fp.write("\n")
      fp.close()


    #print "M02*"


if __name__ == "__main__":

  grb = pygerber()

  #grb.quickSetup()
  grb.formatSpecification( 'L', 'A', 2, 4, 2, 4 )
  grb.defineApertureCircle( 10, 0.250 )
  grb.mode("IN")
  grb.apertureSet( 10 )
  grb.moveLightsOff( 0, 0 )
  grb.moveLightsOn( 1, 0 )
  grb.moveLightsOn( 1, 1 )
  grb.moveLightsOn( 0, 1 )
  grb.moveLightsOn( 0, 0 )
  grb.flash(0.5,0.5)
  grb.end()

  grb._print()

