import itertools
import math
import multiprocessing as mp

import numpy as np

from PydroSquid.core.algebra import AABB, Vector
from PydroSquid.core.blocks import Block, BlockStorage
from PydroSquid.core.body import Bodies
from PydroSquid.core.field import Cell, CellInterval, Field
from core.algebra.factorization import factors


class UniformBlock(Block):

    def __init__(self, block_id, cell_interval, domain):
        Block.__init__(self, block_id)
        self._ci = cell_interval
        self._domain = domain

    def addField(self, identifier, dtype, ghost_level=0, init=0):
        """ Adds a new field with given parameters to the block.

        :param identifier: Unique field identifier.
        :param dtype: Numpy array dtype.
        :param ghost_level: Number of ghost layers.
        :param init: Initial field value.
        """
        self._data[identifier] = Field(self._ci.size, dtype, ghost_level, init)

    def addBodies(self, identifier, bodies, remove_pure_locals=True):
        """

        :param identifier:
        :param bodies: The set of bodies that will be added to the block
        :param remove_pure_locals: Whether to remove pure local bodies from the returned bodies
        :return: An updated set of bodies (bodies - pure local bodies)
        """
        bodies = Bodies(bodies)

        # create set of local body (body whose center belongs to the current block)
        local_bodies = bodies.subset(lambda body: self.domain().contains(body.center()))
        # create non-local set of body
        non_local_bodies = bodies.difference(local_bodies)

        shadows = set()
        for non_local in non_local_bodies:
            if self.domain().intersects(non_local.aabb()):
                # skip shadow copies from periodic mapping
                if non_local.is_shadow_copy():
                    shadows.add(non_local)
                else:
                    shadow = non_local.create_shadow_copy()
                    shadows.add(shadow)

        self._data[identifier] = Bodies(local_bodies | shadows)

        if remove_pure_locals:
            # create a set of pure-local bodies (bodies whose extent is fully contained in the block domain)
            pure_local_bodies = local_bodies.subset(lambda body: self.domain().contains(body.aabb()))
            # remove pure-local bodies from global list and return it
            bodies = bodies.difference(pure_local_bodies)

        return bodies

    def cellInterval(self):
        return self._ci

    def domain(self):
        return self._domain


class UniformBlockStorage(BlockStorage):

    def __init__(self, cells, num_blocks=mp.cpu_count(), dx=1, periodicity=(False, False, False), origin=(0, 0, 0)):
        BlockStorage.__init__(self)

        assert float(dx)
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
            raise TypeError('numBlocks must be either an "int" or a 3D tuple')

        self._np = self._numBlocks.prod()

        self._dx = Vector(dx)
        self._periodic = np.array(periodicity)
        self._origin = Vector(origin)
        self._cellBB = CellInterval(0, self._numBlocks * self._cellsPerBlock - np.array([1, 1, 1]))
        self._domain = AABB(self._origin, self._origin + self.dx() * self._cellBB.size)

        self._fieldIds = []

        self._setup_blocks()

    def addBodies(self, identifier, bodies):
        if self.has_data(identifier):
            raise ValueError('Bodies with identifier %s already exist!' % identifier)

        if self._periodic.any():
            mapped = set()
            for body in bodies:
                mapped = mapped.union(self.mapToPeriodicDomain(body))
            bodies = bodies.union(mapped)

        for block in self._blocks:
            bodies = block.addBodies(identifier, bodies)

        self._ids.append(identifier)

    def addField(self, identifier, dtype, ghost_level=0, init=0):
        if self.has_data(identifier):
            raise ValueError('Field with identifier %s already exists!' % identifier)
        for block in self._blocks:
            block.addField(identifier, dtype, ghost_level, init)

        self._ids.append(identifier)
        self._fieldIds.append(identifier)

    def cell(self, pos):
        pos = pos - self.origin()
        return Cell(pos // self.dx())

    def cellCenter(self, global_cell):
        return self._origin + (Vector(global_cell) + Vector(0.5)) * self._dx

    def clipToDomain(self, bodies, domain_filter='intersectsBoundingBox', block_id=None):
        domain = self.globalDomain(block_id)
        if domain_filter == 'intersectsBoundingBox':
            return bodies.subset(lambda body: domain.intersects(body.aabb()))
        if domain_filter == 'containsCenter':
            return bodies.subset(lambda body: domain.contains(body.center()))
        if domain_filter == 'containsBoundingBox':
            return bodies.subset(lambda body: domain.contains(body.aabb()))

    def dx(self):
        return self._dx

    def globalCellInterval(self, block_id=None):
        return self._cellBB if block_id is None else self._cellBBs[block_id]

    def globalDomain(self, block_id=None):
        return self._domain if block_id is None else self._domains[block_id]

    def isPeriodic(self, axis):
        return self._periodic[axis]

    def mapBlockLocalToGlobal(self, item, blockId):
        if isinstance(item, Cell):
            return self.globalCellInterval(blockId).min + item
        if isinstance(item, CellInterval):
            return item.shifted(self.globalCellInterval(blockId).min)
        if isinstance(item, Vector):
            return self.globalDomain(blockId).min + item
        if isinstance(item, AABB):
            return item.shifted(self.globalDomain(blockId).min)
        raise TypeError('Not implemented for type %s' % type(item))

    def mapDomainToCellInterval(self, domain, block_id=None):
        p_min = domain.min - self.origin()
        p_max = domain.max - self.origin()

        c_min = Cell(p_min//self.dx())
        c_max = Cell(p_max//self.dx())

        return self.globalCellInterval(block_id).intersect(CellInterval(c_min, c_max))

    def mapGlobalToBlockLocal(self, item, blockId):
        if isinstance(item, Cell):
            return item - self.globalCellInterval(blockId).min
        if isinstance(item, CellInterval):
            return item.shifted(-self.globalCellInterval(blockId).min)
        if isinstance(item, Vector):
            return item - self.globalDomain(blockId).min
        if isinstance(item, AABB):
            return item.shifted(-self.globalDomain(blockId).min)
        raise TypeError('Not implemented for type %s' % type(item))

    def mapToPeriodicDomain(self, body):
        if not self._periodic.any():
            return Bodies()

        result = Bodies()
        result.add(body)

        domain = self._domain

        if not np.less_equal(body.aabb().size, domain.size).all():
            raise ValueError('Body bounding box must not be bigger than domain')

        for axis in [0, 1, 2]:
            bodies = result.copy()
            for body in bodies:
                if self._periodic[axis]:

                    bb = body.aabb()
                    delta = np.array([0, 0, 0])
                    if bb.min[axis] < domain.min[axis]:
                        delta[axis] = domain.size[axis]
                    elif bb.max[axis] > domain.max[axis]:
                        delta[axis] = -domain.size[axis]

                    if delta.any():
                        assert not domain.contains(body.center() + delta)
                        mapped = body.create_shadow_copy()
                        mapped.set_center(body.center() + delta)
                        result.add(mapped)

        result.remove(body)
        return result

    def numBlocks(self):
        return self._numBlocks

    def numCells(self):
        return self._cellsPerBlock * self._numBlocks

    def origin(self):
        return self._origin

    def periodicity(self):
        return self._periodic

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
