from paralyze.core.algebra import AABB, Vector
from paralyze.core.bodies import *

import unittest


class BodiesTests(unittest.TestCase):

    def test_shadow(self):
        sph = Sphere(Vector(0), 1.0)
        shadow = sph.create_shadow_copy()

        del sph

        self.assertEqual(shadow.source(), None)

    def test_sphere(self):
        pass

    def test_plane(self):
        pass