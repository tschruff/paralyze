from ..parsable import Parsable

import numpy as np


class Cell(np.ndarray, Parsable):

    Pattern = r"(?P<value>\({0},{0},{0}\))".format(Parsable.Integer)

    def __new__(cls, value):
        if isinstance(value, str):
            value = tuple(map(int, value.replace('(', '').replace(')', '').split(',')))
        elif not hasattr(value, '__len__'):
            value = (value, value, value)
        elif len(value) != 3:
            raise IndexError('Cell can only be initialized with a single number or a 3D tuple/list')
        return np.asarray(value, np.int64).view(cls)

    def __eq__(self, other):
        return np.array_equal(self, other)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return 'Cell([{c[0]:d}, {c[1]:d}, {c[2]:d}])'.format(c=self)

    def __str__(self):
        return '({c[0]:d}, {c[1]:d}, {c[2]:d})'.format(c=self)

    def shifted(self, delta):
        return self + Cell(delta)

    @property
    def x(self):
        return self[0]

    @property
    def y(self):
        return self[1]

    @property
    def z(self):
        return self[2]
