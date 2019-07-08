from ..algebra import AABB, Vector, Quaternion

import uuid
import abc
import numpy as np


DEFAULT_DTYPE = 'float32'


class ISolid(object):

    def __init__(self):
        self.__id = uuid.uuid4().int
        self._dirty = False

    def __hash__(self):
        return self.id

    @property
    @abc.abstractmethod
    def aabb(self):
        """Returns the solids axis-aligned bounding box (with respect to the
        roation of the solid).
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def center(self):
        """Returns the solids center coordinates.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def contains(self, point):
        """Returns a bool indicating whether the given ``point`` is inside
        the solid.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def equivalent_mesh_size(self):
        """Returns the bodies size equal to the mesh size at which the bodies
        would not fit through a sieving mesh anymore.
        """
        raise NotImplementedError

    @property
    def id(self):
        return self.__id

    @abc.abstractmethod
    def move(self, delta):
        """Moves the center of the solid by a given ``delta`` vector.
        """
        raise NotImplementedError

    def requires_update(self):
        """Returns a bool indicating whether the solids' state has changed and
        :func:`update` must be called in order to adjust to the changes.
        """
        return self._dirty

    @abc.abstractmethod
    def rotate(self, axis, angle):
        """Rotates the solid by ``angle`` around the given ``axis``.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def rotation_matrix(self):
        """Returns the solids rotation matrix (3x3 matrix).
        """
        raise NotImplementedError

    @abc.abstractmethod
    def set_rotation(self, *args, **kwargs):
        """
        """
        raise NotImplementedError

    @abc.abstractmethod
    def update_aabb(self):
        """
        """
        raise NotImplementedError

    def update(self):
        """Update solid state if necessary.
        """
        if self._dirty:
            self.update_aabb()
            self._dirty = False

    @property
    @abc.abstractmethod
    def volume(self):
        """Returns the solids volume.
        """
        raise NotImplementedError

    @property
    def x(self):
        """Returns the x-coordinate of the solid's center.
        """
        return self.center.x

    @property
    def y(self):
        """Returns the y-coordinate of the solid's center.
        """
        return self.center.y

    @property
    def z(self):
        """Returns the z-coordinate of the solid's center.
        """
        return self.center.z


class IDynamicSolid(ISolid):

    @property
    @abc.abstractmethod
    def angular_velocity(self):
        """Returns the current angular (rotational) velocity of the solid (Vector).
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def density(self):
        """Returns the solids density (float).
        """
        raise NotImplementedError

    @abc.abstractmethod
    def add_force(self, force, pos=None):
        """
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def force(self):
        """Returns the force that acts on the solid (Vector).
        """
        raise NotImplementedError

    @abc.abstractmethod
    def reset_force(self):
        """Resets the force that acts on the solid to zero.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def inertia(self):
        """Returns the solids inertia (3x3 matrix).
        """
        raise NotImplementedError

    @abc.abstractmethod
    def update_inertia(self):
        """
        """
        raise NotImplementedError

    def update(self):
        """Update solid state if necessary.
        """
        if self._dirty:
            self.update_aabb()
            self.update_inertia()
            self._dirty = False

    @property
    def inertia_tensor(self):
        """
        """
        r = self.rotation_matrix
        return r * self.inertia * r.T

    @property
    @abc.abstractmethod
    def linear_velocity(self):
        """Returns the current linear (translational) velocity of the solid (Vector).
        """
        raise NotImplementedError

    @property
    def mass(self):
        """Returns the solids mass (float).
        """
        return self.volume * self.density

    @abc.abstractmethod
    def add_torque(self, torque):
        """
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def torque(self):
        """Returns the torque that acts in the solid (Vector).
        """
        raise NotImplementedError

    @abc.abstractmethod
    def reset_torque(self):
        """Resets the torque that acts on the solid to zero.
        """
        raise NotImplementedError


