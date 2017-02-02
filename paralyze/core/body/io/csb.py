from paralyze.core.body import Bodies, Plane, Sphere
from paralyze.core.algebra import Vector

import glob
import os
import logging


class CSBFile(object):

    SphereType = 1
    BoxType = 2
    CapsuleType = 3
    CylinderType = 4
    PlaneType = 5
    TriangleMeshType = 6
    UnionType = 7
    EllipsoidType = 8

    AllTypes = (SphereType, BoxType, CapsuleType, CylinderType, PlaneType, TriangleMeshType, UnionType, EllipsoidType)
    SupportedTypes = (SphereType, PlaneType)

    # public interface members

    @staticmethod
    def load(filename, delimiter=',', **kwargs):
        log = logging.getLogger(__name__)

        bodies = Bodies()
        parser = CSBFile()

        names = glob.glob(filename)
        if not len(names):
            log.error('No such file or directory: %s' % filename)
            return bodies

        for name in names:
            with open(name, 'r') as csb:
                for line in csb:
                    line = line.split(delimiter)
                    g_type = int(line[0])

                    if g_type not in CSBFile.SupportedTypes:
                        log.warn("Geometry %d is currently not supported by CSBFile. Skipping import." % g_type)
                    else:
                        bodies.add(parser.parse_body(g_type, line, **kwargs))

        return bodies

    @staticmethod
    def save(filename, bodies, delimiter=','):
        parser = CSBFile()
        with open(filename, 'w') as csb:
            for body in bodies:
                data = parser.get_data(body)
                csb.write(delimiter.join(map(str, data)) + os.linesep)

    # instance members

    def get_geom_type(self, body):
        """

        :param body:
        :rtype: int
        """
        if isinstance(body, Sphere):
            return self.SphereType

    def get_data(self, body):
        pos = body.position()
        data = [self.get_geom_type(body), pos[0], pos[1], pos[2]]

        if isinstance(body, Sphere):
            data.append(body.radius() * 2.0)

        return data

    # parser methods

    def parse_body(self, geom_type, line, **kwargs):
        if geom_type == self.SphereType:
            return self.parse_sphere(line, **kwargs)
        elif geom_type == self.PlaneType:
            return self.parse_plane(line, **kwargs)

    def parse_vector(self, line):
        assert len(line) == 3
        return Vector((float(line[0]), float(line[1]), float(line[2])))

    def parse_sphere(self, line, **kwargs):
        assert int(line[0]) == self.SphereType
        assert len(line) >= 5

        center = self.parse_vector(line[1:4])
        diameter = float(line[4])

        return Sphere(center, diameter / 2.0, **kwargs)

    def parse_plane(self, line, **kwargs):
        assert int(line[0]) == self.PlaneType
        assert len(line) >= 7

        center = self.parse_vector(line[1:4])
        normal = self.parse_vector(line[4:7])

        return Plane(center, normal, **kwargs)
