from ..algebra import Vector, AABB, Quaternion
from ..algebra import ReferenceFrame as RF
from .bodystorage import BodyStorage

import copy
import uuid
import abc


class Body(object):

    def __init__(self, center, parent=None, visible=True, **kwargs):

        self._id = uuid.uuid4()
        self._pos = Vector(center)
        self._center = Vector(0)
        self._aabb = AABB(0)
        self._q = Quaternion()
        self._scale = Vector(1)
        self._data = kwargs

        self._parent = parent

        self._source = None  # the source body id
        self._shadows = []  # a list of shadow copy ids

        self._visible = visible

        # body volume
        self._v = 0.0

    def __copy__(self):
        """ Creates a shadow copy of *self*.

        Returns
        -------
        shadow: Body
            A shadow copy of the underlying bodies instance.
        """

        # if called instance is a shadow copy itself call parent
        # bodies to create a shadow copy instead
        if self.is_shadow_copy():
            assert isinstance(self._source, Body)
            return self._source.create_shadow_copy()
        # called bodies instance is the original bodies (not a shadow copy)
        else:
            # create a new bodies instance
            shadow = type(self)(self._pos, **self._data)
            # copy also all subclass specific content from __dict__
            # except for id, source, and shadow copies
            data = self.__dict__.copy()
            data['_source'] = self.id()
            del data['_id']
            del data['_shadows']
            # and update the new instance with this data
            shadow.__dict__.update(data)
            # store shadow id
            self._shadows.append(shadow.id())
            return shadow

    def __del__(self):
        if self.is_shadow_copy():
            source = BodyStorage().get(self._source)
            if source is not None:  # maybe the source has already been deleted
                source.remove_shadow_copy(self)

    def __eq__(self, other):
        """

        Parameters
        ----------
        other: Body
            Another body instance to compare *self* to

        Returns
        -------
        equal: bool
            A bool indicating whether *self* and *other* are equal
        """
        if self.is_shadow_copy() and other.is_shadow_copy():
            return self._source == other.source_id()
        elif self.is_shadow_copy():
            return self._source == other.id()
        elif other.is_shadow_copy():
            return self.id() == other.source_id()
        return self.id() == other.id()

    def __getitem__(self, key):
        return self.get(key)

    def __hash__(self):
        return hash(self._id)

    def __setitem__(self, key, value):
        self.set(key, value)

    def id(self):
        return self._id

    def is_visible(self):
        return self._visible

    def set_visible(self, visible):
        self._visible = visible

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value

    def parent(self):
        return self._parent

    #################
    # Shadow copies #
    #################

    def create_shadow_copy(self):
        return copy.copy(self)

    def is_shadow_copy(self):
        return self._source is not None

    def num_shadow_copies(self):
        return len(self._shadows)

    def source_id(self):
        return self._source

    def shadow_copy_ids(self):
        return self._shadows

    def remove_shadow_copy(self, shadow):
        self._shadows.remove(shadow.id())

    #################
    # Body geometry #
    #################

    def aabb(self):
        return self._aabb

    def center(self):
        return self._center

    @abc.abstractmethod
    def equivalent_mesh_size(self):
        """ Returns the bodies size equal to the mesh size at which the bodies
        would not fit through the mesh anymore.
        """

    @abc.abstractmethod
    def contains(self, point):
        """

        :param point:
        :return:
        """

    def move(self, delta):
        self._pos += delta
        self._update_geometry()

    def position(self):
        return self._pos

    def rotate(self, delta):
        self._q *= delta
        self._update_geometry()

    def set_center(self, center):
        self._center = center
        self._update_geometry()

    def set_rotation(self, *args, frame=RF.GLOBAL):
        if len(args) == 1 and isinstance(args[0], Quaternion):  # we've got a quaternion
            q = args[0]
        elif len(args) == 2:  # we've got an axis and an angle
            q = Quaternion(vector=args[0], axis=args[1])
        elif len(args) == 3:  # we've got three Euler angles
            q = Quaternion(vector=args)
        elif len(args) == 4:  # we've got three values describing an axis and the angle
            q = Quaternion(vector=args[:-1], axis=args[-1])
        else:
            raise TypeError()

        if frame == RF.GLOBAL:
            self._pos = q.rotate(self._pos)
        self._update_geometry()

    def set_position(self, pos, frame=RF.GLOBAL):
        if frame == RF.GLOBAL:
            self._pos = pos
        elif frame == RF.PARENT:
            self._pos = self.parent().origin() + pos
        elif frame == RF.LOCAL:
            self._pos += pos
        self._update_geometry()

    def volume(self):
        return self._v

    @abc.abstractmethod
    def _update_geometry(self):
        """

        :return:
        """
