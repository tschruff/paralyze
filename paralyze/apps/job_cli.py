from paralyze import ARCH, VERSION
from paralyze.core import Workspace, type_cast, rdict
from paralyze.core.io import ParalyzeJSONEncoder

import os
import ast
import argparse
import sys
import logging
import json

import jinja2

logger = logging.getLogger(__name__)

LOG_STREAM_FORMAT = '[%(levelname)-7s] %(message)s'

REQUIRED_WORKSPACE_KEYS = ['job_name', 'run_dir', 'templates', 'template_dirs']
OPTIONAL_WORKSPACE_KEYS = ['schedule_cmd']

# default workspace settings
WORKSPACE_TEMPLATE_FILE = ""


def save_job_file(wsp, template_key, force=False):
    """Parses template variables from template_file and adds them as argument to
    the command line.

    Parameters
    ----------
    template_key: str
        Name of template
    force: bool
        Force overriding existing files

    Notes
    -----
    Existing files will only be overridden if *force* is set True.
    """
    out_file = wsp.get('files')[template_key]
    if os.path.exists(out_file) and not force:
        logger.error('could not create file "{}" because a file with same name already exists!'.format(out_file))
        return

    content = wsp.render_template_file(template_key)
    if not len(content):
        return

    with open(out_file, 'w') as job:
        job.write(content)

    # log progress
    logger.info('created file "{}"'.format(out_file))


def generate_file_paths(wsp):
    """

    Rendered files will be saved to
    <wsp_root>/<run_dir>/<template_key>/<job_name>.<template_file_suffix>
    """
    wsp['files'] = {}
    for key in wsp['templates'].keys():

        template_file = wsp['templates'][key]
        suffix = template_file[template_file.rfind('.'):]
        folder = os.path.join(wsp['run_dir'], key)
        wsp['files'][key] = os.path.join(folder, wsp['job_name'] + suffix)

        if not os.path.exists(folder):
            logger.info('creating sub-folder in run_dir "{}"'.format(key))
            try:
                os.makedirs(folder)
            except OSError as e:
                logger.error(e.args[0])
                sys.exit(1)


def check_workspace(wsp):
    error = False
    for key in REQUIRED_WORKSPACE_KEYS:
        if key not in wsp:
            logger.error('Missing required workspace key "{}"'.format(key))
            error = True
    for key in OPTIONAL_WORKSPACE_KEYS:
        if key not in wsp:
            logger.warning('Missing optional workspace key "{}" may cause problems!'.format(key))
    if error:
        sys.exit(1)


def main():

    parser = argparse.ArgumentParser()
    # add job_cli arguments
    parser.add_argument(
        '--create_workspace',
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
        '--job',
        type=str,
        default='',
        help='import job settings to the global scope (may replace global settings)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        default=False,
        help='increase logging output'
    )

    args, custom_args = parser.parse_known_args()

    if args.verbose:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING
    # configure logging and add stream handler
    logging.basicConfig(format=LOG_STREAM_FORMAT, level=log_level)

    # create workspace
    try:
        if args.create_workspace:
            # create workspace and exit
            with open(WORKSPACE_TEMPLATE_FILE, "r") as workspace_file:
                settings = workspace_file.read().format(PARALYZE_VERSION=VERSION)
                settings = json.loads(settings, cls=ParalyzeJSONDecoder)
            wsp = Workspace(auto_create=True, settings=settings)
            logger.info('created new workspace at {}'.format(wsp.root))
            sys.exit()
        else:
            # create workspace and continue
            wsp = Workspace()
    except IOError as e:
        print('Error: {}'.format(e.args[0]))
        sys.exit(1)

    # override settings with job specific variables before init the workspace
    if args.job != '':
        jobs = wsp.pop('jobs')
        if args.job in jobs:
            logger.info('temporarily overriding default workspace settings with job variables from "{}"'.format(args.job))
            wsp.update(jobs[args.job])
        else:
            logger.error('job "{}" does not exist!'.format(args.job))
            sys.exit(1)

    # initialize workspace variables with command line arguments
    job_args = wsp.init(custom_args, main_logger=logger)

    # check if all required workspace keys exist
    check_workspace(wsp)

    # generates a file path for each item in "templates" to the workspace settings
    generate_file_paths(wsp)

    # SAVE rendered template files
    for template_key in wsp.get('templates').keys():
        try:
            save_job_file(wsp, template_key, args.force)
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
            logger.error(e.args[0])
            sys.exit(1)

    # SCHEDULE job
    if args.schedule:
        logger.info('scheduling job "{}" for execution'.format(context['job_name']))
        os.system(context['schedule_cmd'])


if __name__ == '__main__':
    main()
