"""Module documentation goes here ...

"""
try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False

from jinja2 import meta
from paralyze.utils import ConfigDict, NestedDict
from .remote import RemoteFileSystemLoader

import os
import sys
import logging
import shutil
import importlib.util
import socket
import getpass
import jinja2
import paralyze
import posixpath
import tempfile
import json


logger = logging.getLogger(__name__)

if not os.path.exists(os.path.expanduser('~/.paralyze')):
    try:
        os.mkdir(os.path.expanduser('~/.paralyze'))
        SSH_LOG_FILE = os.path.expanduser('~/.paralyze/ssh_log.txt')
        SSH_CON_FILE = os.path.expanduser('~/.paralyze/ssh_conn.txt')
    except OSError:
        SSH_LOG_FILE = ""
        SSH_CON_FILE = ""
else:
    SSH_LOG_FILE = os.path.expanduser('~/.paralyze/ssh_log.txt')
    SSH_CON_FILE = os.path.expanduser('~/.paralyze/ssh_conn.txt')

CONFIG_DIR = ".paralyze"
CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "__version__": "",

    "template": {
        "environment": {
            "block_start_string": "{%",
            "block_end_string": "%}",
            "variable_start_string": "{{",
            "variable_end_string": "}}",
            "comment_start_string": "{#",
            "comment_end_string": "#}",
            "line_statement_prefix": "",
            "line_comment_prefix": "",
            "trim_blocks": False,
            "lstrip_blocks": False,
            "newline_sequence": "\n",
            "keep_trailing_newline": False,
            "extensions": "",
            "optimized": True,
            "autoescape": True,
            "cache_size": 400,
            "auto_reload": True,
            "enable_async": True
        },

        "loader": {
            "dirs": [],
            "follow_links": True,
            "encoding": "utf-8"
        },

        "context_extension_dirs": []
    },

    "parameter_module": "",

    "logging": {
        "level": "WARNING",
        "file": "log.txt",
        "file_format": "[%(asctime)-15s][%(levelname)-7s] %(message)s"
    }
}


