from paralyze import ARCH, VERSION
from paralyze.core import Workspace

import os


RUN_COMMANDS = {
    'bluegene': 'llsubmit {env_run_path}',
    'lsf': 'bsub < {env_run_path}',
    'windows': '{env_run_path}',
    'unix': '{env_run_path}',
    'macOS': './{env_run_path}'
}

# default workspace settings
DEFAULTS = {

    # general settings
    'paralyze_version': VERSION,

    # environment settings
    'env_app_dir': 'apps',  # application folder
    'env_app_file': '',
    'env_app_path': os.path.join('{env_app_dir}', '{env_app_file}'),
    'env_config_dir': 'configs',  # config file folder
    'env_config_file': '{comp_config}.prm',
    'env_config_path': os.path.join('{env_config_dir}', '{env_config_file}'),
    'env_log_dir': 'logs',  # log file folder
    'env_log_file': '{comp_job_name}_log.txt',
    'env_log_path': os.path.join('{env_log_dir}', '{env_log_file}'),
    'env_log_error_file': '{comp_job_name}_errors.txt',
    'env_log_error_path': os.path.join('{env_log_dir}', '{env_log_error_file}'),
    'env_run_dir': 'run',  # run folder
    'env_run_file': '{comp_job_name}.sh',
    'env_run_path': os.path.join('{env_run_dir}', '{env_run_file}'),
    'env_template_dir': 'templates',  # job script templates folder
    'env_template_file': '{comp_config}.txt',
    'env_template_path': os.path.join('{env_template_dir}', '{env_template_file}'),

    # computational settings
    'comp_job_name': '{comp_config}_{comp_case}',
    'comp_cores_per_node': 16,
    'comp_nodes': 4096,
    'comp_memory_per_process': 512,
    'comp_wc_limit': '4:00:00',
    'comp_notify_start': False,
    'comp_notify_end': False,
    'comp_notify_error': False,
    'comp_notify_user': '',

    'comp_run_cmd': RUN_COMMANDS[ARCH]
}


FOLDER_KEYS = [
    'env_app_dir', 'env_config_dir', 'env_log_dir', 'env_run_dir', 'env_template_dir'
]


CONTEXT_EXTENSIONS = {
    # export functions to context
    'rpath': Workspace.rel_path,  # TODO: rel_path must be static in order to work
    'apath': Workspace.abs_path,
}


def perform_check(wsp, logger):
    result = True
    if not os.path.exists(wsp.abs_path('env_app_path')):
        logger.warning('application {} does not exist'.format(wsp.get('env_app_path')))
        result = False
    if not os.path.exists(wsp.abs_path('env_config_path')):
        logger.warning('configuration {} does not exist'.format(wsp.get('env_config_path')))
        result = False
    if not os.path.exists(wsp.abs_path('env_log_dir')):
        logger.warning('log folder {} does not exist'.format(wsp.get('env_log_dir')))
        result = False
    if not os.path.exists(wsp.abs_path('env_template_path')):
        logger.error('run script template file {} does not exist'.format(wsp.get('env_template_path')))
        result = False
    if not os.path.exists(wsp.abs_path('env_run_dir')):
        logger.error('run folder {} does not exist'.format(wsp.get('env_run_dir')))
        result = False
    return result


def main():

    import argparse
    import os
    import sys
    import logging

    from jinja2 import meta
    import jinja2

    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()

    # add job_cli arguments
    parser.add_argument('--create-workspace', action='store_true', default=False, dest='create_workspace')
    parser.add_argument('--schedule', action='store_true', default=False, help='schedule job after creation?')
    parser.add_argument('--verbose', action='store_true', default=False)

    args, custom_args = parser.parse_known_args()

    if args.create_workspace:
        wsp = Workspace(os.getcwd(), True, DEFAULTS)
    else:
        wsp = Workspace(os.getcwd(), False)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # add workspace variables as command line arguments
    parser = argparse.ArgumentParser()
    for var in wsp.variables():
        parser.add_argument('--%s' % var, required=True)
    wsp_args = parser.parse_args(custom_args)

    # update workspace settings directly with command line values
    wsp.update(vars(wsp_args))

    # get all settings stored in workspace
    # template strings will all be replaced with values
    data = wsp.get_settings()

    # export custom extensions to jinja context
    # and make them accessible in the template files
    # e.g. to write something like:
    #   {% rpath( run_path ) %}
    data.update(CONTEXT_EXTENSIONS)
    data.update(wsp.get_context_extensions())

    paths_exist = perform_check(wsp, logger)

    run_template_dir = wsp.abs_path('env_template_dir')  # folder which contains the run script template files
    run_template_file = wsp.get('env_template_file')     # file name of run script template
    run_path = wsp.get('env_run_path')                   # path to run script file

    try:
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(run_template_dir))
        template = env.get_template(run_template_file)

        ast = env.parse(template)
        var = meta.find_undeclared_variables(ast)
        for v in var:
            if v not in set(data.keys()):
                logger.warning('parameter "{0}" in run script template is undefined!'.format(v))

        # render and write run script file
        with open(run_path, 'w') as script:
            script.write(template.render(**data))

    except jinja2.exceptions.UndefinedError as e:
        logger.error('usage of undefined parameter "{0}" in run script template!'.format(e.args[0]))
        sys.exit(1)
    except jinja2.exceptions.TemplateNotFound:
        logger.error('template file not found!')
        sys.exit(1)

    logger.info('created run script: {}'.format(run_path))

    if args.schedule:
        if paths_exist:
            logger.info('scheduling run script: {}'.format(run_path))
            os.system(wsp['comp_run_cmd'])
        else:
            logger.error('cannot execute run script! Check previous warnings/errors')


if __name__ == '__main__':
    main()
