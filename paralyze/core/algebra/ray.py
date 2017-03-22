from .vector import Vector


class Ray(object):

    def __init__(self, origin, direction):
        self._origin = Vector(origin)
        self._direction = Vector(direction).normalized()

    def at(self, t):
        return self.origin + self.direction * t

    @property
    def direction(self):
        return self._direction

    @property
    def origin(self):
        return self._origin

    @staticmethod
    def x_axis():
        return Ray(0, Vector.x_axis())

    @staticmethod
    def y_axis():
        return Ray(0, Vector.y_axis())

    @staticmethod
    def z_axis():
        return Ray(0, Vector.z_axis())
