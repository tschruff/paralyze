import glob
import os
import sys

from paralyze.core.algebra import AABB, Vector
from paralyze.core.solids import CSBFile

########################################################################################################################
# USER INPUT
########################################################################################################################

DOMAIN = '[<24,24,0>,<136,136,80>]'
SCALE = 1000.0
OFFSET = Vector(-240, -240, -50)

INPUT = '/Users/tobs/sciebo/Diss/Data/Packings/periodic-256/beds/uniform-8.csv'

OUTPUT = '/Users/tobs/sciebo/Diss/Data/Packings/periodic-256/beds/uniform-8_svd_z_NEW.csv'

AXIS = 'z'

NUM_SLICES = 350


########################################################################################################################
# SCRIPT
########################################################################################################################

if INPUT == '' or len(glob.glob(INPUT)) == 0:
    print('ERROR: No such file or directory %s' % INPUT)
    sys.exit()

if isinstance(AXIS, str):
    AXIS = ['x', 'y', 'z'].index(AXIS)

if OUTPUT == '':
    OUTPUT = os.path.dirname(os.path.abspath(INPUT)) + 'spatial_volume_distribution_%s.csv' % (['x', 'y', 'z'][AXIS])

domain = AABB.parse(DOMAIN)
bodies = CSBFile.load(INPUT, scale=SCALE, offset=OFFSET)
bodies = bodies.subset(lambda body: domain.intersects(body.domain()))

if len(bodies) == 0:
    print('No bodies found in file %s' % INPUT)
    sys.exit()

body_slices = [[] for _ in range(NUM_SLICES)]

slices = domain.slices(AXIS, NUM_SLICES)
slice_centers = [slice.center[AXIS] for slice in slices]
slice_volumes = [0.0 for _ in range(NUM_SLICES)]
slice_bodies = [[] for _ in range(NUM_SLICES)]

vs = VoxelVolume((0, 0, 0), 10, 1.0)

for body in bodies.iter_bodies():
    for i, slice in enumerate(slices):
        if body.domain().intersects(slice):
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
