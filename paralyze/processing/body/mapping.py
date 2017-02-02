
def map_bodies_to_field(block, blocks, bodies_id, field_id, solid_value):

    field = block[field_id]
    cc = blocks.cellCenter  # for a little more performance

    for body in block[bodies_id].iter_bodies():
        cells = blocks.mapDomainToCellInterval(body.aabb())
        cells = blocks.mapGlobalToBlockLocal(cells, block.id)
        cells = block.cellInterval().intersect(cells)

        for local_cell in cells:
            cell = blocks.mapBlockLocalToGlobal(local_cell, block.id)
            if body.contains(cc(cell)):
                field[local_cell] = solid_value

    return block


def map_bodies_to_field_p(block, blocks, bodies_id, field_id, solid_value):
    import cProfile, pstats

    global result

    cProfile.runctx('global result; result = map_bodies_to_field(block, blocks, bodies_id, field_id, solid_value)', globals(), locals(),
                    'map_bodies_to_field_{}.prof'.format(block.id))

    stats = pstats.Stats('map_bodies_to_field_{}.prof'.format(block.id))
    stats.strip_dirs()
    stats.sort_stats('time').print_stats(10)

    return result
