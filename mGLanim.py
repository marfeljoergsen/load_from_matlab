# ---------------------------------------------
# mGLanim = "Multibody openGL ANimation" viewer
# ---------------------------------------------
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
import OpenGL.GLUT # for glutBitmapCharacter
from pygame.locals import *
#from pygame.constants import *

import scipy
import numpy
import getWavefrontOBJs
import gl_utils # for various good things...
#import ipdb # ipdb.set_trace() # debugger stops using breakpoint here...
from IPython import embed

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



# --------------------- class graphicsEngine: ---------------------
# If you want to debug this, in a Python console, type:
# from load_from_matlab_scipy import *
# nordTank = matlabLoader() # load data
# nordTank.printMatlab() # print extra info out
# g = mGLanim.graphicsEngine(nordTank)

class graphicsEngine:
    def __init__(self, matlabData):
        #-------- Simple variables:
        self.mlab = matlabData # or else matlabData is lost (local var)
        # self.viewport = (800,600)
        self.viewport = (1024, 768)
        self.title = "Multibody viewer: Use mouse buttons"\
                     " left+right+scroll wheel. ESC to quit."
        # self.screen is made in setupGL (outside __init__)

        # Initialize dicts (updated at each new step)
        self.LCS = {}     # xyz-coordinates
        self.mat33 = {}   # 3x3 rotation matrix
        self.mat44 = {}   # 4x4 rotation matrix

        for b in range(0,self.mlab.bodies):
            self.LCS[b] = numpy.ndarray([0,0,0])
            self.mat33[b] = numpy.eye(3) # 3x3 OpenGL matrices
            self.mat44[b] = numpy.eye(4) # 4x4 OpenGL matrices

        self.smartRotCenter = False
        self.rotCenter = (0, 0, 0)
        self.rotate = self.move = self.zoom = False

        # Last RGBA-value is alpha:{0=transp, 1=opaque}
        # self.backGroundColorRGBA = (0.5, 0.5, 0.8, 1.0) # light blue
        # self.backGroundColorRGBA = (0.4, 0.4, 0.7, 1.0) #
        self.backGroundColorRGBA = (0.5, 0.6, 0.8, 1.0) # "AIR"
        self.HGTmapColorRGBA = (0.3, 0.7, 0.3, 1.0) # "LINES IN GROUND"
        self.HGTmapGroundColorRGBA = (0.2, 0.2, 0.1, 1.0) # "GROUND"

        self.ballColorRGBA = (0.9, 0.9, 0.1, 0.5)
        self.cylinderColorRGBA = (1.0, 1.0, 1.0, 0.5)

        if len(self.mlab.Anim_dataDescription) > 0:
            self.extraAnimInfo = True
        else:
            self.extraAnimInfo = False

        self.interact = False
        # self.BBsystemGlobal = True
        self.BBsystemGlobal = False # default, to see rotating system...

        self.hud = True
        self.polyMode = False
        if 0:
            self.perspective = True
        else:
            self.perspective = False

        self.animDelay = 0
        self.orthoZoom = min(orthoInterval)
        self.orthoZoomFactor = \
          (max(orthoInterval)-min(orthoInterval)) / 19.0
        self.running = True
        self.step = 0 # Current Matlab step to show...
        #self.skipSteps = 1
        self.skipSteps = 8 # default increment
        #self.skipSteps = 7
        self.resetTime = 0
        self.cameraDemo = False

        # ----
        if 0:
            v = (0,0,0)
        else:
            v = (90,0,90)
        premultiply_mat = gl_utils.rotXYZ(v) # 3x3 matrix
        self.premultiply_mat = gl_utils.expand33to44(premultiply_mat) # 4x4 matrix
        # ---
        self.rx, self.ry, self.rz = (0,0,0) # rotation
        self.tx, self.ty = (0, 0) # translation

        # Hardcoded cylinder radii (not so good, but unavoidable here)
        self.cylHgt = 0.1 # self.wavefront.BoundingBox_diagGlobal / 20
        self.cylRadius = 0.1 # self.wavefront.BoundingBox_diagGlobal / 30

        # ----------------------------------------
        # Load OBJ files...
        #self.wavefront = getWavefrontOBJs.getOBJs("cfg/testOBJ.txt") # arst
        self.wavefront = getWavefrontOBJs.getOBJs("cfg/nordTankOBJs.txt")
        self.wavefront.load() # load from text-file now...
        # self.wavefront.printBoundingBoxInfoAllBodies(showGlobal = True)

        if self.wavefront.bodies < 1:
            print "Error - nothing loaded - it is required for this program!"
            exit(1) # else zNear and zFar should not be 0...

        if 0:
            print "MAKING ALL OBJECTS FIXED!"
            self.wavefront.makeAllOBJsFIXED()

        # ====================================================
        # end of __init__(self, matlabData)


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
        pygame.init()
        OpenGL.GLUT.glutInit() # for glutBitmapCharacter

        self.screen = pygame.display.set_mode(self.viewport,\
                                           OPENGL | DOUBLEBUF | RESIZABLE)
        glEnable(GL_DEPTH_TEST) # enabling depth test is recommended!
        glShadeModel(GL_SMOOTH) # most obj files expect to be smooth-shaded
        glClearColor(*self.backGroundColorRGBA)

        glEnable(GL_CULL_FACE) # enabling culling is STRONGLY recommended!

        #info = pygame.display.Info()
        #print info

        gl_utils.setupLight(0,0,1) # (x,y,z)

        # Enable blending / transparancy
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.wavefront.constructAllDisplayLists()
        pygame.display.set_caption(self.title)
        # end of initializeOpenGL():


    def initBBandDerivedValues(self):
        # --------------------------------------------------------------
        #   All below heavily relies on the (size of the) bounding box
        # --------------------------------------------------------------
        # Update the "total" Bounding Box for all bodies:
        gl_utils.update_allBodies_BB( self.mlab.bodies, \
            self.mat33, self.wavefront)

        # function of BB diagonal!!!
        self.makeCoordSysDisplayList(self.wavefront.BoundingBox_diagGlobal/20)

        self.zNear = self.wavefront.BoundingBox_diagGlobal / 150
        self.zFar = self.wavefront.BoundingBox_diagGlobal * 5

        # try and error
        self.translFactor = self.wavefront.BoundingBox_diagGlobal / 50
        # -------------------------
        self.setInitial_tz()
        # end of initBBandDerivedValues(self)


    def setInitial_tz(self):
        viewAngle = 120.0/180*scipy.pi # in radians
        dx_dy = max(self.wavefront.dyGlobal, \
                    self.wavefront.dxGlobal/4*3) # dx is typically wider...

        self.tz = -self.wavefront.MinMaxGlobal['z'][1] +\
                  -dx_dy/(2*scipy.arctan(viewAngle/2))


    def setRotationCenter(self):
        if self.smartRotCenter:
            # Calculate center of bounding box:
            self.rotCenter = \
              self.wavefront.MinMaxGlobal['x'][0] + \
              self.wavefront.dxGlobal/2, \
              self.wavefront.MinMaxGlobal['y'][0] + \
              self.wavefront.dyGlobal/2, \
              self.wavefront.MinMaxGlobal['z'][0] + \
              self.wavefront.dzGlobal/2
        else:
            self.rotCenter = (0,0,0)


    def makeCoordSysDisplayList(self, length):
        # ---------------------------------
        #  Make display list
        # ---------------------------------
        self.myDisplayList = glGenLists(1)
        glNewList(self.myDisplayList, GL_COMPILE)
        error = glGetError()
        if error:
            msg = gluErrorString(error)
            raise Exception(msg)

        glPushMatrix()
        gl_utils.drawCoordSys(0.0, 0.0, 0.0, length)

        glPopMatrix()
        glEndList()
        # ---------------------------------


    def makeHGTmap(self, numRows, numCols, distZ, distY):
        if 1:
            numRows = numRows+1
            numCols = numCols+1
        self.hgtMap = numpy.zeros((numRows, numCols)) + 34
        self.zaxis = numpy.linspace(-distZ, distZ, numRows)
        self.yaxis = numpy.linspace(-distY, distY, numCols)

    def drawHGTmap(self):

        glDisable(GL_LIGHTING)
        # GL_POLYGON only supports convex polygons!
        #ipdb.set_trace()
        if 1:
            yend = len(self.yaxis)-1
            zend = len(self.zaxis)-1
            glColor4f( *self.HGTmapGroundColorRGBA )
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

            glBegin(GL_QUADS)
            glVertex3f(self.hgtMap[0][0], self.yaxis[0], self.zaxis[0])
            glVertex3f(self.hgtMap[zend][0], self.yaxis[0], self.zaxis[zend])
            glVertex3f(self.hgtMap[zend][yend], self.yaxis[yend], self.zaxis[zend])
            glVertex3f(self.hgtMap[0][yend], self.yaxis[yend], self.zaxis[0])
            glEnd()

        if 1:
            # Anti-aliasing lines - frem red book?
            glEnable(GL_LINE_SMOOTH)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
            glLineWidth(1.5)

            glColor4f(*self.HGTmapColorRGBA)
            # First direction:
            raiseLevel = -0.1
            glBegin(GL_LINES)
            for z in range(0, len(self.zaxis) ):
                for y in range(0, len(self.yaxis)-1 ):
                    glVertex3f(self.hgtMap[z][y]+raiseLevel, \
                               self.yaxis[y], self.zaxis[z])
                    glVertex3f(self.hgtMap[z][y+1]+raiseLevel, \
                               self.yaxis[y+1], self.zaxis[z])
            glEnd()
            # Second direction:
            glBegin(GL_LINES)
            for z in range(0, len(self.zaxis)-1 ):
                for y in range(0, len(self.yaxis) ):
                    glVertex3f(self.hgtMap[z][y], self.yaxis[y], self.zaxis[z])
                    glVertex3f(self.hgtMap[z+1][y], self.yaxis[y], self.zaxis[z+1])
            glEnd()
        glEnable(GL_LIGHTING)


    def RunCameraDemo(self, step):
        fraction = float(step) / self.mlab.steps
        self.ry = fraction * 1000
            # glTranslate( self.tx, self.ty, self.tz )
            # glRotate(self.rx, 1, 0, 0)
            # glRotate(self.ry, 0, 1, 0)


    def drawCylinder(self, cylRadius, cylHgt):
        glDepthMask(GL_FALSE)
        glColor4f(*self.cylinderColorRGBA)
        cyl_obj = gluNewQuadric()
        glPushMatrix()
        # ------------------------------------------
        # Draw cylinder body (check the effect of culling on/off!)
        # ------------------
        glTranslate( 0.0, 0.0, -cylHgt/2 )
        # gluCylinder(gluNewQuadr, Radius_base, Radius_top,
        #               height, slices, stacks)
        gluCylinder(cyl_obj, cylRadius, cylRadius, \
            cylHgt, 12, 1)

        # Draw right disk:
        glTranslate( 0.0, 0.0, cylHgt )
        # gluQuadricOrientation(GLUquadricObj, orientation)
        #gluQuadricOrientation(cyl_obj, GLU_OUTSIDE) # culling
        # gluDisk (GLUquadricObj, innerRadius, outerRadius, slices, rings)
        gluDisk(cyl_obj, 0.0, cylRadius, 12, 1)

        # Draw left disk:
        glTranslate( 0.0, 0.0, -cylHgt )
        # gluQuadricOrientation(GLUquadricObj, orientation)
        gluQuadricOrientation(cyl_obj, GLU_INSIDE) # culling
        # gluDisk (GLUquadricObj, innerRadius, outerRadius, slices, rings)
        gluDisk(cyl_obj, 0.0, cylRadius, 12, 1)

        glPopMatrix()
        # ------------------------------------------
        glDepthMask(GL_TRUE)


    def checkKeyPress(self):
        for e in pygame.event.get():
            if e.type == QUIT:
                # pygame.quit(); sys.exit()
                self.running = False
            elif e.type == KEYDOWN and e.key == K_ESCAPE:
                self.running = False
                # pygame.quit(); sys.exit()
            elif e.type == VIDEORESIZE:
                self.viewport = e.size
                gl_utils.onResize(self)
            elif e.type == KEYDOWN and e.key == K_KP_PLUS:
                self.animDelay += 10
            elif e.type == KEYDOWN and e.key == K_KP_MINUS:
                self.animDelay -= 10
                if self.animDelay < 0:
                    self.animDelay = 0
            elif e.type == KEYDOWN and e.key == K_KP_MULTIPLY:
                self.translFactor = self.translFactor*2
                print "self.translFactor = " + gl_utils.engNotation(self.translFactor)
            elif e.type == KEYDOWN and e.key == K_KP_DIVIDE:
                self.translFactor = self.translFactor/2
                print "self.translFactor = " + gl_utils.engNotation(self.translFactor)
            elif e.type == KEYDOWN and e.key == K_h:   # H=help
                print " key: H     = help"
                print " key: ESC   = quit"
                print " key: [+-]  = speed up/down"
                print " key: [*/]  = transl.factor up/down"
                print " key: TAB   = print info (HUD) on/off"
                print " key: S     = bounding box local/global system"
                print " key: I     = interactive python console"
                print " key: E     = toggle extra anim info (on/off)"
                print " key: R     = reset view"
                print " key: P     = perspective vs. ortho (on/off)"
                print " key: C     = rotation center (origo/geom. center)"
                print " key: F1    = polygon mode on/off"
                print " key: F12   = camera demo mode on/off"
            elif e.type == KEYDOWN and e.key == K_TAB: # print info
                self.hud = not self.hud
            elif e.type == KEYDOWN and e.key == K_F1: # polygon mode
                self.polyMode = not self.polyMode
            elif e.type == KEYDOWN and e.key == K_F12: # camera demo mode
                self.cameraDemo = not self.cameraDemo
                print "Camera demo = " + str(self.cameraDemo)

            elif e.type == KEYDOWN and e.key == K_p: # perspective on/off
                self.perspective = not self.perspective

            elif e.type == KEYDOWN and e.key == K_i:   # Python console...
                self.interact = True

            elif e.type == KEYDOWN and e.key == K_e:   # Extra anim info
                if len(self.mlab.Anim_dataDescription) > 0:
                    self.extraAnimInfo = not self.extraAnimInfo
                else:
                    print "ERROR: Extra Matlab data unavailable!"
                    self.extraAnimInfo = False
                print "self.extraAnimInfo = " + str(self.extraAnimInfo)

            elif e.type == KEYDOWN and e.key == K_s:   # Bounding Box local/global
                self.BBsystemGlobal = not self.BBsystemGlobal
                print "self.BBsystemGlobal = " + str(self.BBsystemGlobal)
                # gl_utils.printBoundBoxInfo(self.BBsystemGlobal, wavefront.objs)

            elif e.type == KEYDOWN and e.key == K_r:   # RESET...
                self.setInitial_tz()
                self.setRotationCenter()
            elif e.type == KEYDOWN and e.key == K_c:   # rotation center
                self.smartRotCenter = not self.smartRotCenter
                self.setRotationCenter()

            # -------- MOUSE ACTIONS --------
            elif e.type == MOUSEBUTTONDOWN:
                if e.button   == M_WHEEL_UP:
                    if self.perspective:
                        self.tz -= self.translFactor*2
                    else:
                        self.orthoZoom -= self.orthoZoomFactor/2
                elif e.button == M_WHEEL_DOWN:
                    if self.perspective:
                        self.tz += self.translFactor*2
                    else:
                        self.orthoZoom += self.orthoZoomFactor/2
                elif e.button == M_LEFT:  self.rotate = True
                elif e.button == M_RIGHT:   self.move = True
                elif e.button == M_MIDDLE:  self.zoom = True

            elif e.type == MOUSEBUTTONUP:
                if e.button   == M_LEFT:  self.rotate = False
                elif e.button == M_RIGHT:   self.move = False
                elif e.button == M_MIDDLE:  self.zoom = False

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
        # Force orthoZoom inside a given interval
        if self.orthoZoom < min(orthoInterval):
            self.orthoZoom = min(orthoInterval)
        elif self.orthoZoom > max(orthoInterval):
            self.orthoZoom = max(orthoInterval)
        # -------- MOUSE ACTIONS --------


    def extraAnimEffects(self):

        glPushAttrib(GL_CURRENT_BIT | GL_ENABLE_BIT | GL_LINE_BIT)
        # or else x-/y-/z- axis doesn't have same color...
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)

        curStepData = self.mlab.Anim_data[:,self.step] # load all rows

        maxDist = 1 # check by manually setting "arrowEnd"
        maxVal = 150e3 # check max-value in Matlab, maybe?
        scaleFactor = maxDist / maxVal

        # ----------------
        barMaxDx = 0.22
        #import ipdb; ipdb.set_trace()
        # test = numpy.absolute( self.mlab.Anim_data[:,:] )
        # barMaxVal = test.max()
        barScaleFactor = barMaxDx / 428e3
        # Matlab:  max(max(abs(pythonAnimInfo.data(26:30,:))))
        # ----------------

        glLineWidth(2.0)
        glColor3f(1.0, 1.0, 0.5)

        # ----------------------------------------
        # use description numbers in this variable
        # ----------------------------------------
        # desc_to_do = 1,3,4
        # desc_to_do = 1,2,5,6,7,8,9
        desc_to_do = 1,2,5,6,9
        # ----------------------------------------
        for desc in desc_to_do:
            text_c1 = self.mlab.Anim_dataDescription[desc][0] # matlab column 1
            numR_c2 = self.mlab.Anim_dataDescription[desc][1] # matlab column 2
            rows_c3 = self.mlab.Anim_dataDescription[desc][2]-1 # matlab col. 3
            # NB: Subtract 1, due to Matlab->Python index!
            curData = curStepData[rows_c3]

            if text_c1 == 'rotorForceMoments':
                # print text_c1
                FxFyFz = curData[0:3]
                MxMyMz = curData[4:6]

                arrowBegin = (0,0,0)
                #arrowEnd = arrowBegin + (maxVal, maxVal, maxVal)
                arrowEnd = (arrowBegin + scaleFactor * FxFyFz)

                # import ipdb; ipdb.set_trace()
                gl_utils.coordSysArrow(\
                    arrowBegin[0], arrowBegin[1], arrowBegin[2],\
                    arrowEnd[0], arrowEnd[1], arrowEnd[2] )


            if text_c1 == 'reactForceMomentBody1':
                # print text_c1
                FxFyFz = curData[0:3]
                MxMyMz = curData[4:6]

                arrowBegin = self.LCS[0]
                arrowEnd = (arrowBegin + scaleFactor * FxFyFz)

                # import ipdb; ipdb.set_trace()
                gl_utils.coordSysArrow(\
                    arrowBegin[0], arrowBegin[1], arrowBegin[2],\
                    arrowEnd[0], arrowEnd[1], arrowEnd[2] )


            if text_c1 == 'reactForceMomentBearing1_Body1':
                # print text_c1
                FxFyFz = curData[0:3]
                MxMyMz = curData[4:6]

                bearingOffset = self.mlab.bearings[0][0][:,0]
                arrowBegin = self.LCS[0] + bearingOffset
                arrowEnd = (arrowBegin + scaleFactor * FxFyFz)

                # import ipdb; ipdb.set_trace()
                gl_utils.coordSysArrow(\
                    arrowBegin[0], arrowBegin[1], arrowBegin[2],\
                    arrowEnd[0], arrowEnd[1], arrowEnd[2] )


            if text_c1 == 'reactForceMomentBearing2_Body1':
                # print text_c1
                FxFyFz = curData[0:3]
                MxMyMz = curData[4:6]

                bearingOffset = self.mlab.bearings[0][0][:,1]
                arrowBegin = self.LCS[0] + bearingOffset
                arrowEnd = (arrowBegin + scaleFactor * FxFyFz)

                # import ipdb; ipdb.set_trace()
                gl_utils.coordSysArrow(\
                    arrowBegin[0], arrowBegin[1], arrowBegin[2],\
                    arrowEnd[0], arrowEnd[1], arrowEnd[2] )


            # ----- Lambda for gears -----
            if text_c1 == 'Ring/planet 1 (2 <-> 3)':
                # import ipdb; ipdb.set_trace()
                curPos = (0.75, 0.35)
                dy = [-0.06, -0.02]
                dx = numpy.absolute( curData[0] ) * barScaleFactor
                gl_utils.printText( curPos[0], curPos[1], text_c1)
                gl_utils.printQuad( (curPos[0], curPos[1]+dy[0]),
                                    (curPos[0]+dx, curPos[1]+dy[1]) )

            if text_c1 == 'Planet 1/sun (3 <-> 4)':
                # import ipdb; ipdb.set_trace()
                curPos = (curPos[0], curPos[1]-0.1)
                dy = [-0.06, -0.02]
                dx = numpy.absolute( curData[0] ) * barScaleFactor
                gl_utils.printText( curPos[0], curPos[1], text_c1)
                gl_utils.printQuad( (curPos[0], curPos[1]+dy[0]),
                                    (curPos[0]+dx, curPos[1]+dy[1]) )

            if text_c1 == 'Ring/planet 2 (2 <-> 5)':
                # import ipdb; ipdb.set_trace()
                curPos = (curPos[0], curPos[1]-0.1)
                dy = [-0.06, -0.02]
                dx = numpy.absolute( curData[0] ) * barScaleFactor
                gl_utils.printText( curPos[0], curPos[1], text_c1)
                gl_utils.printQuad( (curPos[0], curPos[1]+dy[0]),
                                    (curPos[0]+dx, curPos[1]+dy[1]) )

            if text_c1 == 'Ring/planet 3 (2 <-> 6)':
                # import ipdb; ipdb.set_trace()
                curPos = (curPos[0], curPos[1]-0.1)
                dy = [-0.06, -0.02]
                dx = numpy.absolute( curData[0] ) * barScaleFactor
                gl_utils.printText( curPos[0], curPos[1], text_c1)
                gl_utils.printQuad( (curPos[0], curPos[1]+dy[0]),
                                    (curPos[0]+dx, curPos[1]+dy[1]) )

            if text_c1 == 'Par.gear.1/2 (4 <-> 7)':
                # import ipdb; ipdb.set_trace()
                curPos = (curPos[0], curPos[1]-0.1)
                dy = [-0.06, -0.02]
                dx = numpy.absolute( curData[0] ) * barScaleFactor
                gl_utils.printText( curPos[0], curPos[1], text_c1)
                gl_utils.printQuad( (curPos[0], curPos[1]+dy[0]),
                                    (curPos[0]+dx, curPos[1]+dy[1]) )

        # --- done ---
        glPopAttrib()




    def drawHUD(self):
        if self.hud:
            # ===== Show basic info =====
            fps = self.clock.get_fps()
            fps_str = "FPS = " + str(int(fps))
            gl_utils.printText(0.85, 0.9, fps_str) # print frames per second

            speed_str = "Speed: " + str(self.animDelay)
            gl_utils.printText(0.85, 0.8, speed_str)

            step_str = "Step: " + str(self.step)
            gl_utils.printText(0.05,  0.9, step_str) # print current step

            simulTime = self.mlab.t[self.step]
            time_str = "Simulation time: " + \
                str( '{0:.2f}'.format(simulTime) )
            gl_utils.printText(0.05,  0.8, time_str) # print current time

            elapsedTime_str = "Time elapsed: " + \
                str( self.elapsedTime )
            gl_utils.printText(0.05, 0.7, elapsedTime_str)

        else:
            # ===== Show advanced info =====
            # Draw rotation center
            glDisable(GL_LIGHTING)
            glDisable(GL_DEPTH_TEST)
            glColor4f(*self.ballColorRGBA)
            sphere = gluNewQuadric() # arst BoundingBox_diagGlobal zNear
            gluSphere(sphere, self.zNear/2, 10, 10)
            glEnable(GL_LIGHTING)
            glEnable(GL_DEPTH_TEST)

            # -----------------------------------------
            printStr = "x: [" + gl_utils.engNotation( \
                self.wavefront.MinMaxGlobal['x'][0] ) + " ; " + \
                gl_utils.engNotation( \
                self.wavefront.MinMaxGlobal['x'][1] ) + "]"
            gl_utils.printText(0.05, 0.9, printStr)

            printStr = "y: [" + gl_utils.engNotation( \
                self.wavefront.MinMaxGlobal['y'][0] ) + " ; " + \
                gl_utils.engNotation( \
                self.wavefront.MinMaxGlobal['y'][1] ) + "]"
            gl_utils.printText(0.05, 0.85, printStr)

            printStr = "z: [" + gl_utils.engNotation( \
                self.wavefront.MinMaxGlobal['z'][0] ) + " ; " + \
                gl_utils.engNotation( \
                self.wavefront.MinMaxGlobal['z'][1] ) + "]"
            gl_utils.printText(0.05, 0.8, printStr)

            printStr = "BB diag (global): " + \
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

            printStr = "rx, ry = " + str(self.rx) + "; " + str(self.ry)
            gl_utils.printText(0.05, 0.6, printStr)

            printStr = "tx, ty, tz = " + \
                       gl_utils.engNotation(self.tx) + "; " + \
                       gl_utils.engNotation(self.ty) + "; " + \
                       gl_utils.engNotation(self.tz)
            gl_utils.printText(0.05, 0.55, printStr)

            printStr = "translFactor = " + \
                       str( gl_utils.engNotation(self.translFactor) )
            gl_utils.printText(0.05, 0.5, printStr)

            if not self.perspective:
                #print str(self.orthoZoom) # DELETE THIS SOON
                printStr = "orthoZoom = " + \
                           str( gl_utils.engNotation(self.orthoZoom) )
                gl_utils.printText(0.05, 0.45, printStr)



    def updateMatlabStep(self):
        # For all bodies, update LCS (x,y,z) + use 4 quaternions
        #      to update rotation matrix at current step
        for b in range(0, self.mlab.bodies):

            # Get (x,y,z)-coordinates using row-indices
            # -----------------------------------------
            XYZrows = scipy.array([0,1,2])
            XYZrows += 7*b # First 3 rows=first body, then add 7 per body
            # Local coordinate system (global coordinates):
            self.LCS[b] = self.mlab.q[XYZrows,self.step] # (x,y,z) coords

            # Get 4 quaternions (last 4 rows=first body 1, then add 7 per body)
            # -----------------------------------------
            Quat_rows = scipy.array([3,4,5,6])
            Quat_rows += 7*b
            quat = self.mlab.q[Quat_rows,self.step] # Current rotation

            # === Convert 4 quaternions to 3x3 and 4x4 rot. matrices ===
            mat33 = gl_utils.quatToMatrix33(quat)
            mat44 = gl_utils.expand33to44(mat33)

            # === Write identical 3x3 and 4x4 result matrices ===
            if 1: # not sure if this make any difference
                self.mat33[b] = mat33
                self.mat44[b] = mat44
            else:
                self.mat33[b] = tuple( mat33.reshape(9) )
                self.mat44[b] = tuple( mat44.reshape(16) )
            # end of loop: for b in range(0, self.mlab.bodies)



    def drawAllObjects(self):
        # ------------
        # Test section
        # ------------
        # Main shaft center 1:   1.62109008
        # Ring gear         2:        2.809
        # Planet 1          3:        2.809
        # Sun gear          4:   3.06615319
        # Planet 2          5:        2.809
        # Planet 3          6:        2.809
        # Lower gear parts  7:   3.51667973
        # Generator + gears 8:   5.38276466
        if 0: # Draw single line:
            glBegin(GL_LINES)
            glVertex3f(0.15, 0, 0) # from
            glVertex3f(0.15, 0, 2.809) # to
            #glVertex3f(0.1, 0, 1.62109008) # to
            glEnd() # GL_LINES

        # ----------------------------------------------------------
        #  DRAW FIXED OBJs FIRST - OVERWRITE WITH MOVING OBJs LATER
        # ----------------------------------------------------------
        for key_Body in self.wavefront.fixedKeys:
            glPushMatrix() # push at this body
            if 0: # Draw line from global to local system:
                gl_utils.drawLineStipple(self.wavefront.objs[key].\
                    xyz_GlobalToLocalSys)
            glTranslate( *self.wavefront.objs[key_Body].\
                         xyz_GlobalToLocalSys )
            gl_utils.drawOBJnow( self.wavefront.objs[key_Body], \
                self.polyMode )
            glPopMatrix()
            gl_utils.drawBoundingBox(self.BBsystemGlobal, \
                                     self.wavefront.objs[key_Body])

        # --------------------------------------------
        #  OVERWRITE WITH MOVING/ROTATING OBJs HERE:
        # --------------------------------------------
        for b in range(0,self.mlab.bodies):
            # Local coordinate system offset + coord.sys orientation
            LCS = self.LCS[b]
            mat = self.mat44[b]
            if 1:
                mat = gl_utils.transpose(mat) # not sure why

            if not (b+1 in self.wavefront.matlabKeys):
                # Draw a cylinder (NOT a Matlab/Wavefront obj-body)
                glPushMatrix() # -- PUSH MODELVIEW MATRIX, this b
                glTranslate( LCS[0], LCS[1], LCS[2] ) # Matlab offset...
                glMultMatrixf( mat )
                self.drawCylinder(self.cylRadius, self.cylHgt)
                glPopMatrix() # -- POP MODELVIEW MATRIX, this "b"

            else:
                # Draw display list for moving Matlab-body
                # === Do translation + rotation ===
                key_Body = b+1 # Add 1 because: b=0 is body 1, etc...
                glPushMatrix() # -- PUSH MODELVIEW MATRIX, this b
                glTranslate( *self.wavefront.objs[key_Body].\
                    xyz_GlobalToLocalSys )
                glMultMatrixf( mat ) # apply Matlab rotation
                gl_utils.drawOBJnow( self.wavefront.objs[key_Body], \
                    self.polyMode  )
                glPopMatrix() # -- POP MODELVIEW MATRIX, this "b"
                gl_utils.drawBoundingBox(self.BBsystemGlobal, \
                                     self.wavefront.objs[key_Body])

        # -----------------------------------------
        #  OVERWRITE WITH ALL COORDINATE SYSTEMS:
        # -----------------------------------------
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        lenSys = self.cylHgt # NB: THIS IS 0.1, A "MANUAL VALUE" !!!
        if 1:
            for b in range(0,self.mlab.bodies):
                key = b+1
                # read lenSys from objloader / objs[key].lenSys...
                glPushMatrix()
                glTranslate( *self.LCS[b] )
                if self.BBsystemGlobal:
                    gl_utils.drawCoordSys(0, 0, 0, lenSys)
                else:
                    # rotate to local sys! not sure why transpose here
                    glMultMatrixf( gl_utils.transpose(self.mat44[b]) )
                    gl_utils.drawCoordSys(0, 0, 0, lenSys)
                glPopMatrix()

        # ------------ Add extra animation effects ------------
        if self.extraAnimInfo:
            self.extraAnimEffects()

        if 1:
            # Draw global coordinate system (maybe rainbow-
            #   colors, timedep. on global system to see diff.)
            gl_utils.drawCoordSys(0, 0, 0, 2.0*self.cylRadius, 5.0)
        glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)

        # end of drawAllObjects(self)
        # --------------------------------------------


    def runNow(self):
        self.setupGL()

        # === UPDATE LCS+mat33+mat44 VALUES FOR THIS STEP ===
        self.updateMatlabStep() # update (now, self.step =  0)...
        gl_utils.updateGlobalXYZoffset( self.wavefront, self.LCS )

        # Print XYZ-offset of LCS info out, at t=0 seconds:
        print " "
        gl_utils.printLCSoffsetInfo( self.wavefront )

        # Get values zNear, zFar etc (MUST run self.updateMatlabStep first!):
        self.initBBandDerivedValues() # all bounding box values...

        # Based on BB values:
        self.setRotationCenter()

        # -------------------------------------------------
        # Check whether key_Body number is valid:
        for matKey in self.wavefront.matlabKeys:
            if matKey < 1 or matKey > self.mlab.bodies:
                print "Invalid Matlab body number!"
                ipdb.set_trace()
                raise Exception("ERROR: invalid Matlab body number!")
        print "*"*75
        print "Fixed objects: " + str(self.wavefront.fixedKeys)
        print "Multibody objects: " + str(self.wavefront.matlabKeys)
        print " "

        # Clock/timing stuff:
        self.clock = pygame.time.Clock() # create clock
        self.elapsedTime = 0

        self.makeHGTmap(20, 20, 200, 200) # num, num, dist, dist

        while self.running:
            # ---------------- Update clock ----------------
            self.clock.tick() # update clock, required for getting FPS
            if self.step >= self.mlab.steps:
                self.step = 0
                self.resetTime = pygame.time.get_ticks() # current time

            # Calculate elapsed time and save it (from ms -> seconds)
            self.elapsedTime = float( \
                pygame.time.get_ticks() - self.resetTime ) / 1000


            # === UPDATE LCS+mat33+mat44 VALUES FOR THIS STEP ===
            self.updateMatlabStep() # update (now, self.step =  0)...
            gl_utils.updateGlobalXYZoffset( self.wavefront, self.LCS )

            # Update the "total" Bounding Box for all bodies:
            gl_utils.update_allBodies_BB( self.mlab.bodies, \
                self.mat33, self.wavefront)


            # ---------------- Prepare drawing ----------------
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity() # now we're at 0,0,0

            # Setup perspective/orthographic mode:
            gl_utils.makeProjectionMatrix(self.perspective,
                *self.viewport, zNear=self.zNear, zFar=self.zFar, \
                hgtFactor=self.orthoZoom)

            if self.cameraDemo:
                self.RunCameraDemo(self.step)

            # add user-defined viewpoint:
            glTranslate( self.tx, self.ty, self.tz )
            glRotate(self.rx, 1, 0, 0)
            glRotate(self.ry, 0, 1, 0)

            # Move to center of bounding box (or 0,0,0):
            glTranslate(-self.rotCenter[0], \
                        -self.rotCenter[1], \
                        -self.rotCenter[2])

            glMultMatrixf( self.premultiply_mat )

            self.drawHGTmap() # draw ground

            # ---------------- Draw objects ----------------
            self.drawAllObjects()

            # DRAW GLOBAL BOUNDING BOX:
            gl_utils.drawBoundingBox(True, self.wavefront)

            # Draw small coord-sys in lower left corner:
            w, h = self.viewport
            gl_utils.drawSmallCS(\
                self.rx, self.ry, self.rz, 0.07, \
                float(w)/h, self.premultiply_mat)
            # --------- Done drawing objects ---------

            self.checkKeyPress()
            self.drawHUD()

            # update the full display Surface to the screen
            pygame.display.flip()

            if self.interact:
                self.interact = False # avoid endless loop
                print "   self.wavefront.objs.keys() = " + \
                  str( self.wavefront.objs.keys() )
                print " "
                print "self.wavefront.objs[keys] = " + \
                  str( self.wavefront.objs.keys() )
                print " "
                print "  Type \"exit\" to return program execution..."
                embed() # this call anywhere in your program will start IPython

            # -------------------------------
            #  INCREMENT TO NEXT TIME-STEP:
            # -------------------------------
            if self.step < self.mlab.steps-self.skipSteps:
                # last step is (self.mlab.steps - self.skipSteps)
                self.step += self.skipSteps
            else:
                self.step = 0 # restart...

            pygame.time.wait( self.animDelay ) # share processor !


# --------------------- class graphicsEngine: ---------------------
