from ..parsable import Parsable
from .vector import Vector

import numpy as np
import itertools


class AABB(Parsable):
    """ Implements an *immutable* half-open interval (min corner is included, max corner is excluded)

    """

    # re pattern that matches a valid AABB object (whitespaces removed)
    Pattern = r"\[(?P<min_corner><{0},{0},{0}>),(?P<max_corner><{0},{0},{0}>)\]".format(Parsable.Decimal)

    def __init__(self, min_corner=(0, 0, 0), max_corner=None, dtype=np.float64):
        self._dtype = np.dtype(dtype)
        self._min = Vector(min_corner, dtype=dtype)
        max_corner = max_corner if max_corner is not None else min_corner
        self._max = Vector(max_corner, dtype=dtype)

    def __contains__(self, item):
        return self.contains(item)

    def __ne__(self, other):
        return not self == other

    def __eq__(self, other):
        return self.min == other.min and self.max == other.max

    def __repr__(self):
        return 'AABB({!s},{!s})'.format(self.min, self.max)

    def __str__(self):
        return '[{!s},{!s}]'.format(self.min, self.max)

    @property
    def dtype(self):
        return self._dtype

    @property
    def center(self):
        return (self.min + self.max) / 2.0

    @property
    def min(self):
        return self._min

    @min.setter
    def min(self, min_corner):
        self._min = Vector(min_corner)

    @property
    def max(self):
        return self._max

    @max.setter
    def max(self, max_corner):
        self._max = Vector(max_corner)

    @property
    def size(self):
        return self.max - self.min

    @property
    def volume(self):
        return self.size.prod()

    def is_empty(self):
        """ An AABB is considered empty if the min and max corner are equal

        Returns
        -------
        result: bool
            A bool indicating whether the AABB is considered empty.
        """
        return self.min == self.max

    def is_valid(self):
        """ An AABB is considered valid if all three size components are greater or equal to zero.

        Returns
        -------
        result: bool
            A bool indicating whether the AABB is considered valid.
        """
        return self.size[0] >= 0 and self.size[1] >= 0 and self.size[2] >= 0

    def contains(self, item):
        """ Tests whether a given *item* is contained in the AABB.

        Parameters
        ----------
        item: AABB or Vector
            The item to test whether it is contained in the AABB

        Returns
        -------
        result: bool
            The result of the test

        Notes
        -----
        The AABB implements a half-open interval of the 3D space according to [min_corner, max_corner)
        That means the min_corner is included and the max_corner is not included in the interval.

        Examples
        --------
        >>> domain = AABB(max_corner=(100, 100, 100))
        >>> p1 = Vector((0, 0, 0))
        >>> domain.contains(p1)
        True
        >>> domain.contains(100)
        False
        >>> domain.contains((99, 99, 99))
        True
        >>> other = AABB((50, 50, 50), (100, 100, 100))
        >>> domain.contains(other)
        False
        >>> domain.contains(domain)
        False
        """
        if isinstance(item, AABB):
            return (self.min[0] <= item.min[0] and self.min[1] <= item.min[1] and self.min[2] <= item.min[2]) and\
                   (item.max[0] < self.max[0] and item.max[1] < self.max[1] and item.max[2] < self.max[2])

        item = Vector(item)
        return (self.min[0] <= item.x and self.min[1] <= item.y and self.min[2] <= item.z) and\
               (item.x < self.max[0] and item.y < self.max[1] and item.z < self.max[2])

    def intersection(self, other):
        """ Calculates and returns the intersect between this AABB instance and another or None
        if AABBs do not intersect.

        Parameters
        ----------
        other: AABB
            Another AABB instance to build the intersect with

        Returns
        -------
        intersection: AABB or None
            The intersection AABB or None if *self* and *other* do not intersect
        """
        if self.intersects(other):
            return AABB(np.maximum(self.min, other.min), np.minimum(self.max, other.max))
        return None

    def intersects(self, other):
        """ Determines whether *self* and *other* intersect, i.e. share a common part of the 3D space.

        Parameters
        ----------
        other: AABB
            Another AABB instance to check for intersection with

        Returns
        -------
        intersects: bool
            The result of the intersection test

        Notes
        -----
        This method will return False if one of both AABBs is empty.

        Examples
        --------
        The following examples are provided to clarify how the method works.
        >>> first = AABB((0, 0, 0), (10, 10, 10))
        >>> second = AABB((5, 5, 5), (15, 15, 15))
        >>> first.intersects(second)
        True
        >>> third = AABB((10, 10, 10), (15, 15, 15))
        >>> first.intersects(third)
        False
        >>> second.intersects(third)
        True
        """
        assert isinstance(other, AABB)
        if self.is_empty() or other.is_empty():
            return False

        return other.max[0] > self.min[0] and other.min[0] < self.max[0] and \
            other.max[1] > self.min[1] and other.min[1] < self.max[1] and \
            other.max[2] > self.min[2] and other.min[2] < self.max[2]

    def merged(self, other):
        assert isinstance(other, AABB)
        return AABB(np.minimum(self.min, other.min), np.maximum(self.max, other.max))

    def scaled(self, factor):
        return AABB(self.min * factor, self.max * factor, self.min.dtype)

    def shifted(self, delta):
        return AABB(self.min + delta, self.max + delta, self.min.dtype)

    def slices(self, axis, num_slices):
        return list([s for s in self.iter_slices(axis, num_slices)])

    def iter_slices(self, axis, num_slices, reverse=False):
        """ Iterates over slices along the specified axis.

        Parameters
        ----------
        axis: int or str
            The axis along which the slices should be created.
            Axis must be either in [0, 1, 2] or ['x', 'y', 'z']
            depending on whether it is an int or str.

        num_slices: int >= 1
            The number of slices that should be created

        reverse: bool
            Determines whether the slices are returned in ascending or descending order along specified axis

        Returns
        -------
        slice: iterator
            The next slice
        """
        if isinstance(axis, str) and axis in ['x', 'y', 'z']:
            axis = ['x', 'y', 'z'].index(axis)
        elif not isinstance(axis, int) or axis not in [0, 1, 2]:
            raise TypeError('Unexpected axis type/value: %s' % str(axis))

        ds = self.size[axis] / num_slices

        for i in range(num_slices):
            slice_min = self.min.copy()
            slice_max = self.max.copy()

            if reverse:
                slice_max[axis] -= i * ds
                slice_min[axis] = slice_max[axis] - ds
            else:
                slice_min[axis] += i * ds
                slice_max[axis] = slice_min[axis] + ds

            yield AABB(slice_min, slice_max)

    def subs(self, level=1):
        """ Returns a list of all octree sub elements for the given depth.

        Parameters
        ----------
        level: int >= 1
            The octree depth level

        Returns
        -------
        subs: list
            The list of all octree sub elements
        """
        return list([s for s in self.iter_subs(level)])

    def iter_subs(self, level=1):
        """ Iterates over all octree sub elements for the given depth.

        Parameters
        ----------
        level: int >= 1
            The octree depth level

        Returns
        -------
        sub: iterator
            The next octree sub element
        """
        if not isinstance(level, int):
            raise TypeError('level argument must be an int >= 1')
        if level < 1:
            raise ValueError('level argument must be >= 1')

        factor = 2**level
        d = self.size / factor
        for i in itertools.product(range(factor), repeat=3):
            delta = np.multiply(i, d)
            yield AABB(self.min + delta, self.min + delta + d)

    def update(self, **kwargs):
        """

        """

        if "min" in kwargs:
            self.min = kwargs["min"]
        else:
            if "x_min" in kwargs:
                self.min.x = kwargs["x_min"]
            if "y_min" in kwargs:
                self.min.y = kwargs["y_min"]
            if "z_min" in kwargs:
                self.min.z = kwargs["z_min"]

        if "max" in kwargs:
            self.max = kwargs["max"]
        else:
            if "x_max" in kwargs:
                self.min.x = kwargs["x_max"]
            if "y_max" in kwargs:
                self.min.y = kwargs["y_max"]
            if "z_max" in kwargs:
                self.min.z = kwargs["z_max"]
