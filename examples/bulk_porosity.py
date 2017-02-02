#!/usr/local/bin/python3

from PydroSquid.core.blocks import UniformBlockStorage
from PydroSquid.core.body import Sphere
from PydroSquid.core.body.io.csb import CSBFile

from PydroSquid.processing.body.mapping import map_bodies_to_field
from PydroSquid.processing.field.io import save_field

import os

import numpy as np


WORK_FOLDER = '/Users/tobs/Programming/PlayGround/PydroSquid'
INPUT = 'uniform-2'

OUTPUT_FORMAT = 'vxl'
OUTPUT_FOLDER = {'vtk': os.path.join(WORK_FOLDER, 'vtk_out'),
                 'vxl': os.path.join(WORK_FOLDER, 'vxl_out')}


def main():

    blocks = UniformBlockStorage((512, 512, 256), 4, dx=0.25, periodicity=(False, False, False), origin=(0, 0, 0))
    print('Created block storage over domain %s' % blocks.globalDomain())

    bodies = CSBFile.load(os.path.join(WORK_FOLDER, INPUT) + '.csv', delimiter=',')
    bodies = bodies.subset(lambda body: isinstance(body, Sphere))
    print('Loaded %d bodies from input file' % len(bodies))
    print()

    blocks.addBodies('body', blocks.clipToDomain(bodies))

    total = 0
    for block in blocks:
        bodies = block['body']
        bodies.print_stats()
        print()
        total += len(bodies)
    print('Added %d bodies in total to %d blocks' % (total, len(blocks)))
    print()

    blocks.addField(INPUT, np.uint8)
    blocks.exec(map_bodies_to_field, blocks=blocks, bodies_id='body', field_id=INPUT, solid_value=1)

    solids = sum(np.count_nonzero(field.data) for field in blocks[INPUT])
    totals = blocks.numCells().prod()
    print('Bulk porosity: %f (local fields)' % ((totals - solids) / totals))
    print()

    if OUTPUT_FORMAT != '':
        blocks.exec(save_field, file_format=OUTPUT_FORMAT, blocks=blocks, field_id=INPUT,
                    abs_folder_path=OUTPUT_FOLDER[OUTPUT_FORMAT])


if __name__ == '__main__':

    import cProfile, pstats

    cProfile.run('main()', 'bulk_porosity.prof')
    stats = pstats.Stats('bulk_porosity.prof')
    stats.strip_dirs()
    stats.sort_stats('time').print_stats(10)
