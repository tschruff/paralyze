
class Ray(object):

    def __init__(self, origin, direction):
        self._origin = origin
        self._direction = direction.normalized()

    def at(self, t):
        return self.origin + self.direction * t

    @property
    def direction(self):
        return self._direction

    @property
    def origin(self):
        return self._origin
