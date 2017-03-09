from .body import Body

import math


class Capsule(Body):

    def __init__(self, start, end, radius=1, **kwargs):
        Body.__init__(self, (start+end)/2, **kwargs)
        assert radius > 0
        self._r = radius
        self._start = start
        self._end = end
        self._l = start.dist(end)
        self._rot = (end-start).angle()
        self._v = 4/3.0 * math.pi * self._r ** 3 + math.pi * self._r ** 2 * self._l

    def __str__(self):
        return 'Capsule(id=%s, center=%s, radius=%f, length=%f)' % (self.id(), self.position(), self._r, self._l)

    def contains(self, point):
        pass

    def length(self):
        return self._l

    def radius(self):
        return self._r

    def start(self):
        """ Returns the start point of axis vector.

        :return:
        """
        return self._start

    def end(self):
        """ Returns the end point of the axis vector.

        :return:
        """
        return self._end
