from ..parsable import Parsable
from .vector import Vector

import numpy as np


class AABB(Parsable):
    """ Implements a half-open interval (min corner is included, max corner is excluded)

    """

    # re pattern that matches a valid AABB object (whitespaces removed)
    Pattern = r"\A\[(?P<min_corner><{0},{0},{0}>),(?P<max_corner><{0},{0},{0}>)\]\Z".format(Parsable.Decimal)

    def __init__(self, min_corner=(0, 0, 0), max_corner=None):
        if max_corner is None:
            max_corner = min_corner

        self._min = Vector(min_corner)
        self._max = Vector(max_corner)

        assert self.is_valid(), '{!r} is not valid'.format(self)

    def __contains__(self, item):
        return self.contains(item)

    def __ne__(self, other):
        return not self == other

    def __eq__(self, other):
        return self.min == other.min and self.max == other.max

    def __repr__(self):
        return 'AABB({!s}, {!s})'.format(self.min, self.max)

    def __str__(self):
        return '[{!s}, {!s}]'.format(self.min, self.max)

    @property
    def center(self):
        return (self.min + self.max) / 2.0

    def contains(self, item):
        if isinstance(item, AABB):
            return (self.min[0] <= item.min[0] and self.min[1] <= item.min[1] and self.min[2] <= item.min[2]) and\
                   (item.max[0] < self.max[0] and item.max[1] < self.max[1] and item.max[2] < self.max[2])
        if isinstance(item, Vector):
            return (self.min[0] <= item.x and self.min[1] <= item.y and self.min[2] <= item.z) and\
                   (item.x < self.max[0] and item.y < self.max[1] and item.z < self.max[2])
        raise TypeError('Unsupported type %s' % type(item))

    def create_slices(self, axis, num_slices):
        if isinstance(axis, str) and axis in ['x', 'y', 'z']:
            axis = ['x', 'y', 'z'].index(axis)
        elif not isinstance(axis, int) or axis not in [0, 1, 2]:
            raise TypeError('Unexpected axis type')

        ds = self.size[axis] / num_slices

        slices = []
        for i in range(num_slices):
            slice_min = self.min.copy()
            slice_max = self.max.copy()

            slice_min[axis] += i * ds
            slice_max[axis] = slice_min[axis] + ds

            slices.append(AABB(slice_min, slice_max))

        return slices

    def intersect(self, other):
        return AABB(np.maximum(self.min, other.min), np.minimum(self.max, other.max))

    def intersects(self, other):
        assert isinstance(other, AABB)
        if self.is_empty() and other.is_empty():
            return False

        return other.max[0] > self.min[0] and other.min[0] < self.max[0] and \
               other.max[1] > self.min[1] and other.min[1] < self.max[1] and \
               other.max[2] > self.min[2] and other.min[2] < self.max[2]

    def is_empty(self):
        """ An AABB is considered empty if the min and max corner are equal

        :return: Returns a bool indicating whether the AABB is considered empty.
        """
        return self.min == self.max

    def is_valid(self):
        """ An AABB is considered valid if all three size components are greater or equal to zero.

        :return: Returns a bool indicating whether the AABB is considered valid.
        """
        return self.size[0] >= 0 and self.size[1] >= 0 and self.size[2] >= 0

    def iter_slices(self, axis, num_slices, reverse=False):
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

    def merged(self, other):
        assert isinstance(other, AABB)
        return AABB(np.minimum(self.min, other.min), np.maximum(self.max, other.max))

    def shifted(self, delta):
        return AABB(self.min + delta, self.max + delta)

    @property
    def min(self):
        return self._min

    @property
    def max(self):
        return self._max

    @property
    def size(self):
        return self.max - self.min

    @property
    def volume(self):
        return np.prod(self.size)

