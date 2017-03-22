from .. import create_capsule, create_cylinder, create_sphere
from paralyze.core.algebra import Vector

import glob
import os
import logging

logger = logging.getLogger(__name__)


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
    def load(filename, delimiter=',', dynamic=False, scale=1.0, offset=Vector(0), filter=None):
        bodies = []

        names = glob.glob(filename)
        if not len(names):
            logger.error('No such file or directory: %s' % filename)
            return bodies

        for name in names:
            with open(name, 'r') as csb:
                for line in csb:
                    line = line.split(delimiter)
                    g_type = int(line[0])

                    if g_type not in CSBFile.SupportedTypes:
                        logger.warn("Geometry %d is not supported by CSBFile. Skipping import." % g_type)
                    else:
                        body = CSBFile._parse_body(g_type, line, dynamic, scale, offset)
                        if filter is None or filter(body):
                            bodies.append(body)

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
        if isinstance(body, Cylinder):
            return CSBFile.CylinderType
        if isinstance(body, Capsule):
            return CSBFile.CapsuleType

    @staticmethod
    def get_data(body):
        pos = body.position()
        data = [CSBFile.get_geom_type(body), pos[0], pos[1], pos[2]]

        if isinstance(body, Sphere):
            data.append(body.radius() * 2.0)

        return data

    # parser methods

    @staticmethod
    def _parse_body(geom_type, line, dynamic, scale, offset, **kwargs):
        if geom_type == CSBFile.CapsuleType:
            return CSBFile._parse_capsule(line, dynamic, scale, offset, **kwargs)
        if geom_type == CSBFile.CylinderType:
            return CSBFile._parse_cylinder(line, dynamic, scale, offset, **kwargs)
        if geom_type == CSBFile.SphereType:
            return CSBFile._parse_sphere(line, dynamic, scale, offset, **kwargs)
        elif geom_type == CSBFile.PlaneType:
            return CSBFile._parse_plane(line, dynamic, scale, offset, **kwargs)

    @staticmethod
    def _parse_vector(data, scale=1.0, offset=Vector(0)):
        assert len(data) == 3
        vector = Vector((float(data[0]), float(data[1]), float(data[2]))) * scale + offset
        return vector

    @staticmethod
    def _parse_sphere(line, dynamic, scale, offset, **kwargs):
        assert int(line[0]) == CSBFile.SphereType
        assert len(line) >= 5

        center = CSBFile._parse_vector(line[1:4], scale, offset)
        diameter = float(line[4]) * scale

        return create_sphere(center, radius=diameter/2, dynamic=dynamic, **kwargs)

    @staticmethod
    def _parse_plane(line, dynamic, scale, offset, **kwargs):
        assert int(line[0]) == CSBFile.PlaneType
        assert len(line) >= 7

        center = CSBFile._parse_vector(line[1:4], scale, offset)
        normal = CSBFile._parse_vector(line[4:7])

        return create_plane(center, normal=normal, dynamic=dynamic, **kwargs)
