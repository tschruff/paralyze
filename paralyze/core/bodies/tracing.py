from paralyze.core.algebra import AABB
from paralyze.core.bodies import Plane, Sphere

import math


def intersectsAABB(self, aabb):
    return False, float('inf')


def intersectsPlane(ray, plane, threshold=1e-6):
    denom = ray.direction.dot(plane.normal())
    if abs(denom) < threshold:
        return False, float('inf')
    d = (plane.center() - ray.origin).dot(plane.normal()) / denom
    if d < 0.0:
        return False, float('inf')
    return True, d


def intersectsSphere(ray, sphere):
    a = ray.direction.dot(ray.direction)
    OS = ray.origin - sphere.center()
    b = 2 * ray.direction.dot(OS)
    c = OS.dot(OS) - sphere.radius() * sphere.radius()
    disc = b * b - 4 * a * c
    if disc > 0:
        distSqrt = math.sqrt(disc)
        q = (-b - distSqrt) / 2.0 if b < 0 else (-b + distSqrt) / 2.0
        t0 = q / a
        t1 = c / q
        t0, t1 = min(t0, t1), max(t0, t1)
        if t1 >= 0:
            return (True, t1) if t0 < 0 else (True, t0)
    return False, float('inf')


def intersects(ray, geometry):
    if isinstance(geometry, Sphere):
        return intersectsSphere(ray, geometry)
    elif isinstance(geometry, AABB):
        return intersectsAABB(ray, geometry)
    elif isinstance(geometry, Plane):
        return intersectsPlane(ray, geometry)
    else:
        raise TypeError('Unsupported algebra type')