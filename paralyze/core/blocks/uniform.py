import itertools
import math
import multiprocessing as mp

import numpy as np

from paralyze.core.algebra import AABB, Vector
from paralyze.core.blocks import Block, BlockStorage
from paralyze.core.bodies import BodyStorage
from paralyze.core.fields import Cell, CellInterval, Field
from paralyze.core.algebra.factorization import factors


class UniformBlock(Block):

    def __init__(self, block_id, cell_interval, domain):
        Block.__init__(self, block_id, cell_interval, domain)


class UniformBlockStorage(BlockStorage):

    def __init__(self, cells, num_blocks=mp.cpu_count(), dx=1, periodicity=(False, False, False), origin=(0, 0, 0)):
        BlockStorage.__init__(self, periodicity=periodicity, origin=origin, resolution=float(dx))

        assert hasattr(cells, '__len__') and len(cells) == 3

        # "cells" is in global coordinates
        if type(num_blocks) is int:
            self._numBlocks = factors(num_blocks, 3, cells)
            self._cellsPerBlock = np.array(([math.ceil(c/n) for c, n in zip(cells, self._numBlocks)]))
        # "cells" is in block coordinates (cells per block)
        elif hasattr(num_blocks, '__len__') and len(num_blocks) == 3:
            self._numBlocks = np.array(num_blocks)
            self._cellsPerBlock = np.array(cells)
        # "cells" is not valid
        else:
            raise TypeError('numBlocks must be either an "int" or a 3D tuple/list')

        self._np = self._numBlocks.prod()

        self._ci = CellInterval(0, self._numBlocks * self._cellsPerBlock - np.array([1, 1, 1]))
        self._domain = AABB(self._origin, self._origin + self.dx() * self._ci.size)

        self._setup_blocks()

    def cell(self, pos):
        pos = pos - self.origin()
        return Cell(pos // self.dx())

    def cellCenter(self, global_cell):
        return self._origin + (Vector(global_cell) + Vector(0.5)) * self._resolution

    def dx(self):
        return self._resolution

    def numBlocks(self):
        return self._numBlocks

    def numCells(self):
        return self._cellsPerBlock * self._numBlocks

    def map_domain_to_cell_interval(self, domain, block_id=None):
        c_min = Cell((domain.min-self.origin()) // self.resolution())
        c_max = Cell((domain.max-self.origin()) // self.resolution())
        return self.cell_interval(block_id).intersection(CellInterval(c_min, c_max))

    def update(self, blocks):
        pass

    def synchFields(self, reduce_op):
        for fieldId in self._fieldIds:
            # iter over all ghost regions along all three axes
            # and update ghost layer cells according to given reduce_op
            pass

    def _setup_blocks(self):
        self._cellBBs = []
        self._blocks = []
        self._domains = []
        self._ids = []

        cpb = self._cellsPerBlock
        lci = CellInterval(0, cpb - Cell(1))
        for x, y, z in itertools.product(*map(range, self._numBlocks)):
            co = np.array([x, y, z]) * cpb

            global_cell_interval = CellInterval(co, co + cpb - Cell(1))
            global_domain = AABB(self.origin() + co * self.dx(), self.origin() + (co + cpb) * self.dx())

            self._cellBBs.append(global_cell_interval)
            self._blocks.append(UniformBlock(len(self._blocks), lci, global_domain))
            self._domains.append(global_domain)
