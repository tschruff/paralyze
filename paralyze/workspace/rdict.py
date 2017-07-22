from string import Formatter
import re


def make_flat(d, prefix='', result=None, nsep='_'):
    """
    """
    f = result or {}
    n = prefix if prefix == '' else prefix+nsep
    for k0, v0 in d.items():
        if isinstance(v0, dict):
            make_flat(v0, n+k0, f, nsep)
        else:
            f[n+k0] = v0
    return f


class Namespace(object):

    def __init__(self, namespace, parent, nsep):
        self._namespace = namespace
        self._parent = parent
        self._nsep = nsep

    def __contains__(self, key):
        return key in self.names() or key in self.namespaces()

    def __len__(self):
        return len(self.names())

    def __getitem__(self, key):
        try:
            return self._parent[self.abs_name(key)]
        except KeyError as e:
            raise e

    def __str__(self):
        return str(self.formatted())

    def __iter__(self):
        return iter(self.formatted())

    def todict(self):
        pdict = self._parent.todict()
        return {k: pdict[self.abs_name(k)] for k in self.names()}

    def formatted(self):
        return self._parent.formatted(self._namespace)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def name(self):
        return self._namespace

    def names(self):
        return [k[len(self._namespace)+1:] for k in self._parent.keys() if k.startswith(self._namespace + self._nsep)]

    def namespaces(self):
        return [k[len(self._namespace)+1:] for k in self._parent.namespaces() if k.startswith(self._namespace+self._nsep)]

    def abs_items(self):
        return {key: self.get(key) for key in self.abs_names()}

    def abs_names(self):
        return [self.abs_name(key) for key in self.names()]

    def abs_name(self, key):
        return self._namespace+self._nsep+key


class ReplacementDict(object):
    """dict with replacement fields.
    """

    FieldPattern = r"(?<!\{)\{([^\{\}]+)\}(?!\})"

    def __init__(self, dict, namespace_separator='_'):
        self._dict = make_flat(dict, nsep=namespace_separator)
        self._formatter = Formatter()
        self._cache = set([])
        self._nsep = namespace_separator

    def __getitem__(self, key):
        try:
            item = self.get_namespace(key)
        except KeyError:
            item = self.get_value(key)
        return item

    def get_value(self, key):
        """
        """
        if key in self._cache:
            raise RecursionError('recursive reference to ReplacementDict item "{}"'.format(key))

        self._cache.add(key)
        try:
            item = self._dict[key]
            result = self.format(item)
        except KeyError as e:
            raise e
        finally:
            self._cache.remove(key)
        return result

    def get_namespace(self, name):
        ns = Namespace(name, self, self._nsep)
        if not len(ns):
            raise KeyError('ReplacementDict has no namespace with name "{}"'.format(name))
        return ns

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            for k, v in make_flat(value, key):
                self._dict[k] = v
        else:
            self._dict[key] = value

    def __delitem__(self, key):
        if self.is_name(key):
            del self._dict[key]
        else:
            for k in self.get_namespace(key).abs_names():
                del self._dict[k]

    def get(self, key, default=None):
        """Returns the item with specified key or ``default`` if ``key``
        does not exist.

        Parameters
        ----------
        key: str

        default: object
        """
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key):
        return key in self.names() or key in self.namespaces()

    def __len__(self):
        return len(self._dict)

    def __iter__(self):
        return iter(self.formatted())

    def __str__(self):
        return str(self.formatted())

    def copy(self):
        return ReplacementDict(self._dict.copy())

    def is_name(self, key):
        return key in self.names()

    def names(self):
        """Returns all leaf-most item names.
        """
        return self._dict.keys()

    def namespaces(self):
        ns = []
        for name in self.names():
            group = name.rsplit(self._nsep, maxsplit=1)
            if len(group) > 1:
                ns.append(group[0])
        return set(ns)

    def update(self, other):
        if isinstance(other, (ReplacementDict, Namespace)):
            self._dict.update(other.todict())
        else:
            self._dict.update(other)

    def pop(self, key, default=None):
        if self.is_name(key):
            return self._dict.pop(key, default)
        return default

    def pop_namespace(self, key):
        popped = {}
        for k in self.get_namespace(key).names():
            popped[k] = self._dict.pop(k)
        return popped

    def todict(self):
        return self._dict

    def format_wrapper(self):
        """
        Returns
        -------
        """
        class Wrapper(object):

            def __init__(self, obj):
                self.__obj = obj

            def __getattr__(self, name):
                attr = self.__obj[name]
                if isinstance(attr, Namespace):
                    return Wrapper(attr)
                return attr

            def __getitem__(self, key):
                item = self.__obj[key]
                if isinstance(item, Namespace):
                    return Wrapper(item)
                return item

        return Wrapper(self)

    def format(self, string):
            """
            """
            while self.contains_field(string):
                try:
                    string = self._formatter.vformat(string, [], self.format_wrapper())
                except KeyError as e:
                    raise e
                except RecursionError as e:
                    raise e
            return string

    def formatted(self, namespace=''):
        if namespace != '':
            return {key: self[key] for key in self.get_namespace(namespace).abs_names()}
        return {key: self[key] for key in self.names()}

    @staticmethod
    def contains_field(string):
        """
        Parameters
        ----------
        string: str
        """
        if type(string) is not str:
            return False
        return len(re.findall(ReplacementDict.FieldPattern, string)) > 0

    def fields(self):
        """Returns the set of replacement fields, i.e. something like this
        '{some_var}', '{dict[key]}', '{obj.attr}'.

        Returns
        -------
        set: The set of replacement fields
        """
        rfields = set([])
        for val in self._dict.values():
            if not isinstance(val, str):
                continue
            result = self._formatter.parse(val)
            for literal_text, field_name, format_spec, conversion in result:
                if field_name is not None:
                    rfields.add(field_name)
        return rfields

    def vars(self):
        """Returns the set of replacement fields which can not
        be replaced, i.e. the variables.
        """
        variables = []
        for field in self.fields():
            try:
                self.format('{'+field+'}')
            except KeyError as e:
                variables.append(e.args[0])
            except RecursionError as e:
                raise e
        return set(variables)

    def var_items(self):
        return {key: self._dict[key] for key in self.vars()}

    def is_valid(self):
        """Checks if the ReplacementDict is valid, i.e. has no variables and no recursive
        references.
        """
        # no recursive references
        try:
            # no variables
            if len(self.vars()):
                return False
            self.formatted()
        except RecursionError:
            return False
        return True
