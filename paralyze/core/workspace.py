import os
import json
import logging
import sys
import importlib

from paralyze.core import rdict

logger = logging.getLogger(__name__)

SETTINGS_DIR = '.paralyze'
SETTINGS_FILE = 'workspace.json'
CONTEXT_EXTENSIONS_DIR = 'context_ext'


class Workspace(object):

    def __init__(self, path, auto_create=False, defaults=None):
        # absolute path to workspace root folder
        self._root = path

        if not os.path.exists(self._root):
            logger.error()
            raise IOError('No such file or directory {}'.format(self._root))

        settings_path = os.path.join(self._root, SETTINGS_DIR, SETTINGS_FILE)

        if not os.path.exists(settings_path):
            if auto_create:
                self.__create(defaults)
            else:
                logger.error('')
                raise RuntimeError('Directory {} is not a paralyze workspace'.format(self._root))

        # load raw dict (with raw template strings)
        self._raw = self.__load()

    def __create(self, defaults=None):
        # create hidden settings folder
        settings_dir = os.path.join(self._root, SETTINGS_DIR)
        if not os.path.exists(settings_dir):
            logger.debug('creating paralyze workspace at {}'.format(self._root))
            os.mkdir(settings_dir)
        # save settings to json file
        settings_path = os.path.join(settings_dir, SETTINGS_FILE)
        with open(settings_path, 'w') as settings_file:
            logger.debug('saving paralyze workspace settings to file {}'.format(SETTINGS_FILE))
            json.dump(defaults or {}, settings_file, indent=4, sort_keys=True)

    def __load(self):
        settings_file = os.path.join(self._root, SETTINGS_DIR, SETTINGS_FILE)
        with open(settings_file, 'r') as settings:
            data = json.load(settings)
        return rdict(data)

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self._raw[key] = value

    def __str__(self):
        return str(self.get_settings())

    @property
    def root(self):
        return self._root

    def rel_path(self, key):
        return os.path.relpath(self.get(key), self.root)

    def abs_path(self, key):
        return os.path.join(self.root, self.get(key))

    def create_folders(self, folder_keys):
        logger.debug('creating workspace folders %s' % ', '.join([self.get(folder) for folder in folder_keys]))
        for folder in folder_keys:
            try:
                os.mkdir(self.get(folder))
            except FileExistsError as e:
                logger.warning(e.args[0])

    def get_context_extensions(self):
        ext_path = os.path.join(self.root, CONTEXT_EXTENSIONS_DIR)
        mod_path = os.path.join(ext_path, '__init__.py')

        ext = {}
        if os.path.exists(mod_path):
            sys.path.append(ext_path)
            mod = importlib.import_module('context_ext')
            for ext_key in mod.__all__:
                ext[ext_key] = getattr(mod, ext_key)
        return ext

    def get(self, key):
        return self._raw[key]

    def get_settings(self, scope_filter=()):
        settings = {}
        for key in self._raw.keys():
            if not len(scope_filter) or sum([key.startswith(scope) for scope in scope_filter]):
                settings[key] = self.get(key)
        return settings

    def update(self, other):
        """ Updates items.

        :param other:
        :return:
        """
        for key in other.keys():
            self._raw[key] = other[key]

    def variables(self):
        return self._raw.variables()
