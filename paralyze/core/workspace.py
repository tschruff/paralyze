import os
import posixpath
import json
import logging
import sys
import shutil
import importlib
import argparse
import socket
import getpass
import jinja2
import paramiko

from jinja2 import meta
from .rdict import rdict
from .cli_ext import type_cast
from .io.json_ext import ParalyzeJSONDecoder, ParalyzeJSONEncoder

logger = logging.getLogger(__name__)

SETTINGS_DIR = ".paralyze"

LOG_FILE = "log.txt"
SSH_LOG_FILE = "ssh_log.txt"
LOG_FILE_FORMAT = "[%(asctime)-15s][%(levelname)-7s] %(message)s"

VERSION = "0.1.0"
VERSION_KEY = "__version__"

SETTINGS_FILE = "workspace.json"
CONNECTIONS_FILE = "connections.json"


class RemoteFileSystemLoader(jinja2.BaseLoader):

    def __init__(self, sftp, *search_path, encoding='utf-8', follow_links=False):
        self._sftp = sftp
        self._path = search_path
        self._enc = encoding
        self._follow_links = follow_links

    def get_source(self, environment, template):
        for path in self._path:
            result = self._get_source(path, environment, template)
            if len(result):
                return result
        raise jinja2.TemplateNotFound(template)

    def _get_source(self, path, environment, template):
        path = posixpath.join(path, template)
        if not self._path_exists(path):
            return ()
        mtime = self._get_stat(path).st_mtime
        with self._sftp.file(path, 'r') as f:
            source = f.read().decode('utf-8')
        return source, path, lambda: mtime == self._get_stat(path).st_mtime

    def _path_exists(self, path):
        try:
            self._get_stat(path)
            return True
        except IOError:
            return False

    def _get_stat(self, path):
        if self._follow_links:
            return self._sftp.stat(path)
        else:
            return self._sftp.lstat(path)


