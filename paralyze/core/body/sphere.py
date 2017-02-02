from paralyze.core.algebra import AABB, Vector
from .body import Body

import math


class Sphere(Body):

    def __init__(self, pos, radius=1, **kwargs):
        """

        :param pos:
        :param radius:
        :param kwargs:
        :return:
        """
        assert radius > 0

        self._r = radius

        Body.__init__(self, pos, **kwargs)

    def __repr__(self):
        return 'Sphere(id=%s, pos=%s, radius=%f)' % (str(self.id()), self.position(), self._r)

    def aabb(self):
        return AABB(self.position() - Vector(self._r), self.position() + Vector(self._r))

    def characteristic_size(self):
        return self.radius() * 2.0

    def contains(self, point):
        return (point - self.position()).sqr_length() <= (self._r * self._r)

    def radius(self):
        return self._r

    def scale(self, scale_factor):
        Body.scale(self, scale_factor)
        self.set_radius(self.radius() * scale_factor)

    def set_radius(self, radius):
        assert radius > 0.0
        self._r = radius
        self._v = 4/3.0 * math.pi * self._r ** 3
