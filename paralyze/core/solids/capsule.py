from ..algebra import AABB, Vector
from .solid import PSolid, DynamicPSolid

import math
import numpy as np


def create_capsule(*args, dynamic=False, **kwargs):
    if not dynamic:
        return StaticCapsule(*args, **kwargs)
    return DynamicCapsule(*args, **kwargs)


class Capsule(PSolid):
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
        return 'Capsule(center=%s, radius=%f, length=%f)' % (self.center, self.radius, self.length)

    def update_aabb(self):
        """
        """
        r = self.rotation_matrix

        # length = self.length
        # radius = self.radius
        # size = Vector((abs( r[0][0]*length ) * .5 + radius,
        #                abs( r[1][0]*length ) * .5 + radius,
        #                abs( r[2][0]*length ) * .5 + radius))

        size = np.abs(r[:,0]) * self.length * .5 + Vector(self.radius)

        self._data[self.AABBSlice] = AABB(self.center - size, self.center + size, dtype=self.dtype)

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
        caps = 4/3.0 * math.pi * self.radius ** 3
        cylinder = math.pi * self.radius ** 2 * self.length
        return cylinder + caps


class StaticCapsule(Capsule):
    pass


class DynamicCapsule(DynamicPSolid, Capsule):
    Length = DynamicPSolid.Length + 2

    def __init__(self, *args, **kwargs):
        DynamicPSolid.__init__(self, *args, **kwargs)
        Capsule.__init__(self, *args, **kwargs)
        self.update_inertia()

    def update_inertia(self):
        rho = self.density
        r = self.radius
        l = self.length

        m_s = 4./3 * math.pi * r**3 * rho # mass of cap sphere
        m_c = math.pi * r**2 * l * rho # mass of cylinder

        ia = r**2 * (.5 * m_c + .4 * m_s)
        ib = m_c * (.25 * r**2 + 1./12 * l**2) + m_s * (.4 * r**2 + .375 * r * l + .25 * l**2)

        self._data[self.InertiaSlice] = np.array([ia, 0, 0, 0, ib, 0, 0, 0, ib], dtype=self.dtype)
