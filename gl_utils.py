from OpenGL.GL import *
from OpenGL.GLU import *
# for glutBitmapCharacter (drawCoordSys + printText etc):
from OpenGL.GLUT import *
from pygame.constants import DOUBLEBUF, OPENGL, RESIZABLE
from pygame import display
# ---------
import math # sqrt + cos/sin etc.
import decimal
import logging
import numpy
import ipdb
# ----------------------------------------

coordSysColorRGB = (1.0, 1.0, 1.0)
HUDtextColorRGB = (0.9, 0.9, 0.0)
stipleLineRGB = (0.9, 0.9, 0.0)


# ------------------------------------------------------------------
def setupLight(x, y, z):
    # Setup light number 0:
    # The first three components give either the
    #   light source position, or in the case of
    #   an infinite light source, the direction the
    #   light is coming from. The fourth component
    #   should be 1.0 for a local light source
    #   and 0.0 for an infinite one.
    glLightfv(GL_LIGHT0, GL_POSITION,  (x, y, z, 0.0)) # infinite light
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.5, 0.5, 0.5, 1.0))

    glEnable(GL_LIGHT0)
    glEnable(GL_LIGHTING)
    glEnable(GL_COLOR_MATERIAL)


def setupLogger(obj,  logger = None):
    if logger == None:
        # if you make a new logger, make flag true to cleanup afterwards
        obj.cleanUpLoggingHandlers = True

        obj.consoleHandler = False
        obj.fileHandler = False
        # obj.consoleHandler = True
        # obj.fileHandler = True

        obj.ch, obj.fh, obj.logger = \
                 makeLogger('objloader.loadOBJfromFile', \
                            obj.consoleHandler, \
                            obj.fileHandler)
    else:
        # Don't try to clean up anything, just takeover logger...
        obj.cleanUpLoggingHandlers = False
        obj.logger = logger

def makeLogger(logName, consoleOut, fileOut=False):
    logger = logging.getLogger(logName)
    logger.setLevel(logging.DEBUG)
    ch = None
    fh = None

    # create formatter and add it to the handlers
    formatter = logging.Formatter(\
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',\
        datefmt='%m/%d/%Y %H:%M:%S')

    if consoleOut: # Console output ?
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)    # Print ALL
        # ch.setLevel(logging.INFO)
        # ch.setLevel(logging.WARN)
        # ch.setLevel(logging.ERROR)
        # ch.setLevel(logging.CRITICAL) # Print almost nothing...
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    if fileOut: # File output ?
        # create file handler which logs even debug messages
        fh = logging.FileHandler(logName + '.log','w')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return ch, fh, logger

def cleanUpLogging(obj):
    if obj.cleanUpLoggingHandlers: # only do this, if this flag is set
        if 1: # new method, removes all handlers...
            handlers = list(obj.logger.handlers)
            for i in handlers:
                ipdb.set_trace()
                obj.logger.removeHandler(i)
                i.flush()
                i.close()
        else: # old method
            if obj.fileHandler:
                obj.fh.close()
                obj.logger.removeHandler(obj.fh) # logger.addHandler(fh)
            if obj.consoleHandler:
                obj.ch.close()
                obj.logger.removeHandler(obj.ch) # logger.addHandler(ch)
# ----------------------------------------------------------------------

def onResize(obj):
    w, h = obj.viewport
    glViewport(0, 0, w, h)
    obj.screenSurf = display.set_mode((w, h),
         OPENGL | DOUBLEBUF | RESIZABLE)

    # Setup perspective/orthographic projection matrix:
    makeProjectionMatrix(obj.perspective,
        *obj.viewport, zNear=obj.zNear, zFar=obj.zFar, \
        hgtFactor=obj.orthoZoom)
    print "You resized the window to: ", obj.viewport

def makeProjectionMatrix(perspective, \
        width, height, zNear, zFar, hgtFactor):
    if perspective:
        makePerspective(width, height, zNear, zFar)
    else:
        makeOrthographic(width, height, zNear, zFar, hgtFactor)

def makeOrthographic(width, height, zNear, zFar, hgtFactor):
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    hgt = height * float(hgtFactor)
    # wth = (aspect_ratio * height)
    wdth = ( float(width) / float(height) ) * hgt
    # glOrtho(left, right, bottom, top, nearVal, farVal);
    glOrtho(-wdth, wdth, -hgt, hgt, zNear, zFar)
    glMatrixMode(GL_MODELVIEW)

def makePerspective(width, height, zNear, zFar):
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    if height == 0:
        height = 1 # avoid dividing by 0 for aspect ratio
    # print "Persp: width, height, zNear, zFar = ", \
    #    width, height, zNear, zFar
    own_gluPerspective(60.0, width/float(height), zNear, zFar)
    glMatrixMode(GL_MODELVIEW)

def own_gluPerspective(fovy, aspect, zNear, zFar):
    # gluPerspective(fovy, aspect, zNear, zFar)
    # gluPerspective(90.0, width/float(height), zNear, zFar)
    if 0:
        # Look at it in 2D: (zNear = x-axis, top = y-axis)
        height = zNear * math.tan(math.radians(fovy)/2)
        width = aspect*height
        glFrustum(-width, width, -height, height, zNear, zFar)
    else:
        yFac = math.tan(math.radians(fovy)/2)
        xFac = yFac * aspect
        newMatrix = (1/xFac, 0, 0, 0,
                     0, 1/yFac, 0, 0,
                     0, 0, -(zFar+zNear)/(zFar-zNear), -1,
                     0, 0, -(2*zFar*zNear)/(zFar-zNear), 0)
        glLoadMatrixf(newMatrix)
# -----------------------------


def scalar_multiply_vector(scalar, vector):
    # Use list comprehension
    newVector = [v * scalar for v in vector]
    return newVector


def convertToEng(num, prec = 4):
    with decimal.localcontext(decimal.Context(prec = prec)):
        eng = (0 + decimal.Decimal(num)).to_eng_string().lower()
        # if num == int(float(eng)) else '~' + eng # ~ means approx...
        return eng # NB: THIS IS A STRING...


