"""Module documentation goes here...

"""
from collections import abc
from .mapping import NestedDict

import logging
import re

logger = logging.getLogger(__name__)


class Template(object):

    def __init__(self, string, var_start='{{', var_end='}}', level_sep=r'\.'):
        self.template = str(string)
        self.var_id = r'[a-zA-Z][a-zA-Z0-9_]*(' + level_sep + r'[_a-zA-Z0-9])*'  # \w+(\.\w+)*
        self.pattern = re.compile(var_start + r'\s*(' + self.var_id + r')\s*' + var_end)

    def variables(self):
        return set([groups[0] for groups in self.pattern.findall(self.template)])

    def substitute(self, **context):
        return self.pattern.sub(lambda match: context[match.group(0)], self.template)

    def safe_substitute(self, **context):
        return self.pattern.sub(lambda match: context.get(match.group(0), match.group(0)), self.template)


class Configuration(NestedDict):

    def __init__(self, mapping, **kwargs):
        """

        Parameters
        ----------
        mapping: mapping
            A dict-like object that contains variable-value items.

        kwargs:

        """
        NestedDict.__init__(self, mapping, kwargs.get('level_sep', ' '))
        self.var_start = kwargs.get('var_start', '{{')
        self.var_end = kwargs.get('var_end', '}}')
        self.buffer = None
        self.buffer = self._prepare()

    def create_template(self, item):
        return Template(item, self.var_start, self.var_end, self.level_separator())

    def render_context(self, **kwargs):

        class Context(abc.Mapping):
            def __init__(self, mapping):
                self.__mapping = mapping

            # def __getattr__(self, name):
            #     return self[name]

            def __getitem__(self, key):
                return self.__mapping[key]

            def __iter__(self):
                return iter(self.__mapping)

            def __len__(self):
                return len(self.__mapping)

        if self.buffer:
            context = self.buffer.copy()
        else:
            context = self.copy()

        context.update(kwargs)
        return Context(context)

    def render(self, **kwargs):
        """Renders all template items given the values specified in kwargs.

        Parameters
        ----------
        kwargs

        Returns
        -------

        """
        return self._render_all(self.buffer, self.render_context(**kwargs))

    def variables(self):
        variables = set([])
        for k, v in self.items():
            if not isinstance(v, str):
                continue
            variables |= self.create_template(v).variables()
        return variables

    def _prepare(self):
        return self._render_all(self.copy(), self.render_context(), True)

    def _render_all(self, mapping, context, prepare=False):
        for k, v in mapping.items():
            if isinstance(v, (list, tuple)):
                mapping[k] = type(v)(map(lambda item: self._render_item(item, context, prepare), mapping[k]))
            else:
                mapping[k] = self._render_item(v, context, prepare)
        return mapping

    def _render_item(self, item, context, prepare):
        """

        Parameters
        ----------
        item:

        Returns
        -------

        """
        if not isinstance(item, str):
            return item

        if prepare:
            return self.create_template(item).safe_substitute(**context)
        return self.create_template(item).substitute(**context)
