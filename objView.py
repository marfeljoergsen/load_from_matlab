#!/usr/bin/python2
""" Static OBJ-viewer for multibody visualization
    Author: MFJO.
"""
# python objload_test.py cube.obj
#--------------------------------------
# Basic OBJ file viewer. needs objloader from:
#  http://www.pygame.org/wiki/OBJFileLoader
# LMB + move: rotate
# RMB + move: pan
# Scroll wheel: zoom in/out
# ---------------------------------
import pygame
from pygame.locals import * # DOUBLEBUF, RESIZABLE, etc.
from pygame.constants import *

import sys # for argv, exit

import ipdb # ipdb.set_trace() # debugger stops using breakpoint here...
#import code # for interactive python console...
# code.interact(local=locals())
# code.interact(local=dict(globals(), **locals()))

import getWavefrontOBJs # for calling objloader, based on input text file
import gl_utils # for various good things...

from math import pi, atan
# ignore pylints error about internal "format" - it isn't redefined:
from OpenGL.GL import *
from OpenGL.GLU import * # for gluSphere()
import OpenGL.GLUT # for glutBitmapCharacter

#----------------------------------------------------------
# Use: "M-x occur" to search for occurences in this file...
#----------------------------------------------------------
# Check code for errors with:
#  a) pylint (=M-x pylint)
#  b) pychecker (=CTRL+C CTRL+W)
#  c) pep8 (=M-x pep8, turns on/off Flymake = slow)
#  d) pyflakes (=M-x pyflakes)
#   most of these can be run from command line too...
#
#------------------------------------------------
# You generate a ~/TAGS file using:
# 1) ctags-exuberant -e -R --languages=python --exclude="__init__.py"
#      or:
# 2) find . -type f -name '*.py' | xargs etags
#  method (1) gives a TAGS file nearly 3 times as big...
#
# You jump around using meta-dot (M-.) + meta-star (M-*)
#------------------------------------------------

