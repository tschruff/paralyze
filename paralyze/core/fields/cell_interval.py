from .cell import Cell
from ..parsable import Parsable

import numpy as np


class CellInterval(Parsable):
    """Represents an *immutable* interval of cells within the given min and max.
    The min and max cells are included!
    """

    Pattern = r"\A\[(?P<min_cell>\({0},{0},{0}\))\.\.\.(?P<max_cell>\({0},{0},{0}\))\]\Z".format(Parsable.Integer)

    def __init__(self, min_cell=(0, 0, 0), max_cell=None):
        max_cell = max_cell or min_cell
        self._min = Cell(min_cell)
        self._max = Cell(max_cell)

    def __sub__(self, other):
        """Returns the set of cells that is the difference (in terms of set theory) between self and other.

        :param other:
        :return:
        """
        diff = self.intersection(other)
        if not diff:  # self and other do not intersect
            return self
        return set([cell for cell in self if cell not in diff])

    def __eq__(self, other):
        return self.min == other.min and self.max == other.max

    def __ne__(self, other):
        return not self == other

    def __len__(self):
        return self.num_cells

    def __contains__(self, item):
        return self.contains(item)

    def __iter__(self):
        for z in range(self.size[2]):
            for y in range(self.size[1]):
                for x in range(self.size[0]):
                    yield self.min + Cell((x, y, z))

    def __repr__(self):
        return 'CellInterval({!s},{!s})'.format(self.min, self.max)

    def __str__(self):
        return '[{!s}...{!s}]'.format(self.min, self.max)

    @property
    def bounds(self):
        return self.min, self.max

    @property
    def min(self):
        return self._min

    @property
    def max(self):
        return self._max

    @property
    def num_cells(self):
        return self.size.prod()

    @property
    def size(self):
        return (self.max - self.min) + Cell(1)

    def is_valid(self):
        return self.max[0] >= self.min[0] and self.max[1] >= self.min[1] and self.max[2] >= self.min[2]

    def contains_cell(self, cell):
        return (self.min <= cell).all() and (cell <= self.max).all()

    def contains_other(self, other):
        return self.contains_cell(item.min) and self.contains_cell(item.max)

    def contains(self, item):
        if isinstance(item, Cell):
            return self.contains_cell(item)
        if isinstance(item, CellInterval):
            return self.contains_other(item)
        raise TypeError('Unsupported type')

    def expanded(self, delta):
        delta = Cell(delta)
        return CellInterval(self.min - delta, self.max + delta)

    def intersection(self, other):
        if not self.intersects(other):
            return None
        return CellInterval(np.maximum(self.min, other.min), np.minimum(self.max, other.max))

    def intersects(self, other):
        assert isinstance(other, CellInterval)
        return other.max[0] > self.min[0] and other.min[0] < self.max[0] and \
               other.max[1] > self.min[1] and other.min[1] < self.max[1] and \
               other.max[2] > self.min[2] and other.min[2] < self.max[2]

    def union(self, other):
        return CellInterval(np.minimum(self.min, other.min), np.maximum(self.max, other.max))

    def shifted(self, cell):
        return CellInterval(self.min + cell, self.max + cell)

    def slice(self, axis):
        assert axis in [0, 1, 2]
        return slice(self.min[axis], self.max[axis])

    @property
    def xslice(self):
        return self.slice(0)

    @property
    def yslice(self):
        return self.slice(1)

    @property
    def zslice(self):
        return self.slice(2)

    @property
    def slices(self):
        return self.xslice, self.yslice, self.zslice
