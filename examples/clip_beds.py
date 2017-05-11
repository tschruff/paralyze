from paralyze.core import Vector, AABB
from paralyze.core.solids.io import CSBFile

import numpy as np

bed = '/Users/tobs/sciebo/Diss/Data/csb/beds/ln-8-1.6.csv'
out = '/Users/tobs/sciebo/Diss/Data/csb/beds/ln-8-1.6_clipped.csv'

domain = AABB(0, (160, 160, 310))
offset = (-216, -216, -50)

print('Loading solids from {}'.format(bed))
solids = CSBFile.load(bed, scale=1000.0, offset=offset, filter=lambda solid: domain.contains(solid.center))
print('Loaded {} solids'.format(len(solids)))
CSBFile.save(out, solids)
print('Saved solids to {}'.format(out))
