from ..algebra import AABB, Vector, Quaternion

import copy
import uuid
import abc
import numpy as np


class ISolid(object):

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

    @abc.abstractmethod
    def move(self, delta):
        """Moves the center of the solid by a given ``delta`` vector.
        """
        raise NotImplementedError

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

    @property
    @abc.abstractmethod
    def volume(self):
        """Returns the solids volume.
        """
        raise NotImplementedError


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


class PSolid(ISolid, np.ndarray):
    Parameters = ["center", "quaternion", "aabb"]
    Length = 13

    CenterSlice = slice(0, 3)
    QuatSlice = slice(3, 7)
    AABBSlice = slice(7, 13)

    def __new__(cls, *args, **kwargs):
        return np.zeros(cls.Length, dtype=np.float64).view(cls)

    def __init__(self, *args, **kwargs):

        center = kwargs.get("center", 0)
        rot_axis = kwargs.get("rotation_axis", (1, 0, 0))
        rot_angle = kwargs.get("rotation_angle", 0)

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
        return self[self.AABBSlice].view(AABB)

    @property
    def center(self):
        return self[self.CenterSlice].view(Vector)

    @center.setter
    def center(self, pos):
        self[self.CenterSlice] = Vector(pos)

    def move(self, delta):
        """Moves the center of the solid by a given ``delta`` vector.
        """
        self.center += delta

    def rotate(self, axis, angle):
        """Rotates the solid by ``angle`` around the given ``axis``.
        """
        self.quaternion += Quaternion(axis=axis, angle=angle)

    @property
    def quaternion(self):
        """Returns a Quaternion view of the quaterion portion of the array.
        """
        return self[self.QuatSlice].view(Quaternion)

    @quaternion.setter
    def quaternion(self, quat):
        self[self.QuatSlice] = Quaternion(quat)

    @property
    def rotation_matrix(self):
        return self.quaternion.rotation_matrix

    def set_rotation(self, *args, **kwargs):
        self.quaternion = Quaternion(*args, **kwargs)


class DynamicPSolid(IDynamicSolid, PSolid):
    Parameters = ["density", "force", "torque", "linear_velocity", "angular_velocity"]
    Length = PSolid.Length + 13

    DensityIndex = PSolid.Length
    ForceSlice   = slice(PSolid.Length+1 , PSolid.Length+4 )
    TorqueSlice  = slice(PSolid.Length+4 , PSolid.Length+7 )
    LinVelSlice  = slice(PSolid.Length+7 , PSolid.Length+10)
    AngVelSlice  = slice(PSolid.Length+10, PSolid.Length+13)

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

    @property
    def angular_velocity(self):
        return self[self.AngVelSlice].view(Vector)

    @angular_velocity.setter
    def angular_velocity(self, angular_velocity):
        self[self.AngVelSlice] = Vector(angular_velocity)

    @property
    def density(self):
        return self[self.DensityIndex]

    @density.setter
    def density(self, density):
        self[self.DensityIndex] = float(density)

    def add_force(self, force, pos=None):
        """
        """
        self.force += force
        if pos is not None:
            self.torque += (pos - self.center) * force

    @property
    def force(self):
        """
        """
        return self[self.ForceSlice].view(Vector)

    @force.setter
    def force(self, force):
        self[self.ForceSlice] = Vector(force)

    def reset_force(self):
        self.force = Vector(0)

    @property
    def linear_velocity(self):
        return self[self.LinVelSlice].view(Vector)

    @linear_velocity.setter
    def linear_velocity(self, linear_velocity):
        self[self.LinVelSlice] = Vector(linear_velocity)

    def add_torque(self, torque):
        """
        """
        self.torque += torque

    @property
    def torque(self):
        return self[self.TorqueSlice].view(Vector)

    @torque.setter
    def torque(self, torque):
        self[self.TorqueSlice] = Vector(torque)

    def reset_torque(self):
        self.torque = Vector(0)
