from ..algebra import AABB, Vector
from .solid import PSolid, DynamicPSolid

import numpy as np


def create_sphere(*args, dynamic=False, **kwargs):
    """Returns a new instance of a static/dynamic Sphere.

    Parameters
    ----------
    dynamic: bool
        Controls the base class of the new Sphere instance.
        If ``False``, the Sphere will be a subclass of StaticSphere and not have
        properties like ``mass``, ``force``, or ``torque``.
        If ``True``, the Sphere will be a subclass of DynamicSphere and therefore
        have all DynamicSphere properties.
        You can test if your instance is derived from DynamicSphere or
        StaticSphere by using Pythons built-in ``isinstance`` method. See the
        example below for more details.

    Notes
    -----

    You can also create instances of static/dynamic Sphere objects by calling
    their respective constructor, i.e.

        >>> from paralyze.core.solids import StaticSphere, DynamicSphere
        >>> static = StaticSphere(*args, **kwargs)
        >>> dynamic = DynamicSphere(*args, **kwargs)

    Examples
    --------

        >>> from paralyze.core.solids import *
        >>> s = create_sphere(dynamic=False)
        >>> isinstance(s, Sphere)
        True
        >>> isinstance(s, StaticSphere)
        True
        >>> isinstance(s, DynamicSphere)
        False
        >>> s = create_sphere(dynamic=True)
        >>> isinstance(s, Sphere)
        True
        >>> isinstance(s, StaticSphere)
        False
        >>> isinstance(s, DynamicSphere)
        True
    """
    if not dynamic:
        return StaticSphere(*args, **kwargs)
    return DynamicSphere(*args, **kwargs)


class Sphere(PSolid):
    Length      = PSolid.Length + 1
    RadiusIndex = PSolid.Length

    def __init__(self, *args, **kwargs):
        """Initializes a new Sphere instance.

        Parameters
        ----------
        center: Vector
            The sphere center.
        radius: float
            The sphere radius.
        """
        radius = kwargs.pop("radius", 1)
        PSolid.__init__(self, *args, **kwargs)
        self.radius = radius

        # only update if Sphere was called directly, i.e. is not a subclass
        # or StaticSphere or DynamicSphere
        if type(self) == Sphere:
            self.update()

    def __repr__(self):
        return 'Sphere(center={!s}, radius={!s})'.format(self.center, self.radius)

    def update_aabb(self):
        # we don't need to do Vector(self.radius) because numpy will take care
        # of the "Vector - float" case
        min_corner = self.center - self.radius
        max_corner = self.center + self.radius
        self._data[self.AABBSlice] = self.aabb.update(min=min_corner, max=max_corner)

    @property
    def equivalent_mesh_size(self):
        return self.radius * 2.

    def contains(self, point):
        return (point - self.center).sqr_length() <= (self.radius * self.radius)

    @property
    def radius(self):
        return self._data[self.RadiusIndex]

    @radius.setter
    def radius(self, radius):
        self._data[self.RadiusIndex] = radius
        self._dirty = True

    @property
    def volume(self):
        return 4/3. * np.pi * np.power(self.radius, 3)


class StaticSphere(Sphere):

    def __init__(self, *args, **kwargs):
        Sphere.__init__(self, *args, **kwargs)
        if type(self) == StaticSphere:
            self.update()


class DynamicSphere(DynamicPSolid, Sphere):
    Length = DynamicPSolid.Length + 1

    def __init__(self, *args, **kwargs):
        DynamicPSolid.__init__(self, *args, **kwargs)
        Sphere.__init__(self, *args, **kwargs)
        if type(self) == DynamicSphere:
            self.update()

    def update_inertia(self):
        i = 0.4 * self.mass * self.radius**2
        self._data[self.InertiaSlice] = np.array([i, 0, 0, 0, i, 0, 0, 0, i], dtype=self.dtype)
