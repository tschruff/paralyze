
def map_bodies_to_field(block, blocks, bodies_id, field_id, solid_value):

    field = block[field_id]
    center = blocks.cell_center  # for a little more performance

    for body in block[bodies_id].iter_bodies():
        cells = blocks.map_domain_to_cell_interval(body.domain())
        cells = blocks.cell_interval(block.id).intersection(cells)

        for global_cell in cells:
            local_cell = blocks.map_global_to_block_local(global_cell, block.id)
            if body.contains(center(global_cell)):
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
