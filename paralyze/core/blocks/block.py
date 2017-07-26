from ..fields.field import Field


class Block(object):
    """The Block class provides generic data storage in form of
    a simple Python dict.

    :ivar _id: A unique block id. There are no constraints for the type of the id.
               It may be a simple int or a more complex type. The type of the id
               must be consistent within a BlockStorage.
    """

    def __init__(self, block_id, cell_interval, domain):
        self._id = block_id
        self._data = {}

        self._ci = cell_interval
        self._domain = domain

    def __getitem__(self, identifier):
        return self._data[identifier]

    @property
    def cell_interval(self):
        return self._ci

    @property
    def domain(self):
        return self._domain

    @property
    def id(self):
        return self._id

    def get(self, identifier, default=None):
        return self._data.get(identifier, default)

    def add_field(self, identifier, dtype, ghost_level=0, init=0):
        """Adds a new field with given parameters to the block.

        Parameters
        ----------
        identifier:
            Unique field identifier.
        dtype: numpy.dtype
            Numpy array dtype.
        ghost_level: int (0, inf)
            Number of ghost layers.
        init: float or int
            Initial field value.
        """
        self._data[identifier] = Field(self._ci.size, dtype, ghost_level, init)

    def add_bodies(self, identifier, bodies, remove_pure_locals=True):
        """

        :param identifier:
        :param bodies: The set of bodies that will be added to the block
        :param remove_pure_locals: Whether to remove pure local bodies from the returned bodies
        :return: An updated set of bodies (bodies - pure local bodies)
        """
        bodies = BodyStorage(bodies)

        # create set of local bodies (bodies whose center belongs to the current block)
        local_bodies = bodies.subset(lambda body: self.domain().contains(body.center()))
        # create non-local set of bodies
        non_local_bodies = bodies.difference(local_bodies)

        shadows = set()
        for non_local in non_local_bodies:
            if self.domain().intersects(non_local.domain()):
                # skip shadow copies from periodic mapping
                if non_local.is_shadow_copy():
                    shadows.add(non_local)
                else:
                    shadow = non_local.create_shadow_copy()
                    shadows.add(shadow)

        self._data[identifier] = BodyStorage(local_bodies | shadows)

        if remove_pure_locals:
            # create a set of pure-local bodies (bodies whose extent is fully contained in the block domain)
            pure_local_bodies = local_bodies.subset(lambda body: self.domain().contains(body.domain()))
            # remove pure-local bodies from global list and return it
            bodies = bodies.difference(pure_local_bodies)

        return bodies
