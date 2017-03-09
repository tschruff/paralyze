from .vector import Vector
from .vertex import Vertex

import numpy as np


class Triangle(np.ndarray):

    def __new__(cls, vertices):
        if len(vertices) != 3:
            raise TypeError('vertices must have three elements')
        return np.asarray([Vertex(v) for v in vertices]).view(cls)

    def __repr__(self):
        return 'Triangle(vertices={})'.format(self)

    def __getitem__(self, item):
        return np.ndarray.__getitem__(self, item).view(Vertex)

    @property
    def area(self):
        """

        Returns
        -------
        area: float
            The area of the triangle
        """
        return .5 * np.linalg.norm(np.cross(self[1][0]-self[0][0], self[2][0]-self[0][0]))

    @property
    def centroid(self):
        """

        Returns
        -------
        centroid: Vector
            The centroid of the triangle
        """
        return (self[0][0]+self[1][0]+self[2][0])/3.

    @property
    def flipped(self):
        """ Returns a new triangle where the vertices are flipped.
        This effectively changes the face orientation of the triangle.

        """
        return Triangle([self[0], self[2], self[1]])

    @property
    def face_normal(self):
        """

        Returns
        -------
        face_normal: Vector
            The normalized face normal of the triangle
        """
        return Vector(np.cross(self[1][0]-self[0][0], self[2][0]-self[0][0])).normalized()

    @property
    def signed_volume(self):
        """

        Returns
        -------
        signed_volume: float
            The signed volume of the triangle
        """
        return self[0][0].dot(np.cross(self[1][0], self[2][0])) / 6.