class PSolid(ISolid):

    Length = 13
    AABBSlice = slice(0, 6)
    CenterSlice = slice(6, 9)
    QuaternionSlice = slice(9, 13)

    def __init__(self, *args, **kwargs):
        ISolid.__init__(self)

        self._data = np.zeros(self.Length, dtype=kwargs.get('dtype', DEFAULT_DTYPE))

        center = kwargs.get('center', 0)
        rot_axis = kwargs.get('rotation_axis', (1, 0, 0))
        rot_angle = kwargs.get('rotation_angle', 0)

        if len(args) > 0:
            center = args[0]
        if len(args) > 1:
            rot_axis = args[1]
        if len(args) > 2:
            rot_angle = args[2]

        self.center = center
        self.quaternion = Quaternion(axis=rot_axis, angle=rot_angle)

    @property
    def aabb(self):
        return self._data[PSolid.AABBSlice].view(AABB)

    @property
    def center(self):
        return self._data[PSolid.CenterSlice].view(Vector)

    @center.setter
    def center(self, center):
        self._data[PSolid.CenterSlice] = center
        self._dirty = True

    @property
    def dtype(self):
        return self._data.dtype

    def move(self, delta):
        """Moves the center of the solid by a given ``delta`` vector.
        """
        self.center += delta

    @property
    def quaternion(self):
        """Returns a Quaternion view of the quaterion portion of the array.
        """
        return self._data[PSolid.QuaternionSlice].view(Quaternion)

    @quaternion.setter
    def quaternion(self, quat):
        self._data[PSolid.QuaternionSlice] = quat
        self._dirty = True

    def rotate(self, axis, angle):
        """Rotates the solid by ``angle`` around the given ``axis``.
        """
        self.quaternion += Quaternion(axis=axis, angle=angle)

    @property
    def rotation_matrix(self):
        return self.quaternion.rotation_matrix

    def set_rotation(self, *args, **kwargs):
        self.quaternion = Quaternion(*args, **kwargs)

    def to_array(self):
        """Returns the numpy array that holds all the solid's data
        """
        return self._data


class DynamicPSolid(IDynamicSolid, PSolid):

    Length = PSolid.Length + 13
    DensityIndex = PSolid.Length
    ForceSlice = slice(PSolid.Length+1 , PSolid.Length+4 )
    TorqueSlice = slice(PSolid.Length+4 , PSolid.Length+7 )
    LinVelSlice = slice(PSolid.Length+7 , PSolid.Length+10)
    AngVelSlice = slice(PSolid.Length+10, PSolid.Length+13)
    InertiaSlice = slice(PSolid.Length+13, PSolid.Length+22)

    def __init__(self, *args, **kwargs):
        density = kwargs.pop("density", 1.)
        force = kwargs.pop("force", 0)
        torque = kwargs.pop("torque", 0)
        linear_velocity = kwargs.pop("linear_velocity", 0)
        angular_velocity = kwargs.pop("angular_velocity", 0)
        PSolid.__init__(self, *args, **kwargs)
        self.density = density
        self.force = force
        self.torque = torque
        self.linear_velocity = linear_velocity
        self.angular_velocity = angular_velocity

    def add_force(self, force, pos=None):
        """
        """
        self.force += force
        if pos is not None:
            self.torque += (pos - self.center) * force

    def add_torque(self, torque):
        """
        """
        self.torque += torque

    @property
    def angular_velocity(self):
        return self._data[self.AngVelSlice].view(Vector)

    @angular_velocity.setter
    def angular_velocity(self, angular_velocity):
        self._data[self.AngVelSlice] = angular_velocity

    @property
    def density(self):
        return self._data[self.DensityIndex]

    @density.setter
    def density(self, density):
        self._data[self.DensityIndex] = density
        self._dirty = True

    @property
    def force(self):
        """
        """
        return self._data[self.ForceSlice].view(Vector)

    @force.setter
    def force(self, force):
        self._data[self.ForceSlice] = force
        self._dirty = True

    @property
    def inertia(self):
        return self._data[self.InertiaSlice].reshape((3, 3))

    @property
    def linear_velocity(self):
        return self._data[self.LinVelSlice].view(Vector)

    @linear_velocity.setter
    def linear_velocity(self, linear_velocity):
        self._data[self.LinVelSlice] = linear_velocity

    def reset_force(self):
        self.force = Vector(0)

    def reset_torque(self):
        self.torque = Vector(0)

    @property
    def torque(self):
        return self._data[self.TorqueSlice].view(Vector)

    @torque.setter
    def torque(self, torque):
        self._data[self.TorqueSlice] = torque
