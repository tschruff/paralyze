from paralyze.core.algebra import Vector, AABB, Quaternion
from paralyze.core.algebra import ReferenceFrame as RF

import copy
import uuid


class Body(object):

    def __init__(self, pos, parent=None, visible=False, **kwargs):

        self._id = uuid.uuid4()
        self._pos = Vector(pos)
        self._center = Vector(0)
        self._aabb = AABB(0)
        self._q = Quaternion()
        self._scale = Vector(1)
        self._data = kwargs

        self._parent = parent
        self._source = None
        self._shadows = []

        self._visible = visible

        # body volume
        self._v = 0.0

    def __copy__(self):
        """ Creates a shadow copy of the underlying bodies instance.

        :return: A shadow copy of the underlying bodies instance.
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
            # except for id, parent, and shadow copies
            data = self.__dict__.copy()
            data['_parent'] = self  # TODO: Is storing a pointer critical?
            del data['_id']
            del data['_shadowIds']
            # and update the new instance with this data
            shadow.__dict__.update(data)
            # store shadow id
            self._shadows.append(shadow.id())
            return shadow

    def __del__(self):
        if self.is_shadow_copy():
            self._source.remove_shadow_copy(self)

    def __eq__(self, other):
        return self.id() == other.id()

    def __getitem__(self, key):
        return self._data[key]

    def __hash__(self):
        return hash(self._id)

    def __setitem__(self, key, value):
        self._data[key] = value

    def id(self):
        return self._id

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set_visible(self, visible):
        self._visible = visible

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

    def source(self):
        return self._source

    def remove_shadow_copy(self, shadow):
        self._shadows.remove(shadow.id())

    #################
    # Body geometry #
    #################

    def bounding_box(self):
        return self._aabb

    def center(self):
        return self._center

    def equivalent_mesh_size(self):
        """
        Returns the bodies size equal to the mesh size at which the bodies
        would not fit through the mesh anymore.

        :return:
        """
        raise NotImplementedError('Every bodies subclass must implement the equivalent_mesh_size() member')

    def contains(self, point):
        raise NotImplementedError('Every Body subclass must implement the contains() member')

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

    def _update_geometry(self):
        raise NotImplementedError()

