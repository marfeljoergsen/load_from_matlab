import objloader
from sys import exit, exc_info
import gl_utils
import ipdb # ipdb.set_trace() # copy to line and debugger makes a breakpoint...
import traceback
from os.path import isfile
from pygame import display
try:
  import cPickle as pickle
except:
  import pickle
from ast import literal_eval # converts string to boolean

# import pprint
# -----------------------
# use M-x pdb in emacs
# -----------------------
#usePickle = True
usePickle = False

class getOBJs:
    def __init__(self, filename = None):
        # NB: These are member variables for the getWavefront-obj
        #  (look into objloader.py for individual obj-variables)
        # =======================================================
        self.fname = filename # of text file (not OBJ-file)
        self.objs = {} # use a dict so it's easy to lookup in...

        self.filenames = {} # use a dict so it's easy to lookup in...
        self.bodies = 0 # number of bodies loaded currently...


        # ----- Bounding box settings (as in objloader.py) -----
        self.BBsettings = {} # create a dict
        # self.BBsettings['drawBB'] = True # default
        self.BBsettings['drawBB'] = False

        self.BBsettings['cullFaceEnabled'] = False # default
        # self.BBsettings['cullFaceEnabled'] = True

        # self.BBsettings['color'] = (0.4, 0.6, 0.0) # green
        # self.BBsettings['color'] = (0.8, 0.8, 0.8)
        self.BBsettings['color'] = (0.8, 0.8, 0.1) # yellow

        self.BBsettings['XYZcoordinates'] = True
        # self.BBsettings['XYZcoordinates'] = False
        # ----- Bounding box settings (as in objloader.py) -----

        # ----- Global bounding box stuff (as in objloader.py) -----
        self.MinMaxGlobal = {} # define a dict
        self.dxGlobal = []
        self.dyGlobal = []
        self.dzGlobal = []
        self.BoundingBox_diagGlobal = []

        # --------- Logging stuff ---------
        self.consoleHandler = False
        # self.consoleHandler = True
        # self.fileHandler = True
        self.fileHandler = False
        self.ch, self.fh, self.logger = \
            gl_utils.makeLogger('getWavefrontOBJs.getOBJs', \
            self.consoleHandler, self.fileHandler)


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


    # def __dict__(self):
    #     print "Calling: __dict__(self), showing self.objs.keys():"
    #     print self.objs.keys() # can this be fixed???


    def createPickle(self, pickleFile, keyBody, curObjFileName, \
            global_offs, rot, local_offs, final_rot,  scaleFCT):
        # Load OBJ file:
        self.objs[ keyBody ] = objloader.loadOBJfromFile( \
            curObjFileName, global_offs, rot, \
            local_offs, final_rot, scaling=scaleFCT)
        # Dump pickle file:
        if usePickle:
            print "Pickle-file will be created: " + pickleFile
            pickle.dump( self.objs[ keyBody ],
                open( self.pickleFile, "wb" ), pickle.HIGHEST_PROTOCOL )


    def loadOrSaveOBJfile(self, curObjFileName, keyBody):
        # -------------------------------------------------------
        # test if body already exist (does keyBody have a filename?) ?
        testExisting = self.filenames.get( keyBody )
        if testExisting != None:
            print "ERROR: Body number: " + str(keyBody) + \
                  ", has already been added (skipping this) !!!"
            print "you should change this in the future so only 1"
            print "  matlab-body is allowed, however, if it is a"
            print "  fixed obj, then you can continue below..."
            print str(  self.objs[ keyBody ].isMatlabBody )
            ipdb.set_trace() # you're not supposed to arrive here, now.
            return

        self.bodies += 1 # add 1 more body now...
        self.filenames[ keyBody ] = curObjFileName
        # -------------------------------------------------------
        if curObjFileName.strip().lower()[-4:]=='.obj':
            self.pickleFile = curObjFileName[:-4] + ".pickle"

            # ----------------------------------------------------
            if isfile( self.pickleFile ):
                print "Loading existing pickle-file: " + self.pickleFile
                self.objs[ keyBody ] = \
                  pickle.load( open( self.pickleFile, "rb" ) )

                # You have to have a new logger for this loaded pickle-file!:
                if self.logger is None:
                    print "Warning: You need a logger here (you can however"\
                      + " continue from this point, with no problems!!!)"
                    ipdb.set_trace()
                gl_utils.setupLogger( self.objs[ keyBody ], self.logger )

            else:
                self.createPickle(self.pickleFile, keyBody, curObjFileName, \
                    [None, None, None], [None, None, None], \
                    [None, None, None], [None, None, None],  None)
        # ----------------------------------------------------
        else:
            print "Don't know what to do with file: ",\
              curObjFileName.lower()[-4:]
            ipdb.set_trace()
            raise Exception("ERROR: invalid input...")
        # -------------------------------------------------------



    def modifyOBJ( self, obj, scaleFCT, offsetMethod, useBBcenter, \
                   global_offs, rot, local_offs, final_rot, isMatlabBody, \
                   drawBB, XYZcoordinates, lenCS ):

        # ----------------------
        # GEOMETRICAL FLAGS/SETTING:
        # ----------------------
        # Overwrite pickle/loaded file with this
        #   specific scaling/offset/orientation:
        obj.scaleFactor = scaleFCT

        # Multiply all offsets by scaleFCT:
        obj.global_offs =\
        [v * scaleFCT for v in global_offs]
        obj.rot = rot
        obj.local_offs =\
        [v * scaleFCT for v in local_offs]
        obj.final_rot = final_rot

        # Store final-rot-matrix, because it's fixed:
        obj.final_rot_mat = gl_utils.rotXYZ( obj.final_rot )

        # ----------------------
        # GENERAL FLAGS/SETTING:
        # ----------------------
        obj.isMatlabBody = isMatlabBody
        obj.BBsettings['drawBB'] = drawBB
        obj.BBsettings['XYZcoordinates'] = XYZcoordinates
        obj.offsetMethod = offsetMethod
        obj.bodyCoordSysBBcenter = useBBcenter
        obj.lenCS = lenCS

        # ---------------------------------
        obj.changeVerticesNow()

        # Use python logger class, if handlers are used:
        #  (this avoids the first time-message: "No handlers
        #  could be found for logger "getWavefrontOBJs.getOBJs")
        if len( obj.logger.handlers ) > 0:
            obj.logDataOut()
        #--------------


    def load(self, fname = None):
        print "===== getWavefrontOBJs.py / getOBJs ====="

        if fname != None:
            self.fname = fname
        if self.fname == None:
            print "Warning: No input file-name given..."
            # exit(1)
            return
        print "Reading fname:", self.fname
        print " "
        try:
            # --- Default values for both .obj and .txt files: ---
            scaleFCT = 1.0
            useBBcenter = False # self.bodyCoordSysBBcenter
            drawBB = False
            XYZcoordinates = False
            lenCS = None

            if self.fname[-4:] == '.obj':
                keyBody = 0

                # Only 1 body is loaded, so put in global system:
                global_offs = 0,0,0
                rot = 0,0,0
                local_offs = 0,0,0
                final_rot = 0,0,0

                # Default when loading *.obj-files:
                isMatlabBody = False # = fixed body
                offsetMethod = 'fixed'

                self.loadOrSaveOBJfile(self.fname, keyBody)

                self.modifyOBJ( self.objs[ keyBody ], scaleFCT, \
                   offsetMethod, useBBcenter, \
                   global_offs, rot, local_offs, final_rot, isMatlabBody,
                   drawBB, XYZcoordinates, lenCS )

            # Read from TXT file - consider replacing with XML-file...
            elif self.fname[-4:] == '.txt':

                # strip(): remove default whitespace characters + "\n"
                f = open(self.fname, "r")
                curLine = 0 # line counter
                for l in f:
                    line = l.strip() # strip whitespace
                    curLine = curLine + 1
                    #if curLine >= 28:
                    #    ipdb.set_trace()

                    if line.startswith('#'): continue
                    values = line.split()
                    if not values: continue

                    # Default values for this line:
                    global_offs = 0,0,0
                    rot = 0,0,0
                    local_offs = 0,0,0
                    final_rot = 0,0,0

                    # ===== The below is for a body inside [] brackets! =====
                    firstStr = values[0]
                    endIndex = firstStr.find("]")
                    if firstStr.startswith('[') and endIndex > 0:
                        curObjFileName = values[1]
                        bodyStr = firstStr[ 1:endIndex ]
                        try:
                            keyBody = int( bodyStr ) # integer
                            isMatlabBody = True # = moving/rotating body
                        except:
                            if isinstance(bodyStr, str):
                                keyBody = bodyStr # it's a string
                                isMatlabBody = False # = fixed body
                            else:
                                print "Something wrong..."
                                ipdb.set_trace()

                        # Extract strings:
                        lineSlashSep = line.split('|')
                        global_offs_str = lineSlashSep[1].split() # offset
                        rot_str = lineSlashSep[2].split() # rotation
                        local_offs_str = lineSlashSep[3].split() # offset
                        if len( lineSlashSep ) <= 4:
                            final_rot_str = ['0', '0', '0'] # rotation
                        else:
                            final_rot_str = lineSlashSep[4].split() # rotation

                        # Convert strings to floats:
                        global_offs = [ float(v) for v in global_offs_str ]
                        rot = [ float(v) for v in rot_str ]
                        local_offs = [ float(v) for v in local_offs_str ]
                        final_rot = [ float(v) for v in final_rot_str ]

                        # Save this OBJ, with corresponding data from text-file:
                        self.loadOrSaveOBJfile(curObjFileName, keyBody)

                        self.modifyOBJ( self.objs[ keyBody ], scaleFCT, \
                                        offsetMethod, useBBcenter, \
                                        global_offs, rot, local_offs, final_rot, isMatlabBody,
                                        drawBB, XYZcoordinates, lenCS )

                        print "Line: " + str(curLine) + ": " + \
                          str(keyBody)

                    # ===== The above is for a body inside [] brackets! =====


                    # --- Choose if global bounding box is visible? ---
                        # NB: THIS APPLIES TO THE TXT FILE/CONTAINER, NOT THE OBJ-FILES!
                        # NB: THIS APPLIES TO THE TXT FILE/CONTAINER, NOT THE OBJ-FILES!
                        # NB: THIS APPLIES TO THE TXT FILE/CONTAINER, NOT THE OBJ-FILES!
                    elif firstStr.lower().startswith('drawglobalbb'):
                        lineSlashSep = line.split('=')
                        try:
                            self.BBsettings['drawBB'] = \
                              literal_eval( lineSlashSep[1].strip() )
                        except:
                            ipdb.set_trace()
                            print "*** WARNING: Ignoring drawBB setting, " + \
                              "should be True/False and is case-sensitive!"
                        print "Line: " + str(curLine) + ": " + \
                          "drawGlobalBB:", self.BBsettings['drawBB']
                        # NB: THIS APPLIES TO THE TXT FILE/CONTAINER, NOT THE OBJ-FILES!
                        # NB: THIS APPLIES TO THE TXT FILE/CONTAINER, NOT THE OBJ-FILES!
                        # NB: THIS APPLIES TO THE TXT FILE/CONTAINER, NOT THE OBJ-FILES!


                    # ===== These apply to the individual OBJ files =====
                    # --- Scaling parameter from the *.TXT file ---
                    elif firstStr.lower().startswith('scaling'):
                        lineSlashSep = line.split('=')
                        scaleFCT = float( lineSlashSep[1].strip() )
                        print "Line: " + str(curLine) + ": " + \
                          "Scaling factor:", scaleFCT

                    # --- Choose offset-method from the *.TXT file ---
                    elif firstStr.lower().startswith('offsetmethod'):
                        lineSlashSep = line.split('=')
                        # remember to use .strip() !
                        offsetMethod = lineSlashSep[1].strip()
                        print "Line: " + str(curLine) + ": " + \
                          "offsetMethod:", offsetMethod

                    # --- Translate coordinates to BB center? ---
                    elif firstStr.lower().startswith('usebbcenter'):
                        lineSlashSep = line.split('=')
                        try: # remember to use .strip() !
                            useBBcenter = \
                              literal_eval( lineSlashSep[1].strip() )
                        except:
                            print "*** WARNING: Ignoring useBBcenter setting, " + \
                              "should be True/False and is case-sensitive!"
                        print "Line: " + str(curLine) + ": " + \
                          "useBBcenter:", useBBcenter

                    # --- Draw BB ? ---
                    elif firstStr.lower().startswith('drawbb'):
                        lineSlashSep = line.split('=')
                        try:
                            # remember to use .strip() !
                            drawBB = \
                              literal_eval( lineSlashSep[1].strip() )
                        except:
                            print "*** WARNING: Ignoring drawBB setting, " + \
                              "should be True/False and is case-sensitive!"
                        print "Line: " + str(curLine) + ": " + \
                          "drawBB:", drawBB

                    # --- Print bounding box info (both at startup + when running) ? ---
                    elif firstStr.lower().startswith('xyzcoordinates'):
                        lineSlashSep = line.split('=')
                        try:
                            # remember to use .strip() !
                            XYZcoordinates = \
                              literal_eval( lineSlashSep[1].strip() )
                        except:
                            print "*** WARNING: Ignoring XYZcoordinates setting, " + \
                              "should be True/False and is case-sensitive!"
                        print "Line: " + str(curLine) + ": " + \
                          "XYZcoordinates:", XYZcoordinates

                    # --- Print coordinate system (numerical length of CS) ? ---
                    elif firstStr.lower().startswith('lencs'):
                        lineSlashSep = line.split('=')
                        lenCS = float( lineSlashSep[1].strip() )
                        print "Line: " + str(curLine) + ": " + \
                          "lenCS:", lenCS

                    # --- Cannot understand this line in the *.TXT file ---
                    else:
                        print "ERROR: Could not read/understand: " + str(values)
                        ipdb.set_trace()
                        exit(1)
                f.close()
            else:
                print " Invalid filename (*.obj or *.txt)... Nothing loaded..."
        except Exception, exc:
            exc_type, exc_obj, exc_tb = exc_info()
            print " --> EXCEPTION --> " + str([exc_type, exc_obj, exc_tb])
            fname = exc_tb.tb_frame.f_code.co_filename
            print
            print " From: " + fname +\
                  ", line:",  exc_tb.tb_lineno
            excDetails = traceback.extract_tb(exc_tb)
            print " --> File: " + excDetails[1][0] + \
                  ", line: " + repr( excDetails[1][1] )
            print "    --> Function: " + excDetails[1][2]
            print "        Containing: " + excDetails[1][3]
            ipdb.set_trace()
            exit(1)
        #--------------
        printAllBBs = False
        for keyBody in self.objs.keys():
            if self.objs[keyBody].BBsettings['XYZcoordinates'] == True:
                printAllBBs = True
        if printAllBBs:
            self.printBoundingBoxInfoAllBodies()
        #--------------
        # Find out which bodies are fixed and which isn't:
        self.separateMovingFixedBodies()
        #--------------


    def printBoundingBoxInfo(self, keyBody, curObj, showGlobal):
        print "-"*70
        print " "*2 + str(keyBody) + ": " + curObj.OBJfname + \
          " (scaling=" + gl_utils.engNotation(curObj.scaleFactor) + ")"

        print " "*10, "Global offset {r} X/Y/Z:   " + str( curObj.global_offs )
        print " "*10, "Rotation around X/Y/Z, {omega}(deg.): " +\
          str( curObj.rot )
        print " "*10, "Local offset {s} X/Y/Z:   " + str( curObj.local_offs )
        print " "*10, "Final rotation {r} X/Y/Z:   " + str( curObj.final_rot )
        print
        print " "*6 + "Local bounding box: "
        print " "*6 + "X=" + gl_utils.engNotation(curObj.MinMaxLocal['x']) + \
           ", Y=" + gl_utils.engNotation(curObj.MinMaxLocal['y']) + \
           ", Z=" + gl_utils.engNotation(curObj.MinMaxLocal['z'])
        if curObj.bodyCoordSysBBcenter:
            print " "*6 + "Local coordinate system moved to center of BB!"
        if showGlobal: # this can/will be offset, so no need to write it out!
            print " "*6 + "Global bounding box: "
            print " "*6 + \
              "X=" + gl_utils.engNotation(curObj.MinMaxGlobalORIGIN['x']) + \
               ", Y=" + gl_utils.engNotation(curObj.MinMaxGlobalORIGIN['y']) + \
               ", Z=" + gl_utils.engNotation(curObj.MinMaxGlobalORIGIN['z'])
        print " "
        # print "-"*70

    def printBoundingBoxInfoAllBodies(self, showGlobal = True):
        for keyBody in self.objs.keys():
            self.printBoundingBoxInfo( \
                keyBody, self.objs[keyBody], showGlobal )


    def separateMovingFixedBodies(self):
        for key in self.objs.keys():
            gl_utils.cleanUpLogging( self.objs[ key ] )

        print " "
        print "-"*50
        if self.bodies < 1:
            print "Warning: No OBJ-files loaded!" # by load()
        else:
            print "Done loading all wavefront OBJ files..."

        # ===============================================================
        # Separate fixed/moving/rotating (=Matlab) bodies + input check:
        # ===============================================================
        self.matlabKeys = set() # ALSO IF NO OBJs ARE LOADED!
        self.fixedKeys = set()  # ALSO IF NO OBJs ARE LOADED!
        for key_Body in self.objs.keys():
            if self.objs[key_Body].isMatlabBody:
                self.matlabKeys.add(key_Body)
            else:
                self.fixedKeys.add(key_Body)
        # Simple check of the sum of two separated sets...
        if len( self.objs.keys() ) != \
            len(self.matlabKeys) + len(self.fixedKeys):
            ipdb.set_trace()
            raise Exception("ERROR: invalid separation sum...")
        # ===============================================================
        print "-"*50


    def constructAllDisplayLists(self):
        display.set_caption("PLEASE WAIT... CONSTRUCTING DISPLAY LISTS...")
        numKeys = len( self.objs.keys() )
        count = 0
        for key in self.objs.keys():
            gl_utils.glClear(\
                gl_utils.GL_COLOR_BUFFER_BIT | gl_utils.GL_DEPTH_BUFFER_BIT)

            count = count + 1
            numVertices = len( self.objs[key].vertices )
            # Construct string:
            printStr = "Display list [" + str(count) + "/" + \
              str(numKeys) + "]: \"" + str(key) + "\" ("
            if self.objs[key].isMatlabBody:
                printStr = printStr + "Matlab "
            else:
                printStr = printStr + "fixed "
            printStr = printStr + "body with: " + \
              str(numVertices) + " vertices)"
            gl_utils.printText(0.15, 0.5, printStr)

            display.flip() # update screen, show text

            print " --> " + printStr # console message
            self.objs[ key ].makeDisplayList() # construct this list


    def makeAllOBJsFIXED(self):
        moveKeys = []
        for mk in self.matlabKeys:
            moveKeys.append(mk)
        if len(moveKeys) > 0:
            print " "
            print "Changing keys: " + \
              str(moveKeys) + " into fixed keys..."
            # Now, convert integer/Matlab keys to strings
            for mk in moveKeys:
                newKey = "Body" + str(mk) + "fix"
                self.objs[newKey] = self.objs[mk] # copy
                del self.objs[mk] # delete
                self.objs[newKey].isMatlabBody = False # change
                self.fixedKeys.add( newKey )
                self.matlabKeys.remove(mk)
        else:
            print "Found no moving keys to make fixed..."


# -----------------------------------------------------

if __name__ == "__main__":

    if 1:
        # wavefront = getOBJs("testOBJ.txt")
        wavefront = getOBJs("nordTankOBJs.txt")
        wavefront.load() # load from text-file now...
    else:
        wavefront = getOBJs("gearbox.obj")
        #wavefront = getOBJs("diamond.obj")
        wavefront.load() # load from text-file now...
        # wavefront.load("nordTankOBJs.txt") # load from text-file now...