def engNotation(number, prec = 4):
    """ Return approximately equal value of 'number' in
    engr. notation. Note, also works if number is a tuple/list"""
    if isinstance(number, (int, float)):
        return convertToEng(number, prec) # scalar value

    elif isinstance(number, (tuple, list, numpy.ndarray)):
        engNotation = [] # empty list
        for n in range( len(number) ):
            engNotation.append( convertToEng(number[n], prec) )
        return str( engNotation ) # return a string!

    else:
        print "Unexpected error - did you send a numpy.ndarray ?"
        ipdb.set_trace()

def constructRotMatrixFromDirection(dVec):
    # dVec is the direction: (dVec = endVec-startVec)
    norm_startVec = dVec / norm(dVec)
    #if any(isnan(norm_startVec))
    #    norm_startVec = zeros(size(norm_startVec))
    #    keyboard
    #end

    zaxis = [0, 0, 1]
    norm_endVec = zaxis / norm(zaxis)
    if numpy.isnan(norm_endVec).any():
        norm_endVec = numpy.zeros( numpy.shape(norm_endVec) )
        ipdb.set_trace()

    # Check if trying to match identital vectors:
    if not ( any(norm_startVec - norm_endVec) > 1e-14 ):
        return numpy.eye(4)

    axb = cross(norm_startVec, norm_endVec) # cross-product of a and b
    norm_axb = axb / norm(axb)
    if numpy.isnan(norm_axb).any():
        norm_axb = numpy.zeros( numpy.shape(norm_axb) )
        ipdb.set_trace()

    ac = math.acos(numpy.dot(norm_startVec, norm_endVec))

    #---------------------------------------------------------------
    # Be tolerant to column vector arguments, produce a row vector
    # r = [axb(:)' ac]
    # r = vrrotvec([dVec(1) dVec(2) dVec(3)],[0 0 1]) - returns r-vector of 4
    #---------------------------------------------------------------

    #---------------------------------------------------------------
    # vrrotvec2mat( r ) - uses the r-vector of 4, returns a 3x3 matrix
    # representation of rotation defined by the axis-angle rotation vector R.
    #---------------------------------------------------------------
    # build the rotation matrix
    s = math.sin( ac )
    c = math.cos( ac )
    t = 1 - c

    x = norm_axb[0]
    y = norm_axb[1]
    z = norm_axb[2]

    mat33 = [ \
       [t*x*x + c,    t*x*y - s*z,  t*x*z + s*y], \
       [t*x*y + s*z,  t*y*y + c,    t*y*z - s*x], \
       [t*x*z - s*y,  t*y*z + s*x,  t*z*z + c], \
       ]
    #---------------------------------------------------------------
    # vrrotvec2mat( r ) - uses the r-vector of 4, returns a 3x3 matrix
    # representation of rotation defined by the axis-angle rotation vector R.
    #---------------------------------------------------------------
    # maybe transpose mat33 ???
    # p = [xs' ys' zs'*ds] * mat33
    return expand33to44(mat33)


def cross(a, b):
    c = [a[1]*b[2] - a[2]*b[1],
         a[2]*b[0] - a[0]*b[2],
         a[0]*b[1] - a[1]*b[0]]
    return c

def norm(vec):
    return numpy.sqrt( numpy.dot(vec, vec) )

def coordSysArrow(x1, y1, z1, x2, y2, z2):

    # Size of cone in arrow:
    coneFractionAxially = 0.15
    coneFractionRadially = 0.05

    # Calculate cone parameters:
    v = numpy.array((x2-x1, y2-y1, z2-z1))
    norm_of_v = norm(v) # numpy.sqrt( numpy.dot(v, v) )
    coneHgt = coneFractionAxially * norm_of_v
    coneRadius = coneFractionRadially * norm_of_v
    vConeLocation = (1.0-coneFractionAxially) * v

    # -----------------------
    #   Draw lines
    # -----------------------
    # Draw single line:
    glBegin(GL_LINES)
    glVertex3f(x1, y1, z1) # from
    glVertex3f(x2, y2, z2) # to
    glEnd() # GL_LINES

    # Construct transformation matrix
    if (norm_of_v > 1e-12):
        # -----------------------
        #   Draw cone
        # -----------------------
        glPushMatrix()
        glPushAttrib( GL_POLYGON_BIT ) # includes GL_CULL_FACE
        glDisable(GL_CULL_FACE) # draw from all sides

        normalized_v = v/norm_of_v

        # ipdb.set_trace()
        if 1: # turn on/off here
            # Move and rotate in position:
            glTranslate( x1, y1, z1 )
            glTranslate( *vConeLocation )

            mat44 = constructRotMatrixFromDirection( normalized_v )
            #glLoadIdentity()
            # multMatrix = tuple(mat44.reshape(16))
            #multMatrix = mat44
            #print multMatrix
            glMultMatrixf( mat44 ) # or use multMatrix ???
            # Make a cone!
            cone_obj = gluNewQuadric()
            # gluCylinder(gluNewQuadr, Radius_base, Radius_top,
            #               height, slices, stacks)
            gluCylinder(cone_obj, coneRadius, 0, \
                coneHgt, 8, 1)

        glPopAttrib() # GL_CULL_FACE
        glPopMatrix()



