from PydroSquid.core.algebra import AABB
from PydroSquid.core.body.io import CSBFile
from PydroSquid.core.voxel import VoxelVolume

import sys
import math
import glob
import os


########################################################################################################################
# USER INPUT
########################################################################################################################

DOMAIN = '[<23,23,0>,<233,233,350>]'

INPUT = '/Users/tobs/sciebo/Diss/Data/Packings/periodic-256/beds/uniform-8.csv'

OUTPUT = '/Users/tobs/sciebo/Diss/Data/Packings/periodic-256/beds/uniform-8_svd_z_NEW.csv'

AXIS = 'z'

NUM_SLICES = 350


########################################################################################################################
# SCRIPT
########################################################################################################################

def equivalent_sphere_diameter(v):
    return (v / math.pi * 3.0/4.0)**(1/3.) * 2.0

if INPUT == '' or len(glob.glob(INPUT)) == 0:
    print('ERROR: No such file or directory %s' % INPUT)
    sys.exit()

if isinstance(AXIS, str):
    AXIS = ['x', 'y', 'z'].index(AXIS)

if OUTPUT == '':
    OUTPUT = os.path.dirname(os.path.abspath(INPUT)) + 'spatial_volume_distribution_%s.csv' % (['x', 'y', 'z'][AXIS])

domain = AABB.parse(DOMAIN)
bodies = CSBFile.load(INPUT)
bodies = bodies.subset(lambda body: domain.intersects(body.aabb()))

if len(bodies) == 0:
    print('No bodies found in file %s' % INPUT)
    sys.exit()

body_slices = [[] for _ in range(NUM_SLICES)]

slices = domain.create_slices(AXIS, NUM_SLICES)
slice_centers = [slice.center[AXIS] for slice in slices]
slice_volumes = [0.0 for _ in range(NUM_SLICES)]
slice_bodies = [[] for _ in range(NUM_SLICES)]

vs = VoxelVolume((0, 0, 0), 10, 1.0)

for body in bodies.iter_bodies():
    for i, slice in enumerate(slices):
        if body.aabb().intersects(slice):
            vs.set_origin(body.origin())
            vs.set_resolution(body.radius() / 10.0)
            slice_volumes[i] += vs.intersection_volume(slice)
            slice_bodies[i].append(body)

with open(OUTPUT, 'w') as csv:

    csv.write('slice_center,solid_volume,geom_mean_diameter\n')

    for i, slice in enumerate(slice_volumes):

        slice_volume = sum(slice)

        diameter = 1.0
        for body in slice_bodies[i]:
            volume = body.volume()
            diameter *= equivalent_sphere_diameter(volume) ** (volume / slice_volume)

        csv.write('%f,%f,%f\n' % (slice_centers[i], slice_volume, diameter))
