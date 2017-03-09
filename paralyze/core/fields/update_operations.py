
def copy(field, field_idxs, neighbor, neighbor_idxs, inverse=False):
    if inverse:
        neighbor[neighbor_idxs] = field[field_idxs]
    else:
        field[field_idxs] = neighbor[neighbor_idxs]
