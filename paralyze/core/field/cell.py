import numpy as np


class Cell(np.ndarray):

    def __new__(cls, c):
        if not hasattr(c, '__len__'):
            c = (c, c, c)
        return np.asarray(c, np.int64).view(cls)

    def __eq__(self, other):
        return np.array_equal(self, other)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return 'Cell([{c[0]:d}, {c[1]:d}, {c[2]:d}])'.format(c=self)

    def __str__(self):
        return '({c[0]:d}, {c[1]:d}, {c[2]:d})'.format(c=self)

    @property
    def x(self):
        return self[0]

    @property
    def y(self):
        return self[1]

    @property
    def z(self):
        return self[2]


class CellInterval(object):

    def __init__(self, min_cell=(0, 0, 0), max_cell=None):
        if max_cell is None:
            max_cell = min_cell

        self._min = Cell(min_cell)
        self._max = Cell(max_cell)

        assert self.is_valid(), '%s is not a valid cell interval' % self

    def __eq__(self, other):
        return self.min == other.min and self.max == other.max

    def __ne__(self, other):
        return not self == other

    def __len__(self):
        return self.numCells

    def __contains__(self, item):
        return self.contains(item)

    def __iter__(self):
        for z in range(self.size.z):
            for y in range(self.size.y):
                for x in range(self.size.x):
                    yield self.min + Cell((x, y, z))

    def __repr__(self):
        return 'CellInterval({!s}, {!s})'.format(self.min, self.max)

    def __str__(self):
        return '[{!s} ... {!s}]'.format(self.min, self.max)

    def contains(self, item):
        if isinstance(item, Cell):
            return self.min <= item <= self.max
        if isinstance(item, CellInterval):
            return self.contains(item.min) and self.contains(item.max)
        raise TypeError('Unsupported type')

    def extended(self, delta):
        delta = Cell(delta)
        return CellInterval(self.min - delta, self.max + delta)

    def intersect(self, other):
        return CellInterval(np.maximum(self.min, other.min), np.minimum(self.max, other.max))

    def is_valid(self):
        return self.max.x >= self.min.x and self.max.y >= self.min.y and self.max.z >= self.min.z

    def merged(self, other):
        return CellInterval(np.minimum(self.min, other.min), np.maximum(self.max, other.max))

    @property
    def min(self):
        return self._min

    @property
    def max(self):
        return self._max

    @property
    def numCells(self):
        return self.size.prod()

    @property
    def size(self):
        return (self.max - self.min) + Cell(1)

    def shifted(self, cell):
        return CellInterval(self.min + cell, self.max + cell)