from unittest import TestCase
from PydroSquid.core.algebra import AABB
from PydroSquid.core.body import Sphere
from PydroSquid.core.voxel import VoxelVolume


class VoxelSphereTests(TestCase):

    def test_intersection_volume(self):

        sphere = Sphere((0, 0, 0), 10)
        volume = VoxelVolume.voxelize(sphere, 1.0)

        full       = AABB((-10, -10, -10), (10, 10, 10))
        oneHalf    = AABB((  0, -10, -10), (10, 10, 10))
        oneQuarter = AABB((  0,   0, -10), (10, 10, 10))
        oneEigth   = AABB((  0,   0,   0), (10, 10, 10))

        self.assertEqual(volume.solid_volume()                 , 4224)
        self.assertEqual(volume.intersection_volume(full)      , 4224)
        self.assertEqual(volume.intersection_volume(oneHalf)   , 2112)
        self.assertEqual(volume.intersection_volume(oneQuarter), 1056)
        self.assertEqual(volume.intersection_volume(oneEigth)  , 528 )

        sphere = Sphere((10.0, 5.0, -2.0), 10)
        volume = VoxelVolume.voxelize(sphere, 2)
        full = AABB((9.0, 4.0, -3.0), (11.0, 6.0, -1.0))
        oneEigth = AABB((10.0, 5.0, -2.0), (11.0, 6.0, -1.0))

        self.assertEqual(volume.intersection_volume(full), 64.0)
        self.assertEqual(volume.intersection_volume(oneEigth), 8.0)
