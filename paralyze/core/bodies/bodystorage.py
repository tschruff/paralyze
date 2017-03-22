from ..algebra import AABB

import uuid


class BodyStorage(object):

    def __init__(self, domain, bodies=()):
        self._bodies = set()
        self._domain = domain
        for body in bodies:
            self.add(body)

    def __iter__(self):
        return iter(self._bodies)

    def __len__(self):
        return len(self._bodies)

    @property
    def bodies(self):
        return self._bodies

    @property
    def domain(self):
        return self._domain

    @property
    def num_bodies(self):
        return len(self)

    @property
    def num_locals(self):
        return len(set(filter(lambda body: body.__local, self)))

    @property
    def num_shadows(self):
        return len(self) - self.num_locals()

    def add(self, body):
        """Adds the specified `body` to the storage if it at least intersects
        with the storage domain.

        Parameters
        ----------
        body: solid-like
            The body that is candidate for addition.

        Notes
        -----
        The specified body will only be added to the storage if it does
        intersect with the storage domain.
        """
        # only assign body id (bid) to new bodies
        if not hasattr(body, "__bid"):
            body.__bid = uuid.uuid4()
        # mark body as local or non-local and add to bodies if
        # body (at least) intersects with the storage domain
        if self._domain.contains(body.center):
            body.__local = True
            self._bodies.add(body)
        elif self._domain.intersects(body.aabb):
            body.__local = False
            self._bodies.add(body)

    def get_body(self, body_id):
        for body in self:
            if body.__bid == body_id:
                return body
        return None

    def iter_bodies(self):
        return iter(self)

    def iter_locals(self):
        for body in self:
            if body.__local:
                yield body

    def iter_shadows(self):
        for body in self:
            if not body.__local:
                yield body

    def print_stats(self):
        print('-- BODY STATS --')
        print('%d locals' % self.num_locals())
        print('%d shadows' % self.num_shadows())
        print('%d in total' % self.num_bodies())

    def remove(self, body):
        self._bodies.remove(body)

    def subset(self, selector):
        return BodyStorage([body for body in self if selector(body)])

    def clipped(self, domain, strict=False):
        """Returns the subset of bodies that are inside the specified `domain`.

        Parameters
        ----------
        domain: AABB
            The clipping domain.
        strict: bool
            Whether only body center (False) or the whole body extent (True) is
            tested to be inside in the specified domain.

        Returns
        -------
        The subset of bodies that is inside the specified `domain`.
        """
        if domain.contains(self.domain()):
            return self
        if strict:
            return self.subset(lambda body: domain.contains(body.aabb))
        return self.subset(lambda body: domain.contains(body.center))

    def split(self, domains, strict=False):
        storages = []
        for domain in domains:
            storages.append(BodyStorage(domain, self.clipped(domain, strict=strict)))
        return storages

    def merge(self, other):
        """Merges `other` and the underlying storage inplace.
        """
        self._domain = self.domain.merged(other.domain)
        for other_body in other.iter_bodies():
            body = self.get_body(other_body.__bid)
            if body is not None:
                # TODO: merge bodies
                pass
            else:
                self.add(other_body)
