"""Module documentation goes here...

"""
from collections import abc
from .mapping import NestedDict

import logging
import re
import copy

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
        # copy of underlying nested dict with simplified templates
        # increases performance of calls to finalize()
        self.buffer = self._preprocess(NestedDict(copy.deepcopy(self._d), self.level_separator()))

    def finalize(self, **kwargs):
        """Renders all template items given the values specified in kwargs.

        Parameters
        ----------
        kwargs

        Returns
        -------
        A NestedDict instance of self where all template variables have been replaced by provided kwargs.
        """
        config = self.buffer.copy()
        config.update(kwargs)
        return self._render_all(config, self.create_context(config))

    def variables(self):
        variables = set([])
        for k, v in self.items():
            if not isinstance(v, str):
                continue
            variables |= self.create_template(v).variables()
        return variables - set(self.keys())

    def create_context(self, mapping):

        class Context(abc.Mapping):
            def __init__(self, mapping):
                self.__mapping = mapping

            def __getitem__(self, key):
                return self.__mapping[key]

            def __iter__(self):
                return iter(self.__mapping)

            def __len__(self):
                return len(self.__mapping)

        return Context(mapping)

    def create_template(self, item):

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

    def _preprocess(self, mapping):
        return self._render_all(mapping, self.create_context(mapping), True)

    def _render_all(self, mapping, context, safe=False):
        for k, v in mapping.items():
            if isinstance(v, (tuple, list)):
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
                new = self.create_template(old).safe_substitute(**context)
                if new == old:
                    break
                else:
                    old = new
            return new
        return self.create_template(item).substitute(**context)
