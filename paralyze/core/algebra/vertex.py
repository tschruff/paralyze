from .vector import Vector

import numpy as np


class Vertex(np.ndarray):
    """ A Vertex is a composite ndarray of two Vectors,
    i.e. position and normal.

    v = [[px,py,pz],
         [nx,ny,nz]]

    """

    def __new__(cls, pos, normal=Vector(0)):
        return np.asarray([Vector(pos), Vector(normal)]).view(cls)

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
        return self[0].view(Vector)

    @property
    def normal(self):
        """

        Returns
        -------
        normal: Vector
            The normal of the vertex
        """
        return self[1].view(Vector)
