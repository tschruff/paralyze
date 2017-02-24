from PydroSquid.core.body import Sphere


def penetration_depth(body0, body1):
    if isinstance(body0, Sphere):
        if isinstance(body1, Sphere):
            return sphere_sphere(body0, body1)
    raise NotImplementedError('penetration_depth not implemented for bodies types %s and %s' % (type(body0), type(body1)))


def sphere_sphere(s0, s1):
    return s0.radius() + s1.radius() - (s0.center() - s1.center()).length()