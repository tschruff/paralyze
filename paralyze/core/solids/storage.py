from collections.abc import Set
from paralyze.core import AABB, Vector

import numpy as np


class Solids(set):

    def __init__(self, solids=[]):
        set.__init__(self, solids)

    def __getitem__(self, key):
        # TODO: Implement []-operator to return solid attributes (e.g. x, y, mass, velocity, etc.)
        pass

    @property
    def aabb(self):
        """TODO: precompute to be more efficient.
        """
        min_x = np.inf
        min_y = np.inf
        min_z = np.inf
        max_x = -np.inf
        max_y = -np.inf
        max_z = -np.inf
        for solid in self:
            center = solid.center
            min_x = min(min_x, center.x)
            min_y = min(min_y, center.y)
            min_z = min(min_z, center.z)
            max_x = max(max_x, center.x)
            max_y = max(max_y, center.y)
            max_z = max(max_z, center.z)
        return AABB((min_x, min_y, min_z), (max_x, max_y, max_z))


class Storage(object):

    def __init__(self, domain=AABB.inf(), solids=()):
        self._domain = domain
        self._solids = Solids([])
        self.add(solids)

    def __and__(self, other):
        return self.intersection(other)

    def __iand__(self, other):
        self = self.intersection(other)

    def __or__(self, other):
        return self.merged(other)

    def __ior__(self, other):
        self = self.merged(other)

    def __len__(self):
        return len(self._solids)

    def add(self, solids):
        """Add all solids to either the local or shadow storage.
        """
        for solid in solids:
            if self.domain.contains(solid.center):
                self._solids.add(solid)

    def clipped(self, domain):
        """Returns the subset of solids that are inside the
        specified ``domain``.

        Parameters
        ----------
        domain: AABB
            The clipping domain.

        Returns
        -------
        filter:
            The subset of bodies that is inside the specified `domain`.
        """
        if domain.contains(self.domain):
            return self.solids
        return filter(lambda solid: self.is_local(solid, domain) or self.is_shadow(solid, domain), self.solids)

    @property
    def domain(self):
        return self._domain

    def intersection(self, other):
        """Returns the solids that are contained in the intersection of
        the domains of ``self`` and ``other`` and merges solids automatically.

        Returns
        -------
        Storage:
            A new storage that spans the intersection domain of self and other.
            The new storage contains no duplicate solids.
        """
        return Storage(self.domain & other.domain, self.solids | other.solids)

    def iter_solids(self):
        return iter(self._solids)

    def merged(self, other):
        """Merges ``other`` storage and ``self``.
        """
        return Storage(self.domain | other.domain, self.solids | other.solids)

    def remove(self, solid):
        pass

    @property
    def solids(self):
        return self._solids

    def split(self, domains, strict=False):
        storages = []
        for domain in domains:
            storages.append(Storage(domain, self.solids))
        return storages
