"""Module documentation goes here ...

"""
from jinja2 import meta
from paralyze.utils import Configuration, NestedDict
from .remote import RemoteFileSystemLoader

import os
import logging
import sys
import shutil
import importlib.util
import socket
import getpass
import jinja2
import paramiko
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
        self.config = dict()
        self.parameters = dict()

        if len(args) == 1:
            kwargs['path'] = str(args[0])

        # create SSH and SFTP connection if required
        if kwargs.get('connection') or kwargs.get('host'):
            self._conn, self._sftp = self._init_ssh_connection(**kwargs)
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

        # check if settings file exists, try to create one if not
        if not self.path_exists(self.config_file_path):
            if kwargs.get('auto_create', False):
                self._create(kwargs.get('config', None))
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
        config = self.config['template.loader'].copy()

        if self.is_remote():
            loader = RemoteFileSystemLoader(
                self._sftp, config['dirs'], encoding=config['encoding'], follow_links=config['follow_links']
            )
        else:
            loader = jinja2.FileSystemLoader(
                config['dirs'], encoding=config['encoding'], followlinks=config['follow_links']
            )

        self.env = jinja2.Environment(loader=loader)

    def _init_context_extensions(self):
        """
        """
        self.extensions = {}
        if self.is_remote():
            self.extensions = self._init_remote_extensions()
        else:
            self.extensions = self._init_local_extensions()

    def _init_local_extensions(self):
        """Loads local context extensions.

        extension_dir/__init__.py
        extension_dir/my_extension.py
        """
        extensions = {}
        for extension_dir in self.config['template.context_extension_dirs']:
            abs_ext_dir = self.abs_path(extension_dir)
            ext_init = self.abs_path(extension_dir, '__init__.py')
            if self.path_exists(ext_init):
                sys.path.append(self.root_dir)
                mod = importlib.import_module(extension_dir)
                for ext_key in mod.__all__:
                    if ext_key in extensions.keys():
                        logger.warn('duplicate extension "{}". Former extension will be replaced!'.format(ext_key))
                    extensions[ext_key] = getattr(mod, ext_key)
            else:
                logger.warn('no __init__.py found in extension directory {}'.format(extension_dir))
        return extensions

    def _init_remote_extensions(self):
        """
        """
        # TODO: Implement remote extension initialization.
        return {}

    def _init_parameter_module(self):
        """Loads the workspace parameters Python module.

        """
        # TODO: Implement exception handling for parameter module initialization
        if self.has_params():
            spec = importlib.util.spec_from_file_location('workspace.parameters', self.get_abs_path('parameter_module'))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.config['root_dir'] = self.root_dir
            self.parameters = module.config
        else:
            self.parameters = dict()

    def _create(self, config=None):
        """Creates a new workspace configuration folder and file.
        """
        # create hidden configuration folder
        if not self.path_exists(self.config_dir):
            logger.info('creating paralyze workspace at {}'.format(self.root_dir))
            self.mkdir(self.config_dir)
        # set paralyze version
        config = config or DEFAULT_CONFIG
        config['__version__'] = paralyze.__version__
        with self.open(self.config_file_path, 'w') as config_file:
            logger.debug('saving paralyze workspace config to file {}'.format(self.config_file_path))
            json.dump(config, config_file, indent='\t', sort_keys=True)

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
            logger.warn('you tried to initialize workspace parameters without an existing or valid parameters module')
            return

        pro = NestedDict(kwargs)  # provided args
        pro_args = set(pro.keys())
        req = NestedDict(self.parameters)  # required args
        req_args = set(req.keys())

        missing = req_args - pro_args
        if len(missing):
            raise KeyError('missing parameters: {!s}'.format(missing))

        config = Configuration(self.parameters, **self.config['template.environment'])
        self.parameters = NestedDict(config.render(**dict(zip(req_args, pro[req_args]))))

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

    def _init_ssh_connection(self, **kwargs):
        if kwargs.get('connection', False):
            # TODO: load connection details from file!
            host = ""
            username = ""
            password = ""
            port = 22
        elif kwargs.get('host', False):
            host = kwargs.get('host')
            username = kwargs.get('username')
            password = getpass.getpass('Password ({}): '.format(host))
            port = kwargs.get('port', 22)
            gss_auth = kwargs.get('gss_auth', False)
            gss_kex = kwargs.get('gss_key', False)
        else:
            raise KeyError('either connection name of connection details (host, username, etc.) must be specified')

        paramiko.util.log_to_file(SSH_LOG_FILE, level=logging.DEBUG)
        hostkey = self._load_host_key(host)

        try:
            conn = paramiko.Transport((host, port))
            conn.connect(
                hostkey,
                username,
                password,
                gss_host=socket.getfqdn(host),
                gss_auth=gss_auth,
                gss_kex=gss_kex
            )
            sftp = paramiko.SFTPClient.from_transport(conn)
        except paramiko.SSHException as e:
            raise OSError('could not connect to remote server {}: {}'.format(host, e.args[0]))

        return conn, sftp

    # ========================
    # FILESYSTEM RELATED STUFF
    # ========================

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
            raise OSError('no such file or directory: {}'.format(file_path))

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

    def _create_temp_file_path(self, file_path):
        """Returns a path to a new temporary file.
        """
        if self.temp_dir is None:
            self.temp_dir = tempfile.mkdtemp(prefix='paralyze')
        # TODO: Create unique file names!
        return os.path.join(self.temp_dir, os.path.basename(file_path))

    # ======================
    # PARAMETER FRAMEWORK
    # ======================

    def get_context(self):
        """Returns the template context (setting + extensions).
        """
        context = self.config
        context.update(self.get_context_extensions())
        return context

    def get_context_extensions(self):
        return self.extensions

    def get_undefined(self, templates=()):
        pars = self.get_module_parameters() | self.get_template_variables(templates)
        keys = self.parameters.keys()
        return pars - keys

    def get_module_parameters(self):
        return Configuration(self.parameters, **self.config['template.environment']).variables()

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
        # remove builtin names
        template_vars = template_vars - self._builtin_names
        return template_vars

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
            set of template variables as strings
        """
        template = self.get_template_source(template)[0]

        try:
            template_ast = self.env.parse(template)
        except jinja2.TemplateSyntaxError as e:
            logger.error('error while parsing template file "{}": {} (line: {})'.format(template, e.message, e.lineno))
            return set()

        template_vars = meta.find_undeclared_variables(template_ast)

        for ref_template in meta.find_referenced_templates(template_ast):
            template_vars.update(self._get_template_variables(ref_template))

        return template_vars

    def render_template(self, template, custom_context=None):
        """

        Parameters
        ----------
        template: str
            The key of the template in the workspace configuration.
        custom_context: mapping

        """
        # load template file
        template = self.get_template(template)

        context = self.get_context()
        context.update(custom_context or {})
        return template.render(**context)

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
