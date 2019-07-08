from ..parsable import Parsable
from .vector import Vector

import numpy as np
import itertools


class AABB(np.ndarray, Parsable):
    """Implements a half-open interval in 3D space, i.e. the ``min_corner`` is
    included and the ```max_corner`` is excluded.

    """

    # re pattern that matches a valid AABB object (whitespaces removed)
    Pattern = r"\[(?P<min_corner><{0},{0},{0}>),(?P<max_corner><{0},{0},{0}>)\]".format(Parsable.Decimal)

    def __new__(cls, min_corner=0, max_corner=None, dtype=None):
        min_corner = Vector(min_corner, dtype=dtype)
        max_corner = Vector(max_corner, dtype=dtype) if max_corner is not None else min_corner
        return np.asarray(np.concatenate((min_corner, max_corner)), dtype=dtype).view(cls)

    def __array_wrap__(self, out_arr, context=None):
        if out_arr.ndim == 0:  # a single scalar
            return out_arr.item()
        return np.ndarray.__array_wrap__(self, out_arr, context)

    def __contains__(self, item):
        return self.contains(item)

    def __ne__(self, other):
        return not self == other

    def __eq__(self, other):
        return self.min == other.min and self.max == other.max

    def __and__(self, other):
        return self.intersection(other)

    def __iand__(self, other):
        self = self.intersection(other)

    def __or__(self, other):
        return self.merged(other)

    def __ior__(self, other):
        self = self.merged(other)

    def __repr__(self):
        return 'AABB(min_corner={!r},max_corner={!r}, dtype={!r})'.format(self.min, self.max, self.dtype)

    def __str__(self):
        return '[{!s},{!s}]'.format(self.min, self.max)

    @property
    def center(self):
        return (self.min + self.max) / 2.0

    @property
    def min(self):
        """The min (low left) corner of the AABB as a Vector.
        """
        return self[:3].view(Vector)

    @min.setter
    def min(self, min_corner):
        self[:3] = Vector(min_corner)

    @property
    def max(self):
        """The max (top right) corner of the AABB as a Vector.
        """
        return self[3:].view(Vector)

    @max.setter
    def max(self, max_corner):
        self[3:] = Vector(max_corner)

    @property
    def size(self):
        """Returns the size of the AABB, i.e. the length along all three axes.
        """
        return self.max - self.min

    @property
    def volume(self):
        """Returns the volume of the AABB, i.e. the product of its size components.
        """
        size = self.size
        return size[0] * size[1] * size[2]

    def is_empty(self):
        """Returns the empy state of the AABB.

        An AABB is considered empty if the min and max corner are equal.

        Returns
        -------
        result: bool
            A bool indicating whether the AABB is considered empty.
        """
        return self.min == self.max

    def is_valid(self):
        """Returns the validity of the AABB.

        An AABB is considered valid if all three size components are greater
        or equal to zero.

        Returns
        -------
        bool:
            A bool indicating whether the AABB is considered valid.
        """
        return self.size[0] >= 0 and self.size[1] >= 0 and self.size[2] >= 0

    def contains(self, item):
        """Tests whether a given *item* is contained in the AABB.

        Parameters
        ----------
        item: array-like
            If item is an array with shape (3,) it is treated as a position vector.
            If item is an array with shape (6,) it is treated as an AABB. Further,
            item may be an array of position vectors or AABBs, i.e. have the shape
            (n, 3) or (n, 6) respectively.

        Returns
        -------
        result: bool or array of booleans
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
        shape = np.shape(item)
        if len(shape) == 1:
            if shape[0] == 3:
                return self.contains_point(item)
            if shape[0] == 6:
                return self.contains_other(item)
        if len(shape) == 2: # item is an array of AABBs or Vectors
            if shape[1] == 3:
                return self.contains_point(item)
            if shape[2] == 6:
                return self.contains_other(item)
        raise TypeError("Unsupported item shape %r" % shape)

    def contains_other(self, aabb):
        shape = np.shape(aabb)
        if len(shape) == 1:
            return np.all(self.min <= aabb[:3]) and np.all(aabb[3:] < self.max)
        if len(shape) == 2:
            return np.all(self.min <= aabb[:, :3], axis=1) & np.all(aabb[:, 3:] < self.max, axis=1)

    def contains_point(self, point):
        shape = np.shape(point)
        if len(shape) == 1:
            return np.all(self.min <= point) and np.all(point < self.max)
        if len(shape) == 2:
            return np.all(self.min <= point, axis=1) & np.all(point < self.max, axis=1)

    def intersection(self, other):
        """Calculates and returns the intersect between this AABB instance and
        ``other`` or ``None`` if they do not intersect.

        Parameters
        ----------
        other: AABB
            Another AABB instance to build the intersect with.

        Returns
        -------
        AABB or None:
            The intersection AABB or ``None`` if ``self`` and ``other`` do not
            intersect.
        """
        if self.intersects(other):
            return AABB(np.maximum(self.min, other.min), np.minimum(self.max, other.max))
        return None

    def intersects(self, other):
        """Determines whether ``self`` and ``other`` intersect, i.e. share a
        common portion of space.

        Parameters
        ----------
        other: AABB
            Another AABB instance to check for intersection with

        Returns
        -------
        bool:
            The result of the intersection test

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
        return (other.max > self.min).all() and (other.min < self.max).all()

    def merged(self, other):
        """Returns a new AABB that is the result of merging ``self`` and ``other``.

        Parameters
        ----------
        other: AABB
            The AABB to merge ``self`` with.

        Returns
        -------
        AABB:
            The new AABB that is the result of the merging.
        """
        return AABB(np.minimum(self.min, other.min), np.maximum(self.max, other.max))

    def scaled(self, factor):
        return AABB(self.min * factor, self.max * factor)

    def shifted(self, delta):
        return AABB(self.min + delta, self.max + delta)

    def slices(self, axis, num_slices, reverse=False):
        return list([s for s in self.iter_slices(axis, num_slices, reverse)])

    def iter_slices(self, axis, num_slices, reverse=False):
        """Iterates over slices along the specified axis.

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
        iterator:
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
        list:
            The list of all octree sub elements
        """
        return [s for s in self.iter_subs(level)]

    def iter_subs(self, level=1):
        """Iterates over all octree sub elements for the given depth.

        Parameters
        ----------
        level: int >= 1
            The octree depth level

        Returns
        -------
        iterator:
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
        """Update the corner coordinates.
        """
        if 'min' in kwargs:
            self.min = kwargs['min']
        else:
            if "x_min" in kwargs:
                self.min.x = kwargs["x_min"]
            if "y_min" in kwargs:
                self.min.y = kwargs["y_min"]
            if "z_min" in kwargs:
                self.min.z = kwargs["z_min"]

        if 'max' in kwargs:
            self.max = kwargs['max']
        else:
            if "x_max" in kwargs:
                self.min.x = kwargs["x_max"]
            if "y_max" in kwargs:
                self.min.y = kwargs["y_max"]
            if "z_max" in kwargs:
                self.min.z = kwargs["z_max"]

    @staticmethod
    def inf(dtype=np.float64):
        return AABB(-np.inf, np.inf, dtype=dtype)
