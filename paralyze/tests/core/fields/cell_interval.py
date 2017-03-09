from unittest import TestCase
from paralyze.core.fields import CellInterval

import unittest


class CellIntervalTest(TestCase):

    def test_init(self):

        a1 = CellInterval((1, 2, 3), (4, 5, 6))
        a2 = CellInterval((1, 2, 3))

        self.assertTrue(a1.is_valid())
        self.assertTrue(a2.is_valid())

    def test_cell_interval(self):
        aabb0 = CellInterval((0,0,0), (5,5,5))
        aabb1 = CellInterval((1,1,1), (4,4,4))
        border = aabb0 - aabb1
        self.assertEqual(len(border), 152)


if __name__ == '__main__':
    unittest.main()
