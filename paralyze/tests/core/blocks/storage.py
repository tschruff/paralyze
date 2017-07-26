from PydroSquid.core.blocks import BlockStorage

import unittest
import numpy as np
import multiprocessing as mp


def func(block, x, y):
    result = x+y
    return block, result


def func_no_return(block):
    return block


def handle_blocks(block, np, blocks):
    result = blocks.num_processes() == np
    return block, result


def handle_blocks_raises(block, blocks):
    result = False
    try:
        blocks.exec(sum, range(10))
    except mp.ProcessError:
        result = True
    return block, result


class TestBlockStorage(unittest.TestCase):

    def test_exec(self):
        blocks = BlockStorage(4)
        self.assertEqual(blocks.exec(func, x=1, y=2, join_func=sum), 4*(1+2))
        blocks.exec(func_no_return)

    def test_pass_blocks(self):
        blocks = BlockStorage(4)
        self.assertTrue(blocks.exec(handle_blocks, np=4, blocks=blocks, join_func=np.all))
        self.assertTrue(blocks.exec(handle_blocks_raises, blocks=blocks, join_func=np.all))
