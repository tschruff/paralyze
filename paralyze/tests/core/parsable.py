from unittest import TestCase

from paralyze.core import AABB, Cell, CellInterval, Interval, Vector
from paralyze.core import type_cast


class ParsableTest(TestCase):

    def test_init(self):
        self.assertIsInstance(type_cast("[<-2,-.3,.0>,<4.,6,inf>]"), AABB)
        self.assertIsInstance(type_cast("(3,5,-5)"), Cell)
        self.assertIsInstance(type_cast("[(-2,3,0)...(5,8,34567)]"), CellInterval)
        self.assertIsInstance(type_cast("(-inf,954456]"), Interval)
        self.assertIsInstance(type_cast("<-.3,-inf,inf>"), Vector)