def drawCoordSys(x, y, z, coordLength, \
        linewidth = 1.0, localSys = None):
    # NB: optional localSys can also be a string!
    # ============================================
    # save, because color is changing below!
    glPushAttrib(GL_CURRENT_BIT | GL_ENABLE_BIT | GL_LINE_BIT)

    # or else x-/y-/z- axis doesn't have same color...
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)

    # ------ lines ------
    #ipdb.set_trace()
    glLineWidth(linewidth)

    glColor3f(1.0, 0.0, 0.0) # red / x-axis:
    coordSysArrow(x, y, z, x+coordLength, y, z)

    glColor3f(0.0, 1.0, 0.0) # green / y-axis:
    coordSysArrow(x, y, z, x, y+coordLength, z)

    glColor3f(0.0, 0.0, 1.0) # blue / z-axis:
    coordSysArrow(x, y, z, x, y, z+coordLength)
    # ------ lines ------

    if not (localSys == None):
        # Now localSys=True/False/Tuple of 3 strings...
        # ---- Draw x/y/z-letters:
        if localSys == False:
            x = 'X'
            y = 'Y'
            z = 'Z'
        elif localSys == True:
            x = 'X\''
            y = 'Y\''
            z = 'Z\''
        else:
            assert len(localSys) == 3, 'Error: ' + \
              'Must have tuple for 3 axis strings...'
            x = localSys[0]
            y = localSys[1]
            z = localSys[2]

        glColor3f(*coordSysColorRGB)
        # you MUST set color BEFORE glRasterPos3f (or calling drawXYZ) !

        drawXYZ(coordLength*1.05, 0.0, 0.0, x) # X-axis
        drawXYZ(0.0, coordLength*1.05, 0.0, y) # Y-axis
        drawXYZ(0.0, 0.0, coordLength*1.05, z) # Z-axis

    # pop, because things was changed above!
    glPopAttrib()


def printLCSoffsetInfo( wavefront ):
    print " "
    print "gl_utils.printLCSoffsetInfo( ) about ...objs[obj].xyz_GlobalToLocalSys:"
    for obj in wavefront.objs:
        print "Body: " + str(obj) + ", [X,Y,Z] = " + \
          engNotation( wavefront.objs[obj].xyz_GlobalToLocalSys )


def drawSmallCS(rx, ry, rz, arrowLgt, aspect, mat=None):
    # aspect = w/h
    glMatrixMode(GL_PROJECTION)
    glPushMatrix() # push projection matrix

    glLoadIdentity()
    # glOrtho: (left/right/bottom/top/nearVal/farVal)
    #glOrtho(-0.1, 1.0, -0.1, 1.0, -1.0, 1.0)
    glOrtho(0, aspect, 0, 1.0, -1.0, 1.0)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix() # push modelview matrix
    glLoadIdentity()
    # ------------------------------

    # Translate to 8% right + 8% up!
    glTranslate(0.08, 0.08, 0)
    glRotate(rx, 1, 0, 0)
    glRotate(ry, 0, 1, 0)
    glRotate(rz, 0, 0, 1)

    if mat is not None:
        glMultMatrixf( mat )

    drawCoordSys(0, 0, 0, arrowLgt) # localSys = False

    # ------------------------------
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix() # <--------------------------- POP MODELVIEW MATRIX

    glMatrixMode(GL_PROJECTION)
    glPopMatrix() # <--------------------------- POP PROJECTION MATRIX

    glMatrixMode(GL_MODELVIEW)


def findBoundingBox(vertices):
    MinMax = {} # define a dict...

    if len(vertices) < 1:
        if 1:
            MinMax['x'] = [0, 0]
            MinMax['y'] = [0, 0]
            MinMax['z'] = [0, 0]
        else:
            MinMax['x'] = [None, None]
            MinMax['y'] = [None, None]
            MinMax['z'] = [None, None]
        dxObj = 0
        dyObj = 0
        dzObj = 0
        BoundingBox_diag = 0

    else:
        # Determine bounding box:
        vertex = vertices[0]

        # same min/max value, first coord.
        MinMax['x'] = [vertex[0], vertex[0]]
        MinMax['y'] = [vertex[1], vertex[1]]
        MinMax['z'] = [vertex[2], vertex[2]]
        for vertex in vertices[1:]:
            # X-direction:
            if vertex[0] < MinMax['x'][0]:
                MinMax['x'][0] = vertex[0]
            if vertex[0] > MinMax['x'][1]:
                MinMax['x'][1] = vertex[0]
            # Y-direction:
            if vertex[1] < MinMax['y'][0]:
                MinMax['y'][0] = vertex[1]
            if vertex[1] > MinMax['y'][1]:
                MinMax['y'][1] = vertex[1]
            # Z-direction:
            if vertex[2] < MinMax['z'][0]:
                MinMax['z'][0] = vertex[2]
            if vertex[2] > MinMax['z'][1]:
                MinMax['z'][1] = vertex[2]
        # --- dx, dy and dz of BB ---
        dxObj = MinMax['x'][1] - MinMax['x'][0] # max - min
        dyObj = MinMax['y'][1] - MinMax['y'][0] # max - min
        dzObj = MinMax['z'][1] - MinMax['z'][0] # max - min
        if dxObj < 0 or dyObj < 0 or dzObj < 0:
            print "dxObj, dyObj, dzObj < 0:", dxObj, dyObj, dzObj
            ipdb.set_trace()

        # --- Length of diagonal of BB ---
        BoundingBox_diag = math.sqrt( dxObj**2 + dyObj**2 + dzObj**2 )

    return MinMax, dxObj, dyObj, dzObj, BoundingBox_diag


def make8nodeBox(MinMax):
    vertices = numpy.zeros((8, 3))

    # Front plane:
    vertices[0,:] = MinMax['x'][0], MinMax['y'][0], MinMax['z'][0]
    vertices[1,:] = MinMax['x'][0], MinMax['y'][0], MinMax['z'][1]
    vertices[2,:] = MinMax['x'][0], MinMax['y'][1], MinMax['z'][1]
    vertices[3,:] = MinMax['x'][0], MinMax['y'][1], MinMax['z'][0]

    # Rear plane:
    vertices[4,:] = MinMax['x'][1], MinMax['y'][0], MinMax['z'][0]
    vertices[5,:] = MinMax['x'][1], MinMax['y'][0], MinMax['z'][1]
    vertices[6,:] = MinMax['x'][1], MinMax['y'][1], MinMax['z'][1]
    vertices[7,:] = MinMax['x'][1], MinMax['y'][1], MinMax['z'][0]

    return vertices


