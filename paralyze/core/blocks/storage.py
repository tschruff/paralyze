import multiprocessing as mp

from functools import partial


class BlockStorage(object):

    def __init__(self, np=0):
        self._blocks = [None for _ in range(np)]
        self._ids = None
        self._np = np

    def __getstate__(self):
        """ The __getstate__ is called when the BlockStorage is send to other
        processes, i.e. when the execute method is called and the BlockStorage is
        passed to worker processes. To prevent copies of all blocks for each worker
        process, we replace the _blocks member from the instance __dict__ with a list
        of empty blocks (None values). This causes all member functions that access
        the _blocks member to return empty (None) blocks instead.

        :return: The current state of the BlockStorage instance with empty blocks.
        """
        state = {key: value for key, value in self.__dict__.items() if key != '_blocks'}
        state['_blocks'] = [None for _ in range(len(self._blocks))]
        return state

    def __iter__(self):
        return iter(self._blocks)

    def __getitem__(self, identifier):
        return [block[identifier] if block is not None else None for block in self._blocks]

    def __len__(self):
        return len(self._blocks)

    def block(self, block_id):
        return self._blocks[block_id]

    def has_data(self, identifier):
        return identifier in self._ids

    def exec(self, func, join_func=None, **kwargs):
        # TODO: Find a better solution for this
        if mp.current_process().name != 'MainProcess':
            raise mp.ProcessError('exec may only be called on the main process')
        kwargs = kwargs or {}
        with mp.Pool(self.np()) as pool:
            result = pool.map(partial(func, **kwargs), self)
            if hasattr(result[0], '__len__'):
                self.update([res[0] for res in result])
                second = [res[1] for res in result]
                if join_func is not None:
                    return join_func(second)
                return second
            else:
                self.update(result)

    def np(self):
        return self._np

    def root_block(self):
        assert len(self._blocks) > 0
        return self._blocks[0]

    def update(self, blocks):
        for block in blocks:
            # TODO: do some more checking?
            if block is None:
                continue
            self._blocks[block.id()] = block
