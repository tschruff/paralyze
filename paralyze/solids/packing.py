from paralyze.core.algebra import Vector, Ray
from paralyze.core.bodies.tracing import intersects

from multiprocessing import Pool
from functools import partial

import numpy as np


# ----------------- #
# INTERFACE METHODS #
# ----------------- #

def calc_mean_solid_fraction(blocks, bodies_id, domain=None):

    if domain is None:
        domain = blocks.domain

    with Pool(blocks.num_processes) as pool:
        results = pool.map(partial(__get_solid_volume, bodies_id=bodies_id, domain=domain), blocks)

    solid = sum(results)
    return solid / domain.volume


def calc_mean_packing_height(blocks, bodies_id, domain=None, position_generator=None, num_samples=100):

    if domain is None:
        domain = blocks.domain

    args = {
        'bodies_id': bodies_id,
        'domain': domain,
        'position_generator': position_generator,
        'num_samples': num_samples
    }

    with Pool(blocks.num_processes) as pool:
        results = pool.map(partial(__sample_packing_height, **args))

    sum_s = 0
    num_s = 0
    for samples in results:
        sum_s += np.sum(samples)
        num_s += len(samples)

    return sum_s / num_s


# WORKER METHODS

def __get_solid_volume(block, bodies_id, domain):
    solid_volume = [body.volume() for body in block[bodies_id] if domain.contains(body.center())]
    return sum(solid_volume)


def __sample_packing_height(block, bodies_id, domain, position_generator, num_samples):
    heights = np.zeros(num_samples)
    # ray tracing algorithm
    for i in range(num_samples):
        pos = position_generator.next()
        ray = Ray(Vector((pos[0], pos[1], domain.z_max)), Vector((0, 0, -1)))
        for body in block[bodies_id]:
            intersection = intersects(ray, body)
            if intersection[0]:
                heights[i] = max(heights[i], ray.at(intersection[1]).z)
    return heights
