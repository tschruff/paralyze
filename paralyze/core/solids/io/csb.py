from .. import Capsule, Cylinder, Sphere
from .. import create_capsule, create_cylinder, create_sphere
from paralyze.core.algebra import Vector

import os
import logging
import codecs

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

    AllTypes = (
        SphereType, BoxType, CapsuleType, CylinderType,
        PlaneType, TriangleMeshType, UnionType, EllipsoidType
    )

    SupportedTypes = (SphereType, PlaneType)

    # public interface members

    @staticmethod
    def load(f, delimiter=',', linesep=os.linesep, encoding='utf-8',
             dynamic=False, scale=1.0, offset=Vector(0),
             filter=lambda solid: True):
        """Loads solids from a file.

        A csb file is a csv (Comma Separated Values) file where each row represents
        a solid body. Each row looks as follows (delimiter=','):

            stype (int),x (float),y (float),z (float),[type specific values]

        A row describing a Sphere would look as follows:

            1,23.4,45.3,-56.34,0.45

        where the last value represents the sphere diameter. For more details,
        please refer to the _parse_* methods below.

        Parameters
        ----------
        f: file-like or path-like
            If f is file-like it is assumed that f is already open for reading
            and f will not be closed after contents have been read.
            If f is path-like a file object will be created, opened, read, and
            closed.
        delimiter: str
            The string or char that is used to limit csv columns. Default is ','.
        linesep: str
            The newline str/char. Defaults to os.linesep.
        encoding: str
            The file encoding. Default is 'utf-8'.
        dynamic: bool
            Determines whether solids should be created as subclasses of
            :class:`paralyze.core.solids.solid.ISolid` or
            :class:`paralyze.core.solids.solid.IDynamicSolid`. Please refer to
            :module:`paralyze.core.solids.solid` for more details. Default is
            False.
        scale: float (0, inf)
            The length scale factor. Default is 1.0.
        offset: Vector
            The offset that is applied to all solid center points. Default is Vector(0).
        filter: function
            A custom filter function, i.e. something like :func:`filter`. The default
            value returns True for all solids.

        Returns
        -------
        set:
            All solids that have been parsed from the file and that conformed to
            the ``filter`` argument.
        """

        solids = set()

        if isinstance(f, str):  # open/read/close if f is path-like
            path = f
            f = codecs.open(path, 'r', encoding=encoding)
            content = f.read()
            f.close()
        else:  # explicit type testing
            path = str(f)
            content = f.read()
            if isinstance(content, bytes):  # convert content to str
                content = content.decode(encoding)
            else:
                content = content
        content = content.split(linesep)

        err_str = """
        Error while reading line {line_num} in file {path}:
            {line}
        Error message: {msg}"""

        for i, line in enumerate(content):
            if line.startswith('#'):  # line is a comment
                continue
            line = line.split(delimiter)
            if len(line) <= 1:  # line is empty
                continue

            try:
                stype = int(line[0])
            except OSError as e:
                raise OSError(err_str.format(line_num=i+1, path=path, line=line, msg=e.args[0]))

            if stype not in CSBFile.SupportedTypes:
                logger.warn("Solid type %d is not supported by CSBFile. Skipping import." % stype)
            else:
                solid = CSBFile._parse_solid(stype, line, dynamic, scale, offset)
                if filter(solid):
                    solids.add(solid)

        return solids

    @staticmethod
    def save(filename, solids, delimiter=',', linesep=os.linesep):
        with open(filename, 'w') as csb:
            for solid in solids:
                data = CSBFile.get_data(solid)
                csb.write(delimiter.join(map(str, data)) + linesep)

    @staticmethod
    def get_type(solid):
        """
        Parameters
        ----------
        solid: Solid

        Returns
        -------
        sid: int
            The internal solid type id used to detect the type of solids, e.g.
            sphere, cylinder, etc.
        """
        if isinstance(solid, Capsule):
            return CSBFile.CapsuleType
        if isinstance(solid, Cylinder):
            return CSBFile.CylinderType
        if isinstance(solid, Sphere):
            return CSBFile.SphereType

    @staticmethod
    def get_data(solid):
        c = solid.center
        data = [CSBFile.get_type(solid), c[0], c[1], c[2]]
        if isinstance(solid, Sphere):
            data.append(solid.radius * 2.0)
        else:
            log.warning('CSBFile.get_data not implemented for solid or type {}'.format(type(solid)))
        return data

    # parser methods

    @staticmethod
    def _parse_solid(stype, line, dynamic, scale, offset, **kwargs):
        if stype == CSBFile.CapsuleType:
            return CSBFile._parse_capsule(line, dynamic, scale, offset, **kwargs)
        if stype == CSBFile.CylinderType:
            return CSBFile._parse_cylinder(line, dynamic, scale, offset, **kwargs)
        if stype == CSBFile.SphereType:
            return CSBFile._parse_sphere(line, dynamic, scale, offset, **kwargs)
        elif stype == CSBFile.PlaneType:
            return CSBFile._parse_plane(line, dynamic, scale, offset, **kwargs)

    @staticmethod
    def _parse_vector(data, scale=1.0, offset=Vector(0)):
        assert len(data) == 3
        return Vector((float(data[0]), float(data[1]), float(data[2]))) * scale + offset

    @staticmethod
    def _parse_capsule(line, dynamic, scale, offset, **kwargs):
        raise NotImplementedError()

    @staticmethod
    def _parse_cylinder(line, dynamic, scale, offset, **kwargs):
        raise NotImplementedError()

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
