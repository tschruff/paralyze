from .triangle import Triangle
from .vertex import Vertex

import numpy as np


class Polygon(np.ndarray):

    def __new__(cls, vertices):
        return np.asarray(vertices).view(cls)

    def __len__(self):
        return self.shape[0]

    def __repr__(self):
        return 'Polygon({})'.format(self[:])

    def __getitem__(self, item):
        return np.ndarray.__getitem__(self, item).view(Vertex)

    def is_convex(self):
        """ Returns True if the polygon is convex, otherwise False.

        If you consider each pair of consecutive vertices as an edge vector, the cross products of each pair
        of consecutive edges have all the same sign (considering zeros to have either sign, or ignoring
        zeros altogether), if the polygon is convex.

        Returns
        -------
        result: bool
            The result of the test
        """
        n = len(self) - 1
        if n < 5:
            return True

        # initialize *sign* with value at last vertex
        sign = np.cross(self[n]-self[n-1], self[0]-self[n]) > 0
        for i in range(n-1):
            if sign != (np.cross(self[i]-self[i-1], self[i+1]-self[i]) > 0):
                return False
        return True

    def triangulate(self, method='simple'):
        """

        Parameters
        ----------
        method: str
            The method used for triangulation. One of:
            - simple
            - delaunay
            - monotone
            - ear_clipping

        Returns
        -------
        triangles: list
            The list of triangles
        """
        if self.is_convex() and method == 'simple':
            return [Triangle([self[0], self[i+1], self[i+2]]) for i in range(len(self)-2)]
        # TODO: Implement triangulate for concave polygons