# ==============================================================
#    Global variables:
# ==============================================================
#These represet mouse states we can query.
M_LEFT = 1
M_MIDDLE = 2
M_RIGHT = 3
M_WHEEL_UP = 4
M_WHEEL_DOWN = 5
orthoInterval = (0.0005, 0.05)
# ------------------------------------
class objView:
    """ OpenGL viewing class """

    def __init__(self, wavefrontOBJ):
        self.wavefront = wavefrontOBJ
        self.title = "Showing: " + \
          self.wavefront.fname + " (keys: H=help)"
        self.running = True
        # self.viewport = (800,600)
        self.viewport = (1024, 768)
        self.rx, self.ry = (0, 0) # rotation
        self.tx, self.ty, self.tz = (0, 0, 0) # translation
        self.rotCenter  = (0, 0, 0)
        self.rotate = self.move = self.zoom = False
        self.translFactor = 0
        self.zNear, self.zFar = (0, 0)
        self.orthoZoom = min(orthoInterval)
        self.orthoZoomFactor = (max(orthoInterval)-min(orthoInterval)) / 19.0
        # self.screenSurf = is made in setupGL (outside __init__)
        self.interact = False
        self.smartRotCenter = True # default for single obj-files...
        self.polyMode = False
        self.lightDone = False
        # ----
        if 0:
            v = (0, 0, 0)
        else:
            v = (90, 0, 90)
        premultiply_mat33 = gl_utils.rotXYZ(v) # 3x3 matrix
        self.premultiply_mat = gl_utils.expand33to44(premultiply_mat33) # 4x4 matrix
        # ---

        # RGB + Alpha:{0=transp, 1=opaque}
        self.backGroundColorRGBA = (0.1, 0.1, 0.1, 1.0)
        self.ballColorRGBA = (0.9, 0.9, 0.1, 0.5)

        if 0:
            self.perspective = True
        else:
            self.perspective = False

        self.BBsystemGlobal = False
        self.BBsystemGlobal = True

        self.smartRotCenter = False
        self.tx, self.ty, self.tz = (0, 0, 0) # translation
        self.rx, self.ry = (0, 0) # rotation

        if 0:
            self.hud = True
        else:
            self.hud = False


    def __call__(self):
        print "Calling: __call__(self), showing normal variables/functions:"
        print "-"*40
        varNames = dir(self)
        # Perhaps also consider: use pprint( varNames )
        # pprint.pprint( varNames )
        ignoredVars = set() # empty set
        for varStr in varNames:
            if varStr.startswith('__') and varStr.endswith('__'):
                ignoredVars.add(varStr)
            else:
                print varStr


    def setupGL(self):
        """ Setups basic OpenGL stuff """
        pygame.init()
        OpenGL.GLUT.glutInit() # for glutBitmapCharacter

        self.screenSurf = pygame.display.set_mode(self.viewport, \
                                      OPENGL | DOUBLEBUF | RESIZABLE)
        glEnable(GL_DEPTH_TEST)
        glShadeModel(GL_SMOOTH) # most obj files expect to be smooth-shaded
        glClearColor(*self.backGroundColorRGBA)

        glEnable(GL_CULL_FACE) # enabling culling is STRONGLY recommended!

        #info = pygame.display.Info()
        #print info

        # maybe setup light here!!! CONSIDER THIS ONLY ONCE!!!!!!!
        # maybe setup light here!!! CONSIDER THIS ONLY ONCE!!!!!!!
        # maybe setup light here!!! CONSIDER THIS ONLY ONCE!!!!!!!

        # Enable blending / transparancy
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.wavefront.constructAllDisplayLists()
        pygame.display.set_caption(self.title)

        # Full-screen problems with icon in upper left corner
        # looks like a bug in pygame in any cases...
        #OpenGL.GLUT.glutReshapeFunc(self.onResize)


    def checkKeyPress(self):
        """ Check for key presses """
        for e in pygame.event.get():
            if e.type == QUIT:
                # pygame.quit() sys.exit()
                self.running = False
            elif e.type == KEYDOWN and e.key == K_ESCAPE:
                # pygame.quit() sys.exit()
                self.running = False
            elif e.type == VIDEORESIZE:
                self.viewport = e.size
                gl_utils.onResize(self)
            elif e.type == KEYDOWN and e.key == K_h:   # H=help
                print " key: H     = help"
                print " key: TAB   = print info (HUD) on/off"
                print " key: B     = show bounding box on/off"
                print " key: S     = bounding box local/global system"
                print " key: I     = interactive python console"
                print " key: R     = reset view"
                print " key: P     = perspective vs. ortho (on/off)"
                print " key: C     = change rotation center (origo/geom. center)"
                print " key: F1    = polygon mode on/off"
            elif e.type == KEYDOWN and e.key == K_TAB: # P=print info
                self.hud = not self.hud
            elif e.type == KEYDOWN and e.key == K_F1: # polygon mode
                self.polyMode = not self.polyMode
            elif e.type == KEYDOWN and e.key == K_p: # perspective on/off
                self.perspective = not self.perspective

            elif e.type == KEYDOWN and e.key == K_i:   # Python console...
                self.interact = True
            elif e.type == KEYDOWN and e.key == K_s:   # Bounding Box local/global
                self.BBsystemGlobal = not self.BBsystemGlobal
                print "self.BBsystemGlobal = " + str(self.BBsystemGlobal)
                # gl_utils.printBoundBoxInfo(BBsystemGlobal, wavefront.objs)

            elif e.type == KEYDOWN and e.key == K_r:   # RESET...
                self.setInitial_tz() # change global variables
            elif e.type == KEYDOWN and e.key == K_c:   # rotation center
                self.smartRotCenter = not self.smartRotCenter
                self.setRotationCenter()

            # -------- MOUSE ACTIONS --------
            elif e.type == MOUSEBUTTONDOWN:
                if e.button   == M_WHEEL_UP:
                    if self.perspective:
                        self.tz -= self.translFactor/2
                    else:
                        self.orthoZoom = self.orthoZoomFactor/2
                elif e.button == M_WHEEL_DOWN:
                    if self.perspective:
                        self.tz += self.translFactor/2
                    else:
                        self.orthoZoom += self.orthoZoomFactor/2
                elif e.button == M_LEFT:    self.rotate = True
                elif e.button == M_RIGHT:     self.move = True
                elif e.button == M_MIDDLE:    self.zoom = True

            elif e.type == MOUSEBUTTONUP:
                if e.button   == M_LEFT:    self.rotate = False
                elif e.button == M_RIGHT:     self.move = False
                elif e.button == M_MIDDLE:    self.zoom = False

            elif e.type == MOUSEMOTION:
                i, j = e.rel
                # rotate = False # TESTING IF ZOOM MIDDLE MOUSE WORKS?
                # move = False # TESTING IF ZOOM MIDDLE MOUSE WORKS?
                if self.rotate:
                    self.rx += j # up/down movement
                    self.ry += i # left/right movment
                if self.move:
                    self.tx += i*self.translFactor/10 # left/right
                    self.ty -= j*self.translFactor/10 # up/down
                if self.zoom:
                    if self.perspective:
                        self.tz += i*self.translFactor/10
                        self.tz -= j*self.translFactor/10
                    else:
                        self.orthoZoom += i*self.orthoZoomFactor/50
                        self.orthoZoom -= j*self.orthoZoomFactor/50
        # Keep orthozoom between something:
        if self.orthoZoom < min(orthoInterval):
            self.orthoZoom = min(orthoInterval)
        elif self.orthoZoom > max(orthoInterval):
            self.orthoZoom = max(orthoInterval)
        # -------- MOUSE ACTIONS --------


    def setInitial_tz(self):
        """ Set initial tz """
        viewAngle = 120.0/180*pi # in radians
        # dx is typically wider... ??? hmmm. arst
        dx_dy = max(self.wavefront.dyGlobal, self.wavefront.dxGlobal/4*3)
        self.tz = -self.wavefront.MinMaxGlobal['z'][1] - dx_dy/(2*atan(viewAngle/2))


    def setRotationCenter(self):
        """ Set (global) rotation center coordinates """
        if self.smartRotCenter:
            self.rotCenter = \
              self.wavefront.MinMaxGlobal['x'][0] + self.wavefront.dxGlobal/2, \
              self.wavefront.MinMaxGlobal['y'][0] + self.wavefront.dyGlobal/2, \
              self.wavefront.MinMaxGlobal['z'][0] + self.wavefront.dzGlobal/2
        else:
            self.rotCenter = (0, 0, 0)


    def drawHUD(self):
        """ Draw HUD """
        # Draw rotation center
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        glColor4f(*self.ballColorRGBA)
        sphere = gluNewQuadric() # arst wavefront.diagGlobal zNear
        gluSphere(sphere, self.zNear/2, 10, 10)
        glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)


        # -----------------------------------------
        printStr = "x: [" + \
          gl_utils.engNotation( self.wavefront.MinMaxGlobal['x'][0] ) + " ; "\
          + gl_utils.engNotation( self.wavefront.MinMaxGlobal['x'][1] ) + "]"
        gl_utils.printText(0.05, 0.9, printStr)

        printStr = "y: [" + \
          gl_utils.engNotation( self.wavefront.MinMaxGlobal['y'][0] ) + " ; "\
          + gl_utils.engNotation( self.wavefront.MinMaxGlobal['y'][1] ) + "]"
        gl_utils.printText(0.05, 0.85, printStr)

        printStr = "z: [" + \
          gl_utils.engNotation( self.wavefront.MinMaxGlobal['z'][0] ) + " ; "\
          + gl_utils.engNotation( self.wavefront.MinMaxGlobal['z'][1] ) + "]"
        gl_utils.printText(0.05, 0.8, printStr)
        # -----------------------------------------

        printStr = "BB diag: " + \
          gl_utils.engNotation( self.wavefront.BoundingBox_diagGlobal )
        gl_utils.printText(0.05, 0.75, printStr)

        # Print coordinates of rotation center (maybe later, this
        #   can be changed from geom. center to user-input...?)
        printStr = "Rotation center (X / Y / Z):"
        gl_utils.printText(0.05, 0.7, printStr)
        printStr = "  (" + \
                      str( gl_utils.engNotation( self.rotCenter[0] ) ) + ' / ' + \
                      str( gl_utils.engNotation( self.rotCenter[1] ) ) + ' / ' + \
                      str( gl_utils.engNotation( self.rotCenter[2] ) ) + ')'
        gl_utils.printText(0.05, 0.65, printStr)

        printStr = "self.rx, self.ry = " + str(self.rx) + "; " + str(self.ry)
        gl_utils.printText(0.05, 0.6, printStr)

        printStr = "tx, ty, tz = " + \
                   gl_utils.engNotation(self.tx) + "; " + \
                   gl_utils.engNotation(self.ty) + "; " + \
                   gl_utils.engNotation(self.tz)
        gl_utils.printText(0.05, 0.55, printStr)

        printStr = "translFactor = " + \
                   str( gl_utils.engNotation(self.translFactor) )
        gl_utils.printText(0.05, 0.5, printStr)

        printStr = "self.zNear, self.zFar = " + \
                   str( gl_utils.engNotation( (self.zNear, self.zFar)  ) )
        gl_utils.printText(0.05, 0.45, printStr)

        if not self.perspective:
            #print str(self.orthoZoom) # DELETE THIS SOON
            printStr = "orthoZoom = " + \
                       str( gl_utils.engNotation(self.orthoZoom) )
            gl_utils.printText(0.05, 0.4, printStr)



    def runNow(self):
        """ This function starts running the openGL viewer! """

        # Simulate Matlab results:
        LCSmatlabEmulation = {} # empty dict
        if 1:
            #for key in self.wavefront.objs.keys():
            #    LCSmatlabEmulation[key] = 0, 0, 0
            # It is ok, that this generates and error,
            #   if body is fixed (it is for objView.py)
            #   and offsetMethod = Matlab
            LCSmatlabEmulation = None
        else:
            #LCSmatlabEmulation['Body1fix'] = [0, 0, 1.621]
            LCSmatlabEmulation['Body1fix'] = [0, 0, 0.1621] # delete this!!!
            LCSmatlabEmulation['Body2fix'] = [0, 0, 2.809]
            LCSmatlabEmulation['Body3fix'] = [0.2775, 0, 2.809]
            LCSmatlabEmulation['Body4fix'] = [0, 0, 3.066]
            LCSmatlabEmulation['Body5fix'] = [-0.1387, 0.2403, 2.809]
            LCSmatlabEmulation['Body6fix'] = [-0.1388, -0.2403, 2.809]
            LCSmatlabEmulation['Body7fix'] = [0.3535, 0, 3.517]
            LCSmatlabEmulation['Body8fix'] = [0.1010, 0, 5.383]
            print "WARNING: disable this LCSmatlabEmulation when done! " * 10

        # Because LCSmatlabEmulation is changed, update xyz_GlobalToLocalSys !
        gl_utils.updateGlobalXYZoffset( self.wavefront, LCSmatlabEmulation )

        # Print XYZ-offset of LCS info out, at t=0 seconds:
        gl_utils.printLCSoffsetInfo( self.wavefront )

        # Update the "total" Bounding Box for all bodies:
        gl_utils.update_allBodies_BB( self.wavefront.bodies, \
            None, self.wavefront)

        self.zNear = self.wavefront.BoundingBox_diagGlobal / 100
        self.zFar = self.wavefront.BoundingBox_diagGlobal * 5

        self.translFactor = self.wavefront.BoundingBox_diagGlobal / 10
        # ----
        self.setInitial_tz() # change global variables
        self.setRotationCenter()

        # below logger needs to be fixed, it is not ok arst!
        # self.logger.debug("Entering openGL display-loop...")

        while self.running:
            # Clear screen
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity() # now we're at 0,0,0
            # clock.tick(50) # limit to 50 FPS???

            # Setup perspective/orthographic mode:
            gl_utils.makeProjectionMatrix(self.perspective,
                *self.viewport, zNear=self.zNear, zFar=self.zFar, \
                hgtFactor=self.orthoZoom)

            # add user-defined viewpoint:
            glTranslate( self.tx, self.ty, self.tz )
            glRotate(self.rx, 1, 0, 0)
            glRotate(self.ry, 0, 1, 0)

            # Move to center of object:
            glTranslate(-self.rotCenter[0], -self.rotCenter[1], -self.rotCenter[2])

            glMultMatrixf( self.premultiply_mat )
            if not self.lightDone:
                # something wrong - only called once in any case! still look ok?
                gl_utils.setupLight(0, -1, 0) # -y=from viewers direction
                # maybe if screen resize/ortho/persp. switch, do again?
                self.lightDone = True # arst ??? does this mean anything???


            # ---------------------------------
            #  DRAW ALL BODIES (ALL ARE FIXED):
            # ---------------------------------
            # for b in range(0, len( self.wavefront.bodies )):
            for key in self.wavefront.objs.keys(): # the key is the body
                glPushMatrix() # push this wavefront.objs.keys-object
                if 0: # Draw line from global to local system:
                    gl_utils.drawLineStipple(self.wavefront.objs[key].\
                        xyz_GlobalToLocalSys)
                glTranslate( *self.wavefront.objs[key].xyz_GlobalToLocalSys )
                gl_utils.drawOBJnow( self.wavefront.objs[key], \
                    self.polyMode )
                glPopMatrix() # done using this wavefront.objs.keys-object
                gl_utils.drawBoundingBox(self.BBsystemGlobal, self.wavefront.objs[key])


            # -----------------------------------------
            #  OVERWRITE WITH ALL COORDINATE SYSTEMS:
            # -----------------------------------------
            glDisable(GL_LIGHTING)
            glDisable(GL_DEPTH_TEST)
            if 1:
                for key in self.wavefront.objs.keys(): # the key is the body
                    lenSys = self.wavefront.objs[key].lenCS
                    glPushMatrix()
                    glTranslate( *self.wavefront.objs[key].xyz_GlobalToLocalSys )
                    if not self.BBsystemGlobal:
                        mat44 = gl_utils.expand33to44( self.wavefront.objs[key].final_rot_mat )
                        glMultMatrixf( gl_utils.transpose( mat44 ) )
                    if 1:
                        if lenSys > 0:
                            gl_utils.drawCoordSys(0, 0, 0, lenSys)
                    glPopMatrix()

            # ==== DRAW GLOBAL IMORTANT STUFF (OVERWRITES STUFF) ====
            # draw GLOBAL bounding box
            gl_utils.drawBoundingBox(True, \
                self.wavefront) # true=global

            # Draw global coordinate system (i.e. localSys=False):
            if 1:
                gl_utils.drawCoordSys(0, 0, 0, 0.2 * \
                    self.wavefront.BoundingBox_diagGlobal, 5.0)

            glEnable(GL_LIGHTING)
            glEnable(GL_DEPTH_TEST)


            # --- Draw HUD ---
            if self.hud:
                self.drawHUD()

            # Draw small coord-sys in lower left corner:
            w, h = self.viewport
            gl_utils.drawSmallCS(\
                self.rx, self.ry, self.rz, 0.07, \
                float(w)/h, self.premultiply_mat)

            # -------------------------------------------------
            pygame.display.flip()
            self.checkKeyPress()
            if self.interact:
                self.interact = False
                ipdb.set_trace()



