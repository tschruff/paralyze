from ..parsable import Parsable

import numpy as np
import re


class Vector(np.ndarray, Parsable):
    """ The Vector class represents a 3D vector.

    >>> v = Vector("<-inf, .45, 34.5>")
    Vector((-inf, 0.45, 34.5))
    >>> v = Vector(3)
    Vector((3, 3, 3))
    >>> v = Vector((1, 2, 1))
    Vector((1, 2, 1))

    """

    Pattern = r"\A(?P<value><{0},{0},{0}>)\Z".format(Parsable.Decimal)

    def __new__(cls, value):
        if isinstance(value, str):
            value = ''.join(value.split())
            if re.match(Vector.Pattern, value):
                value = tuple(map(float, value.replace('<', '').replace('>', '').split(',')))
            else:
                raise ValueError('Given argument {} is not a valid Vector str'.format(value))
        elif not hasattr(value, '__len__'):
            value = (value, value, value)
        elif len(value) != 3:
            raise IndexError('Vector can only be initialized with a str, a single number or a 3D tuple/list')
        return np.asarray(value).view(cls)

    def __len__(self):
        return 3

    def __eq__(self, other):
        return np.array_equal(self, other)

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return '<{:f},{:f},{:f}>'.format(self[0], self[1], self[2])

    def __repr__(self):
        return 'Vector(({:f},{:f},{:f}))'.format(self[0], self[1], self[2])

    @property
    def x(self):
        return self[0]

    @property
    def y(self):
        return self[1]

    @property
    def z(self):
        return self[2]

    @property
    def length(self):
        return np.linalg.norm(self)

    def angle(self, other):
        """ Returns the angle to *other* in radians.

        Parameters
        ----------
        other: Vector
            The vector to which the angle to should be determined

        Returns
        -------
        angle: float
            The angle in radians.

        Examples
        --------
        >>> v = Vector((1, 0, 0))
        >>> v.angle((0, 1, 0))
        1.5707963267948966
        >>> v.angle((1, 0, 0))
        0.0
        >>> v.angle((-1, 0, 0))
        3.141592653589793
        """
        if not isinstance(other, Vector):
            other = Vector(other)
        return np.arccos(np.clip(np.dot(self.normalized(), other.normalized()), -1.0, 1.0))

    def dist(self, other):
        """ Returns the distance of *self* to *other*.

        Parameters
        ----------
        other: Vector
            The vector to which the distance should be determined

        Returns
        -------
        dist: float
            The distance to *other*
        """
        return np.linalg.norm(self - other)

    def normalized(self):
        return self / self.length

    def sqr_length(self):
        return np.dot(self, self)
