from .vector import Vector

import numpy as np


class Vertex(np.ndarray):
    """ A Vertex is a composite ndarray of two Vectors:
    position and normal vector.

    v = [[px,py,pz],
         [nx,ny,nz]]

    """

    def __new__(cls, pos, normal=Vector(0)):
        return np.asarray(Vector(pos) + Vector(normal)).view(cls)

    def __array_wrap__(self, out_arr, context=None):
        out = np.ndarray.__array_wrap__(self, out_arr, context)
        # FIXME: Same issue as in Vector class
        print("returning from __array_wrap__: {}".format(out))
        return out

    def __repr__(self):
        return 'Vertex(pos={!r}, normal={!r})'.format(self.pos, self.normal)

    def __getitem__(self, item):
        return np.ndarray.__getitem__(self, item).view(Vector)

    @property
    def pos(self):
        """

        Returns
        -------
        pos: Vector
            The position of the vertex
        """
        return self[:3].view(Vector)

    @property
    def normal(self):
        """

        Returns
        -------
        normal: Vector
            The normal of the vertex
        """
        return self[3:].view(Vector)
