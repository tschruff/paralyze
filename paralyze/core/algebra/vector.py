import numpy as np


class Vector(np.ndarray):
    """ The Vector class represents a 3D vector.

    >>> v = Vector(3)
    Vector(3, 3, 3)
    >>> v = Vector((1, 2, 1))
    Vector(1, 2, 1)

    """

    def __new__(cls, v):
        if not hasattr(v, '__len__'):
            v = (v, v, v)
        elif len(v) != 3:
            raise IndexError('Vector can only be initialized with a number of a 3D tuple/list')
        return np.asarray(v).view(cls)

    def __len__(self):
        return 3

    def __eq__(self, other):
        return np.array_equal(self, other)

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return '<{:f}, {:f}, {:f}>'.format(self.x, self.y, self.z)

    def __repr__(self):
        return 'Vector(({:f}, {:f}, {:f}))'.format(self.x, self.y, self.z)

    def angle_to(self, other):
        """ Returns the angle in radians to vector 'other'.

        >>> v = Vector((1, 0, 0))
        >>> v.angle_to((0, 1, 0))
        1.5707963267948966
        >>> v.angle_to((1, 0, 0))
        0.0
        >>> v.angle_to((-1, 0, 0))
        3.141592653589793

        :param other: The vector to which the angle to should be determined.
        """
        if not isinstance(other, Vector):
            other = Vector(other)
        return np.arccos(np.clip(np.dot(self.normalized(), other.normalized()), -1.0, 1.0))

    def dist(self, other):
        """

        :param other:
        :return:
        """
        return np.linalg.norm(self - other)

    def length(self):
        return np.linalg.norm(self)

    def normalized(self):
        return self / self.length()

    @staticmethod
    def parse(string):
        # remove all kinds of whitespaces
        string = ''.join(string.split())
        if string[0] != '<' or string[-1] != '>':
            raise ValueError('Invalid Vector string')

        string = string.replace('<', '').replace('>', '')
        values = string.split(',')

        if len(values) != 3:
            raise ValueError('Invalid Vector string')

        values = tuple(map(float, values))
        return Vector(values)

    def sqr_length(self):
        return np.dot(self, self)

    @property
    def x(self):
        return self[0]

    @property
    def y(self):
        return self[1]

    @property
    def z(self):
        return self[2]
