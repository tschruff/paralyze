from ..algebra import AABB, Vector
from .solid import PSolid, DynamicPSolid

import math
import numpy as np


def create_capsule(*args, dynamic=False, **kwargs):
    if not dynamic:
        return StaticCapsule(*args, **kwargs)
    return DynamicCapsule(*args, **kwargs)


class Capsule(PSolid):
    Parameters = ["radius", "length"]
    Length = PSolid.Length + 2
    RadiusIndex = PSolid.Length
    LengthIndex = PSolid.Length + 1

    def __init__(self, *args, **kwargs):
        radius = kwargs.pop("radius", 1)
        start = Vector(kwargs.pop("start", 0))
        end = Vector(kwargs.pop("end", 1))
        PSolid.__init__(self, *args, **kwargs)
        self.radius = radius
        self.length = start.dist(end)

    def __repr__(self):
        return 'Capsule(center=%s, radius=%f, length=%f)' % (self.center, self.radius, self.length)

    @property
    def aabb(self):
        """
        """
        r = self.rotation_matrix

        # length = self.length
        # radius = self.radius
        # size = Vector((abs( r[0][0]*length ) * .5 + radius,
        #                abs( r[1][0]*length ) * .5 + radius,
        #                abs( r[2][0]*length ) * .5 + radius))

        size = np.abs(r[:,0]) * self.length * .5 + Vector(self.radius)

        return AABB(self.center - size, self.center + size)

    def contains(self, point):
        return False

    @property
    def equivalent_mesh_size(self):
        return self.radius * 2.

    @property
    def length(self):
        return self[self.LengthIndex]

    @length.setter
    def length(self, length):
        self[self.LengthIndex] = float(length)

    @property
    def radius(self):
        return self[self.RadiusIndex]

    @radius.setter
    def radius(self, radius):
        self[self.RadiusIndex] = float(radius)

    @property
    def volume(self):
        caps = 4/3.0 * math.pi * self.radius ** 3
        cylinder = math.pi * self.radius ** 2 * self.length
        return cylinder + caps


class StaticCapsule(Capsule):
    pass


class DynamicCapsule(DynamicPSolid, Capsule):
    Length = DynamicPSolid.Length + len(Capsule.Parameters)

    def __init__(self, *args, **kwargs):
        DynamicPSolid.__init__(self, *args, **kwargs)
        Capsule.__init__(self, *args, **kwargs)

    @property
    def inertia(self):
        density = self.density
        radius = self.radius
        length = self.length

        sphere_mass = 4./3 * math.pi * radius**3 * density
        cylinder_mass = math.pi * radius**2 * length * density

        ia = radius**2 * (.5 * cylinder_mass + .4 * sphere_mass)
        ib = cylinder_mass * (.25 * radius**2 + 1./12 * length**2) + sphere_mass * (.4 * radius**2 + .375 * radius * length + .25 * length**2)
        return np.array([ia, 0, 0, 0, ib, 0, 0, 0, ib], dtype=np.float64).reshape((3, 3))
