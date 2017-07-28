"""Module documentation goes here ...

"""
from paralyze import SETTINGS
from paralyze.utils import ConfigDict, NestedDict
from jinja2 import meta
from importlib.machinery import SourceFileLoader

import os
import sys
import logging
import jinja2
import paralyze
import json
import importlib

logger = logging.getLogger(__name__)


class Workspace(object):
    """
    """

    DEFAULT_CONFIG = SETTINGS['WORKSPACE_CONFIG']

    def __init__(self, *args, **kwargs):
        """Create new workspace and load existing (remote) workspace configuration.
        """
        self.config = NestedDict(dict())

        if len(args) == 1:
            kwargs['path'] = str(args[0])

        # check if workspace root folder exists
        path = kwargs.get('path', os.getcwd())
        if not os.path.exists(path):
            raise OSError('no such file or directory: {}'.format(path))

        # root directory is set here
        self._root = path

        # check if config file exists, try to create one if not
        if not os.path.exists(self.config_file_path):
            if kwargs.get('auto_create', False):
                self._create(kwargs.get('config'))
            else:
                raise OSError('{} is not a paralyze workspace directory'.format(self.root_dir))

        # load config
        with open(self.config_file_path, 'r') as config:
            self.config = NestedDict(json.load(config))

        self._init()

    def _create(self, config):
        """Creates a new workspace configuration folder and file.
        """
        # create hidden configuration folder
        if not self.path_exists(self.config_dir):
            logger.info('creating paralyze workspace at {}'.format(self.root_dir))
            self.mkdir(SETTINGS['WORKSPACE_CONFIG_DIR'])
        # set paralyze version
        config['__version__'] = paralyze.__version__
        with open(self.config_file_path, 'w') as f:
            logger.info('saving paralyze workspace config to file {}'.format(self.config_file_path))
            json.dump(config or self.DEFAULT_CONFIG, f, indent='\t', sort_keys=True)

    def _init(self):
        """Initialize workspace.
        """
        self._validate_config()
        # init main logger
        self._init_logger()
        # check workspace and code version compatibility
        self._check_version()

    def _validate_config(self):
        """
        """
        pass

    def _init_logger(self):
        """Initialize logger.
        """
        fh = logging.FileHandler(self.config['logging.file'])
        fh.setFormatter(logging.Formatter(self.config['logging.file_format']))
        fh.setLevel(self.config['logging.level'])
        logger.addHandler(fh)

    def _check_version(self):
        """Checks code and workspace version compatibility.
        """
        wsp_version = self.version          # workspace version
        run_version = paralyze.__version__  # code version

    def get(self, key, default=None):
        return self.config.get(key, default)

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
        return self.abs_path(SETTINGS['WORKSPACE_CONFIG_DIR'])

    @property
    def config_file_path(self):
        """Returns the absolute path to the main workspace settings file.
        """
        return self.abs_path(self.config_dir, SETTINGS['WORKSPACE_CONFIG_FILE'])

    def rel_path(self, arg):
        return os.path.relpath(arg, self.root_dir)

    def abs_path(self, *args):
        return os.path.join(self.root_dir, *args)

    def mkdir(self, folder):
        """

        Parameters
        ----------
        folder: str
            path of folder relative to root_dir

        Returns
        -------

        """
        os.mkdir(self.abs_path(folder))

    def open(self, file_path, mode='r', encoding='utf-8'):
        """Opens the file specified by ``file_path`` in the given ``mode``.

        If workspace is remote, the remote file is copied to a local
        temporary folder first and then opened from there.

        Parameters
        ----------
        file_path: str
            path to file to be opened
        mode: str
            Any valid open mode, e.g. 'r', 'w', 'w+', ...
        encoding: str
            The file encoding. Default is utf-8.

        Raises
        ------
        OSError:
            if file does not exist.
        """
        return open(self.abs_path(file_path), mode, encoding=encoding)

    def path_exists(self, path):
        return os.path.exists(self.abs_path(path))


