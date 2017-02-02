import os
import json
import logging

from paralyze import VERSION
from paralyze.core import rdict

logger = logging.getLogger(__name__)

SETTINGS_DIR = '.paralyze'
SETTINGS_FILE = 'workspace.json'

# default workspace settings
DEFAULTS = {

    # general settings
    'paralyze_version': VERSION,

    # environment settings
    'env_app_dir': 'apps',
    'env_app_file': '',
    'env_app_path': os.path.join('{env_app_dir}', '{env_app_file}'),
    'env_config_dir': 'configs',
    'env_config_file': '{comp_config}.prm',
    'env_config_path': os.path.join('{env_config_dir}', '{env_config_file}'),
    'env_log_dir': 'logs',
    'env_log_file': '{comp_job_name}_log.txt',
    'env_log_path': os.path.join('{env_log_dir}', '{env_log_file}'),
    'env_log_error_file': '{comp_job_name}_errors.txt',
    'env_log_error_path': os.path.join('{env_log_dir}', '{env_log_error_file}'),
    'env_run_dir': 'run',
    'env_run_file': '{comp_job_name}.sh',
    'env_run_path': os.path.join('{env_run_dir}', '{env_run_file}'),
    'env_template_dir': 'templates',
    'env_template_file': '{comp_config}.txt',
    'env_template_path': os.path.join('{env_template_dir}', '{env_template_file}'),

    # computational settings
    'comp_config': '',
    'comp_case': '',
    'comp_job_name': '{comp_config}_{comp_case}',
    'comp_arch': 'juqueen',
    'comp_cores_per_node': 16,
    'comp_nodes': 4096,
    'comp_memory_per_process': 512,
    'comp_wc_limit': '4:00:00',
    'comp_notify_start': False,
    'comp_notify_end': False,
    'comp_notify_error': False,
    'comp_notify_user': '',

    'comp_run_cmd': {
        'juqueen': 'llsubmit {env_run_path}',
        'lsf': 'bsub < {env_run_path}'
    }
}


class Workspace(object):

    def __init__(self, path, auto_create=False):
        # absolute path to workspace root folder
        self._root = path

        if not os.path.exists(self._root):
            logger.error()
            raise IOError('No such file or directory {}'.format(self._root))

        settings_path = os.path.join(self._root, SETTINGS_DIR, SETTINGS_FILE)

        if not os.path.exists(settings_path):
            if auto_create:
                self.__create()
            else:
                logger.error('')
                raise IOError('No such file or directory {}'.format(settings_path))

        # load raw dict (with templates)
        self._raw = self.__load()

    def __create(self):
        settings_dir = os.path.join(self._root, SETTINGS_DIR)
        if not os.path.exists(settings_dir):
            logger.info('creating paralyze workspace {}'.format(settings_dir))
            os.mkdir(settings_dir)
        settings_file = os.path.join(settings_dir, SETTINGS_FILE)
        with open(settings_file, 'w') as settings:
            logger.info('creating paralyze workspace settings file {}'.format(SETTINGS_FILE))
            json.dump(DEFAULTS, settings, indent=4, sort_keys=True)

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

    def get(self, key):
        return self._raw[key]

    def get_settings(self, scope_filter=()):
        settings = {}
        for key in self._raw.keys():
            if not len(scope_filter) or sum([key.startswith(scope) for scope in scope_filter]):
                settings[key] = self.get(key)
        return settings

    def update(self, other):
        """ Updates EXISTING items.

        :param other:
        :return:
        """
        for key in self._raw.keys():
            self._raw[key] = other[key]

    def perform_check(self):
        result = True
        if not os.path.exists(self.abs_path('env_app_path')):
            logger.warning('application {} does not exist'.format(self.get('env_app_path')))
            result = False
        if not os.path.exists(self.abs_path('env_config_path')):
            logger.warning('configuration {} does not exist'.format(self.get('env_config_path')))
            result = False
        if not os.path.exists(self.abs_path('env_log_dir')):
            logger.warning('log folder {} does not exist'.format(self.get('env_log_dir')))
            result = False
        if not os.path.exists(self.abs_path('env_template_path')):
            logger.error('run script template file {} does not exist'.format(self.get('env_template_path')))
            result = False
        if not os.path.exists(self.abs_path('env_run_dir')):
            logger.error('run folder {} does not exist'.format(self.get('env_run_dir')))
            result = False
        return result
