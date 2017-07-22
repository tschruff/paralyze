from .algebra import AABB, Vector
from .fields import Cell, CellInterval


def map_aabb_to_cell_interval(aabb, field_orig, field_res, field=None):
    """Maps an ``aabb`` to a ``CellInterval``of the ``field``.

    Parameters
    ----------
    aabb: AABB
        The domain to be mapped.
    field_orig: Vector

    field_res: float

    Notes
    -----
    Only if ``field`` is specified the returned CellInterval is ensured to be
    valid or empty in case aabb does not intersect with the field.
    """
    c CellInterval(
        (aabb.min-field_orig)//field_res,
        (aabb.max-field_orig)//field_res
    )

    if field is not None:
        return field.cell_interval.intersection(c)
    return c


def map_solids(solids, field, field_orig=Vector(0), field_res=Vector(1), solid_value=1, void_value=0):
    """Maps all ``solids`` onto the ``field``.

    Parameters
    ----------

    Notes
    -----
    In contrast to :func:`map_solid_volume_fraction` this function maps solids in
    a binary manner, i.e. the cell value will be set to either ``solid_value``
    or ``void_value`` depending on whether the cell center is inside the solid.
    """
    for solid in solids:
        cell_interval = map_aabb_to_cell_interval(solid.aabb, field, field_orig, field_res)
        for cell in cell_interval:
            cell_center = field_orig + field_res * (Vector(cell) + Vector(0.5))
            if solid.contains(cell_center):
                field[cell] = solid_value


def map_solid_volume_fraction(solids, field, level=1, field_orig=Vector(0), field_res=Vector(1)):
    """Maps the solid volume fraction of ``solids`` onto the ``field``.

    Parameters
    ----------
    solids: array-like
        The set of solids that will be mapped.
    field: Field
        The field onto which the solids will be mapped.
    level: int
        The octree level during mapping. If level == 0, this function is equivalent
        to calling :func:`map_solids` with ``solid_value`` = 1.
    field_orig: Vector
        The origin of the field.
    field_res: Vector
        The resolution of the field.
    """
    if level == 0:
        map_solids(solids, field, field_orig, field_res, solid_value=1)
        return

    dv = 1./8**level
    for solid in solids:
        cell_interval = map_aabb_to_cell_interval(solid.aabb, field, field_orig, field_res)
        for cell in cell_interval:
            solid_fraction = 0.0
            cell_aabb = AABB(cell, cell.shifted(1)).scaled(field_res).shifted(field_orig)
            # loop through all octree elements of the cell and test if
            # cell center is inside solid
            for sub in cell_aabb.iter_subs(level):
                if solid.contains(sub.center):
                    solid_fraction += dv
            # set cell value
            field[cell] += solid_fraction
