from paralyze.core.algebra import AABB, Vector
from paralyze.core.bodies import *

import unittest
import multiprocessing as mp
import os


def get_pid():
    return os.getpid()


class BodiesTests(unittest.TestCase):

    def test_shadow(self):

        sph = Sphere(Vector(0), 1.0)

        storage = BodyStorage()
        with mp.Pool(2) as pool:
            result = pool.map(get_pid, storage)
        print(result)

    def test_sphere(self):
        pass

    def test_plane(self):
        pass

if __name__ == '__main__':
    unittest.main()
