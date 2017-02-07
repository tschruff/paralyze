from string import Formatter
import re


class rdict(object):

    def __init__(self, dictionary):
        self._format = Formatter()
        self._dict = dictionary
        self._sub = set([])

    def __getitem__(self, key):
        if key in self._sub:
            raise ValueError("Cyclic reference. Key: %s." % key)
        self._sub.add(key)
        value = self._dict[key]
        if type(value) == str:
            value = self._format.vformat(value, [], self)
        self._sub.remove(key)
        return value

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __str__(self):
        return str(self._dict)

    def keys(self):
        return self._dict.keys()

    def update(self, other):
        self._dict.update(other)

    def variables(self):
        vars = []
        for item in self._dict.values():
            if type(item) != str:
                continue
            vars.extend(re.findall(r"\{([a-zA-Z_]+)\}", item))
        vars = set(vars)
        keys = set(self._dict)
        return vars.difference(keys)
