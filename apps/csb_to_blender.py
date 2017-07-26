import argparse

import bpy

from paralyze.core.solids import CSBFile
from paralyze.core.solids import Sphere


def create_blender_spheres(spheres, segments, rings):
    for sphere in spheres:
        bpy.ops.mesh.primitive_uv_sphere_add(location=sphere.center,
                                             size=sphere.radius,
                                             segments=segments,
                                             ring_count=rings)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str)
    parser.add_argument("--delimiter", type=str, default=",")
    parser.add_argument("--segments", type=int, default=32)
    parser.add_argument("--rings", type=int, default=16)
    parser.add_argument("--dynamic", action="store_true", default=False)

    args = parser.parse_args()

    bodies = CSBFile.load(args.file, delimiter=args.delimiter, dynamic=args.dynamic)
    create_blender_spheres(filter(lambda body: isinstance(body, Sphere), bodies), args.segments, args.rings)
