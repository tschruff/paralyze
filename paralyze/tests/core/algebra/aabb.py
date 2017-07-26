from unittest import TestCase
from paralyze.core.algebra import AABB

import unittest


class AABBTest(TestCase):

    def test_init(self):

        a1 = AABB((1, 2, 3), (4, 5, 6))
        a2 = AABB((1, 2, 3))

        self.assertTrue(a1.is_valid())
        self.assertTrue(a2.is_valid())
        self.assertTrue(a2.is_empty())

    def test_aabb(self):
        aabb0 = AABB((0,1,4), (7,3,9))
        aabb1 = AABB((4,2,3), (9,4,6))
        aabb01 = aabb0.merged(aabb1)
        self.assertEqual(aabb01, AABB((0,1,3), (9,4,9)), 'AABB merge passed')


if __name__ == '__main__':
    unittest.main()

