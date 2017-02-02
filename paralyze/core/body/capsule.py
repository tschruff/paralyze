from paralyze.core.algebra import AABB, Vector
from .body import Body


import math


class Capsule(Body):

    def __init__(self, pos, radius=1, length=1, rotation=None, **kwargs):
        Body.__init__(self, pos, **kwargs)
        assert radius > 0
        self._r = radius
        self._l = length
        self._rot = rotation

    def __str__(self):
        return 'Capsule(id=%s, center=%s, radius=%f, length=%f)' % (self.id(), self.position(), self._r, self._l)

    def aabb(self):
        pass

    def contains(self, point):
        pass

    def length(self):
        return self._l

    def scale(self, scale_factor):
        Body.scale(self, scale_factor)
        self._l *= scale_factor
        self._r *= scale_factor
        self.updateVolume()

    def setLength(self, length):
        assert length > 0.0
        self._l = length
        self.updateVolume()

    def radius(self):
        return self._r

    def setRadius(self, radius):
        assert radius > 0.0
        self._r = radius
        self.updateVolume()

    def updateVolume(self):
        self._v = 4/3.0 * math.pi * self._r ** 3 + math.pi * self._r ** 2 * self._l
