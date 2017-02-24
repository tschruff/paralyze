from ..sphere import Sphere
import numpy as np


def save_spheres(bodies, filename):

    spheres = bodies.subset(lambda body: isinstance(body, Sphere))
    n = len(spheres)

    data = np.zeros(n, [('position', np.float32, 3),
                        ('radius'  , np.float32, 1)])

    data['position'] = np.array([sphere.position() for sphere in spheres])
    data['radius']   = np.array([sphere.radius() for sphere in spheres])

    np.save(filename, data)