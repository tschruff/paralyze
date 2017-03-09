from .parsable import Parsable
from .algebra import AABB, Interval, Vector
from .fields import Cell, CellInterval

import re
import ast


def get_input(prompt, default=None, options=()):
    value = input('>> %s %s: [%s] ' % (prompt, '/'.join(map(str, options)), str(default or '-'))) or default
    if default:
        return type(default)(value)
    return value


def type_cast(arg):
    if re.match(AABB.Pattern, arg):
        return AABB.parse(arg)
    if re.match(Interval.Pattern, arg):
        return Interval.parse(arg)
    if re.match(Vector.Pattern, arg):
        return Vector.parse(arg)
    if re.match(Cell.Pattern, arg):
        return Cell.parse(arg)
    if re.match(CellInterval.Pattern, arg):
        return CellInterval.parse(arg)
    if re.match(Parsable.Integer, arg):
        return int(arg)
    if re.match(Parsable.Decimal, arg):
        return float(arg)
    # consider everything else a string
    return str(arg)