# ====================================================================

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit("ERROR: You need to pass an 'obj'-filename" + \
                 " as input argument...")
    else:
        inputFile = args[0]


    # ===== Logging =====
    if 1:
        consoleOut = True
        fileOut = False
    else:
        consoleOut = False
        fileOut = True
    # --- Fix this later, now it is not passed to anything! ---
    ch, fh, logger = gl_utils.makeLogger('objView', consoleOut, fileOut)


    # LOAD WAVEFRONT OBJECT FILE:
    #       arst logger=logger - need to pass own logger to getOBJs arst!
    wavefront = getWavefrontOBJs.getOBJs() # init empty getOBJs-class
    wavefront.load(inputFile) # load from text-file now...
    # wavefront.printBoundingBoxInfoAllBodies(showGlobal = True)

    if wavefront.bodies < 1:
        print "Error - nothing loaded - it is required for this program!"
        exit(1)

    # -----------------------------------------------------------------
    # Very important to make all of these objects fixed in ANY cases
    #  (because no Matlab input file is loaded, so nothing can move)
    # -----------------------------------------------------------------
    wavefront.makeAllOBJsFIXED()

    # -----------------------------------------------------------
    # Now openGL part begins...
    # -----------------------------------------------------------
    prog = objView(wavefront)
    logger.info(' ---- Initializing pygame and openGL-stuff... ----')

    prog.setupGL() # Before objViewer-stuff, because displaylists are made!
    prog.runNow()

    print "Done..."
    pygame.quit()

