import argparse
import logging
import os
import sys
import csv
import datetime

from paralyze.utils.io import type_cast
from paralyze.workspace import TemplateWorkspace

logger = logging.getLogger(__name__)

LOG_STREAM_FORMAT = '[%(levelname)-7s] %(message)s'

REQUIRED_WORKSPACE_KEYS = ['run_dir', 'job_id', 'tasks', 'templates', 'history_dir']
OPTIONAL_WORKSPACE_KEYS = ['schedule_cmd', 'make_dirs']

HISTORY_FILE = "{task}_history.csv"


def render_and_save(wsp, template_key, force=False):
    """Renders and saves the template to a file.

    Parameters
    ----------
    wsp: TemplateWorkspace

    template_key: str
        Name of template
    force: bool
        Force overwriting existing files

    """
    template = wsp.params['templates'][template_key]
    ext = os.path.splitext(template)[1]
    out_file = wsp.params.get('files', {}).get(template_key, os.path.join(wsp.params['run_dir'], wsp.params['job_id']+'.'+ext))
    abs_out = wsp.abs_path(out_file)
    if os.path.exists(abs_out) and not force:
        logger.error('file "{}" already exists, specify "--force" to replace.'.format(out_file))
        return False

    content = wsp.render_template(template)

    with open(abs_out, 'w') as dest:
        dest.write(content)

    logger.info('created file "{}"'.format(out_file))
    return True


def make_dirs(wsp):
    """

    Parameters
    ----------
    wsp: TemplateWorkspace

    """
    for key in wsp.params.get('make_dirs', []):
        folder = wsp.abs_path(key)
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
                logger.info('created folder "{}"'.format(key))
            except OSError as e:
                logger.error(str(e))
                sys.exit(1)


def check_workspace(wsp):
    """

    Parameters
    ----------
    wsp: TemplateWorkspace

    Returns
    -------

    """
    error = False
    for key in REQUIRED_WORKSPACE_KEYS:
        if key not in wsp.params:
            logger.error('missing required workspace item: {}'.format(key))
            error = True
    for key in OPTIONAL_WORKSPACE_KEYS:
        if key not in wsp.params:
            logger.info('undefined optional workspace item: {}'.format(key))
    if error:
        sys.exit(1)


def import_task_settings(wsp, task):
    """
    Parameters
    ----------
    wsp: TemplateWorkspace

    task: str

    """
    if 'tasks' not in wsp.params:
        logger.error('missing parameter config item: tasks')
        sys.exit(1)

    tasks = wsp.params['tasks']
    if task in tasks:
        logger.debug('temporarily overriding workspace with task variables (task: {})'.format(task))
        wsp.params.update(tasks[task])
        wsp.params['job_task'] = task
        return wsp
    else:
        logger.error('undefined task: {}'.format(task))
        sys.exit(1)


def add_to_history(wsp, task, params):
    """

    Parameters
    ----------
    wsp: TemplateWorkspace
    task: str
    params: dict

    Returns
    -------

    """
    history_file = wsp.abs_path(wsp.params['history_dir'], HISTORY_FILE.format(task=task))
    exists = os.path.exists(history_file)

    params['schedule_date'] = datetime.datetime.now()
    params['executed'] = "nan"
    params['finished'] = "nan"

    if exists:
        with open(history_file, 'r') as csv_file:
            field_names = csv.DictReader(csv_file).fieldnames
    else:
        field_names = params.keys()

    with open(history_file, 'a') as csv_file:
        writer = csv.DictWriter(csv_file, field_names)
        if not exists:
            writer.writeheader()
        writer.writerow(params)

    logger.info('added job to history file "{}"'.format(history_file))


def argument_parser():
    """
    """
    parser = argparse.ArgumentParser()
    # add job_cli arguments
    parser.add_argument('task', type=str,
                        help='import task settings to the global scope (may replace global settings)')

    parser.add_argument('--create-workspace', action='store_true', default=False,
                        help="create a new workspace at the current work directory")

    parser.add_argument('--force', action='store_true', default=False,
                        help='ignore and override existing files')

    parser.add_argument('--schedule', action='store_true', default=False,
                        help='add job to the system scheduler after creation')

    parser.add_argument('--verbose', action='store_true', default=False,
                        help='set log level to DEBUG')

    parser.add_argument('--print-vars', action='store_true', default=False,
                        help='print undefined parameter variables to stdout')

    return parser


def main():

    parser = argument_parser()
    args, wsp_args = parser.parse_known_args()

    if args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    # configure logging and add stream handler
    logging.basicConfig(format=LOG_STREAM_FORMAT, level=log_level)

    # create workspace instance
    try:
        if args.create_workspace:
            # create workspace and exit
            wsp = TemplateWorkspace(auto_create=True)
            logger.info('created new workspace at: {}'.format(wsp.root_dir))
            sys.exit()
        else:
            # create workspace and continue
            wsp = TemplateWorkspace()
    except OSError as e:
        logger.error(str(e))
        sys.exit(1)

    # import task settings into the top-level namespace
    import_task_settings(wsp, args.task)

    # check if all required workspace keys exist
    check_workspace(wsp)

    # add workspace variables as required command line arguments
    wsp_parser = argparse.ArgumentParser()

    undefined = wsp.get_variables(templates=wsp.params['templates'].values())
    if args.print_vars:
        if not len(undefined):
            logger.info('no undefined variables')
        else:
            logger.info('variables for task "{}": {}'.format(args.task, ', '.join(undefined)))
        sys.exit(0)

    for var in undefined:
        wsp_parser.add_argument('--%s' % var, required=True, type=type_cast)
    wsp_args, unused_args = wsp_parser.parse_known_args(wsp_args)
    wsp_args = vars(wsp_args)

    # initialize workspace variables with command line arguments
    wsp.init_vars(**wsp_args)

    # create directories
    make_dirs(wsp)

    # SAVE rendered template files
    for template_key in wsp.params['templates'].keys():
        success = render_and_save(wsp, template_key, args.force)
        if not success:
            sys.exit(1)

    # SCHEDULE job
    if args.schedule:
        logger.info('scheduling job "{}" for execution'.format(wsp.params['job_id']))
        if 'schedule_cmd' in wsp.params:
            os.system(wsp.params['schedule_cmd'])
            add_to_history(wsp, args.task, dict(zip(undefined, [wsp_args[k] for k in undefined])))
        else:
            logger.error('"schedule_cmd" not defined in parameter config')
            sys.exit(1)


if __name__ == '__main__':
    main()
