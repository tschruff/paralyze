import multiprocessing as mp
import numpy as np

from functools import partial
from .block import Block
from ..algebra import AABB, Vector
from ..fields import Cell, CellInterval, Field, update_operations


class BlockStorage(object):
    """ The base class for any block storage.

    :ivar _blocks: An iterable type that holds all block instances.
                   Must implement the __getitem__ member and return the
                   block for the corresponding block_id, i.e.

                   block = self._blocks[block_id]
    :ivar _ids: The list of existing block data identifiers

    """

    def __init__(self, origin=(0, 0, 0), periodicity=(False, False, False), resolution=1, num_processes=mp.cpu_count()):
        self._origin = Vector(origin)
        self._periodic = np.array(periodicity)
        self._resolution = Vector(resolution)
        self._np = num_processes

        self._blocks = []  # The most simple form of the _blocks member is a list of blocks

        self._ids = []
        self._domain = AABB()
        self._ci = CellInterval()

    def __getstate__(self):
        """ The __getstate__ member is called when the BlockStorage is send to other
        processes, i.e. when the *execute* member is called and copies of the BlockStorage are
        send to worker processes. To prevent unnecessary copies of block data on
        each worker process, we replace non-local blocks from the instance's
        __dict__ with None values.

        :return: The current state of the BlockStorage instance with non-local blocks set to None.
        """
        state = {key: value for key, value in self.__dict__.items() if key != '_blocks'}
        state['_blocks'] = [None for _ in range(len(self._blocks))]
        return state

    def __iter__(self):
        return iter(self._blocks)

    def __getitem__(self, identifier):
        return [block.get(identifier, None) for block in self._blocks]

    def __len__(self):
        return len(self._blocks)

    def block(self, block_id):
        return self._blocks[block_id]

    def cell_center(self, cell):
        raise NotImplemented

    def cell_interval(self, block_id=None):
        """ Returns the domain or block cell interval
        if block_id is not None in global coordinates.

        :param block_id:
        :return:
        """
        if not block_id:
            return self._ci
        return self.block(block_id).cell_interval

    def domain(self, block_id=None):
        """ Returns the domain or block aabb
        if block_id is not None in global coordinates.

        :param block_id:
        :return:
        """
        if not block_id:
            return self._domain
        return self.block(block_id).domain

    def has_data(self, identifier):
        return identifier in self._ids

    def is_periodic(self, axis):
        return self._periodic[axis]

    def neighbor_blocks(self, block_id, *args):
        raise NotImplemented

    def num_processes(self):
        return self._np

    def origin(self):
        return self._origin

    def periodicity(self):
        return self._periodic

    def resolution(self):
        return self._resolution

    def root_block(self):
        assert len(self._blocks) > 0
        return self._blocks[0]

    def add_bodies(self, identifier, bodies):
        if self.has_data(identifier):
            raise ValueError('Data with identifier %s already exist!' % identifier)

        if self._periodic.any():
            mapped = set()
            for body in bodies:
                mapped = mapped.union(self.map_to_periodic_domain(body))
            bodies = bodies.union(mapped)

        for block in self._blocks:
            bodies = block.add_bodies(identifier, bodies)

        self._ids.append(identifier)

    def add_field(self, identifier, dtype, ghost_level=0, init=0):
        if self.has_data(identifier):
            raise ValueError('Data with identifier %s already exists!' % identifier)
        for block in self._blocks:
            block.add_field(identifier, dtype, ghost_level, init)

        self._ids.append(identifier)

    def clip_to_domain(self, bodies, block_id=None, strict=False):
        domain = self.domain(block_id)
        return bodies.clipped(domain, strict)

    def map_block_local_to_global(self, item, block_id):
        if isinstance(item, Cell):
            return self.cell_interval(block_id).min + item
        if isinstance(item, CellInterval):
            return item.shifted(self.cell_interval(block_id).min)
        if isinstance(item, Vector):
            return self.domain(block_id).min + item
        if isinstance(item, AABB):
            return item.shifted(self.domain(block_id).min)
        if hasattr(item, '__len__'):
            return type(item)([self.map_block_local_to_global(i, block_id) for i in item])
        raise TypeError('Not implemented for type %s' % type(item))

    def map_global_to_block_local(self, item, block_id):
        if isinstance(item, Cell):
            return item - self.cell_interval(block_id).min
        if isinstance(item, CellInterval):
            return item.shifted(-self.cell_interval(block_id).min)
        if isinstance(item, Vector):
            return item - self.domain(block_id).min
        if isinstance(item, AABB):
            return item.shifted(-self.domain(block_id).min)
        if hasattr(item, '__len__'):
            return type(item)([self.map_global_to_block_local(i, block_id) for i in item])
        raise TypeError('Not implemented for type %s' % type(item))

    def map_to_periodic_domain(self, body):
        if not self._periodic.any():
            if body.position() in self._domain:
                return BodyStorage([body, ])
            return BodyStorage()

        result = BodyStorage()
        result.add(body)

        domain = self._domain

        if not np.less_equal(body.domain().size, domain.size).all():
            raise ValueError('Body bounding box must not be bigger than domain')

        for axis in [0, 1, 2]:
            bodies = result.copy()
            for body in bodies:
                if self._periodic[axis]:

                    bb = body.domain()
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

    def exec(self, func, join_func=None, **kwargs):
        if mp.current_process().name != 'MainProcess':
            raise mp.ProcessError('BlockStorage.exec may only be called on the main process')
        kwargs = kwargs or {}
        with mp.Pool(self.num_processes()) as pool:
            result = pool.map(partial(func, **kwargs), self)
            if hasattr(result[0], '__len__'):
                self.update([res[0] for res in result])
                second = [res[1] for res in result]
                if join_func is not None:
                    return join_func(second)
                return second
            else:
                self.update(result)

    def update(self, blocks):
        for block in blocks:
            # TODO: do some more checking?
            if block is None:
                continue
            self._blocks[block.id] = block

    def _validate_block_id(self, block_id):
        if isinstance(block_id, Block):
            return block_id.id
        assert block_id in self._blocks
        return block_id

    def _update_field(self, identifier, update_op=update_operations.copy):
        """

        :param identifier:
        :param update_op: function with signature (local_field, local_field_indexes, neighbor_field, neighbor_field_indexes)
        :return:
        """
        if not isinstance(self.root_block().get(identifier), Field):
            raise TypeError('Data %s is not a field' % identifier)

        # loop over all field tiles
        for block in self._blocks:
            # loop over all ghost regions at the borders with south, bottom, and west neighbors
            ghost_region = self.map_block_local_to_global(block.get(identifier).ghost_cells, block.id)
            for neighbor in self.neighbor_blocks(block, 'south', 'bottom', 'west'):
                common_cells = ghost_region.intersection(self.cell_interval(neighbor.id))
                bi = self.map_global_to_block_local(common_cells, block.id)
                ni = self.map_global_to_block_local(common_cells, neighbor.id)
                update_op(block.get(identifier), bi, neighbor.get(identifier), ni)
