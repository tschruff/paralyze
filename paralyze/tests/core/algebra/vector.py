from unittest import TestCase
from paralyze.core.algebra import Vector

import unittest
import math
import numpy as np


class VectorTest(TestCase):

    def test_init(self):
        v1 = Vector(1)
        v2 = Vector((1, 1, 1))

        self.assertEqual(v1, Vector(1))
        self.assertEqual(v2, Vector(1))

    def test_vector(self):
        v0 = Vector((1., 1., 1.))
        v1 = Vector([1, 2, 3])
        v2 = Vector(np.array([4, 5, 6]))
        v3 = Vector([1, 1, -1])

        self.assertEqual(v0.x, 1)
        self.assertEqual(v0.y, 1)
        self.assertEqual(v0.z, 1)

        len0Sqr = 3
        len0 = math.sqrt(3)  # v0.length()
        sum01 = Vector((2, 3, 4))  # v0 + v1
        dot12 = 32  # v1.dot(v2)
        dist02 = math.sqrt(3**2 + 4**2 + 5**2)  # v0.dist(v2)

        self.assertEqual(v0.sqr_length(), len0Sqr)
        self.assertEqual(v0.length(), len0)
        self.assertEqual(v0+v1, sum01)
        self.assertEqual(v1.dot(v2), dot12)
        self.assertEqual(v0.dist(v2), dist02)

        self.assertTrue(v0 == v0)

        self.assertTrue(v1 > v0)
        self.assertTrue(v1 >= v0)
        self.assertFalse(v3 > v0)
        self.assertFalse(v3 >= v0)


if __name__ == '__main__':
    unittest.main()
