from ..parsable import Parsable

import sys
import operator


class Interval(Parsable):
    """Represents a numeric interval.

    """

    Pattern = r"\A(?P<min_bound>[\[\(])" \
              r"(?P<min>[-+]?(\d*\.?\d+|\d+\.?|inf))\," \
              r"(?P<max>[-+]?(\d*\.?\d+|\d+\.?|inf))" \
              r"(?P<max_bound>[\]\)])\Z"

    MinBoundStr = ['[', '(']
    MinBoundOp = [operator.ge, operator.gt]
    MaxBoundStr = [']', ')']
    MaxBoundOp = [operator.le, operator.lt]

    Open, Closed = range(2)
    Inf = sys.maxsize

    def __init__(self, *args, **kwargs):
        """

        Parameters
        ----------
        args:

        kwargs:
            - min_value
            - max_value
            - min_bound
            - max_bound
            - bounds

        """
        args = list(args)

        self.min = args[0] if len(args) > 0 else float(kwargs.get('min', -float('inf')))
        self.max = args[1] if len(args) > 1 else float(kwargs.get('max', float('inf')))

        if len(args) == 3:
            self.min_bound = args[2][0]
            self.max_bound = args[2][1]
        elif len(args) == 4:
            self.min_bound = args[2]
            self.max_bound = args[3]
        elif 'bounds' in kwargs:
            bounds = kwargs['bounds']
            self.min_bound = bounds[0]
            self.max_bound = bounds[1]
        elif 'min_bound' in kwargs and 'max_bound' in kwargs:
            self.min_bound = kwargs['min_bound']
            self.max_bound = kwargs['max_bound']
        else:
            self.min_bound = self.Open
            self.max_bound = self.Open

        if isinstance(self.min_bound, str):
            self.min_bound = self.MinBoundStr.index(self.min_bound)
        else:
            self.min_bound = int(self.min_bound)
        if isinstance(self.max_bound, str):
            self.max_bound = self.MaxBoundStr.index(self.max_bound)
        else:
            self.max_bound = int(self.max_bound)

        self._op_max = self.MaxBoundOp[self.max_bound]
        self._op_min = self.MinBoundOp[self.min_bound]

    def __bool__(self):
        return self.is_valid

    def __contains__(self, value):
        return self._op_min(value, self.min) and self._op_max(value, self.max)

    def __str__(self):
        return '{}{},{}{}'.format(self.MinBoundStr[self.min_bound], str(self.min), str(self.max), self.MaxBoundStr[self.max_bound])

    def __repr__(self):
        return 'Interval(min={}, max={}, bounds=({}, {}))'.format(self.min, self.max, self.min_bound, self.max_bound)

    @property
    def bounds(self):
        return self.min_bound, self.max_bound

    @property
    def is_valid(self):
        return self.max > self.min

    @staticmethod
    def inf():
        return Interval(-sys.maxsize - 1, sys.maxsize)
