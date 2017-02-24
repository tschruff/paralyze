import os
import json
import logging
import sys
import importlib
import argparse

from paralyze.core import rdict, type_cast
from paralyze.core.io.json_ext import ParalyzeDecoder, ParalyzeEncoder

logger = logging.getLogger(__name__)

LOG_FILE = 'log.txt'
LOG_FILE_FORMAT = '[%(asctime)-15s][%(levelname)-7s] %(message)s'
LOG_STREAM_FORMAT = '[%(levelname)-7s] %(message)s'
SETTINGS_DIR = '.paralyze'
SETTINGS_FILE = 'workspace.json'
CONTEXT_EXTENSIONS_DIR = 'context_ext'


class Workspace(object):

    def __init__(self, path=None, auto_create=False, settings=None, log_level=logging.INFO):
        # absolute path to workspace root folder
        self._root = path or os.getcwd()

        if not os.path.exists(self._root):
            raise IOError('No such file or directory {}'.format(self._root))

        settings_path = os.path.join(self._root, SETTINGS_DIR, SETTINGS_FILE)

        if not os.path.exists(settings_path):
            if auto_create:
                self.__create(settings)
            else:
                raise IOError('Directory {} is not a paralyze workspace'.format(self._root))

        # init main logger
        self.init_logger(log_level)

        # load raw dict (with variables as raw template strings)
        self._raw = self.__load()

        # check if custom context extensions exist
        ext_path = os.path.join(self.root, CONTEXT_EXTENSIONS_DIR, '__init__.py')
        if os.path.exists(ext_path):
            self._has_ext = True
            sys.path.append(self._root)
        else:
            self._has_ext = False

    def __create(self, settings=None):
        # create hidden settings folder
        settings_dir = os.path.join(self._root, SETTINGS_DIR)
        if not os.path.exists(settings_dir):
            logger.info('creating paralyze workspace at {}'.format(self._root))
            os.mkdir(settings_dir)
        # save settings to json file
        settings_path = os.path.join(settings_dir, SETTINGS_FILE)
        with open(settings_path, 'w') as settings_file:
            logger.debug('saving paralyze workspace settings to file {}'.format(SETTINGS_FILE))
            json.dump(settings or {}, settings_file, indent=4, sort_keys=True, cls=ParalyzeEncoder)

    def __load(self):
        settings_file = os.path.join(self._root, SETTINGS_DIR, SETTINGS_FILE)
        with open(settings_file, 'r') as settings:
            data = json.load(settings, object_hook=ParalyzeDecoder.decode_ext)
        return rdict(data)

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self._raw[key] = value

    def __str__(self):
        return str(self.get_settings())

    def init_logger(self, level=logging.INFO):
        main_logger = logging.getLogger()
        # configure and add file handler
        file_h = logging.FileHandler(os.path.join(self.root, SETTINGS_DIR, LOG_FILE))
        file_h.setFormatter(logging.Formatter(LOG_FILE_FORMAT))
        file_h.setLevel(logging.DEBUG)
        main_logger.addHandler(file_h)
        # configure and add stream handler
        bash_h = logging.StreamHandler()
        bash_h.setFormatter(logging.Formatter(LOG_STREAM_FORMAT))
        bash_h.setLevel(level)
        main_logger.addHandler(bash_h)

    def init_variables(self, args=None):
        """ Initializes variables in the settings dict with values given in args.

        :param args: a dict with variable names as keys or a list of command line arguments.
        :return: a list of unused command line arguments if args is a list or an empty list if args is a dict.
        """
        # init variables from dict
        if isinstance(args, dict):
            self.update(args)
            return []
        # init variables from argument list
        parser = argparse.ArgumentParser(allow_abbrev=False)
        # add workspace variables as required command line arguments
        for var in self.variables():
            parser.add_argument('--%s' % var, required=True, type=type_cast)
        wsp_args, custom_args = parser.parse_known_args(args or sys.argv)
        # update workspace settings directly with command line values
        self.update(vars(wsp_args))
        return custom_args

    @property
    def root(self):
        return self._root

    def rel_path(self, key):
        return os.path.relpath(self.get(key), self.root)

    def abs_path(self, key):
        return os.path.join(self.root, self.get(key))

    def get_context_extensions(self):
        if self._has_ext:
            mod = importlib.import_module('context_ext')
            ext = {}
            for ext_key in mod.__all__:
                ext[ext_key] = getattr(mod, ext_key)
            return ext
        return {}

    def get(self, key, default=None, raw=False):
        if raw:
            return self._raw.get_raw(key, default)
        else:
            return self._raw.get(key, default)

    def get_settings(self, scope_filter=()):
        settings = {}
        for key in self._raw.keys():
            if not len(scope_filter) or sum([key.startswith(scope) for scope in scope_filter]):
                settings[key] = self.get(key)
        return settings

    def keys(self, private=False):
        if private:
            return self._raw.keys()
        return [key for key in self._raw.keys() if not key.startswith('__')]

    def update(self, other):
        """ Updates items.

        :param other:
        :return:
        """
        self._raw.update(other)

    def variables(self):
        return self._raw.variables()