def drawBox(BBsettings, MinMax):
    if BBsettings['drawBB'] == True:

        glPushMatrix()
        # --------------
        verts = make8nodeBox(MinMax)
        # ipdb.set_trace()

        # Order: left, front, bottom, right, rear, top
        drawFaces = True, True, True, True, True, True

        # OpenGL face culling calculates the signed area of the filled
        # primitive in window coordinate space. The signed area is
        # positive when the window coordinates are in a counter-
        # clockwise order and negative when clockwise.

        glColor3f(*BBsettings['color'])
        if 0: # NB: verts[0,:] = verts[0] etc...!
            for v in range(0, len(verts)):
                drawXYZ( *verts[v], txtStr=str(v) )
        # ----
        glPushAttrib( GL_POLYGON_BIT ) # includes GL_CULL_FACE
        if BBsettings['cullFaceEnabled']:
            glEnable(GL_CULL_FACE)
        else:
            glDisable(GL_CULL_FACE)
        # ----
        glPolygonMode( GL_FRONT_AND_BACK, GL_LINE ) # turn on polygon-mode
        glBegin(GL_QUADS) # glEnd()

        if drawFaces[0]: # 1, XY-plane (left)
            glVertex3f( *verts[3,:] )
            glVertex3f( *verts[7,:] )
            glVertex3f( *verts[4,:] )
            glVertex3f( *verts[0,:] )

        if drawFaces[1]: # 2, YZ-plane (front)
            glVertex3f( *verts[0,:] )
            glVertex3f( *verts[1,:] )
            glVertex3f( *verts[2,:] )
            glVertex3f( *verts[3,:] )

        if drawFaces[2]: # 3, ZX-plane (bottom)
            glVertex3f( *verts[4,:] )
            glVertex3f( *verts[5,:] )
            glVertex3f( *verts[1,:] )
            glVertex3f( *verts[0,:] )

        if drawFaces[3]: # 4, XY-plane (right)
            glVertex3f( *verts[1,:] )
            glVertex3f( *verts[5,:] )
            glVertex3f( *verts[6,:] )
            glVertex3f( *verts[2,:] )

        if drawFaces[4]: # 5, XY-plane (rear)
            glVertex3f( *verts[7,:] )
            glVertex3f( *verts[6,:] )
            glVertex3f( *verts[5,:] )
            glVertex3f( *verts[4,:] )

        if drawFaces[5]: # 6, ZX-plane (top)
            glVertex3f( *verts[3,:] )
            glVertex3f( *verts[2,:] )
            glVertex3f( *verts[6,:] )
            glVertex3f( *verts[7,:] )
        # ----
        glEnd() # glBegin(GL_QUADS)
        # --------------
        # turn off polygon-mode:
        glPolygonMode( GL_FRONT_AND_BACK, GL_FILL )
        glPopAttrib() # get GL_POLYGON_BIT
        glPopMatrix()


def addVectors(list1xyz, list2xyz):
    # NB: Must be LIST input and output, to ensure it works when
    #     numpy is out of scope/everywhere in the program...
    listOut = numpy.asarray(list1xyz) + numpy.asarray(list2xyz)
    return list( listOut )


def drawLineStipple(toXYZ, fromXYZ=(0,0,0) ):
    glColor3f(*stipleLineRGB)
    if 1:
        glLineStipple(1, 0x3F07)
        glEnable(GL_LINE_STIPPLE)

    # ipdb.set_trace()
    glBegin(GL_LINES)
    glVertex3f( *fromXYZ )
    glVertex3f( *toXYZ )
    glEnd()
    glDisable(GL_LINE_STIPPLE)



def returnUseXYZoffset(offsetMethod, LCS, obj):

    offMethod = offsetMethod.strip().lower()
    # ------------------------------------------------
    if offMethod == 'matlab':
        if LCS is None:
            print "Invalid setting - cannot have " + \
              +"offsetMethod=matlab without LCS"
            ipdb.set_trace() # type "up" to see stack trace
        else:
            # Use Matlab (global) coordinate system offset
            useXYZoffset = ( LCS[0], LCS[1], LCS[2] )

    elif offMethod == 'fixed':
        if 1: # Really recalculate? Is it necessary?
            useXYZoffset = \
              ( GetGlobalXYZ(obj.rot, \
                             obj.local_offs, \
                             obj.global_offs) )
        else: # Use the old xyz_GlobalToLocalSys-value...
            useXYZoffset = \
              obj.xyz_GlobalToLocalSys

    elif (offMethod == 'matlab+fixed') or (offMethod == 'fixed+matlab'):
        # Use a combination of the two above:
        orig_useXYZoffset = \
            GetGlobalXYZ(obj.rot, obj.local_offs, obj.global_offs)
        if 1: # std. python: List comprehension
            useXYZoffset = [x+y for x,y in zip( \
                LCS, orig_useXYZoffset )]
        else: # numpy/scipy?
            useXYZoffset = LCS + orig_useXYZoffset

    else: # default
        print "-"*60
        print "WARNING: File: " + obj.OBJfname + \
          ", invalid valued: " + \
          "offsetMethod = " + offMethod
        print "-"*60
        ipdb.set_trace()
        useXYZoffset = \
          ( GetGlobalXYZ(obj.rot, \
                         obj.local_offs, \
                         obj.global_offs) )
    # ------------------
    return useXYZoffset # RETURN THE RESULT !
    # ------------------------------------------------

