from paralyze.core.algebra import AABB, ReferenceFrame


class Bodies(set):

    def __new__(cls, seq=()):
        return set.__new__(Bodies, seq)

    def aabb(self, locals_only=False):
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

    def scale(self, scale_factor):
        for body in self:
            body.scale(scale_factor)

    def translate(self, delta):
        for body in self:
            body.set_position(delta, ReferenceFrame.LOCAL)

    def subset(self, selector):
        sub = Bodies()
        for body in self:
            if selector(body):
                sub.add(body)
        return sub

    def clipped(self, domain, strict=False):
        """ Returns a subset of bodies that are inside the specified domain.

        :param domain:
        :type domain: AABB
        :param strict: whether body center (False) or the whole body (True) is tested to be inside in the given domain
        :type strict: bool
        :returns: subset to bodies that is inside the given domain
        """
        if domain.contains(self.aabb()):
            return self
        if strict:
            return self.subset(lambda body: domain.contains(body.aabb()))
        return self.subset(lambda body: domain.contains(body.position()))
