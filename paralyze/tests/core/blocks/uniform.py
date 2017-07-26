from PydroSquid.core.blocks import *
from PydroSquid.core.algebra import *
from PydroSquid.core.body import *
from PydroSquid.core.field import *

import unittest


class UniformBlockStorageTests(unittest.TestCase):

    def test_uniform_block_storage(self):

        blocks = UniformBlockStorage((100, 100, 100), 4)
        domain = AABB((0, 0, 0), (100, 100, 100))

        self.assertEqual(blocks.num_cells().prod(), 1000000)
        self.assertEqual(blocks.num_processes(), 4)
        self.assertEqual(blocks.global_domain(), domain)
        self.assertEqual(blocks.numBlocks().prod(), 4)
        self.assertFalse(blocks.is_x_periodic())
        self.assertFalse(blocks.is_y_periodic())
        self.assertFalse(blocks.is_z_periodic())
        self.assertEqual(blocks.map_domain_to_cell_interval(domain).num_cells(), 1000000)
        self.assertEqual(blocks.globalCellInterval().min, (0, 0, 0))
        self.assertEqual(blocks.globalCellInterval().max, (99, 99, 99))
        self.assertEqual(blocks.cellCenter(Cell(49)), (49.5, 49.5, 49.5))
        self.assertEqual(blocks.cell(Vector(49.5)), (49, 49, 49))

        lCell = Cell(25)
        lPos = Vector(25)
        lCellBB = CellInterval(Cell(0), Cell(10))
        lAABB = AABB(Vector(0), Vector(10))

        for block in blocks:

            gCell = blocks.map_block_local_to_global(lCell, block.id())
            gPos = blocks.map_block_local_to_global(lPos, block.id())
            gCellBB = blocks.map_block_local_to_global(lCellBB, block.id())
            gAABB = blocks.map_block_local_to_global(lAABB, block.id())

            self.assertEqual(gCell, blocks.globalCellInterval(block.id()).min + lCell)
            self.assertEqual(gPos, blocks.global_domain(block.id()).min + lPos)
            self.assertEqual(gCellBB, lCellBB.shifted(blocks.globalCellInterval(block.id()).min))
            self.assertEqual(gAABB, lAABB.shifted(blocks.global_domain(block.id()).min))

            self.assertEqual(blocks.map_global_to_block_local(gCell, block.id()), lCell)
            self.assertEqual(blocks.map_global_to_block_local(gPos, block.id()), lPos)
            self.assertEqual(blocks.map_global_to_block_local(gCellBB, block.id()), lCellBB)
            self.assertEqual(blocks.map_global_to_block_local(gAABB, block.id()), lAABB)

    def test_body_bounding_box(self):

        blocks = UniformBlockStorage((10, 10, 10), 1)
        sphere = Sphere((5, 5, 5), 5)
        blocks.addBodies('bodies', {sphere, })

        self.assertEqual(sphere.domain(), AABB((0, 0, 0), (10, 10, 10)))

        cellBB = blocks.map_domain_to_cell_interval(sphere.domain())
        cells = CellInterval((0, 0, 0), (9, 9, 9))
        self.assertEqual(cellBB, cells, '%s != %s' % (cellBB, cells))

    def test_bodies_on_periodic_blocks(self):

        blocks = UniformBlockStorage((25, 50, 50), (2, 1, 1), periodicity=(True, True, True))

        sphere = Sphere((0, 0, 0), 10)
        blocks.addBodies('bodies', {sphere, })
        for bodies in blocks['bodies']:
            self.assertEqual(len(bodies), 4)

            for body in bodies:
                if body.is_shadow_copy():
                    self.assertEqual(body.source(), sphere)
                    self.assertEqual(body.num_shadow_copies(), 0)
                else:
                    self.assertEqual(body.num_shadow_copies(), 7)

    def test_body_shadow_copies(self):

        blocks = UniformBlockStorage((25, 50, 50), (2, 1, 1))
        sphere = Sphere((25, 25, 25), 10)
        blocks.addBodies('bodies', {sphere, })

        for bodies in blocks['bodies']:
            self.assertEqual(len(bodies), 1)
            for body in bodies:
                if body.is_shadow_copy():
                    self.assertEqual(body.source(), sphere)
                    self.assertEqual(body.num_shadow_copies(), 0)
                else:
                    self.assertEqual(body.num_shadow_copies(), 1)


if __name__ == '__main__':
    unittest.main()
