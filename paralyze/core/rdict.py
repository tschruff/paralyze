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

    def get(self, key, default=None):
        if key in self.keys():
            return self[key]
        else:
            return default

    def get_raw(self, key, default=None):
        return self._dict.get(key, default)

    def keys(self):
        return self._dict.keys()

    def update(self, other):
        self._dict.update(other)

    def variables(self):
        var = []
        for item in self._dict.values():
            if type(item) != str:
                continue
            var.extend(re.findall(r"\{([a-zA-Z_]+)\}", item))
        var = set(var)
        keys = set(self._dict)
        return var.difference(keys)
