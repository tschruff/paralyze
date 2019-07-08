"""Module doc goes here...
"""
from pyevtk.hl import pointsToVTK
import numpy as np


def save(filename, solids, attributes=('volume', )):
    pointsToVTK(filename, solids.x, solids.y, solids.z, data={a: solids[a] for a in attributes})


# Example 1
npoints = 100
x = np.random.rand(npoints)
y = np.random.rand(npoints)
z = np.random.rand(npoints)
pressure = np.random.rand(npoints)
temp = np.random.rand(npoints)
pointsToVTK("./rnd_points", x, y, z, data = {"temp" : temp, "pressure" : pressure})