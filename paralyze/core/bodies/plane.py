from ..algebra import Vector
from .body import Body


class Plane(Body):

    def __init__(self, pos, normal=(1, 0, 0), **kwargs):
        Body.__init__(self, pos, **kwargs)
        self._normal = Vector(normal).normalized()

    def __str__(self):
        return 'Plane(id=%s, pos=%s, normal=%s)' % (str(self.id()), self.position(), self.normal())

    def equivalent_mesh_size(self):
        return 0.0

    def contains(self, point):
        return False

    def normal(self):
        return self._normal

    def set_normal(self, normal):
        self._normal = normal
