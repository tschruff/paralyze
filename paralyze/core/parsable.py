import re


class Parsable(object):

    Decimal = r"[+-]?(\d*\.?\d+|\d+\.?|inf)"
    Integer = r"[+-]?\d+"

    Pattern = r""

    @classmethod
    def parse(cls, str):
        if not len(cls.Pattern):
            raise NotImplementedError('Every subclass of Parsable must implement the Pattern member!')
        pattern = re.compile(cls.Pattern)
        str = ''.join(str.split())
        if not pattern.match(str):
            raise ValueError('{} is not a valid representation of {}'.format(str, cls))
        kwargs = [m.groupdict() for m in pattern.finditer(str)][0]
        return cls(**kwargs)
