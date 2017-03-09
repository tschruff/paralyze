from ..algebra import AABB, ReferenceFrame


class BodyStorage(object):

    def __init__(self, bodies=()):
        self._bodies = set(bodies)

    def __iter__(self):
        return iter(self._bodies)

    def __len__(self):
        return len(self._bodies)

    def add(self, body):
        self._bodies.add(body)

    def domain(self, locals_only=False):
        # TODO: cache aabb and only recompute if necessary, i.e. bodies have been added/removed/edited etc.
        if not len(self):
            return AABB()
        if locals_only:
            box = None
            for body in self.iter_locals():
                box = body.aabb()
                break
            assert box
            for body in self.iter_locals():
                box = box.merged(body.aabb())
        else:
            box = None
            for body in self.iter_bodies():
                box = body.aabb()
                break
            assert box
            for body in self.iter_bodies():
                box = box.merged(body.aabb())
        return box

    def get(self, body_id):
        for body in self:
            if body.id() == body_id:
                return body
        return None

    def iter_bodies(self):
        return iter(self)

    def iter_locals(self):
        for body in self:
            if not body.is_shadow_copy():
                yield body

    def iter_shadows(self):
        for body in self:
            if body.is_shadow_copy():
                yield body

    def num_bodies(self):
        return len(self)

    def num_locals(self):
        return len(self) - self.num_shadows()

    def num_shadows(self):
        return len(set(filter(lambda body: body.is_shadow_copy(), self)))

    def print_stats(self):
        print('-- BODY STATS --')
        print('%d locals' % self.num_locals())
        print('%d shadows' % self.num_shadows())
        print('%d in total' % self.num_bodies())

    def remove(self, body):
        self._bodies.remove(body)

    def translate(self, delta):
        for body in self:
            body.set_position(delta, ReferenceFrame.LOCAL)

    def subset(self, selector):
        return BodyStorage([body for body in self if selector(body)])

    def clipped(self, domain, strict=False):
        """ Returns a subset of bodies that are inside the specified domain.

        :param domain:
        :type domain: AABB
        :param strict: whether only body center (False) or the whole body extent (True) is tested to be inside in the given domain
        :type strict: bool
        :returns: subset of bodies that is inside the given domain
        """
        if domain.contains(self.domain()):
            return self
        if strict:
            return self.subset(lambda body: domain.contains(body.aabb()))
        return self.subset(lambda body: domain.contains(body.position()))

    def split(self, domains, strict=False):
        bodies = []
        for domain in domains:
            bodies.append(self.clipped(domain, strict=strict))
        return bodies

    def sliced(self, axis, num_slices, domain=None, strict=False):
        if not domain:
            domain = self.domain()
        sliced_bodies = []
        for domain_slice in domain.iter_slices(axis, num_slices):
            sliced_bodies.append(self.clipped(domain_slice, strict))
        return sliced_bodies
