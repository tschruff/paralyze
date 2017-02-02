from paralyze.core.algebra import AABB, Vector, Ray

from multiprocessing import Pool
from functools import partial

import math
import numpy


# ----------------- #
# INTERFACE METHODS #
# ----------------- #

def calc_bulk_porosity(blocks, bodies_id, domain=None):
    if domain is None:
        domain = blocks.globalDomain

    with Pool(blocks.np) as pool:
        results = pool.map(partial(__volumeFractions, bodiesId=bodies_id, domain=domain), blocks)

    solid = 0.0
    total = 0.0
    for s, t in results:
        solid += s
        total += t

    return (total - solid) / total


def calc_mean_packing_height(blocks, bodies_id, domain=None, randomGenerator=None, numSamples=100):

    numSamplesPerProcess = math.ceil(numSamples/blocks.np)

    args = partitions
    for i in range(len(args)):
        args[i]['numSamples'] = numSamplesPerProcess
        args[i]['randomGenerator'] = randomGenerator

    with Pool(np) as pool:
        results = numpy.array(pool.map(__meanPackingHeight, args))

    return results.mean()


# WORKER METHODS

def __volumeFractions(block, bodiesId, domain=None):
    if domain is None:
        domain = block.globalDomain
    else:
        domain = block.globalDomain.intersect(domain)

    totalVolume = domain.volume
    solidVolume = 0.0

    for body in block[bodiesId]:
        if domain.contains(body.center()):
            solidVolume += body.volume()

    return solidVolume, totalVolume


def __meanPackingHeight(block, domain, numSamples):

    domain = args['domain']
    numSamples = args['numSamples']
    randomGenerator = args['randomGenerator']
    bodies = args['body']

    if randomGenerator is None:
        randomGenerator = InsideAABB(domain)
    
    heights = numpy.array([domain.zMin for i in range(numSamples)])

    # ray tracing algorithm
    for i in range(numSamples):
        pos = randomGenerator.next()
        ray = Ray(Vector(pos[0], pos[1], domain.zMax), Vector(0, 0, -1))
        for body in bodies:
            intersection = ray.intersects(body)
            if intersection[0]:
                heights[i] = max(heights[i], ray.at(intersection[1]).z)

    return heights.mean()
