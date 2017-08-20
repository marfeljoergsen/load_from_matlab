import OpenGL.GL as GL # avoid putting all in top namespace (too confusing) !
from sys import exit, stdout, exc_info, argv
from string import find
from gl_utils import *
import ipdb # ipdb.set_trace() # debugger makes a breakpoint here...
import pygame


class loadOBJfromFile:

    def __init__(self, OBJfilename, global_offs, rot, local_offs, \
                 final_rot, logger=None, scaling=1):

        """Loads a Wavefront OBJ file. """
        # --------------------------------
        # Settings from *.TXT file:
        self.OBJfname = OBJfilename # for debugging purposes
        self.global_offs = global_offs
        self.rot = rot
        self.local_offs = local_offs
        self.final_rot = final_rot
        self.scaleFactor = scaling
        self.final_rot_mat = rotXYZ( [0, 0, 0] ) # overwrite later

        # Required for *.OBJ file format:
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        self.errorLoadingMTLfile = False
        self.offsetMethod = '' # empty string

        # Other parameters
        self.isMatlabBody = False # default
        self.bodyCoordSysBBcenter = False # default


        # ----- Bounding box settings -----
        self.BBsettings = {} # create a dict

        # self.BBsettings['drawBB'] = True # default
        self.BBsettings['drawBB'] = False

        self.BBsettings['cullFaceEnabled'] = False # default
        # self.BBsettings['cullFaceEnabled'] = True

        # self.BBsettings['color'] = (0.4, 0.6, 0.0) # green
        self.BBsettings['color'] = (0.8, 0.8, 0.8)
        # self.BBsettings['color'] = (0.8, 0.8, 0.1) # yellow

        self.BBsettings['XYZcoordinates'] = False # default
        # self.BBsettings['XYZcoordinates'] = True # confusing


        # -- Bounding box values: --
        self.MinMaxLocal = {} # define a dict...
        self.dxLocal = []
        self.dyLocal = []
        self.dzLocal = []
        self.BoundingBox_diagLocal = []

        self.MinMaxGlobal = {} # define a dict...
        self.MinMaxGlobalORIGIN = {} # define a dict...
        self.dxGlobal = []
        self.dyGlobal = []
        self.dzGlobal = []
        self.BoundingBox_diagGlobal = []


        # -----------------------------------
        # YOU CAN NOT HAVE FILE-LOGGERS, IF YOU WRITE A PICKLE-FILE!
        setupLogger( self, logger=logger )
        self.load_OBJ_and_MTL() # load from *.obj and *.mtl files...


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


    def BBswitch(self):
        self.BBsettings['drawBB'] = not self.BBsettings['drawBB']


    def changeVerticesNow(self): # SCALING + FINAL ROTATION...
        self.rescaleVertices()   # scale with: self.scaleFactor

        #  --> Convert to a LIST (sometimes numpy is unknown/out of scope!)
        # (return numpy-array), Calculate the whole offset: {r}+[A]{s'}:
        # def GetGlobalXYZ(angles, localVector, globalOffset = (0,0,0),...)
        self.xyz_GlobalToLocalSys = list( GetGlobalXYZ(self.rot, \
                                                       self.local_offs, \
                                                       self.global_offs) )

        # =================================================
        # --- Update local bounding box ---
        self.MinMaxLocal, \
          self.dxLocal, self.dyLocal, self.dzLocal, \
          self.BoundingBox_diagLocal = findBoundingBox(self.vertices)

        if self.bodyCoordSysBBcenter:

            # Find middle of bounding box:
            minCoord = \
              self.MinMaxLocal['x'][0], \
              self.MinMaxLocal['y'][0], \
              self.MinMaxLocal['z'][0]
            dHalf = self.dxLocal/2, self.dyLocal/2, self.dzLocal/2
            offset = [-(minC+dH) \
                for minC, dH in zip( minCoord, dHalf)]

            self.translVertices( offset )

            # --- Update local bounding box AGAIN! ---
            self.MinMaxLocal, \
              self.dxLocal, self.dyLocal, self.dzLocal, \
              self.BoundingBox_diagLocal = findBoundingBox(self.vertices)


        # Apply final_rot (= move orientation of local coord.sys)
        self.rotateVerticesAndNormals(self.final_rot)

        # --- Update global bounding box, (using inital final_rot!) ---
        updateGlobalBBcurObj(self, numpy.eye(3)) # eye = no rotation!
        # =================================================


    # below two are for pickle...
    def __getstate__(self): # when saving, pickle will go here
        old_dict = self.__dict__.copy() # copy the dict since we change it
        del old_dict['ch']              # remove filehandle entry
        del old_dict['fh']              # remove filehandle entry
        del old_dict['consoleHandler']
        del old_dict['fileHandler']
        del old_dict['cleanUpLoggingHandlers']
        old_dict['logger'] = None
        return old_dict


    def __setstate__(self, dict): # when loading, pickle goes here
        # dict is the loaded dictionary (from the pickle file), self is the current object...
        # see http://stackoverflow.com/questions/3375443/cant-pickle-loggers
        # http://stackoverflow.com/questions/2999638/how-to-stop-attributes-from-being-pickled-in-python
        setupLogger(self) # make "None"-logger. If you want something else, run [...].setupLogger( ) afterwards
        self.__dict__.update(dict) # update self using dict


    # ----------------------
    def rescaleVertices(self):
        if self.scaleFactor != 1.0: # only rescale, if necessary
            for i in range(len(self.vertices)):
                old_V = self.vertices[i]
                new_V = [v * self.scaleFactor for v in old_V] # list comprehension
                self.vertices[i] = new_V # save rescaled vertices

    def translVertices(self, xyzGlobal):
        if xyzGlobal[0:3]!=[0.0, 0.0, 0.0]: # only rotate if necessary
            # NB: Length of vertices and normals (=face) is likely different
            for i in range(len(self.vertices)):
                old_V = self.vertices[i]
                new_V = [a+b for a,b in zip(old_V, xyzGlobal)]
                self.vertices[i] = list( new_V )
            # Normals are the same as before translation...

    def rotateVerticesAndNormals(self, rotVector):
        if rotVector[0:3]!=[0.0, 0.0, 0.0]: # only rotate if necessary
            rotMatrix = rotXYZ( rotVector )

            # NB: Length of vertices and normals (=face) is likely different
            self.vertices = rotateVertices(rotMatrix, self.vertices)
            self.normals = rotateVertices(rotMatrix, self.normals)
    # ----------------------


    def load_OBJ_and_MTL(self):
        material = None
        try:
            if len( self.logger.handlers ) > 0:
                self.logger.info('==================================')
                self.logger.info('Opening: ' + self.OBJfname)
                self.logger.info('==================================')
            f = open(self.OBJfname, "r")
            for line in f:
                if line.startswith('#'): continue
                values = line.split()
                if not values: continue
                if values[0] == 'v':
                    v = map(float, values[1:4])
                    self.vertices.append( v )
                elif values[0] == 'vn':
                    v = map(float, values[1:4])
                    self.normals.append( v )
                elif values[0] == 'vt':
                    texCrds = map(float, values[1:3])
                    self.texcoords.append( texCrds )
                elif values[0] in ('usemtl', 'usemat'):
                    material = values[1] # will be appended to self.faces below...
                elif values[0] == 'mtllib': # load material from input file...
                    try: # loadMTLfromFile(file)
                        self.MTL_filename = values[1]
                        self.loadMTLfromFile()
                    except:
                        #print "Exception: ", exc_info()
                        if len( self.logger.handlers ) > 0:
                            self.logger.warn("Could not load (" + values[1] +\
                                  ") from MTL-file: Skipping materials...")
                        self.errorLoadingMTLfile = True
                elif values[0] == 'f':
                    face = [] # will be appended below
                    texcoords = [] # will be appended below
                    norms = [] # will be appended below
                    for v in values[1:]:
                        w = v.split('/')
                        face.append(int(w[0]))
                        if len(w) >= 2 and len(w[1]) > 0:
                            texcoords.append(int(w[1]))
                        else:
                            texcoords.append(0)
                        if len(w) >= 3 and len(w[2]) > 0:
                            norms.append(int(w[2]))
                        else:
                            norms.append(0)
                    self.faces.append((face, norms, texcoords, material))
                elif values[0] == 'o':
                    if len( self.logger.handlers ) > 0:
                        self.logger.debug(" Object name found (but not used): " +\
                                     str( values[1:] ))
                elif values[0] == 'g':
                    if len( self.logger.handlers ) > 0:
                        self.logger.debug(" Group name found (but not used): " +\
                                     str( values[1:] ))
                elif values[0] == 's':
                    if len( self.logger.handlers ) > 0:
                        self.logger.debug(" Smooth shading found (but not used): " +\
                                     str( values[1:] ))
                else:
                    if len( self.logger.handlers ) > 0:
                        self.logger.debug("*** Ignoring: " + str( values ))

            f.close()
            if len( self.logger.handlers ) > 0:
                self.logger.info('Closing: ' + self.OBJfname)

        except Exception, err:
            print " ERROR OPENING FILE (from objloader.py): ", self.OBJfname
            self.logger.critical(" ERROR OPENING FILE (from objloader.py): ",\
                            self.OBJfname)
            self.logger.critical(" --> " + str( err ))

            exc_type, exc_obj, exc_tb = exc_info()
            print " --> EXCEPTION --> " + str([exc_type, exc_obj, exc_tb])
            fname = exc_tb.tb_frame.f_code.co_filename
            print
            print " From: " + fname +\
                  ", line:",  exc_tb.tb_lineno
            excDetails = traceback.extract_tb(exc_tb)
            print excDetails[:]
            #print " --> File: " + excDetails[1][0] + \
            #      ", line: " + repr( excDetails[1][1] )
            #print "    --> Function: " + excDetails[1][2]
            #print "        Containing: " + excDetails[1][3]

            # ipdb.set_trace()
            # exit(1)




    def loadMTLfromFile(self):
       contents = {}
       mtl = None
       self.logger.debug(" Opening (loadMTLfromFile): " + self.MTL_filename)
       f = open(self.MTL_filename, "r")
       for line in f:
           if line.startswith('#'): continue
           values = line.split()
           if not values: continue
           # if values[0] == 'newmtl' or values[0] == '\xef\xbb\xbfnewmtl':
           # UTF8-encoding is used in the latter case...
           if find( values[0], 'newmtl') >= 0: # also handles UTF8-encoding
               self.logger.debug("   ===> newmtl = " + str(values[1]))
               mtl = contents[values[1]] = {}
           elif mtl is None:
               errMsg = "mtl file doesn't start with newmtl stmt"
               self.logger.critical(errMsg)
               raise ValueError, errMsg
           elif values[0] == 'map_Kd':
               # load the texture referred to by this declaration
               self.logger.debug(" ===> Loading texture:" + str(values[1]))
               mtl[values[0]] = values[1]
               try:
                   surf = pygame.image.load(mtl['map_Kd'])
                   image = pygame.image.tostring(surf, 'RGBA', 1)
                   ix, iy = surf.get_rect().size
                   texid = mtl['texture_Kd'] = glGenTextures(1)
                   glBindTexture(GL_TEXTURE_2D, texid)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                                   GL_LINEAR)
                   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER,
                                   GL_LINEAR)
                   glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA,
                                GL_UNSIGNED_BYTE, image)
               except Exception, err:
                   print exc_info()
                   self.logger.debug(" --> " + str(err))
           else:
               mtl[values[0]] = map(float, values[1:])
       f.close()
       self.logger.debug(" Closing (loadMTLfromFile): " + self.MTL_filename)
       self.mtl = contents


    def logDataOut(self):
            # Print data to screen/file:
            self.logger.info('==================================')
            self.logger.info('          GENERAL DATA:')
            self.logger.info('==================================')
            self.logger.info('From OBJ-file:')
            self.logger.info("  Number of vertices:" + str(len( self.vertices )))
            self.logger.info("  --> Local Bounding Box:")
            self.logger.info("      [-x, +x] = [" + str(self.MinMaxLocal['x'][0]) +\
                  ", " + str(self.MinMaxLocal['x'][1]) + "]")
            self.logger.info("      [-y, +y] = [" + str(self.MinMaxLocal['y'][0]) +\
                  ", " + str(self.MinMaxLocal['y'][1]) + "]")
            self.logger.info("      [-z, +z] = [" + str(self.MinMaxLocal['z'][0]) +\
                  ", " + str(self.MinMaxLocal['z'][1]) + "]")
            self.logger.info("      |Bounding Box diagonal (local)| = " + \
                        str(self.BoundingBox_diagLocal))

            # print
            self.logger.info("  Number of faces:" + str(len( self.faces )))
            self.logger.info("  Number of normals:" + str(len( self.normals )))
            self.logger.info("  Number of texture coords:" + \
                        str(len( self.texcoords )))

            if not self.errorLoadingMTLfile and hasattr(self,'mtl'):
                self.logger.info("From MTL-file:")
                self.logger.info("  --> Number of materials:" + str(len( self.mtl )))
                self.logger.info("  --> Materials / self.mtl.keys() = " +\
                            str(self.mtl.keys()) )
            else:
                self.logger.info("  --> No materials defined... Using default...")
            self.logger.debug("====================================================")
        # ---------- DONE READING FROM OBJ AND MTL FILES ----------



    def makeDisplayList(self):
        #     Now, generate display list and draw the geometry
        # ---------------------------------------------------------

        # Use python logger class, if handlers are used:
        #  (this avoids the first time-message: "No handlers
        #  could be found for logger "getWavefrontOBJs.getOBJs")
        useLogging = False # default
        if self.logger is not None:
            if len( self.logger.handlers ) > 0:
                useLogging = True
        if 1:
            showDefFaceWarning = False
        else:
            showDefFaceWarning = True
        if useLogging:
            self.logger.debug("Generating display list...")

        finishingLineBreak = False # default
        self.gl_list = GL.glGenLists(1)
        GL.glNewList(self.gl_list, GL.GL_COMPILE)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glFrontFace(GL.GL_CCW)
        faceNum = 0
        printMaxfaceNumbers = 15
        oldMat = None
        for face in self.faces:
            vertices, normals, texture_coords, material = face
            faceNum += 1 # increment
            mtl = None # reset

            if material is not None and not self.errorLoadingMTLfile:
                try:
                    if oldMat is None or material != oldMat:
                        if useLogging:
                            self.logger.debug(\
                                "  ==> Trying to use: mtl = self.mtl[" \
                                + material + "]") # don't print always...
                        oldMat = material # don't come here until new material
                    mtl = self.mtl[material]
                except:
                    if useLogging:
                        self.logger.warn("Face:" + str(faceNum))
                        self.logger.warn(" --> Failed using material:" +\
                            str(material))
                        self.logger.warn(" --> Check if your OBJ-file has "\
                            "the \"mtllib (filename)\" in it")
                        self.logger.warn(" --> Using default material...")
                    else:
                        print "Something is wrong..."
                        ipdb.set_trace()

            if mtl is None:
                if faceNum == 1:
                    if showDefFaceWarning:
                        finishingLineBreak = True
                        print "WARNING: List of faces that must use"\
                              "default material (material not defined):"
                        stdout.write(str( faceNum )) # face number 1
                        stdout.flush() # print to screen
                elif faceNum < printMaxfaceNumbers:
                    if showDefFaceWarning:
                        finishingLineBreak = True
                        stdout.write(", " + str( faceNum ))
                        stdout.flush() # print to screen
                elif faceNum == printMaxfaceNumbers:
                    if showDefFaceWarning:
                        finishingLineBreak = True
                        stdout.write(" and a lot more...")
                        stdout.flush() # print to screen
                        # print # consider this extra line
                # --- Default material below: ---
                # newmtl default
                # Ka 0.4000 0.4000 0.4000
                # Kd 0.8000 0.8000 0.8000
                # Ks 0.3000 0.3000 0.3000
                # illum 2
                # d 0.5000
                # Ns 60.0000
                lines = {}
                lines[0] = "Ka 0.5 0.5 0.5" # ambient color
                lines[1] = "Kd 0.5 0.5 0.5" # diffuse color
                lines[2] = "Ks 0.4 0.3 0.4" # specular color
                lines[3] = "illum 2" # illumination type/mode
                            #(0=constant, 1=diffuse, 2=diffuse+specular, ...)
                lines[4] = "d 0.45" # alpha/transparancy (also called Tr!)
                lines[5] = "Ns 60.0" # specular exponent (i.e. the shininess).
                #--- Experimental:
                # lines[6] = "r ??" # reflection
                # lines[7] = "sharpness ??" # glossy
                # lines[8] = "Ni ??" # refract index
                # lines[9] = "map_Kd filename" # texture map
                # lines[10] = "map_Ka filename" # texture map
                # lines[11] = "Ke ?" # emission
                # lines[12] = "Tf ?" # transmission filter
                #--- Experimental:
                mtl = {}
                for line in lines:
                    values = lines[line].split()
                    mtl[values[0]] = map(float, values[1:])

            if 'texture_Kd' in mtl:
                # use diffuse texmap
                glBindTexture(GL_TEXTURE_2D, mtl['texture_Kd'])
            else:
                # ---------------------------------------------
                # --- Illumination models: Not implemented: ---
                # 0. Color on and Ambient off
                # 1. Color on and Ambient on
                # 2. Highlight on
                # 3. Reflection on and Ray trace on
                # 4. Transparency: Glass on, Reflection: Ray trace on
                # 5. Reflection: Fresnel on and Ray trace on
                # 6. Transparency: Refraction on, Reflection:
                #       Fresnel off and Ray trace on
                # 7. Transparency: Refraction on, Reflection:
                #       Fresnel on and Ray trace on
                # 8. Reflection on and Ray trace off
                # 9. Transparency: Glass on, Reflection: Ray trace off
                # 10. Casts shadows onto invisible surfaces
                # ---------------------------------------------

                # Use diffuse color + alpha (transparancy)
                try:
                    var = mtl['Kd'] + mtl['d'] # concatenate
                    GL.glColor4f(*var)
                except KeyError: # alpha not read into 'd'-key...
                    try: # sometimes "Tr" is used instead of "d":
                        var = mtl['Kd'] + mtl['Tr'] # concatenate
                        GL.glColor4f(*var)
                    except KeyError: # alpha not read into 'd'-key...
                        GL.glColor(*mtl['Kd']) # (*): unpacking into 3 arguments...

            GL.glBegin(GL.GL_POLYGON)
            for i in range(len(vertices)):
                if normals[i] > 0:
                    glNormal3fv(self.normals[normals[i] - 1])
                if texture_coords[i] > 0:
                    glTexCoord2fv(self.texcoords[texture_coords[i] - 1])
                GL.glVertex3fv(self.vertices[vertices[i] - 1])
            GL.glEnd()

        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEndList()
        if finishingLineBreak == True:
            print " "
        if useLogging:
            self.logger.debug(\
                "  ==> DONE reading and creating display list ==--")
            self.logger.debug(' ')


# ----------------------------------

if __name__ == "__main__":


    try:
        fname = argv[1]
    except:
        print "You need to supply either a *.obj or a "\
          "*.txt file as input argument..."
        exit(1)

    global_offs = (0, 0, 0)
    rot = (0, 0, 0)
    local_offs = (0, 0, 0)
    final_rot = (0, 0, 0)

    testMain = loadOBJfromFile(fname, global_offs,\
        rot, local_offs, final_rot,\
        logger=None, scaling=1)

    print "Done testing..."



