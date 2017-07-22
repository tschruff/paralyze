from paralyze.core.io import ParalyzeJSONEncoder, type_cast
from paralyze.workspace import *

import paralyze
import os
import ast
import argparse
import sys
import logging
import json

import jinja2

logger = logging.getLogger(__name__)

LOG_STREAM_FORMAT = '[%(levelname)-7s] %(message)s'

REQUIRED_WORKSPACE_KEYS = ['job_id', 'job_task', 'tasks', 'templates']
OPTIONAL_WORKSPACE_KEYS = ['schedule_cmd', 'make_dirs']

# default workspace settings
DEFAULT_PARAMETER_CONFIG = {}


def save_job_file(wsp, template, force=False):
    """Renders and saves the template to a file.

    Parameters
    ----------
    template: str
        Name of template
    force: bool
        Force overwriting existing files

    """
    out_file = wsp.abs_path(wsp.parameters['templates'][template])
    if os.path.exists(out_file) and not force:
        logger.error('file "{}" already exists, specify --force to overwrite.'.format(out_file))
        return False

    content = wsp.render_template(template)

    with open(out_file, 'w') as dest:
        dest.write(content)

    logger.info('created file "{}"'.format(out_file))
    return True


def make_dirs(wsp):
    """
    """
    for key in wsp.parameters.get('make_dirs', []):
        folder = wsp.abs_path(key)
        if not os.path.exists(folder):
            logger.info('creating folder in workspace "{}"'.format(folder))
            try:
                os.makedirs(folder)
            except OSError as e:
                logger.error(str(e))
                sys.exit(1)


def check_workspace(wsp):
    """
    """
    error = False
    for key in REQUIRED_WORKSPACE_KEYS:
        if key not in wsp.parameters:
            logger.error('missing required workspace item "{}"'.format(key))
            error = True
    for key in OPTIONAL_WORKSPACE_KEYS:
        if key not in wsp.parameters:
            logger.warning('undefined optional workspace item "{}"'.format(key))
    if error:
        sys.exit(1)


def import_task_settings(task, wsp):
    """
    """
    if 'tasks' not in wsp.parameters:
        logger.error('missing parameter config item: tasks')
        sys.exit(1)

    tasks = wsp.parameters['tasks']
    if task in tasks:
        logger.info('temporarily overriding workspace with task variables from "{}"'.format(task))
        wsp.parameters.update(tasks[task])
        wsp.parameters['job_task'] = task
        return wsp
    else:
        logger.error('undefined task "{}"'.format(task))
        sys.exit(1)


def perform_tests_and_exit(wsp):
    """
    """
    sys.exit(0)


def argument_parser():
    """
    """
    parser = argparse.ArgumentParser()
    # add job_cli arguments
    parser.add_argument(
        '--create-workspace',
        action='store_true',
        default=False,
        help="create a new workspace at the current work directory"
    )
    parser.add_argument(
        '--force',
        action='store_true',
        default=False,
        help='ignore and override existing files'
    )
    parser.add_argument(
        '--schedule',
        action='store_true',
        default=False,
        help='add job to the system scheduler after creation'
    )
    parser.add_argument(
        '--task',
        type=str,
        default='',
        help='import task settings to the global scope (may replace global settings)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        default=False,
        help='increase logging output'
    )
    parser.add_argument(
        '--print-vars',
        action='store_true',
        default=False,
        help='prints undefined parameter variables to stdout'
    )
    return parser


def main():

    parser = argument_parser()
    args, wsp_args = parser.parse_known_args()

    if args.verbose:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING

    # configure logging and add stream handler
    logging.basicConfig(format=LOG_STREAM_FORMAT, level=log_level)

    # create workspace instance
    try:
        if args.create_workspace:
            # create workspace and exit
            wsp = Workspace(auto_create=True)
            logger.info('created new workspace at: {}'.format(wsp.root_dir))
            sys.exit()
        else:
            # create workspace and continue
            wsp = Workspace()
    except OSError as e:
        logger.error(str(e))
        sys.exit(1)

    # import task settings into the top-level namespace
    import_task_settings(args.task, wsp)

    # check if all required workspace keys exist
    check_workspace(wsp)

    # add workspace variables as required command line arguments
    wsp_parser = argparse.ArgumentParser()

    vars = wsp.get_undefined(wsp.parameters['templates'].keys())
    if args.print_vars:
        print('undefined variables: {!s}'.format(vars))
        sys.exit(0)

    for var in vars:
        wsp_parser.add_argument('--%s' % var, required=True, type=type_cast)
    wsp_args, unused_args = wsp_parser.parse_known_args(wsp_args)

    # initialize workspace variables with command line arguments
    wsp.init_params(**vars(wsp_args))

    # create directories
    make_dirs(wsp)

    # SAVE rendered template files
    for template_key in wsp.parameters['templates'].items():
        try:
            if not save_job_file(wsp, template_key, args.force):
                sys.exit(1)
        except jinja2.exceptions.UndefinedError as e:
            logger.error('usage of undefined parameter "{}" in template "{}"!'.format(e.message, template_key))
            sys.exit(1)
        except jinja2.exceptions.TemplateNotFound as e:
            logger.error('template file "{}" not found for template "{}"!'.format(e.message, template_key))
            sys.exit(1)
        except jinja2.exceptions.TemplateSyntaxError as e:
            logger.error('syntax error in template "{}": {}'.format(template_key, e.message))
            sys.exit(1)
        except IOError as e:
            logger.error(str(e))
            sys.exit(1)

    # SCHEDULE job
    if args.schedule:
        logger.info('scheduling job "{}" for execution'.format(wsp['job_id']))
        os.system(wsp['schedule_cmd'])


if __name__ == '__main__':
    main()
