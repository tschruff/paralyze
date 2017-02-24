from .cell import Cell, CellInterval

import numpy as np


class Field(object):

    def __init__(self, size, dtype, ghost_level=0, init=0):
        self._gl = ghost_level
        self._ci = CellInterval(Cell(0), size - Cell(1))
        self._ci = self._ci.extended(self._gl)
        self._data = np.full(self._ci.size, init, dtype)

    def __setitem__(self, index, value):
        if isinstance(index, Cell):
            index += Cell(self._gl)
            self._data[index[0], index[1], index[2]] = value
        if isinstance(index, CellInterval):
            index = index.shifted(self._gl)
            self._data[index.min.x:index.max.x + 1, index.min.y:index.max.y + 1, index.min.z:index.max.z + 1] = value

    def __getitem__(self, index):
        if isinstance(index, Cell):
            index += Cell(self._gl)
            return self._data[index[0], index[1], index[2]]
        if isinstance(index, CellInterval):
            index = index.shifted(self._gl)
            return self._data[index.min.x:index.max.x + 1, index.min.y:index.max.y + 1, index.min.z:index.max.z + 1]

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

    def iterGhostLayerXYZ(self):
        pass

    def iterXYZ(self):
        pass

    @property
    def size(self):
        return self._ci.size

    @property
    def shape(self):
        return self._data.shape