def updateGlobalXYZoffset( wavefront, LCSmatlabEmulation ):
    # ====== Update xyz_GlobalToLocalSys ======
    for key in wavefront.objs.keys():
        offsetMethod = wavefront.objs[key].offsetMethod
        # -----------------------------
        if wavefront.objs[key].isMatlabBody:
            try:
                useXYZoffset = returnUseXYZoffset(
                    offsetMethod, LCSmatlabEmulation[key-1], wavefront.objs[key] )
            except:
                print "This doesn't look like a Matlab object!"*10
                ipdb.set_trace()
                raise
        else:
            try:
                useXYZoffset = returnUseXYZoffset(
                    offsetMethod, LCSmatlabEmulation[key], wavefront.objs[key] )
            except:
                # This is ok, LCSmatlabEmulation has no key
                useXYZoffset = returnUseXYZoffset(
                    offsetMethod, None, wavefront.objs[key] )
                # You can get an error here, if you have a fixed obj
                #   and set offsetMethod = Matlab, if you don't
                #   provide any LCS[key] input to this function
        # -----------------------------
        # Save new update xyz_GlobalToLocalSys-value:
        wavefront.objs[key].xyz_GlobalToLocalSys = useXYZoffset


def updateGlobalBBcurObj(curObj, matrix33):
    #     Never touch MinMaxLocal, after loading data file -
    #     but keep changing MinMaxGlobal+MinMaxGlobalORIGIN
    # ---------------------------------------------------------
    # Seek to avoid numerical issues (by re-reading orig. vertices):
    local_vertices = make8nodeBox(curObj.MinMaxLocal)

    if 1:
        # 1. rotation: Apply the "final_rot" rotation...
        if  curObj.final_rot[0:3]!=[0.0, 0.0, 0.0]:
            # final_rot_mat = rotXYZ( curObj.final_rot )
            global_vertices = rotateVertices(\
                curObj.final_rot_mat, local_vertices)
        else:
            global_vertices = local_vertices

        # 2. rotation: Apply the rotating/time-dependent rotation...
        if numpy.array_equal( matrix33, numpy.eye(3) ):
            rotVertices = global_vertices # no rotation after "final_rot"
        else: # rotate coordinates again
            rotVertices = rotateVertices(matrix33, global_vertices)
    else:
        # multiply the two matrices together
        #   and THEN rotate vertices only once
        ipdb.set_trace() # on the TODO-list!
        # ( At least include this, just for educational purposes )

    # Finish by updating global bounding box values for this object:
    curObj.MinMaxGlobal, \
      curObj.dxGlobal, curObj.dyGlobal, curObj.dzGlobal, \
      curObj.BoundingBox_diagGlobal = findBoundingBox(rotVertices)

    # Add global offset for printing values from global XYZ:
    if hasattr(curObj,'xyz_GlobalToLocalSys'):
        # MUST COPY TO "MM" LIKE HERE TO AVOID PASS-BY-REF.!
        MM = {} # defines a dict
        MM['x'] = curObj.MinMaxGlobal['x'][:]
        MM['y'] = curObj.MinMaxGlobal['y'][:]
        MM['z'] = curObj.MinMaxGlobal['z'][:]
        # Very important that MM is ONLY a copy of MinMaxGlobal !!!
        # NB: MM is a reference to MinMax, so they have/share same values:
        curObj.MinMaxGlobalORIGIN = \
          addGlobalOffset(curObj.xyz_GlobalToLocalSys, MM)
    else:
        # ipdb.set_trace()
        raise Exception("INTERNAL ERROR: Contact developer!")

def addMinMaxGlobalPNTtoVertices(vertices, obj):
    # Reference object with MinMaxGlobalORIGIN-data
    # ---------------------------------------------
    if 0: # Leave this option for a while!
        # Get 8 vertices for a new BB:
        BBvertices = make8nodeBox(obj.MinMaxGlobalORIGIN)
        # Find min/max of this 8-node BB:
        MinMaxGlobalORIGIN, dxGlobal, dyGlobal, dzGlobal, \
          BoundingBox_diagGlobal = findBoundingBox(BBvertices)
        MM = MinMaxGlobalORIGIN # THIS IS A NEW/"SAFE" PASS-BY-VALUE COPY
    else:
        MM = obj.MinMaxGlobalORIGIN # THIS IS A PASS-BY-REFERENCE VALUE

    # Get coordinates of bounding box from object MinMaxGlobalORIGIN:
    x1, x2 = MM['x']
    y1, y2 = MM['y']
    z1, z2 = MM['z']
    minPnt = (x1, y1, z1)
    maxPnt = (x2, y2, z2)

    # Add min/max values to vertices
    vertices.append( numpy.asarray( minPnt ) ) # minimum x/y/z
    vertices.append( numpy.asarray( maxPnt ) ) # maximum x/y/z

def update_allBodies_BB( maxNumBodies, \
                         mat33, waveFrontOBJ):
    # Update global BB (it is ALWAYS necessary to do this because
    #   maybe you've rotated previously and later come back un-
    #   rotated - hence this situation requires an update ALWAYS):
    vertices = []

    # ==============================================
    #  Add vertices from all time-dependent objects
    # ==============================================
    countProccessedOBJs = 0
    for key in waveFrontOBJ.matlabKeys:
        countProccessedOBJs = countProccessedOBJs+1 # counter
        # === A Matlab body has numeric key, a fixed does not ===
        b = key-1

        # Always do this, because this body moves/rotates
        updateGlobalBBcurObj(waveFrontOBJ.objs[key], mat33[b])
        addMinMaxGlobalPNTtoVertices(vertices, waveFrontOBJ.objs[key])

    if countProccessedOBJs != len( waveFrontOBJ.matlabKeys ):
        ipdb.set_trace()
        raise Exception("INTERNAL ERROR: Contact developer!")

    # ===========================
    #  Add fixed object vertices
    # ===========================
    for key in waveFrontOBJ.fixedKeys:
        # Update BB for fixed objects to be consistent!
        updateGlobalBBcurObj(waveFrontOBJ.objs[key], numpy.eye(3))

        # ASSUMING THAT obj.MinMaxGlobalORIGIN is ok below!!!:
        addMinMaxGlobalPNTtoVertices(vertices, waveFrontOBJ.objs[key])
        # --- Loop for ALL objs! ---

    # -------------------------------------------------
    # --- SAVE GLOBAL BOUNDING BOX TO WAVEFRONT OBJ ---
    # -------------------------------------------------
    # NB: This is exactly like in objloader.py
    #   (but for a whole wavefront-container)
    waveFrontOBJ.MinMaxGlobal, \
      waveFrontOBJ.dxGlobal, waveFrontOBJ.dyGlobal,\
      waveFrontOBJ.dzGlobal, waveFrontOBJ.BoundingBox_diagGlobal = \
      findBoundingBox(vertices)
    # NB: MinMaxGlobalORIGIN was updated in "updateGlobalBBcurObj(..)"
    # ========================================


