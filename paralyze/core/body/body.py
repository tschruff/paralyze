from paralyze.core.algebra import Vector
from paralyze.core.algebra import ReferenceFrame as RF

# try to import the fast c version of superimposition_matrix
# if that fails, fall back to bundled (slow) python version
try:
    from _transformations import superimposition_matrix
except ImportError:
    from paralyze.core.algebra.transformations import superimposition_matrix

import copy
import uuid


class Body(object):

    def __init__(self, pos, parent=None, visible=False, **kwargs):

        self._id = uuid.uuid4()
        self._pos = Vector(pos)
        self._center = Vector(0)
        self._data = kwargs

        self._parent = parent
        self._source = None
        self._shadows = []

        self._visible = visible

        # body volume
        self._v = 0.0

    def __copy__(self):
        """ Creates a shadow copy of the underlying body instance.

        :return: A shadow copy of the underlying body instance.
        """

        # if called instance is a shadow copy itself call parent
        # body to create a shadow copy instead
        if self.is_shadow_copy():
            assert isinstance(self._source, Body)
            return self._source.create_shadow_copy()
        # called body instance is the original body (not a shadow copy)
        else:
            # create a new body instance
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

    def aabb(self):
        raise NotImplementedError('Every Body subclass must implement the aabb() method')

    def center(self):
        return self._center

    def characteristic_size(self):
        """ Returns the body size equal to the mesh size at which the body
        would not fit through the mesh anymore.

        :return:
        """
        raise NotImplementedError('Every body subclass must implement the characteristic_size() method')

    def contains(self, point):
        raise NotImplementedError('Every Body subclass must implement the contains() method')

    def create_shadow_copy(self):
        return copy.copy(self)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def id(self):
        return self._id

    def is_shadow_copy(self):
        return self._source is not None

    def num_shadow_copies(self):
        return len(self._shadows)

    def scale(self, scale_factor):
        self.set_position(self.position() * scale_factor, RF.GLOBAL)

    def set_visible(self, visible):
        self._visible = visible

    def source(self):
        return self._source

    def parent(self):
        return self._parent

    def position(self):
        return self._pos

    def remove_shadow_copy(self, shadow):
        self._shadows.remove(shadow.id())

    def set_center(self, center):
        self._center = center

    def set_rotation(self, *args, frame=RF.LOCAL):
        pass

    def set_position(self, pos, frame=RF.GLOBAL):
        if frame == RF.GLOBAL:
            self._pos = pos
        elif frame == RF.PARENT:
            self._pos = self.parent().origin() + pos
        elif frame == RF.LOCAL:
            self._pos += pos

    def volume(self):
        return self._v
