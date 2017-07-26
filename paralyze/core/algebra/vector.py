# -*- coding: utf-8 -*-
"""Module documentation goes here ...

"""
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

    Pattern = r"(?P<value><{0},{0},{0}>)".format(Parsable.Decimal)

    def __new__(cls, value=0, dtype=np.float64):
        if isinstance(value, str):
            value = ''.join(value.split())
            if re.match(Vector.Pattern, value):
                value = tuple(map(float, value.replace('<', '').replace('>', '').split(',')))
            else:
                raise ValueError('Given argument {} is not a valid Vector str'.format(value))
        elif not hasattr(value, '__len__'):
            value = (value, value, value)
        elif len(value) != 3:
            raise TypeError('Vector cannot be initialized with: {}'.format(value))
        return np.asarray(value, dtype=dtype).view(cls)

    def __array_wrap__(self, out_arr, context=None):
        if out_arr.ndim == 0:  # a single scalar
            return out_arr.item()
        return np.ndarray.__array_wrap__(self, out_arr, context)

    def __eq__(self, other):
        # Do not use (self == other).all() here because that will lead to
        # infinite recursion!
        return np.array_equal(self, other)

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return '<{},{},{}>'.format(self.x, self.y, self.z)

    def __unicode__(self):
        return str(self)

    def __repr__(self):
        return 'Vector(({},{},{}))'.format(self.x, self.y, self.z)

    @property
    def x(self):
        return self[0]

    @x.setter
    def x(self, x):
        self[0] = x

    @property
    def y(self):
        return self[1]

    @y.setter
    def y(self, y):
        self[1] = y

    @property
    def z(self):
        return self[2]

    @z.setter
    def z(self, z):
        self[2] = z

    @property
    def length(self):
        return np.linalg.norm(self)

    def angle(self, other):
        """Returns the angle to *other* in radians.

        Parameters
        ----------
        other: Vector
            The vector to which the angle to should be calculated.

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

    def update(self, **kwargs):
        """Updates vector components.

        Parameters
        ----------
        kwargs: dict
            Valid arguments are: x, y, and z.

        """
        if "x" in kwargs:
            self.x = kwargs["x"]
        if "y" in kwargs:
            self.y = kwargs["y"]
        if "z" in kwargs:
            self.z = kwargs["z"]

    @staticmethod
    def x_axis():
        return Vector((1, 0, 0))

    @staticmethod
    def y_axis():
        return Vector((0, 1, 0))

    @staticmethod
    def z_axis():
        return Vector((0, 0, 1))
