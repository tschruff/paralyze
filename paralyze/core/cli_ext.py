from .parsable import Parsable
from .algebra import AABB, Interval, Vector
from .fields import Cell, CellInterval

import re
import ast
import logging

logger = logging.getLogger(__name__)


def get_input(prompt, default=None, options=()):
    value = input('>> %s %s: [%s] ' % (prompt, '/'.join(map(str, options)), str(default or '-'))) or default
    if default:
        return type(default)(value)
    return value


def type_cast(arg):
    try:
        if re.fullmatch(AABB.Pattern, arg):
            return AABB.parse(arg)
        if re.fullmatch(Interval.Pattern, arg):
            return Interval.parse(arg)
        if re.fullmatch(Vector.Pattern, arg):
            return Vector.parse(arg)
        if re.fullmatch(Cell.Pattern, arg):
            return Cell.parse(arg)
        if re.fullmatch(CellInterval.Pattern, arg):
            return CellInterval.parse(arg)
        if re.fullmatch(Parsable.Integer, arg):
            return int(arg)
        if re.fullmatch(Parsable.Decimal, arg):
            return float(arg)
    except ValueError as e:
        logger.error('error during type conversion: {}'.format(e.args[0]))
        raise e
    # consider everything else a string
    return str(arg)