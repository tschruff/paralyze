import sys
import operator
import re


class Interval(object):
    """ Represents a numeric interval.

    """

    Open, Closed = range(2)
    Inf = sys.maxsize

    def __init__(self, *args, **kwargs):
        """
        :param args:
        :param kwargs:
            - min_value
            - max_value
            - bounds
        :return:
        """
        args = list(args)

        # only str argument is provided
        if len(args) == 1:
            bounds = self.__init_from_str(args[0])
        else:
            self.min = args[0] if len(args) > 0 else kwargs['min_value']
            self.max = args[1] if len(args) > 1 else kwargs['max_value']
            bounds = args[2] if len(args) > 2 else kwargs.get('bounds', (self.Open, self.Open))
        self.min_bound = bounds[0]
        self.max_bound = bounds[1]

        if bounds[0] == Interval.Open:
            self._op_min = operator.ge
        elif bounds[0] == Interval.Closed:
            self._op_min = operator.gt
        else:
            raise ValueError('Unexpected lower bound value: %s' % str(bounds[0]))

        if bounds[1] == Interval.Open:
            self._op_max = operator.le
        elif bounds[1] == Interval.Closed:
            self._op_max = operator.lt
        else:
            raise ValueError('Unexpected upper bound value: %s' % str(bounds[1]))

        if not self.is_valid():
            raise ValueError('Invalid interval: %s' % str(self))

    def __bool__(self):
        return self.is_valid()

    def __contains__(self, value):
        return self._op_min(value, self.min) and self._op_max(value, self.max)

    def __str__(self):
        min_bounds = ['[', '(']
        max_bounds = [']', ')']
        return '{}{}, {}{}'.format(min_bounds[self.min_bound], str(self.min), str(self.max), max_bounds[self.max_bound])

    def __repr__(self):
        return 'Interval("{}")'.format(str(self))

    def is_valid(self):
        return self.max > self.min

    #############################################
    # PRIVATE MEMBER METHODS
    #############################################

    def __init_from_str(self, interval):
        p = re.compile('([\[\(])([-+]?(?:[0-9]+(?:.[0-9]*)?|inf))\s?,\s?([-+]?(?:[0-9]+(?:.[0-9]*)?|inf))([\]\)])')
        m = p.match(interval)
        if not m:
            raise ValueError('Invalid interval str: %s' % interval)
        bounds = (self.__str_to_bounds(m.group(1)), self.__str_to_bounds(m.group(4)))

        self.min = float(m.group(2))
        self.max = float(m.group(3))

        return bounds

    def __str_to_bounds(self, bounds_str):
        if bounds_str in ['(', ')']:
            return self.Closed
        elif bounds_str in ['[', ']']:
            return self.Open
        raise ValueError('Unexpected bounds str: %s' % bounds_str)

    @staticmethod
    def inf():
        return Interval(-sys.maxsize - 1, sys.maxsize)

    @staticmethod
    def parse(string):
        return Interval(string)
