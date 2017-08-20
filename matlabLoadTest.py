#!/usr/bin/python2

import scipy
import scipy.io
import sys
#import numpy # don't need with scipy

# load data
timesteps = 2
bodies = 4
q = scipy.arange(0, bodies*7*timesteps).reshape(timesteps,bodies*7).T
print "type(q) = ", type(q)
print "q.shape =", q.shape
print "q = "
print q
print

LCS=scipy.zeros((bodies,3)) # bodies rows and 3 columns (x,y,z)
for x in range(0,timesteps):
     print
     print "Step: ", x
     print "------------------"

     rows=scipy.array([0,1,2]) # first rows, for body 1 (increment per body)
     LCS=scipy.zeros((bodies,3))
     for b in range(0,bodies):
          LCS[b,:] = q[rows,x]
          rows = rows + 7 # go to next body
          print "Body", str(b+1) +": LCS(x,y,z) =", LCS[b,:]