def addGlobalOffset(offs, MinMax):
    MM = MinMax # copy to destination
    MM['x'] = [x + offs[0] for x in MM['x']]
    MM['y'] = [y + offs[1] for y in MM['y']]
    MM['z'] = [z + offs[2] for z in MM['z']]
    return MM


def drawBoundingBox(BBsystemGlobal, obj):
    if obj.BBsettings['drawBB']:
        # Save GL_LIGHTING + GL_DEPTH_TEST w/ GL_ENABLE_BIT:
        glPushAttrib(GL_ENABLE_BIT)

        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)

        glPushMatrix()

        # -----------------
        if BBsystemGlobal:
            boxCoords = obj.MinMaxGlobalORIGIN
            if 1 and hasattr(obj,'MinMaxGlobalORIGIN'): # "normal objs"
                MinMaxTXT = obj.MinMaxGlobalORIGIN
            else: # this is for global/wavefront/allBodies BB...
                MinMaxTXT = obj.MinMaxGlobal

        else:
            glTranslate( *obj.xyz_GlobalToLocalSys )
            boxCoords = obj.MinMaxLocal
            if  obj.final_rot[0:3]!=[0.0, 0.0, 0.0]:
                glRotate( obj.final_rot[0], 1, 0, 0)
                glRotate( obj.final_rot[1], 0, 1, 0)
                glRotate( obj.final_rot[2], 0, 0, 1)
            MinMaxTXT = obj.MinMaxLocal
        # -----------------
        drawBox(obj.BBsettings, boxCoords) # only draws the box


        # Draw local coordinate system:
        if hasattr(obj,'BoundingBox_diagLocal'): # not for wavefront BB!!!
            lenSys = 0.5*\
              (obj.BoundingBox_diagLocal + obj.BoundingBox_diagGlobal) # average
        else:
            lenSys = obj.BoundingBox_diagGlobal # for global bounding boxes...
        lenSys = 0.2 * lenSys # always: make smaller than the diagonal...


        # ----- Below: Print coordinates at BB -----
        if obj.BBsettings['XYZcoordinates'] == True:
            # Minimum values of BB-box:
            min_str = engNotation( MinMaxTXT['x'][0] ) + ' ; ' +\
                  engNotation( MinMaxTXT['y'][0] ) + ' ; ' +\
                  engNotation( MinMaxTXT['z'][0] )

            # Maximum values of BB-box:
            max_str = engNotation( MinMaxTXT['x'][1] ) + ' ; ' +\
                  engNotation( MinMaxTXT['y'][1] ) + ' ; ' +\
                  engNotation( MinMaxTXT['z'][1] )

            # you MUST set color BEFORE glRasterPos3f (or calling drawXYZ) !
            glColor3f(*obj.BBsettings['color'])

            # Draw text at min/max locations:
            drawXYZ(boxCoords['x'][0],\
                    boxCoords['y'][0],\
                    boxCoords['z'][0], min_str)
            drawXYZ(boxCoords['x'][1],\
                    boxCoords['y'][1],\
                    boxCoords['z'][1], max_str)
        glPopMatrix()
        # Restore GL_LIGHTING + GL_DEPTH_TEST w/ GL_ENABLE_BIT:
        glPopAttrib() # get GL_ENABLE_BIT
    # end of drawBoundingBox(BBsystemGlobal, obj)...


def printBoundBoxInfo(BBsystemGlobal, objs):
    print "-"*40
    print " "*10 + "Bounding box info: (BBsystemGlobal="\
      + str(BBsystemGlobal) + ")"
    print "-"*40

    for key_Body in objs.keys(): # the key is the body
        if BBsystemGlobal:
            dXdYdZ = objs[key_Body].dxGlobal,\
                        objs[key_Body].dyGlobal,\
                        objs[key_Body].dzGlobal
            MinMax = objs[key_Body].MinMaxGlobal
        else:
            dXdYdZ = objs[key_Body].dxLocal,\
                        objs[key_Body].dyLocal,\
                        objs[key_Body].dzLocal
            MinMax = objs[key_Body].MinMaxLocal

        # This works for both local / global systems:
        print "   *** Body: " + str(key_Body) + " ***"

        print " "*5 + "Min (x/y/z) = " + \
              engNotation(MinMax['x'][0]) + " ; " +\
              engNotation(MinMax['y'][0]) + " ; " +\
              engNotation(MinMax['z'][0]) + " ; "
        print " "*5 + "Max (x/y/z) = " + \
              engNotation(MinMax['x'][1]) + " ; " +\
              engNotation(MinMax['y'][1]) + " ; " +\
              engNotation(MinMax['z'][1]) + " ; "

        print " "*5 + "Diff. (dx/dy/dz) = " + \
              engNotation(dXdYdZ[0]) + " ; " +\
              engNotation(dXdYdZ[1]) + " ; " +\
              engNotation(dXdYdZ[2])

    print "-"*40
    print


def drawXYZ(x,y,z, txtStr):
    glRasterPos3f(x, y, z)
    for s in txtStr: # GLUT_BITMAP_8_BY_13
        #print "(xpos/ypos/s) = ", xpos, ypos, ord(s)
        glutBitmapCharacter(GLUT_BITMAP_8_BY_13, ord(s) )
        # ord(s) returns ASCII/integer code for character s, e.g. "Z"=90