class Workspace(object):
    """
    """

    def __init__(self, *args, **kwargs):
        """
        """
        self._conn = None
        self._sftp = None
        self._root = ""
        self._builtin_template_vars = set([name for name in __builtins__ if not name.startswith('_')])
        self._extensions = {}
        self._raw = {}
        self._temp_dir = ""
        self._template_env = None

        # parse arguments from command line if they where not provided
        # explicitly
        if len(args) + len(kwargs) == 0:
            kwargs = self._parse_args()
        elif len(args) == 1:
            path = args[0]
            kwargs["path"] = path

        # create SSH connection if required
        self._conn, self._sftp = self._init_ssh_connection(**kwargs)

        cwd = self._sftp.getcwd() if self.is_remote() else os.getcwd()
        path = kwargs.get("path", cwd)

        auto_create = kwargs.get("auto_create", False)
        settings = kwargs.get("settings", {})

        # absolute path to workspace root folder
        if not self.path_exists(path):
            raise OSError('No such file or directory "{}""'.format(path))

        self._root = path

        if not self.path_exists(self.settings_file_path):
            if auto_create:
                self._create(settings)
            else:
                raise OSError('Directory "{}" is not a paralyze workspace'.format(self.root))

        # load raw dict (with variables as raw template strings)
        self._raw = self._load()
        self._check_version()

    def __del__(self):
        if self.is_remote():
            self._conn.close()

        if self._temp_dir != "":
            shutil.rmtree(self._temp_dir)

    def __contains__(self, item):
        return item in self._raw

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self._raw[key] = value

    def __str__(self):
        return str(self.get_settings())

    @property
    def version(self):
        return self._raw[VERSION_KEY]

    def get(self, key, default=None, raw=False):
        if raw:
            return self._raw.get_raw(key, default)
        else:
            return self._raw.get(key, default)

    def get_settings(self):
        settings = {}
        for key in self._raw.keys():
            settings[key] = self.get(key)
        return settings

    def keys(self, private=False):
        if private:
            return self._raw.keys()
        return [key for key in self._raw.keys() if not key.startswith('__')]

    def pop(self, key):
        return self._raw.pop(key)

    def update(self, other):
        self._raw.update(other)

    # ========================
    # WORKSPACE INITIALIZATION
    # ========================

    def init(self, args=None, main_logger=None):
        """

        Returns
        -------
        remaining_args: list
            The list of all args that have not been used during initialization.
        """
        args = args or sys.argv
        # init workspace variables first because template or extension settings
        # might depend on workspace variables
        remaining_args = self._init_workspace_variables(args)
        # init main logger to enable logging during remaining initialization
        self._init_logger(main_logger)
        # init custom constext extensions
        self._extension_dirs = self._load_context_extensions()
        # init template environment before first template access
        self._template_env  = self._get_template_env()
        remaining_args = self._init_template_variables(remaining_args)
        return remaining_args

    def _parse_args(self):

        parser = argparse.ArgumentParser()
        # add job_cli arguments
        parser.add_argument(
            '--create_workspace',
            action='store_true',
            default=False,
            help="create a new workspace at the current work directory"
        )
        parser.add_argument(
            '--path',
            type=str,
            default='.'
        )
        parser.add_argument(
            '--host',
            type=str,
            default=''
        )
        parser.add_argument(
            '--username',
            type=str,
            default=''
        )
        parser.add_argument(
            '--password',
            type=str,
            default=''
        )

        args, custom_args = parser.parse_known_args()
        return vars(args)

    def _create(self, settings=None):
        # create hidden settings folder
        if not self.path_exists(self.settings_dir):
            logger.info('creating paralyze workspace at {}'.format(self.root))
            self.mkdir(settings_dir)
        # set paralyze version
        settings[VERSION_KEY] = VERSION
        settings.pop("root_path")
        # save settings to json file
        with self.open(self.settings_file_path, 'w') as settings_file:
            logger.debug('saving paralyze workspace settings to file {}'.format(self.settings_file_path))
            json.dump(settings or {}, settings_file, indent=4, sort_keys=True, cls=ParalyzeJSONEncoder)

    def _load(self):
        with self.open(self.settings_file_path, 'r') as settings:
            data = json.load(settings, cls=ParalyzeJSONDecoder)
        data["root_path"] = self.root
        return rdict(data)

    def _check_version(self):
        """TODO: Implement version comparison and policy.
        """
        wsp_version = self.version
        core_version = VERSION

    def _init_workspace_variables(self, args):
        """Initializes variables in the settings dict with values given in args.

        Parameters
        ----------
        args: dict or list
            A dict with variable names as keys or a list of command line
            arguments.

        Returns
        -------
        custom_args: dict or list
            The list of unused command line arguments if args is a list or an
            empty list if args is a dict.
        """
        # init variables from dict
        if isinstance(args, dict):
            self.update(args)
            return []

        # init variables from argument list
        parser = argparse.ArgumentParser()
        # add workspace variables as required command line arguments
        for var in self.get_workspace_variables():
            parser.add_argument('--%s' % var, required=True, type=type_cast)
        wsp_args, unknown_args = parser.parse_known_args(args or sys.argv)
        # update workspace settings directly with command line values
        self.update(vars(wsp_args))
        return unknown_args

    def _init_logger(self, main_logger=None):
        log_level = self.get("log_level", logging.DEBUG)
        log_format = self.get("log_format", LOG_FILE_FORMAT)

        file_handler = logging.FileHandler(self.log_file_path)
        file_handler.setFormatter(logging.Formatter(log_format))
        file_handler.setLevel(log_level)

        if main_logger:
            main_logger.addHandler(file_handler)

        logger.addHandler(file_handler)

    # =======================
    # SSH/SFTP INITIALIZATION
    # =======================

    def _load_host_key(self, host):
        hostkeytype = None
        hostkey = None
        try:
            host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
        except IOError:
            try:
                # try ~/ssh/ too, because windows can't have a folder named ~/.ssh/
                host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/ssh/known_hosts'))
            except IOError:
                raise OSError('Unable to open ssh host keys file')
                host_keys = {}

        if host in host_keys:
            hostkeytype = host_keys[host].keys()[0]
            hostkey = host_keys[host][hostkeytype]

        return hostkey

    def _init_ssh_connection(self, **kwargs):
        if kwargs.get("connection", False):
            # TODO: Implement!
            host = ""
            username = ""
            password = ""
            port = 22
        elif kwargs.get("host", False):
            host = kwargs.get("host")
            username = kwargs.get("username")
            password = getpass.getpass("Password ({}): ".format(host))
            port = kwargs.get("port", 22)
            gss_auth = kwargs.get("gss_auth", False)
            gss_kex = kwargs.get("gss_key", False)
        else:
            return None, None

        paramiko.util.log_to_file(SSH_LOG_FILE, level=logging.DEBUG)

        hostkey = self._load_host_key(host)

        try:
            conn = paramiko.Transport((host, port))
            conn.connect(hostkey, username, password, gss_host=socket.getfqdn(host), gss_auth=gss_auth, gss_kex=gss_kex)
            sftp = paramiko.SFTPClient.from_transport(conn)
        except paramiko.SSHException as e:
            raise OSError('Could not connect to remote server {}: {}'.format(host, e.args[0]))

        return conn, sftp

    # ========================
    # FILESYSTEM RELATED STUFF
    # ========================

    @property
    def root(self):
        return self._root

    @property
    def settings_dir(self):
        return self.abs_path(SETTINGS_DIR)

    @property
    def settings_file_path(self):
        return self.abs_path(SETTINGS_DIR, SETTINGS_FILE)

    @property
    def log_file_path(self):
        return self.abs_path(self.get("log_file", LOG_FILE))

    def rel_path(self, arg):
        if self.is_remote():
            return posixpath.relpath(arg, self.root)
        return os.path.relpath(arg, self.root)

    def abs_path(self, *args):
        if self.is_remote():
            return posixpath.join(self.root, *args)
        return os.path.join(self.root, *args)

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
        """Opens the file specified by `file_path` in the given `mode`.
        If workspace is remote, the remote file is copied to a local
        temporary folder first and then openend from there.

        Parameters
        ----------
        file_path: str
            Path to file to be openend.
        mode: str
            Any valid open mode, e.g. 'r', 'w', 'w+', ...
        encoding: str
            The file encoding. Default is utf-8.

        Raises
        ------
        OSError: In case file does not exist.
        """
        if not self.is_abs_path(file_path):
            file_path = self.abs_path(file_path)

        # file_path is absolute from here on!
        if not self.path_exists(file_path):
            raise OSError("No such file or directory: {}".format(file_path))

        if self.is_remote():
            # copy remote file to temp dir and open it from there
            open_path = self._temp_file_path(file_path)
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

    def _temp_file_path(self, file_path):
        """Returns a path to a new temporary file.
        """
        if self._temp_dir is None:
            self._temp_dir = tempfile.makedtemp(prefix='paralyze')
        # TODO: Create unique file names!
        return os.path.join(self._temp_dir, os.path.basename(file_path))

    # ======================
    # TEMPLATE RELATED STUFF
    # ======================

    def get_context(self):
        context = self.get_settings()
        context.update(self.get_context_extensions())
        return context

    def get_context_extensions(self):
        return self._extensions

    def get_variables(self):
        return self.get_workspace_variables() + self.get_template_variables()

    def get_workspace_variables(self):
        return self._raw.vars()

    def get_template_variables(self):
        template_vars = set([])
        for template_key in self.get("templates", {}).keys():
            var = self._get_template_variables(template_key)
            template_vars.update(var)
        # remove builtin names
        template_vars = template_vars - self._builtin_template_vars
        return template_vars

    def render_template_file(self, template_key, custom_context=None):
        """

        Parameters
        ----------
        template_key: str
            The name of the template.
        """
        # load template file
        template = self._get_template(template_key)

        try:
            context = self.get_context()
            if isinstance(custom_context, dict):
                context.update(custom_context)
            return template.render(**context)
        except TypeError as e:
            logger.error('error during rendering of template file "{}": {}'.format(template_key, e.args[0]))
            return ""

    def _get_template_variables(self, template_key):
        """Recursively parse undeclared variables in template file and all
        referenced files.

        Parameters
        ----------
        filename: str
            name of template file

        Returns
        -------
        template_vars: set
            set of template variables as strings
        """
        template = self._get_template_source(template_key)

        try:
            template_ast = self._template_env.parse(template)
        except jinja2.TemplateSyntaxError as e:
            logger.error('error while parsing template file "{}": {} (line: {})'.format(template_file, e.message, e.lineno))
            sys.exit(1)

        template_vars = meta.find_undeclared_variables(template_ast)

        for ref_template in meta.find_referenced_templates(template_ast):
            template_vars.update(self._get_template_variables(ref_template))

        return template_vars

    def _get_template_source(self, key):
        if key in self.get("templates", []):
            key = self.get("templates")[key]
        return self._template_env.loader.get_source(self._template_env, key)[0]

    def _get_template(self, key):
        if key in self.get("templates", []):
            key = self.get("templates")[key]
        return self._template_env.get_template(key)

    def _get_template_env(self):
        if self.is_remote():
            loader = RemoteFileSystemLoader(self._sftp, self.get("template_dirs", []))
        else:
            loader = jinja2.FileSystemLoader(self.get("template_dirs", []))

        return jinja2.Environment(loader=loader)

    def _init_template_variables(self, args):

        existing_names = set(self.keys())
        existing_names.update(set(self.get_context_extensions().keys()))

        template_vars = self.get_template_variables() - existing_names

        if not len(template_vars):
            return []

        parser = argparse.ArgumentParser()
        # parse all variables as strings first
        for var in template_vars:
            parser.add_argument('--%s' % var, required=True, type=type_cast)
        # parse template args from command line
        template_args, unknown_args = parser.parse_known_args(args)
        # and add them to the context
        self.update(vars(template_args))
        return unknown_args

    def _load_context_extensions(self):
        """
        """
        self._extensions = {}
        if self.is_remote():
            self._extensions = self._load_remote_extensions()
        else:
            self._extensions = self._load_local_extensions()

    def _load_local_extensions(self):
        extensions = {}
        for extension_dir in self.get("context_extension_dirs", []):
            abs_ext_dir = self.abs_path(extension_dir)
            ext_init = self.abs_path(extension_dir, "__init__.py")
            if self.path_exists(ext_init):
                sys.path.append(self.root)
                mod = importlib.import_module(extension_dir)
                for ext_key in mod.__all__:
                    if ext_key in extensions.keys():
                        logger.warn('duplicate extension "{}". Former extension will be replaced!'.format(ext_key))
                    extensions[ext_key] = getattr(mod, ext_key)
            else:
                logger.warn('No __init__.py found in extension directory {}'.format(extension_dir))
        return extensions

    def _load_remote_extensions(self):
        """TODO: Implement.
        """
        return {}
