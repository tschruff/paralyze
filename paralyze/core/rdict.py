from collections.abc import MutableMapping
from string import Formatter
import re


class rdict(MutableMapping):

    VarPattern = r"(?<!\{)\{([^\{\}]+)\}(?!\})"

    def __init__(self, dict):
        self._dict = dict
        self._format = Formatter()
        self._sub = set([])
        self._p = None

    def __delitem__(self, key):
        del self._dict[key]

    def __getitem__(self, key):
        return self.get(key)

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)

    def __setitem__(self, key, value):
        self._dict[key] = value

    def keys(self):
        return self._dict.keys()

    def get(self, key, default=None):

        if key in self._sub:
            raise ValueError('Cyclic reference for key "{}".'.format(key))

        self._sub.add(key)
        if key in self._dict:
            value = self._dict[key]
            # formatting is only applied to the first dict level
            while self.contains_var(value):
                value = self._format.vformat(value, [], self._dict)

        else:
            value = default

        self._sub.remove(key)
        return value

    def get_raw(self, key, default=None):
        return self._dict.get(key, default)

    def fields(self):
        """ Parses all dict values for variables, e.g. something like this "{some_var}", "{dict[key]}", "{obj.attr}"
        and returns them as a set.

        Returns
        -------
        fields: set
            The set of replacement fields
        """
        var = []
        for val in self._dict.values():
            if not isinstance(val, str):
                continue
            result = self._format.parse(val)
            for literal_text, field_name, format_spec, conversion in result:
                if field_name is not None:
                    var.append(field_name)
        return set(var)

    def vars(self):
        variables = []
        for field in self.fields():
            try:
                self._format.get_field(field, [], self._dict)
            except KeyError:
                variables.append(field)
        return set(variables)

    def var_items(self):
        return {var: self[var] for var in self.vars() if var in self}

    @staticmethod
    def contains_var(value):
        if type(value) is not str:
            return False
        return len(re.findall(rdict.VarPattern, value)) > 0
