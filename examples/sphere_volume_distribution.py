import os
import sys
import math
import csv
import numpy as np

from paralyze.core import AABB, Vector
from paralyze.core.solids import create_sphere
from paralyze.core.solids.io import CSBFile

PI_THIRDS = math.pi/3.
FOUR_THIRDS_PI = 4/3. * math.pi


def intersection_volume(domain_slice, sphere):
    
    c = sphere.center
    v = sphere.volume
    r = sphere.radius

    h = c.z + r - domain_slice.max.z
    if 0 < h <= r: # top sphere cap
        v -= PI_THIRDS * h**2 * (3*r - h)
    elif h > r:
        h = 2*r - h
        v -= FOUR_THIRDS_PI * r**3 - PI_THIRDS * h**2 * (3*r - h)

    h = domain_slice.min.z - (c.z - r)
    if 0 < h <= r: # bottom sphere cap
        v -= PI_THIRDS * h**2 * (3*r - h)
    elif h > r:
        h = 2*r - h
        v -= FOUR_THIRDS_PI * r**3 - PI_THIRDS * h**2 * (3*r - h)

    return v


def create_depth_column(domain, n_slices, transform_func=None):
    depth = []
    for domain_slice in domain.iter_slices(2, n_slices, reverse=True):
        if transform_func:
            depth.append(transform_func(domain_slice.center[2]))
        else:
            depth.append(domain_slice.center.z)
    return depth


def create_volume_distribution(domain, bodies, n_slices):
    volumes = np.zeros(n_slices)
    domain_top = domain.max.z
    domain_slices = domain.slices(2, n_slices, reverse=True)
    dz = domain.size.z / n_slices
    num_bodies = len(bodies)
    for k, body in enumerate(bodies):
        aabb = body.aabb
        i_min = int((domain_top-aabb.max.z) / dz)
        i_max = int((domain_top-aabb.min.z) / dz) + 1
        print('Mapping body {} of {}'.format(k+1, num_bodies), end='\r')
        for j, domain_slice in enumerate(domain_slices[i_min:i_max]):
            volumes[i_min+j] += intersection_volume(domain_slice, body)
    volumes /= domain.volume / n_slices
    return volumes


def save_volume_distribution(filename, domain, columns, n_slices):
    # create headers
    headers = ['depth', 'bed']
    depth = columns.pop("depth")
    bed = columns.pop("bed")
    times = list(sorted(columns.keys()))
    headers.extend(times)
    # write data
    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(headers)
        for i in range(len(depth)):
            # start each line with depth and bed volume fraction
            line = [depth[i], bed[i]]
            # and append all remaining data to the row
            line.extend([columns[time][i] for time in times])
            writer.writerow(line)


def main():

    surface = 203

    bed_path = "/Users/tobs/Programming/Python/paralyze/data/uniform-8.csv"
    out_path = "/Users/tobs/Programming/Python/paralyze/data/uniform-8_vd.csv"

    n_top_slices = 16
    x_bounds     = (24, 232)
    y_bounds     = (24, 232)
    n_slices     = int(surface/2)
    dz           = surface / float(n_slices)
    z_top        = surface + n_top_slices * dz
    total_slices = n_slices + n_top_slices
    domain       = AABB((x_bounds[0], y_bounds[0], 0), (x_bounds[1], y_bounds[1], z_top))

    if not os.path.exists(bed_path):
        print('No such file: {}'.format(bed_path))
        sys.exit(1)

    print('Surface:', surface, '; Number of slices:', n_slices, '; Slice height:', dz)
    print('Loading CSB file')
    bodies = CSBFile.load(bed_path, filter=lambda body: domain.contains(body.center))
    print('{} bodies loaded'.format(len(bodies)))
    columns = {}
    print('Creating depth array')
    columns["depth"] = create_depth_column(domain, n_slices, lambda z: surface-z)
    print('Creating volume distribution')
    columns["bed"] = create_volume_distribution(domain, bodies, total_slices)
    print('Saving output to file')
    save_volume_distribution(out_path, domain, columns, total_slices)


if __name__ == '__main__':

    import cProfile, pstats

    cProfile.run('main()', 'sphere_volume_distribution.prof')
    stats = pstats.Stats('sphere_volume_distribution.prof')
    stats.strip_dirs()
    stats.sort_stats('time').print_stats(10)
