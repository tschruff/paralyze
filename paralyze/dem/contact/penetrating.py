from .penetration import penetration_depth


class Penetrating(object):

    Threshold = -1.0E-5  # [m]

    def __init__(self, body0, body1):
        self._b0 = body0
        self._b1 = body1

        self._pos, self._normal, self._p = self._compute_penetration()

    def __bool__(self):
        return self._p > Penetrating.Threshold

    def b0(self):
        return self._b0

    def b1(self):
        return self._b1

    def p(self):
        return self._p

    def pos(self):
        return self._pos

    def normal(self):
        pass

    def _compute_penetration(self):
        if not self._b0.domain().intersects(self._b1.domain()):
            return -float('inf')
        return penetration_depth(self._b0, self._b1)
