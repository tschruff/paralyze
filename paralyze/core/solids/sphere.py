from ..algebra import AABB, Vector
from .solid import PSolid, DynamicPSolid

import math
import numpy as np


def create_sphere(*args, dynamic=False, **kwargs):
    """Returns a new instance of a static/dynamic Sphere.

    Parameters
    ----------
    dynamic: bool
        Controls the base class of the new Sphere instance.
        If `false`, the Sphere will be a subclass of StaticSphere and not have
        properties like `mass`, `force`, or `torque`.
        If `true`, the Sphere will be a subclass of DynamicSphere and therefore
        have all DynamicSphere properties.
        You can test if your instance is derived from DynamicSphere or
        StaticSphere by using Pythons built-in `isinstance` method. See the
        example below for more details.

    Notes
    -----

    You can also create instances of static/dynamic Sphere objects by calling
    their respective constructor, i.e.

        >>> from paralyze.core.solids import StaticSphere, DynamicSphere
        >>> static = StaticSphere()
        >>> dynamic = DynamicSphere()

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
    Parameters = ["radius"]
    Length = PSolid.Length + 1
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
        self.update_aabb()

    def __repr__(self):
        return 'Sphere(center={!s}, radius={!s})'.format(self.center, self.radius)

    def update_aabb(self):
        self[self.AABBSlice] = AABB(self.center - Vector(self.radius),
                                    self.center + Vector(self.radius))

    @property
    def equivalent_mesh_size(self):
        return self.radius * 2.

    def contains(self, point):
        return (point - self.center).sqr_length() <= (self.radius * self.radius)

    @property
    def radius(self):
        return self[self.RadiusIndex]

    @radius.setter
    def radius(self, radius):
        radius = float(radius)
        if radius <= 0:
            raise ValueError("sphere radius may not be smaller than zero!")
        self[self.RadiusIndex] = radius

    @property
    def volume(self):
        return 4/3. * math.pi * self.radius**3


class StaticSphere(Sphere):
    pass


class DynamicSphere(DynamicPSolid, Sphere):
    Length = DynamicPSolid.Length + len(Sphere.Parameters)

    def __init__(self, *args, **kwargs):
        DynamicPSolid.__init__(self, *args, **kwargs)
        Sphere.__init__(self, *args, **kwargs)

    @property
    def inertia(self):
        i = 0.4 * self.mass * self.radius**2
        return np.array([[i, 0, 0], [0, i, 0], [0, 0, i]])