def GetGlobalXYZ(angles, localVector, globalOffset = (0,0,0), deg=True):
    if len(angles) != 3:
        print "ERROR! Input v MUST be a 3-tuple (x/y/z-rotation)!"
        exit(1)
    if len(localVector) != 3:
        print "ERROR! Input localVector MUST be a 3-tuple (x/y/z-offset)!"
        exit(1)
    Amatrix = rotXYZ(angles, deg)
    v = numpy.transpose( numpy.asarray(localVector) ) # transpose!
    globalVect = multAwithVec(Amatrix, v)
    retVal = globalOffset + globalVect # for debugging
    return retVal


def transpose(mat):
    return numpy.transpose( mat )


def expand33to44(matrix33):
    matrix43 = numpy.vstack([matrix33, [0,0,0]]) # add row (3 zeros)
    matrix44 = numpy.column_stack([matrix43, [0,0,0,1]]) # add column
    return matrix44


def rotateVertices(Amatrix, vertices):
    if 1:
        sz = len(vertices) # get the size of the vertices-list (number of rows)
        rotated_vertices = [[0.0, 0.0, 0.0]] * sz
    else:
        sz = numpy.shape(vertices) # get the size (shape) as (rows, cols)
        rotated_vertices = numpy.zeros(sz) # initialize using same size
    # print rotated_vertices

    for i in range(len(vertices)):
        old_V = vertices[i]
        new_V = multAwithVec(Amatrix, old_V)
        rotated_vertices[i] = list( new_V ) # convert to list
    # print rotated_vertices
    # ipdb.set_trace()
    return ( rotated_vertices )


def multAwithVec(Amatrix, vector):
    return numpy.dot(Amatrix, vector)


def rotXYZ(angles, deg=True): # v is a 3-tuple!
    # --- Inspiration: See Matlab file: Nordtank/rotateAroundAxis.m
    # Debug: Type "rotXYZ((45,0,0))", etc...
    if len(angles) != 3:
        print "ERROR! Input v MUST be a 3-tuple!"
        exit(1)
    else:
        if deg == True: # convert, degrees to radians
            v = math.radians(angles[0]),\
                math.radians(angles[1]),\
                math.radians(angles[2]),
        else:
            v = angles # keep in radians

    # The following have the angle in radians as argument:
    sx = math.sin(v[0])
    sy = math.sin(v[1])
    sz = math.sin(v[2])
    cx = math.cos(v[0])
    cy = math.cos(v[1])
    cz = math.cos(v[2])

    Dx = numpy.array([[1, 0, 0],[0, cx, -sx],[0, sx, cx]])
    Cy = numpy.array([[cy, 0, sy],[0, 1, 0],[-sy, 0, cy]])
    Bz = numpy.array([[cz, -sz, 0],[sz, cz, 0],[0, 0, 1]])

    #  Rotate: A = Dx * Cy * Bz
    tmp = numpy.dot(Cy, Bz) # matrix multiplication...
    Amatrix = numpy.dot(Dx, tmp)
    #  First local sys = global sys. Rotate around global X. Then
    #    rotate around local Y. Finally around local Z. Pre-multiply
    #    with a matrix to rotate in global system and post-multiply
    #    to rotate around axes in local system...
    return Amatrix


def printQuad( beginPos, endPos ):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix() # push projection matrix

    glLoadIdentity()
    # glOrtho: (left/right/bottom/top/nearVal/farVal)
    glOrtho(0.0, 1.0, 0.0, 1.0, -1.0, 1.0)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix() # push modelview matrix
    glLoadIdentity()

    #--------------
    glPushAttrib(GL_ENABLE_BIT) # save GL_LIGHTING and many more...

    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    #--------------
    glColor3f(*HUDtextColorRGB)

    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    glBegin(GL_QUADS)
    glVertex2f( beginPos[0], beginPos[1] ) # x1,y1
    glVertex2f( endPos[0], beginPos[1] )   # x2,y1
    glVertex2f( endPos[0], endPos[1] )     # x2,y2
    glVertex2f( beginPos[0], endPos[1] )   # x1,y2
    glEnd()

    #--------------
    # restore GL_ENABLE_BIT => GL_LIGHTING and many more...
    glPopAttrib()
    #--------------

    glMatrixMode(GL_MODELVIEW)
    glPopMatrix() # <--------------------------- POP MODELVIEW MATRIX

    glMatrixMode(GL_PROJECTION)
    glPopMatrix() # <--------------------------- POP PROJECTION MATRIX

    glMatrixMode(GL_MODELVIEW)



def printText(xpos, ypos, charWritten):

    glMatrixMode(GL_PROJECTION)
    glPushMatrix() # push projection matrix

    glLoadIdentity()
    # glOrtho: (left/right/bottom/top/nearVal/farVal)
    glOrtho(0.0, 1.0, 0.0, 1.0, -1.0, 1.0)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix() # push modelview matrix
    glLoadIdentity()

    #--------------
    glPushAttrib(GL_ENABLE_BIT) # save GL_LIGHTING and many more...

    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    #--------------
    glColor3f(*HUDtextColorRGB)

    glRasterPos2f(xpos,ypos)
    for s in charWritten: # GLUT_BITMAP_8_BY_13
        #print "(xpos/ypos/s) = ", xpos, ypos, ord(s)
        glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(s) )
    #--------------
    # restore GL_ENABLE_BIT => GL_LIGHTING and many more...
    glPopAttrib()
    #--------------

    glMatrixMode(GL_MODELVIEW)
    glPopMatrix() # <--------------------------- POP MODELVIEW MATRIX

    glMatrixMode(GL_PROJECTION)
    glPopMatrix() # <--------------------------- POP PROJECTION MATRIX

    glMatrixMode(GL_MODELVIEW)



