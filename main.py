#!/usr/bin/python2

#import numpy as np # don't need this with scipy
import scipy
import scipy.io

import mGLanim
#from sys import exit # pychecker: (exit) shadows builtin

# If you want to debug this, in a Python console, type:
# from load_from_matlab_scipy import *
# nordTank = matlabLoader() # load data
# nordTank.printMatlab() # print extra info out
# g = mGLanim.graphicsEngine(nordTank)

# --------------------- class matlabLoader: ---------------------
class matlabLoader:
    def __init__(self):
        #fname = 'tmp.mat'
        fname = 'mat/20sec_Matlab.mat'
        matlab = scipy.io.loadmat(fname)

        # Or you can do (Matlab >= 7.3 using H5PY):
        # X=h5py.File('python_test.mat','r')
        # test = X['alpha_w'].value  <--
        #    the above gives the alpha_w value from Matlab

        self.q = matlab['q']
        self.bodies = matlab['bodies'][0][0]
        self.steps = self.q.shape[1] # get number of columns
        self.t = matlab['time'][0]
        if self.t.size==self.steps:
            print
            print "==================================================="
            print "Successfully loaded Matlab data for", self.steps, "steps..."
            print "Time-interval = [", \
                  self.t[0], ";", self.t[self.steps-1], "] seconds..."
            print "==================================================="
            print

        # -------------- Python additional animation info -----------
        print
        self.Anim_dataDescription = [] # empty list
        if 'pythonAnimInfo' in matlab:
            print "-"*50
            print "Found variable 'pythonAnimInfo' in Matlab file..."

            # Short notation:
            Anim_dataDescription = \
              matlab['pythonAnimInfo']['dataDescription'][0][0][0]

            print "-"*50
            for desc in range(0, Anim_dataDescription.shape[0]):
                col1 = Anim_dataDescription[desc][0][0][0]
                col2 = Anim_dataDescription[desc][0][1][0]
                col3 = Anim_dataDescription[desc][0][2][0]
                print "[" + str(desc) + "]:" + col1 + " row(s): " + str( col3 )
                self.Anim_dataDescription.append( (col1,col2,col3) )
            print "-"*50
            print

            # --- Exclude/include intermediate time-step data from ODE45? ---
            removeIntermediate = False # should not be used, need interpolate
            removeIntermediate = True

            if removeIntermediate:
                if self.Anim_dataDescription[0][0] == 'time':
                    timeRow = self.Anim_dataDescription[0][2][:]-1
                    allTimes = \
                      matlab['pythonAnimInfo']['data'][timeRow][0][0][0]
                else:
                    print "Something wrong, cannot find big time-vector..."
                    import ipdb; ipdb.set_trace()

                print "  Removing intermediate ODE45-timesteps..."
                allTimesCount = 0
                hugeDataArray = matlab['pythonAnimInfo']['data'][0][0]
                sz = hugeDataArray.shape
                self.Anim_data = scipy.zeros(( sz[0], len(self.t) )) # init

                for s in range(0, len(self.t)):
                    while self.t[s] != allTimes[allTimesCount]:
                        allTimesCount = allTimesCount+1
                        if allTimesCount > sz[1]:
                            print "ERROR: Cannot find all time-data"
                            import ipdb; ipdb.set_trace()

                    # Times are equal now, then save...
                    #   TODO: Sometimes - the same time (e.g. 10.00 sec)
                    #   is found two places in a row - best to take
                    #   the last column from Matlab instead of the
                    #   first, as we do it now... Maybe fix this later.
                    self.Anim_data[:,s] = hugeDataArray[:,allTimesCount]
                print "  Done removing intermediate ODE45-timesteps..."

            else:
                self.Anim_data = hugeDataArray # don't remove intermediate steps

        else:
            print "No 'pythonAnimInfo' was found in Matlab file..."

        # Save bearing positions (relative to local coordinate system!):
        self.bearings = matlab['bearings']
        # import ipdb; ipdb.set_trace()


    def printMatlab(self):
        print "------------------------------------"
        print "type(q) = ", type(self.q)
        # i.e. 2-dimensional = the "rank" in python
        #print "q.ndim =", self.q.ndim
        # i.e. 56x40 (has 56 rows in Matlab,
        #  and 40 columns), size = rows * columns
        print "q.shape =", self.q.shape
        #print "q.size =",  self.q.size
        print "q.dtype =", self.q.dtype
        print "bodies = ", self.bodies
        print "------------------------------------"
        print
# --------------------- class matlabLoader: ---------------------





if __name__ == "__main__":

    nordTank = matlabLoader() # class init (this does load data)
    nordTank.printMatlab() # print extra info out

    g = mGLanim.graphicsEngine(nordTank)
    g.runNow()
