# load_from_matlab
Visualization - OpenGL - Wind Turbine model


# Wind Turbine Visualization

This is Python-code for visualization of wind turbine forces calculated in Matlab, as part of my PhD-project "Aerodynamic and Mechanical System Modelling", at Technical University of Denmark during the years 2010-2013 - my thesis can be found online, however the thesis does not completely describe this project. This code illustrates how to work with OpenGL (rotations, translations etc) and 3D geometries, including conversion to/from Euler angles/quaternions.
![Alt text](/data/WT.png?raw=true "Wind Turbine Visualization")


## Getting Started

This Python- project runs standalone, it will not install locally as no installer is included. Some text files ("*.txt") are used to adjust scaling and coordinate system locations of the individually used CAD files.


### Prerequisites

The packages "python2-scipy" and probably "python2-pygame/python2-pygame-sdl2" and "python2-opengl" + maybe other stuff is needed. When you try to run, Python will complain if you do not fullfill the needed dependencies. In this case you need to continue to install what you need, e.g.:

```
apt-get install (package-name you need, check your console for error messages)
yum install (package-name you need, check your console for error messages)
pacman -S (package-name you need, check your console for error messages)
```


### Running the program

When all dependencies are satisfied, you should be able to run the program using e.g. "python2.7 main.py" (only tested on Linux). The program will open up an OpenGL window with some info/statistics about what it's doing:
![Alt text](/data/screenshot_with_console.png?raw=true "Console output")


```
$ python2.7 main.py

===================================================
Successfully loaded Matlab data for 4683 steps...
Time-interval = [ 0.0 ; 20.0 ] seconds...
===================================================


--------------------------------------------------
Found variable 'pythonAnimInfo' in Matlab file...
--------------------------------------------------
[0]:time row(s): [1]
[1]:rotorForceMoments row(s): [2 3 4 5 6 7]
[2]:reactForceMomentBody1 row(s): [ 8  9 10 11 12 13]
[3]:reactForceMomentBearing1_Body1 row(s): [14 15 16 17 18 19]
[4]:reactForceMomentBearing2_Body1 row(s): [20 21 22 23 24 25]
[5]:Ring/planet 1 (2 <-> 3) row(s): [26]
[6]:Planet 1/sun (3 <-> 4) row(s): [27]
[7]:Ring/planet 2 (2 <-> 5) row(s): [28]
[8]:Ring/planet 3 (2 <-> 6) row(s): [29]
[9]:Par.gear.1/2 (4 <-> 7) row(s): [30]
--------------------------------------------------

  Removing intermediate ODE45-timesteps...
  Done removing intermediate ODE45-timesteps...
------------------------------------
type(q) =  <type 'numpy.ndarray'>
q.shape = (56, 4683)
q.dtype = float64
bodies =  8
------------------------------------

===== getWavefrontOBJs.py / getOBJs =====
Reading fname: nordTankOBJs.txt

Line: 11: lenCS: 0.1
Line: 14: drawGlobalBB: False
Line: 16: Scaling factor: 0.001
Line: 20: offsetMethod: fixed
No handlers could be found for logger "objloader.loadOBJfromFile"
Line: 23: gearfix
Line: 24: tower_fix
Line: 25: gen_fix
Line: 27: houseFix
Line: 30: useBBcenter: True
Line: 32: offsetMethod: matlab
Line: 33: 2
Line: 34: 3
Line: 35: 5
Line: 36: 6
Line: 37: offsetMethod: matlab+fixed
Line: 38: 4
Line: 39: 7
Line: 40: 8
Line: 42: useBBcenter: False
Line: 43: 1
Line: 45: Scaling factor: 0.1

--------------------------------------------------
Done loading all wavefront OBJ files...
--------------------------------------------------
 --> Display list [1/12]: "1" (Matlab body with: 6874 vertices)
 --> Display list [2/12]: "2" (Matlab body with: 22840 vertices)
 --> Display list [3/12]: "3" (Matlab body with: 13844 vertices)
 --> Display list [4/12]: "4" (Matlab body with: 18030 vertices)
 --> Display list [5/12]: "5" (Matlab body with: 13844 vertices)
 --> Display list [6/12]: "6" (Matlab body with: 13844 vertices)
 --> Display list [7/12]: "7" (Matlab body with: 7374 vertices)
 --> Display list [8/12]: "8" (Matlab body with: 14562 vertices)
 --> Display list [9/12]: "gen_fix" (fixed body with: 9222 vertices)
 --> Display list [10/12]: "tower_fix" (fixed body with: 6583 vertices)
 --> Display list [11/12]: "gearfix" (fixed body with: 6404 vertices)
 --> Display list [12/12]: "houseFix" (fixed body with: 3307 vertices)


gl_utils.printLCSoffsetInfo( ) about ...objs[obj].xyz_GlobalToLocalSys:
Body: 1, [X,Y,Z] = ['0', '0', '0.9501']
Body: 2, [X,Y,Z] = ['0', '0', '2.809']
Body: 3, [X,Y,Z] = ['0.2775', '0', '2.809']
Body: 4, [X,Y,Z] = ['0', '0', '2.960']
Body: 5, [X,Y,Z] = ['-0.1387', '0.2403', '2.809']
Body: 6, [X,Y,Z] = ['-0.1388', '-0.2403', '2.809']
Body: 7, [X,Y,Z] = ['-0.3535', '0', '3.450']
Body: 8, [X,Y,Z] = ['-0.1010', '0', '4.111']
Body: gen_fix, [X,Y,Z] = ['-0.09900', '0', '4.850']
Body: tower_fix, [X,Y,Z] = ['0', '0', '1']
Body: gearfix, [X,Y,Z] = ['0', '0', '2.225']
Body: houseFix, [X,Y,Z] = ['0', '0', '1.050']
***************************************************************************
Fixed objects: set(['gen_fix', 'tower_fix', 'gearfix', 'houseFix'])
Multibody objects: set([1, 2, 3, 4, 5, 6, 7, 8])
```


### Other comments

There are no unit-tests or similar in this package. This has been a stand-alone exercise for me to learn more about 3D OpenGL coding, coordinate transformations etc and I'm sure it can be improved many places if I had more time. I also believe some years prior to putting this project here, this code ran at around 60 FPS - instead of only 4 FPS. I have not investigated this issue. The intention of the project was only to visualize some Matlab results and make a small library for 3D operations.
![Alt text](/data/gearbox_closeup.png?raw=true "Close-up")


## Authors

* **Martin Felix Jørgensen**


## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details


## Acknowledgments

* The Ph.D. project was funded by DSF and DTU. Their support is gratefully acknowledged.
