from .parsable import Parsable
from .algebra import AABB, Interval, Vector
from .field import Cell, CellInterval

import re
import ast


def get_input(prompt, default=None, options=()):
    value = input('>> %s %s: [%s] ' % (prompt, '/'.join(map(str, options)), str(default or '-'))) or default
    if default:
        return type(default)(value)
    return value


def type_cast(str):
    str = ''.join(str.split())
    if re.match(AABB.Pattern, str):
        return AABB.parse(str)
    if re.match(Interval.Pattern, str):
        return Interval.parse(str)
    if re.match(Vector.Pattern, str):
        return Vector.parse(str)
    if re.match(Cell.Pattern, str):
        return Cell.parse(str)
    if re.match(CellInterval.Pattern, str):
        return CellInterval.parse(str)
    if re.match(Parsable.Decimal, str):
        return float(str)
    if re.match(Parsable.Integer, str):
        return int(str)
    # consider everything else a string
    return str