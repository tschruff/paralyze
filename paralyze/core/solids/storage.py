
class Solids(set):
    """A set container that holds solid instances and takes care of merging
    and splitting procedures.
    """
    pass


class Storage(object):

    def __init__(self, domain=None, solids=()):
        self._domain = domain
        self._locals = Solids()
        self._shadows = Solids()
        self.add(solids)

    def __and__(self, other):
        return self.intersection(other)

    def __iand__(self, other):
        self = self.intersection(other)

    def __or__(self, other):
        return self.merged(other)

    def __ior__(self, other):
        self = self.merged(other)

    def add(self, solids):
        """Add all solids to either the local or shadow storage.
        """
        for solid in solids:
            if self.is_local(solid):
                self._locals.add(solid)
            if self.is_shadow(solid):
                self._shadows.add(solid)

    def clipped(self, domain):
        """Returns an iterator of the subset of solids that are inside the
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
            return self.iter_solids()
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

    def is_local(self, solid, domain=None):
        domain = domain or self._domain
        return domain.contains(solid.center)

    def is_shadow(self, solid, domain=None):
        domain = domain or self._domain
        return domain.intersects(solid.aabb)

    def iter_solids(self):
        return iter(self._locals | self._shadows)

    def iter_locals(self):
        return iter(self._locals)

    def iter_shadows(self):
        return iter(self._shadows)

    def merged(self, other):
        """Merges ``other`` storage and ``self``.
        """
        return Storage(self._domain | other.domain, self.solids | other.solids)

    def remove(self, solid):
        pass

    @property
    def solids(self):
        return self._locals | self._shadows

    def split(self, domains, strict=False):
        storages = []
        for domain in domains:
            storages.append(Storage(domain, self.solids))
        return storages
