from unittest import TestCase

from paralyze.core.algebra import Vector


class VectorTest(TestCase):

    def test_init(self):

        v1 = Vector(1)
        v2 = Vector((1, 1, 1))

        self.assertEqual(v1, Vector(1))
        self.assertEqual(v2, Vector(1))