def drawOBJnow( obj, polyMode):
    """ Draw object using display-list + draw BB """
    # -------------------------------------
    #   DRAW OBJECT (USING DISPLAY LIST):
    # -------------------------------------
    if polyMode == True:
        glPolygonMode( GL_FRONT_AND_BACK, GL_LINE )
        glCallList(obj.gl_list) # draw body
        glPolygonMode( GL_FRONT_AND_BACK, GL_FILL )
    else:
        glCallList(obj.gl_list) # draw body



#---------------------------------------------------------------------
# BELOW THIS POINT IS EXPERIMENTALLY WORK...
# BELOW THIS POINT IS EXPERIMENTALLY WORK...
# BELOW THIS POINT IS EXPERIMENTALLY WORK...
#---------------------------------------------------------------------
def MatrixToEulerParam(A33): # THIS COULD BE HANDY SOMEWHERE
    # Using Nikravesh (6.25 - 6.26c), p.161/162
    a11 = A33[0,0]
    a22 = A33[1,1]
    a33 = A33[2,2]

    e0sq = ( numpy.trace(A33)+1 )/4 # 6.25
    e1sq = ( 1+2*a11-numpy.trace(A33) )/4 # 6.26a
    e2sq = ( 1+2*a22-numpy.trace(A33) )/4 # 6.26b
    e3sq = ( 1+2*a33-numpy.trace(A33) )/4 # 6.26c

    EulerParamTest = [\
        math.sqrt(e0sq) , math.sqrt(e1sq) ,\
        math.sqrt(e2sq) , math.sqrt(e3sq)]

    e0 = math.sqrt(e0sq)
    if e0==0: # use eq. 6.28, p.162
        ipdb.set_trace() # e2+e3 not defined yet!
        e1 = (A33(2,1)+A33(1,2))/(4*e2)
        e2 = (A33(3,1)+A33(1,3))/(4*e1)
        e3 = (A33(3,2)+A33(2,3))/(4*e3)
    else: # use eq. 6.27, p.162
        e1 = (A33(3,2)-A33(2,3))/(4*e0)
        e2 = (A33(1,3)-A33(3,1))/(4*e0)
        e3 = (A33(2,1)-A33(1,2))/(4*e0)

    EulerParam = [e0 , e1 , e2, e3]
    EulerParamSQ = sum(EulerParam**2)
    if abs(EulerParamSQ-1)>1e-3:
        raise Exception("Tolerance exceeded!")

    return EulerParam # end # THIS COULD BE HANDY SOMEWHERE


def EulerParamToMatrix(p4): # this is typically in a "transform.m"-file

    l = len(p4)
    if not l==4:
        raise Exception("Wrong input length!")
    else:
        e0 = p4(1)
        e1 = p4(2)
        e2 = p4(3)
        e3 = p4(4)

        const0 = p4.T*p4-1 # 6.23

        e = [e1, e2, e3].T
        const1 = e0^2 + e(1)^2 + e(2)^2 + e(3)^2

        tmp = [const0, const1]

    if 1:
        # eq. 6.18, p.159
        A = (2*e0^2-1)*numpy.eye(3) + \
            2*(e*e.T + e0*skewmat(e))
    else:
        # eq. 6.19, p.160
        A = 2* [
            e0^2+e1^2-1/2, e1*e2-e0*e3, e1*e3+e0*e2,
            e1*e2+e0*e3, e0^2+e2^2-1/2, e2*e3-e0*e1,
            e1*e3-e0*e2, e2*e3+e0*e1, e0^2+e3^2-1/2 ]
    return A # end


def skewmat(vec): # required by EulerParamToMatrix !
    mat = [  0,    -vec(3),  vec(2),
         vec(3),   0,     -vec(1),
        -vec(2),  vec(1),    0 ]
    return mat


def quatToMatrix33(p):
    qw = p[0]
    qx = p[1]
    qy = p[2]
    qz = p[3]
    n = 1.0 / math.sqrt(qx*qx+qy*qy+qz*qz+qw*qw)
    # Maybe maximize your screen to see this matrix with no linebreaking:
    #Amatrix33 = numpy.array([[1,2,3],[4,5,6],[7,8,9]])
    Amatrix33 = numpy.array([\
        [1.0 - 2.0*qy*qy - 2.0*qz*qz, 2.0*qx*qy - 2.0*qz*qw      , 2.0*qx*qz + 2.0*qy*qw ],
        [2.0*qx*qy + 2.0*qz*qw      , 1.0 - 2.0*qx*qx - 2.0*qz*qz, 2.0*qy*qz - 2.0*qx*qw],
        [2.0*qx*qz - 2.0*qy*qw      , 2.0*qy*qz + 2.0*qx*qw      , 1.0 - 2.0*qx*qx - 2.0*qy*qy]])
    return Amatrix33


def quatToMatrix44(p):
    Amatrix33 = quatToMatrix33(p)
    Amatrix44 = expand33to44(Amatrix33)
    return Amatrix44


# def randomQuaternion()

# p = zeros(4,1); # make a column vector
# sum = 0;

# # w-component in computer graphics language
# p(1) = rand(1)*2 - 1;
# sum = sum + p(1)^2;

# # x-component in computer graphics language
# p(2) = sqrt(1-sum) * (rand(1)*2 - 1);
# sum = sum + p(2)^2;

# # y-component in computer graphics language
# p(3) = sqrt(1-sum) * (rand(1)*2 - 1);
# sum = sum + p(3)^2;

# # z-component in computer graphics language

# if rand(1) < 0.5
#     p(4) = sqrt(1-sum) * (-1);
# else
#     p(4) = sqrt(1-sum);
# end

# return p # end




# ------------------
if __name__ == "__main__":
    print "Testing..."
    angles = (180, -112, 22) # in degrees
    localVector = (10, 20, -10) # vector in local XYZ-system
    globalXYZoffset = GetGlobalXYZ(angles, localVector, deg=True)
    # print angles
    # print localVector
    print globalXYZoffset
    # -----
    # print "Where:"
    # A = rotXYZ(angles)
    # print A
    # print "Bye..."