class TemplateWorkspace(Workspace):

    DEFAULT_CONFIG = SETTINGS['TEMPLATE_WORKSPACE_CONFIG']

    def __init__(self, *args, **kwargs):
        Workspace.__init__(self, *args, **kwargs)

        self.env = None
        self.params = NestedDict({})
        self.extensions = {}

        # add workspace to path to import "extensions" package easily
        sys.path.append(self._root)

        # init jinja's template environment
        self._init_template_env()
        # init parameter Python module
        self._init_parameter_module()
        # init custom context extensions
        self._init_extensions()

    def _validate_config(self):
        Workspace._validate_config(self)

    def _init_template_env(self):
        """Create and return a new jinja2 environment.

        Jinja2 uses a central object called the template Environment. Instances
        of this class are used to store the configuration and global objects,
        and are used to load templates from the file system or remote locations.
        """
        config = self.config['template.loader']
        loader = jinja2.FileSystemLoader(
            config['dirs'], encoding=config['encoding'], followlinks=config['follow_links']
        )

        config = self.config['template.environment']
        config['undefined'] = jinja2.make_logging_undefined(logger=logger, base=jinja2.StrictUndefined)
        self.env = jinja2.Environment(loader=loader, **config)

    def _init_parameter_module(self):
        """Loads the workspace parameters Python module.
        """
        param_mod_path = self.config["parameter_module"]
        if not os.path.isabs(param_mod_path):
            param_mod_path = self.abs_path(param_mod_path)

        try:
            params = SourceFileLoader("paralyze.workspace.parameters", param_mod_path).load_module().parameters
            params['root_dir'] = self.root_dir
            self.params = NestedDict(params)
        except ImportError as e:
            logger.error(str(e))
        except AttributeError as e:
            logger.error(str(e))

    def _init_extensions(self):
        """
        """
        self.extensions = {}
        pkg = importlib.import_module('extensions')
        for key in pkg.__all__:
            if key in self.extensions.keys():
                logger.warning('duplicate extension name "{}". Former one will be replaced!'.format(key))
            self.extensions[key] = getattr(pkg, key)

    def _config_dict(self, mapping):
        env = self.config['template.environment']
        return ConfigDict(mapping, var_start=env['variable_start_string'], var_end=env['variable_end_string'])

    def init_vars(self, **kwargs):
        """Initializes parameter configuration and template variables.

        Parameters
        ----------
        kwargs:
        - ignore_missing: bool

        """
        pro = NestedDict(kwargs)  # provided args
        pro_args = set(pro.leaf_keys())
        req_args = self.get_parameter_variables()  # required args

        missing = req_args - pro_args
        if len(missing) and not kwargs.get('ignore_missing', False):
            raise KeyError('missing parameters: {!s}'.format(', '.join(missing)))

        context = dict(zip(req_args, pro[req_args]))
        params = self._config_dict(self.params)
        self.params = params.finalize(**context)

        logger.debug('initialized params: {}'.format(self.params))

    def get_context(self, **kwargs):
        """Returns the template context (parameters + extensions).
        """
        context = self.params.to_dict()
        context.update(self.extensions)
        context.update(kwargs)
        return context

    def get_variables(self, templates=()):
        """Returns all undefined workspace variables.

        Parameters
        ----------
        templates

        Returns
        -------

        """
        return self.get_parameter_variables() | self.get_template_variables(templates)

    def get_parameter_variables(self):
        """Returns the set of undefined parameters

        Returns
        -------

        """
        return self._config_dict(self.params).variables()

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

    def render_template(self, template, **kwargs):
        """

        Parameters
        ----------
        template: str

        kwargs:

        """
        template = self.env.get_template(template)
        context = self.get_context(**kwargs)
        return template.render(**context)

    def _get_template_variables(self, template):
        """Recursively parses undeclared variables in template and all
        referenced templates.

        Parameters
        ----------
        template: str
            name of template file

        Returns
        -------
        template_vars: set
            the set of template variables (strings)
        """
        source = self.env.loader.get_source(self.env, template)[0]
        template_ast = self.env.parse(source)

        template_vars = meta.find_undeclared_variables(template_ast)
        for ref_template in meta.find_referenced_templates(template_ast):
            template_vars.update(self._get_template_variables(ref_template))

        return template_vars