class Workspace(object):
    """
    """

    def __init__(self, *args, **kwargs):
        """Create new workspace and load existing (remote) workspace configuration.
        """
        self._builtin_names = set([name for name in __builtins__ if not name.startswith('_')])
        self.extensions = dict()
        self.temp_dir = None
        self.env = None
        self.config = NestedDict(dict())
        self.params = NestedDict(dict())

        if len(args) == 1:
            kwargs['path'] = str(args[0])

        # create SSH and SFTP connection if required
        if kwargs.get('connection') or kwargs.get('host'):
            if HAS_PARAMIKO:
                self._conn, self._sftp = self._init_ssh_connection(**kwargs)
            else:
                raise ImportError('missing dependency: paramiko (install using "pip install paramiko")')
        else:
            self._conn = None
            self._sftp = None

        # check if workspace root folder exists
        cwd = self._sftp.getcwd() if self.is_remote() else os.getcwd()
        path = kwargs.get('path', cwd)
        if not self.path_exists(path):
            raise OSError('no such file or directory: {}'.format(path))

        # IMPORTANT: root directory is set here!
        self._root = path

        # check if config file exists, try to create one if not
        if not self.path_exists(self.config_file_path):
            if kwargs.get('auto_create', False):
                self._create(kwargs.get('config', DEFAULT_CONFIG))
            else:
                raise OSError('"{}" is not a paralyze workspace directory'.format(self.root_dir))

        self._init()

    def __del__(self):
        """Clean-up ssh connection and temporary folder.
        """
        if self.is_remote():
            self._conn.close()

        if self.temp_dir:
            shutil.rmtree(self.temp_dir)

    @property
    def version(self):
        return self.config['__version__']

    @property
    def root_dir(self):
        """Returns the root directory of the workspace instance.
        """
        return self._root

    @property
    def config_dir(self):
        """Returns the absolute path to the workspace settings folder.
        """
        return self.abs_path(CONFIG_DIR)

    @property
    def config_file_path(self):
        """Returns the absolute path to the main workspace settings file.
        """
        return self.abs_path(self.config_dir, CONFIG_FILE)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def get_abs_path(self, key, mapping=None):
        mapping = mapping or self.config
        return self.abs_path(mapping[key])

    def rel_path(self, arg):
        if self.is_remote():
            return posixpath.relpath(arg, self.root_dir)
        return os.path.relpath(arg, self.root_dir)

    def abs_path(self, *args):
        if self.is_remote():
            return posixpath.join(self.root_dir, *args)
        return os.path.join(self.root_dir, *args)

    def is_abs_path(self, path):
        if self.is_remote():
            return posixpath.isabs(path)
        return os.path.isabs(path)

    def is_file(self, path):
        if self.is_remote():
            return posixpath.isfile(path)
        return os.path.isfile(path)

    def is_remote(self):
        return self._sftp is not None

    def mkdir(self, folder):
        if self.is_remote():
            self._sftp.mkdir(folder)
        else:
            os.mkdir(folder)

    def open(self, file_path, mode='r', encoding='utf-8'):
        """Opens the file specified by ``file_path`` in the given ``mode``.

        If workspace is remote, the remote file is copied to a local
        temporary folder first and then opened from there.

        Parameters
        ----------
        file_path: str
            Path to file to be opened.
        mode: str
            Any valid open mode, e.g. 'r', 'w', 'w+', ...
        encoding: str
            The file encoding. Default is utf-8.

        Raises
        ------
        OSError: If file does not exist.
        """
        if not self.is_abs_path(file_path):
            file_path = self.abs_path(file_path)
        # file_path is absolute from here on!

        if not mode.startswith('w') and not self.path_exists(file_path):
            raise IOError('no such file: {}'.format(file_path))

        if self.is_remote():
            # copy remote file to temp dir and open it from there
            open_path = self._create_temp_file_path(file_path)
            self._sftp.get(file_path, open_path)
        else:
            open_path = file_path

        return open(open_path, mode, encoding=encoding)

    def path_exists(self, path):
        if self.is_remote():
            try:
                self._sftp.stat(path)
                return True
            except IOError:
                return False
        return os.path.exists(path)

    # ==============
    # INITIALIZATION
    # ==============

    def _init(self):
        self.config = NestedDict(json.load(open(self.config_file_path, 'r')))
        self._validate_config()
        # init main logger
        self._init_logger()
        # check workspace and code version compatibility
        self._check_version()
        # init jinja's template environment
        self._init_template_env()
        # init custom context extensions
        self._init_context_extensions()
        # init parameter Python module
        self._init_parameter_module()

    def _validate_config(self):
        # TODO: Implement nested dict key validation
        pass

    def _init_logger(self):
        logging_config = self.config['logging']
        ll = logging_config['level']
        lf = logging_config['file']
        ff = logging_config['file_format']

        fh = logging.FileHandler(lf)
        fh.setFormatter(logging.Formatter(ff))
        fh.setLevel(ll)

        logger.addHandler(fh)

    def _check_version(self):
        """Checks code and workspace version compatibility.

        """
        # TODO: Implement version comparison and policy.
        wsp_version = self.version          # workspace version
        run_version = paralyze.__version__  # code version

    def _init_template_env(self):
        """Create and return a new jinja2 environment.

        Jinja2 uses a central object called the template Environment. Instances
        of this class are used to store the configuration and global objects,
        and are used to load templates from the file system or remote locations.
        """
        config = self.config['template.loader']

        if self.is_remote():
            loader = RemoteFileSystemLoader(
                self._sftp, config['dirs'], encoding=config['encoding'], follow_links=config['follow_links']
            )
        else:
            loader = jinja2.FileSystemLoader(
                config['dirs'], encoding=config['encoding'], followlinks=config['follow_links']
            )

        env_config = self.config['template.environment']
        env_config['undefined'] = jinja2.make_logging_undefined(logger=logger, base=jinja2.StrictUndefined)
        self.env = jinja2.Environment(loader=loader, **env_config)

    def _init_context_extensions(self):
        """
        """
        self.extensions = {}
        if self.is_remote():
            # TODO: Implement remote extension initialization
            pass
        else:
            self.extensions = self._init_local_extensions()

    def _init_local_extensions(self):
        """Loads local context extensions (Python packages).
        """
        ext = {}
        for i, ext_dir in enumerate(self.config['template.context_extension_dirs']):
            abs_ext_dir = self.abs_path(ext_dir)
            ext_mod = self.load_package(abs_ext_dir)
            for ext_key in ext_mod.__all__:
                if ext_key in ext.keys():
                    logger.warning('duplicate extension name "{}". Former one will be replaced!'.format(ext_key))
                ext[ext_key] = getattr(ext_mod, ext_key)
        return ext

    def _init_parameter_module(self):
        """Loads the workspace parameters Python module.
        """
        if self.has_params():
            mod = self.load_module('parameters', self.abs_path(self.config['parameter_module']))
            mod.config['root_dir'] = self.root_dir
            self.params = NestedDict(mod.config)
        else:
            self.params = NestedDict(dict())

    def _create(self, config):
        """Creates a new workspace configuration folder and file.
        """
        # create hidden configuration folder
        if not self.path_exists(self.config_dir):
            logger.info('creating paralyze workspace at {}'.format(self.root_dir))
            self.mkdir(self.config_dir)
        # set paralyze version
        config['__version__'] = paralyze.__version__
        with self.open(self.config_file_path, 'w') as config_file:
            logger.info('saving paralyze workspace config to file {}'.format(self.config_file_path))
            json.dump(config, config_file, indent='\t', sort_keys=True)

    # ========================
    # FILESYSTEM RELATED STUFF
    # ========================

    def _create_temp_file_path(self, file_path):
        """Returns a path to a new temporary file.
        """
        self.temp_dir = self.temp_dir or tempfile.mkdtemp(prefix='paralyze')
        # TODO: Create unique file names!
        return os.path.join(self.temp_dir, os.path.basename(file_path))

    def _create_config(self, mapping):
        env = self.config['template.environment']
        return ConfigDict(mapping, var_start=env['variable_start_string'], var_end=env['variable_end_string'])

    # ==============
    # PARAMETERS
    # ==============

    def has_params(self):
        if self.config['parameter_module'] != '':
            if os.path.exists(self.get_abs_path('parameter_module')):
                return True
        return False

    def init_params(self, **kwargs):
        """Initializes parameter configuration and template variables.

        Parameters
        ----------
        kwargs:


        """
        if not self.has_params():
            logger.warning('you tried to initialize workspace parameters without an existing parameters module')
            return

        pro = NestedDict(kwargs)  # provided args
        pro_args = set(pro.leaf_keys())
        req_args = self.get_parameter_variables()

        missing = req_args - pro_args
        if len(missing) and not kwargs.get('ignore_missing', False):
            raise KeyError('missing parameters: {!s}'.format(', '.join(missing)))

        context = dict(zip(req_args, pro[req_args]))
        self.params = self._create_config(self.params).finalize(**context)
        logger.debug('initialized params: {}'.format(self.params))

    def get_context(self, **kwargs):
        """Returns the template context (parameters + extensions).
        """
        context = self.params.to_dict()
        context.update(self.get_context_extensions())
        context.update(kwargs)
        return context

    def get_context_extensions(self):
        return self.extensions

    def get_variables(self, templates=()):
        return self.get_parameter_variables() | self.get_template_variables(templates)

    def get_parameter_variables(self):
        return self._create_config(self.params).variables()

    def get_template_variables(self, templates):
        """Recursively parses undeclared variables in all template files and
        referenced files.

        Parameters
        ----------
        templates: list-of-str
            names of template files

        Returns
        -------
        template_vars: set
            set of template variables as strings
        """
        template_vars = set([])
        for template in templates:
            var = self._get_template_variables(template)
            template_vars.update(var)
        return template_vars - set(self.params.keys())

    def _get_template_variables(self, template):
        """Recursively parses undeclared variables in template file and all
        referenced files.

        Parameters
        ----------
        template: str
            name of template file

        Returns
        -------
        template_vars: set
            the set of template variables (strings)
        """
        logger.debug('loading template: {}'.format(template))
        source = self.get_template_source(template)[0]

        try:
            logger.debug('parsing template source ...')
            template_ast = self.env.parse(source)
        except jinja2.TemplateSyntaxError as e:
            logger.error('while parsing template {}: {} (line: {})'.format(template, e.message, e.lineno))
            return set()

        logger.debug('searching for undeclared variables ...')
        template_vars = meta.find_undeclared_variables(template_ast)
        logger.debug('found undeclared variables: {}'.format(template_vars))

        for ref_template in meta.find_referenced_templates(template_ast):
            template_vars.update(self._get_template_variables(ref_template))

        return template_vars

    def render_template(self, template, **custom_context):
        """

        Parameters
        ----------
        template: str
            The key of the template in the workspace configuration.
        custom_context: mapping

        """
        # load template file
        template = self.get_template(template)
        context = self.get_context(**custom_context)

        logger.debug('render context: {!r}'.format(context))

        try:
            return template.render(**context)
        except jinja2.exceptions.UndefinedError as e:
            logger.error('{} (template: {})'.format(e.message, template.filename))
            raise
        except jinja2.exceptions.TemplateNotFound as e:
            logger.error('file "{}" not found for template: {}'.format(e.message, template.filename))
            raise
        except jinja2.exceptions.TemplateSyntaxError as e:
            logger.error('{} in template: {}'.format(e.message, template.filename))
            raise
        except IOError as e:
            logger.error(str(e))
            raise

    def get_template_source(self, template):
        """Returns the (source, filename, uptodate) tuple of the specified template.

        Parameters
        ----------
        template: str

        """
        return self.env.loader.get_source(self.env, template)

    def get_template(self, template):
        """Returns the specified template.

        Parameters
        ----------
        template: str

        """
        return self.env.get_template(template)

    # =======================
    # SSH/SFTP INITIALIZATION
    # =======================

    def _load_host_key(self, host):
        knownhosts = os.path.expanduser('~/.ssh/known_hosts')
        hostkey = None
        try:
            host_keys = paramiko.util.load_host_keys(knownhosts)
        except IOError:
            try:
                # try ~/ssh/ too, because windows can't have a folder named ~/.ssh/
                host_keys = paramiko.util.load_host_keys(knownhosts)
            except IOError:
                raise OSError('Unable to open ssh host keys file')

        if host in host_keys:
            hostkeytype = host_keys[host].keys()[0]
            hostkey = host_keys[host][hostkeytype]

        return hostkey

    def _get_connection(self, **kwargs):
        import collections
        Connection = collections.namedtuple('Connection', 'host username password port gss_auth gss_kex')
        if kwargs.get('connection', False):
            # TODO: load connection details from file!
            host = ""
            username = ""
            password = ""
            port = 22
            gss_auth = False
            gss_kex = False
        elif kwargs.get('host', False):
            return Connection(
                host=kwargs['host'],
                username=kwargs['username'],
                password=kwargs.get('password', getpass.getpass('Password ({}): '.format(kwargs['host']))),
                port=kwargs.get('port', 22),
                gss_auth=kwargs.get('gss_auth', False),
                gss_kex=kwargs.get('gss_kex', False)
            )
        else:
            raise KeyError('either connection name of connection details (host, username, etc.) must be specified')

    def _init_ssh_connection(self, **kwargs):
        c = self._get_connection(**kwargs)

        paramiko.util.log_to_file(SSH_LOG_FILE, level=logging.DEBUG)
        hostkey = self._load_host_key(c.host)

        try:
            conn = paramiko.Transport((c.host, c.port))
            conn.connect(
                hostkey,
                c.username,
                c.password,
                gss_host=socket.getfqdn(c.host),
                gss_auth=c.gss_auth,
                gss_kex=c.gss_kex
            )
            sftp = paramiko.SFTPClient.from_transport(conn)
        except paramiko.SSHException as e:
            raise OSError('could not connect to remote server {}: {}'.format(c.host, str(e)))

        return conn, sftp

    # =======================
    # UTILITIES
    # =======================

    def load_module(self, name, abs_path):
        if not self.path_exists(abs_path):
            logger.error('specified module {} does not exist'.format(abs_path))
            return None
        spec = importlib.util.spec_from_file_location('paralyze.workspace.' + name, abs_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def load_package(self, abs_path):
        """

        Parameters
        ----------
        abs_path: str
            path to package folder

        Returns
        -------
        the loaded package.
        """
        if not self.path_exists(abs_path):
            logger.error('specified package {} does not exist'.format(abs_path))
            return None
        if not self.path_exists(os.path.join(abs_path, '__init__.py')):
            logger.error('package {} has no __init__.py'.format(abs_path))
            return None
        parent_path, name = os.path.split(abs_path)
        if parent_path not in sys.path:
            sys.path.append(parent_path)
        return importlib.import_module(name)