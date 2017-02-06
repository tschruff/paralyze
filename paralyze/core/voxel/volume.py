from PydroSquid.core.algebra import AABB, Vector

import numpy as np
import math


class VoxelVolume(object):

    def __init__(self, origin, resolution, shape, dtype=np.uint8, solid_value=1):
        self._o = origin
        self._r = resolution
        self._s = solid_value
        self._v = np.full(shape, 0, dtype)

    def __setitem__(self, key, value):
        self._v[key] = value

    def aabb(self):
        return AABB(self.origin(), self.origin() + Vector(self._v.shape) * self._r)

    def solid_volume(self):
        return self._v.sum() / self._s

    def voxel_center(self, index):
        center_shift = Vector(0.5) * self._r
        return self.origin() + Vector(index) + center_shift

    def intersection_volume(self, aabb):
        assert isinstance(aabb, AABB)
        intersect = self.aabb().intersect(aabb)
        if intersect.is_empty():
            return 0.0

        local_intersect = intersect.shifted(-self.origin())

        min = list(map(round, local_intersect.min / self._r))
        max = list(map(round, local_intersect.max / self._r))

        solids = self._v[min[0]:max[0], min[1]:max[1], min[2]:max[2]].sum()
        return solids * self._r ** 3

    def iter_local_xyz(self):
        for z in range(self._v.shape[2]):
            for y in range(self._v.shape[1]):
                for x in range(self._v.shape[0]):
                    yield x, y, z

    def iter_xyz(self):
        for index in self.iter_local_xyz():
            yield self.voxel_center(index)

    def origin(self):
        return self._o

    def set_origin(self, pos):
        self._o = pos

    def set_resolution(self, resolution):
        self._r = resolution

    @staticmethod
    def voxelize(body, resolution, dtype=np.uint8, solid_value=1):
        shape = tuple(map(math.ceil, body.aabb().size / resolution))
        volume = VoxelVolume(body.aabb().min, resolution, shape, dtype, solid_value)
        for x, y, z in volume.iter_local_xyz():
            cell_center = volume.voxel_center((x, y, z))
            if body.contains(cell_center):
                volume[x, y, z] = solid_value
        return volume
