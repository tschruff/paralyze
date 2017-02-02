from PydroSquid.core.algebra.vector import Vector


class CartesianGrid(object):

    def __init__(self, origin, delta, size):
        assert isinstance(origin, Vector)
        assert len(delta) == 3
        assert len(size) == 3

        self._origin = origin
        self._delta = delta
        self._size = size

    def numVertices(self):
        return self._size[0] * self._size[1] * self._size[2]

    def vertex(self, index):

        z = index / (self._size[0] * self._size[1])
        y = (index / self._size[0]) % self._size[1]
        x = index % self._size[0]

        return Vector(self._origin[0] + x * self._delta[0],
                      self._origin[1] + y * self._delta[1],
                      self._origin[2] + z * self._delta[2])
