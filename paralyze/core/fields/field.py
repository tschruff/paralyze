from .cell import Cell
from .cell_interval import CellInterval

import numpy as np


class Field(object):
    """ The Field class wraps a numpy array and adds some features such as
    cell interval and ghost layers

    """

    def __init__(self, size, dtype, ghost_level=0, init=0):
        self._gl = ghost_level
        self._ci = CellInterval(Cell(0), size - Cell(1)).extended(self._gl)
        self._data = np.full(self._ci.size, init, dtype)

    def __setitem__(self, index, value):
        if isinstance(index, Cell):
            index += Cell(self._gl)
            self._data[index[0], index[1], index[2]] = value
        if isinstance(index, CellInterval):
            index = index.shifted(self._gl)
            self._data[index.min[0]:index.max[0]+1, index.min[1]:index.max[1]+1, index.min[2]:index.max[2]+1] = value
        else:
            self._data[index] = value

    def __getitem__(self, index):
        if isinstance(index, Cell):
            index += Cell(self._gl)
            return self._data[index[0], index[1], index[2]]
        if isinstance(index, CellInterval):
            index = index.shifted(self._gl)
            return self._data[index.min[0]:index.max[0]+1, index.min[1]:index.max[1]+1, index.min[2]:index.max[2]+1]
        else:
            return self._data[index]

    @property
    def cell_interval(self):
        return self._ci

    @property
    def data(self):
        return self._data

    @property
    def dtype(self):
        return self._data.dtype

    @property
    def ghost_level(self):
        return self._gl

    @property
    def num_cells(self):
        return self.size.prod()

    @property
    def size(self):
        return self._ci.size

    @property
    def shape(self):
        return self._data.shape

    @property
    def ghost_cells(self):
        return self._ci - self._ci.extended(-self._gl)

    def iter_ghost_layer_cells(self):
        return iter(self.ghost_cells)

    def iter_cells(self, include_gl=False):
        if not include_gl:
            return iter(self._ci.extended(-self._gl))
        return iter(self._ci)
