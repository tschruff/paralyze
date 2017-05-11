from ..sphere import Sphere, create_sphere
import numpy as np


def load_spheres(f, dynamic=False):
    data = np.load(f)
    spheres = set()
    if not dynamic:
        for i in range(len(data)):
            spheres.add(create_sphere(
                center=data['center'][i], radius=data['radius'][i]
            ))
    else:
        for i in range(len(data)):
            spheres.add(create_sphere(dynamic=True,
                center=data['center'][i], radius=data['radius'][i],
                density=data['density'][i],
                angular_velocity=data['angular_velocity'][i],
                linear_velocity=data['linear_velocity'][i],
                force=data['force'][i], torque=data['torque'][i]
            ))

    return spheres

def save_spheres(solids, f, dynamic=False, dtype=np.float32):

    spheres = list(filter(lambda solid: isinstance(solid, Sphere), solids))
    n = len(spheres)

    if not dynamic:
        data = np.zeros(n, [('center', dtype, 3),
                            ('radius', dtype, 1)])

        data['center'] = np.array([sphere.center for sphere in spheres])
        data['radius'] = np.array([sphere.radius for sphere in spheres])

    else:
        data = np.zeros(n, [('center'          , dtype, 3),
                            ('radius'          , dtype, 1),
                            ('density'         , dtype, 1),
                            ('angular_velocity', dtype, 3),
                            ('linear_velocity' , dtype, 3),
                            ('force'           , dtype, 3),
                            ('torque'          , dtype, 3)])

        data['center'] = np.array([sphere.center for sphere in spheres])
        data['radius'] = np.array([sphere.radius for sphere in spheres])
        data['density'] = np.array([sphere.density for sphere in spheres])
        data['angular_velocity'] = np.array([sphere.angular_velocity for sphere in spheres])
        data['linear_velocity'] = np.array([sphere.linear_velocity for sphere in spheres])
        data['force'] = np.array([sphere.force for sphere in spheres])
        data['torque'] = np.array([sphere.torque for sphere in spheres])

    np.save(f, data)
