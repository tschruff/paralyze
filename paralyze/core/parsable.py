import re


class Parsable(object):

    Decimal = r"[+-]?(\d*\.?\d+|\d+\.?|inf)"
    Integer = r"[+-]?\d+"

    Pattern = r""

    @classmethod
    def parse(cls, str):
        if not len(cls.Pattern):
            raise NotImplementedError('Every subclass of Parsable must implement the Pattern member!')
        if not re.fullmatch(cls.Pattern, str):
            raise ValueError('{} is not a valid representation of {}'.format(str, cls))
        pattern = re.compile(cls.Pattern)
        kwargs = [m.groupdict() for m in pattern.finditer(str)][0]
        return cls(**kwargs)
