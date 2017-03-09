from ..vector import Vector


class CartesianGrid(object):

    def __init__(self, origin, delta, size):
        self._origin = Vector(origin)
        self._delta = Vector(delta)
        self._size = Vector(size)

    def __iter__(self):
        for i in range(self.num_vertices):
            yield self.vertex(i)

    def __len__(self):
        return self.num_vertices

    @property
    def num_vertices(self):
        return self._size.prod()

    def vertex(self, index):

        z = index / (self._size[0] * self._size[1])
        y = (index / self._size[0]) % self._size[1]
        x = index % self._size[0]

        return Vector((self._origin[0] + x * self._delta[0],
                       self._origin[1] + y * self._delta[1],
                       self._origin[2] + z * self._delta[2]))
