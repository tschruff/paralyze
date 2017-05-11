from paralyze.core.solids.io import *
from paralyze.core.solids.sphere import create_sphere
from timeit import default_timer
import os
import numpy as np

CSB = "/Users/tobs/Programming/Python/paralyze/data/uniform-8.csv"
NPY = "/Users/tobs/Programming/Python/paralyze/data/uniform-8.npy"

start = default_timer()
bodies = CSBFile.load(CSB)
end = default_timer()
print("Loading {} bodies from file {} took {:f} seconds".format(len(bodies), CSB, end-start))

if not os.path.exists(NPY):
    save_spheres(bodies, NPY)

start = default_timer()
body_data = np.load(NPY)
bodies = []
for i in range(len(body_data)):
    bodies.append(create_sphere(center=body_data["center"][i], radius=body_data["radius"][i]))
end = default_timer()
print("Loading {} bodies from file {} took {:f} seconds".format(len(bodies), NPY, end-start))
