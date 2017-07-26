"""Module documentation goes here...

"""
from collections import abc

import logging

logger = logging.getLogger(__name__)


class NestedDict(abc.MutableMapping):
    """

    Notes
    -----
    - the values or types of ``mapping`` are not modified.
    - all keys must be str instances
    """

    def __init__(self, mapping, level_sep='.'):

        if isinstance(mapping, NestedDict):
            self._d = dict(mapping.to_dict())
        else:
            self._d = dict(mapping)

        self._sep = level_sep

        for k, _ in iter_nested_mapping(self._d):
            if not isinstance(k, str):
                raise TypeError('all keys must be str, not {}'.format(type(k)))
            if len(k.split(level_sep)) > 1:
                raise ValueError('key "{}" must not contain level separator "{}"'.format(k, level_sep))

    def __getitem__(self, key):
        """
        Parameters
        ----------
        key

        Returns
        -------

        Notes
        -----
        Nested mapping types are returned as-is,
        that means they are not converted to NestedDict instances.

        """
        # logger.debug('NestedDict.__getitem__({})'.format(key))
        if isinstance(key, (list, tuple, set)):
            return tuple(self.__get(k) for k in key)
        return self.__get(key)

    def __get(self, key):
        item = self._d
        for level in self.split_key(key):
            item = item[level]
        return item

    def __setitem__(self, key, value):
        if len(self.split_key(key)) == 1:
            self._d[key] = value
        else:
            self.item_parent(key)[self.leaf_key(key)] = value

    def __delitem__(self, key):
        if len(self.split_key(key)) == 1:
            del self._d[key]
        else:
            del self.item_parent(key)[self.leaf_key(key)]

    def __iter__(self):
        return self.__iter_keys__(self._d)

    def __iter_leaf_items__(self, mapping, parent_key=''):
        for key, value in mapping.items():
            nested_key = self.join_keys(parent_key, key)
            if isinstance(value, abc.Mapping):
                yield from self.__iter_leaf_items__(value, nested_key)
            else:
                yield nested_key, value

    def __iter_items__(self, mapping, parent_key=''):
        for key, value in mapping.items():
            nested_key = self.join_keys(parent_key, key)
            yield nested_key, value
            if isinstance(value, abc.Mapping):
                yield from self.__iter_items__(value, nested_key)

    def __iter_keys__(self, mapping, parent_key=''):
        for key, value in mapping.items():
            nested_key = self.join_keys(parent_key, key)
            yield nested_key
            if isinstance(value, abc.Mapping):
                yield from self.__iter_keys__(value, nested_key)

    def __iter_leaf_keys__(self, mapping, parent_key=''):
        for key, value in mapping.items():
            nested_key = self.join_keys(parent_key, key)
            if isinstance(value, abc.Mapping):
                yield from self.__iter_leaf_keys__(value, nested_key)
            else:
                yield nested_key

    def __iter_values__(self, mapping):
        for value in mapping.values():
            yield value
            if isinstance(value, abc.Mapping):
                yield from self.__iter_values__(value)

    def __iter_leaf_values__(self, mapping):
        for value in mapping.values():
            if isinstance(value, abc.Mapping):
                yield from self.__iter_leaf_values__(value)
            else:
                yield value

    def __len__(self):
        """Returns the total number of items.
        """
        return len(self.keys())

    def __repr__(self):
        return 'NestedDict({!r}, level_sep={!r})'.format(self._d, self._sep)

    def __str__(self):
        return str(self._d)

    def clear(self):
        self._d = dict()

    def copy(self):
        return NestedDict(self._d, self._sep)

    def item_parent(self, key):
        parent = self
        for level in self.split_key(key)[:-1]:
            parent = parent[level]
        return parent

    def join_keys(self, *keys):
        keys = list(keys)
        if keys[0] == '':
            del keys[0]
        return self._sep.join(keys)

    def keys(self):
        return [k for k in self.__iter_keys__(self._d)]

    def leaf_items(self):
        return {k: self[k] for k in self.__iter_leaf_keys__(self._d)}

    def leaf_keys(self):
        return [k for k in self.__iter_leaf_keys__(self._d)]

    def leaf_key(self, key):
        return self.split_key(key)[-1]

    def level_separator(self):
        return self._sep

    def split_key(self, key):
        return key.split(self._sep)

    def to_dict(self):
        return dict(self._d)

    def values(self):
        return [v for v in self.__iter_values__(self._d)]

    def leaf_values(self):
        return [v for v in self.__iter_leaf_values__(self._d)]


def iter_nested_mapping(mapping):
    """

    Credits to:
    https://stackoverflow.com/questions/10756427/loop-through-all-nested-dictionary-values

    Parameters
    ----------
    mapping

    Returns
    -------

    """
    for key, value in mapping.items():
        if isinstance(value, abc.Mapping):
            yield from iter_nested_mapping(value)
        else:
            yield key, value


def map_nested_mapping(mapping, func):
    for k, v in mapping.items():
        if isinstance(v, abc.Mapping):
            map_nested_mapping(v, func)
        elif isinstance(v, abc.Iterable):
            mapping[k] = map(func, v)
        else:
            mapping[k] = func(v)


def split_mapping(required_keys, mapping):
    variables = required_keys
    values = set(mapping.keys())

    actual = {k: mapping[k] for k in values.union(variables)}
    missing = {k: mapping[k] for k in variables-values}
    remaining = {k: mapping[k] for k in values-variables}

    return actual, missing, remaining
