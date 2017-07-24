"""Module documentation goes here...

"""
from collections import abc
from .mapping import NestedDict

import logging
import re

logger = logging.getLogger(__name__)


class ConfigDict(NestedDict):

    def __init__(self, mapping, **kwargs):
        """

        Parameters
        ----------
        mapping: mapping
            A dict-like object that contains variable-value items.

        kwargs:

        """
        NestedDict.__init__(self, mapping, kwargs.get('level_sep', '.'))
        self.var_start = kwargs.get('var_start', '{{')
        self.var_end = kwargs.get('var_end', '}}')
        self.buffer = None
        self.buffer = self._simplify()

    def render(self, **kwargs):
        """Renders all template items given the values specified in kwargs.

        Parameters
        ----------
        kwargs

        Returns
        -------

        """
        return self._render_all(self.buffer.copy(), self._render_context(**kwargs))

    def variables(self):
        variables = set([])
        for k, v in self.items():
            if not isinstance(v, str):
                continue
            variables |= self._create_template(v).variables()
        return variables - set(self.keys())

    def _create_template(self, item):

        class Template(object):
            pattern = r'{start}\s*(?P<var>{id})\s*{end}'.format(
                start=re.escape(self.var_start),
                id=r'[a-zA-Z][a-zA-Z0-9_]*(?:'+re.escape(self.level_separator())+r'[a-zA-Z][_a-zA-Z0-9]*)*',
                end=re.escape(self.var_end)
            )

            def __init__(self, template):
                self.template = template
                self.pattern = re.compile(Template.pattern)

            def variables(self):
                return set([var for var in self.pattern.findall(self.template)])

            def substitute(self, **context):
                return self.pattern.sub(lambda mo: str(context[mo.group('var')]), self.template)

            def safe_substitute(self, **context):
                def safe_get(mo):
                    return str(context.get(mo.group('var'), mo.group(0)))
                return self.pattern.sub(safe_get, self.template)

        return Template(item)

    def _render_context(self, **kwargs):

        class Context(abc.Mapping):
            def __init__(self, mapping):
                self.__mapping = mapping

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

    def _simplify(self):
        return self._render_all(self.copy(), self._render_context(), True)

    def _render_all(self, mapping, context, safe=False):
        for k, v in mapping.items():
            if isinstance(v, (list, tuple)):
                mapping[k] = type(v)(map(lambda item: self._render_item(item, context, safe), mapping[k]))
            else:
                mapping[k] = self._render_item(v, context, safe)
        return mapping

    def _render_item(self, item, context, safe):
        """

        Parameters
        ----------
        item:

        Returns
        -------

        """
        if not isinstance(item, str):
            return item

        if safe:
            old = item
            while True:
                new = self._create_template(old).safe_substitute(**context)
                if new == old:
                    break
                else:
                    old = new
            return new
        return self._create_template(item).substitute(**context)
