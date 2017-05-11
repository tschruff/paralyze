from ..algebra import AABB, Vector
from .solid import PSolid, DynamicPSolid

import math
import numpy as np


def create_cylinder(*args, dynamic=False, **kwargs):
    if not dynamic:
        return StaticCylinder(*args, **kwargs)
    return DynamicCylinder(*args, **kwargs)


class Cylinder(PSolid):
    Length      = PSolid.Length + 2
    RadiusIndex = PSolid.Length
    LengthIndex = PSolid.Length + 1

    def __init__(self, *args, **kwargs):
        radius = kwargs.pop("radius", 1)
        start = Vector(kwargs.pop("start", 0))
        end = Vector(kwargs.pop("end", 1))
        kwargs["center"] = (start + end) / 2
        PSolid.__init__(self, *args, **kwargs)
        self.radius = radius
        self.length = start.dist(end)
        self.update_aabb()

    def __repr__(self):
        return 'Cylinder(center=%s, radius=%f, length=%f)' % (self.center, self.radius, self.length)

    def update_aabb(self):
        """Returns the axis-aligned bounding box of the cylinder.

        An exact bounding box for a cylinder can be calculated by projecting the center line on the
        x-, y-, and z-axes and adding the projection of the two cap circles. Knowing the two cylinder
        end points A and B and the radius r, the bounding box offset from the center of mass is
        calculated by:

            dx = (1/2)*abs( R[0] )*length + kx * radius;
            dy = (1/2)*abs( R[3] )*length + ky * radius;
            dz = (1/2)*abs( R[6] )*length + kz * radius;

        where

            kx = sqrt( ( (A[1]-B[1])^2 + (A[2]-B[2])^2 ) / ( (A[0]-B[0])^2 + (A[1]-B[1])^2 + (A[2]-B[2])^2 ) )
            ky = sqrt( ( (A[0]-B[0])^2 + (A[2]-B[2])^2 ) / ( (A[0]-B[0])^2 + (A[1]-B[1])^2 + (A[2]-B[2])^2 ) )
            kz = sqrt( ( (A[0]-B[0])^2 + (A[1]-B[1])^2 ) / ( (A[0]-B[0])^2 + (A[1]-B[1])^2 + (A[2]-B[2])^2 ) )

        Alternatively, an exact bounding box can be calculated using the rotation matrix:

            dx = (1/2)*abs( R[0] )*length + sqrt( R[1]^2 + R[2]^2 )*radius
            dy = (1/2)*abs( R[3] )*length + sqrt( R[4]^2 + R[5]^2 )*radius
            dz = (1/2)*abs( R[6] )*length + sqrt( R[7]^2 + R[8]^2 )*radius

        However, in order to avoid the three costly square root calculations (in both formulations),
        a loosely fitting bounding box is calculated instead by the three following equations:

            dx = (1/2)*abs( R[0] )*length + abs( R[1] )*radius + abs( R[2] )*radius
            dy = (1/2)*abs( R[3] )*length + abs( R[4] )*radius + abs( R[5] )*radius
            dz = (1/2)*abs( R[6] )*length + abs( R[7] )*radius + abs( R[8] )*radius
        """
        r = self.rotation_matrix

        # length = self.length
        # radius = self.radius
        # xsize = .5 * abs(r[0][0]) * length + ( abs(r[0][1]) + abs(r[0][2]) ) * radius
        # ysize = .5 * abs(r[1][0]) * length + ( abs(r[1][1]) + abs(r[1][2]) ) * radius
        # zsize = .5 * abs(r[2][0]) * length + ( abs(r[2][1]) + abs(r[2][2]) ) * radius
        # size = Vector((xsize, ysize, zsize))

        size = .5 * np.abs(r[:,0]) * self.length + (np.abs(r[:,1]) + np.abs(r[:,2])) * self.radius
        aabb = AABB(self.center - size, self.center + size, dtype=self.dtype)

        # assert aabb.is_valid()
        # assert aabb.contains(self.center)

        self._data[self.AABBSlice] = aabb

    def contains(self, point):
        return False

    @property
    def equivalent_mesh_size(self):
        return self.radius * 2.

    @property
    def length(self):
        return self._data[self.LengthIndex]

    @length.setter
    def length(self, length):
        self._data[self.LengthIndex] = length

    @property
    def radius(self):
        return self._data[self.RadiusIndex]

    @radius.setter
    def radius(self, radius):
        self._data[self.RadiusIndex] = radius

    @property
    def volume(self):
        return math.pi * self.radius**2 * self.length


class StaticCylinder(Cylinder):
    pass


class DynamicCylinder(DynamicPSolid, Cylinder):
    Length = DynamicPSolid.Length + 2

    def __init__(self, *args, **kwargs):
        DynamicPSolid.__init__(self, *args, **kwargs)
        Cylinder.__init__(self, *args, **kwargs)
        self.update_inertia()

    def update_inertia(self):
        ia = .5 * self.mass * self.radius**2
        ib = self.mass * (.25 * self.radius**2 + 1./12 * self.length**2)
        self._data[self.InertiaSlice] = np.array([ia, 0, 0, 0, ib, 0, 0, 0, ib], dtype=self.dtype)
