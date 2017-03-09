from ..algebra import AABB, Vector
from .body import Body


class Sphere(Body):

    def __init__(self, center=(0, 0, 0), radius=1, **kwargs):
        """

        Parameters
        ----------
        center: Vector

        radius: float

        kwargs: dict

        """
        Body.__init__(self, center, **kwargs)
        assert radius > 0

        self._r = radius
        self._update_geometry()

    def __repr__(self):
        return 'Sphere(center={}, radius={})'.format(self.position(), self._r)

    def equivalent_mesh_size(self):
        return self.radius() * 2.0

    def contains(self, point):
        return (point - self.position()).sqr_length() <= (self._r * self._r)

    def radius(self):
        return self._r

    def _update_geometry(self):
        self._aabb = AABB(self.position() - Vector(self._r), self.position() + Vector(self._r))
