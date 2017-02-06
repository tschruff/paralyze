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
                        bodies.add(CSBFile.parse_body(g_type, line, **kwargs))

        return bodies

    @staticmethod
    def save(filename, bodies, delimiter=','):
        with open(filename, 'w') as csb:
            for body in bodies:
                data = CSBFile.get_data(body)
                csb.write(delimiter.join(map(str, data)) + os.linesep)

    @staticmethod
    def get_geom_type(body):
        """

        :param body:
        :rtype: int
        """
        if isinstance(body, Sphere):
            return CSBFile.SphereType

    @staticmethod
    def get_data(body):
        pos = body.position()
        data = [CSBFile.get_geom_type(body), pos[0], pos[1], pos[2]]

        if isinstance(body, Sphere):
            data.append(body.radius() * 2.0)

        return data

    # parser methods

    @staticmethod
    def parse_body(geom_type, line, **kwargs):
        if geom_type == CSBFile.SphereType:
            return CSBFile.parse_sphere(line, **kwargs)
        elif geom_type == CSBFile.PlaneType:
            return CSBFile.parse_plane(line, **kwargs)

    @staticmethod
    def parse_vector(line):
        assert len(line) == 3
        return Vector((float(line[0]), float(line[1]), float(line[2])))

    @staticmethod
    def parse_sphere(line, **kwargs):
        assert int(line[0]) == CSBFile.SphereType
        assert len(line) >= 5

        center = CSBFile.parse_vector(line[1:4])
        diameter = float(line[4])

        return Sphere(center, diameter / 2.0, **kwargs)

    @staticmethod
    def parse_plane(line, **kwargs):
        assert int(line[0]) == CSBFile.PlaneType
        assert len(line) >= 7

        center = CSBFile.parse_vector(line[1:4])
        normal = CSBFile.parse_vector(line[4:7])

        return Plane(center, normal, **kwargs)
