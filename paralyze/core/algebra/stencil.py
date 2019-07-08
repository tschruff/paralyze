from paralyze.core.fields.cell_interval import CellInterval
import numpy as np


class Stencil(object):
    Dirs = []

    def __iter__(self):
        return iter(self.Dirs)


class D2Q4(Stencil):
    Dirs = [(1, 0), (0, 1), (-1, 0), (0, -1)]


class D3Q6(Stencil):
    Dirs = [(1, 0, 0), (0, 1, 0), (0, 0, 1),
            (-1, 0, 0), (0, -1, 0), (0, 0, -1)]
