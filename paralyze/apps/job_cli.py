from paralyze import ARCH, VERSION
from paralyze.core import Workspace

import os
import ast


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


def perform_check(wsp, logger):
    result = True
    if not os.path.exists(wsp.abs_path('app_path')):
        logger.warning('application {} does not exist'.format(wsp.get('app_path')))
        result = False
    if not os.path.exists(wsp.abs_path('log_dir')):
        logger.warning('log folder {} does not exist'.format(wsp.get('log_dir')))
        result = False
    if not os.path.exists(wsp.abs_path('template_path')):
        logger.error('run script template file {} does not exist'.format(wsp.get('template_path')))
        result = False
    if not os.path.exists(wsp.abs_path('run_dir')):
        logger.error('run folder {} does not exist'.format(wsp.get('run_dir')))
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
        parser.add_argument('--%s' % var, required=True, type=ast.literal_eval)
    wsp_args, job_args = parser.parse_known_args(custom_args)

    # update workspace settings directly with command line values
    wsp.update(vars(wsp_args))

    # get all settings stored in workspace
    # template strings will all be replaced with values
    context = wsp.get_settings()

    # export custom extensions to jinja context
    # and make them accessible in the template files
    # e.g. to write something like:
    #   {% rpath( run_path ) %}
    context_extensions = {
        'rpath'    : wsp.rel_path,
        'apath'    : wsp.abs_path,
        'root_path': wsp.root
	}

    context.update(context_extensions)
    context.update(wsp.get_context_extensions())

    paths_exist = perform_check(wsp, logger)

    template_dir = wsp.abs_path('template_dir')  # folder which contains the run script template files
    template_file = wsp.get('template_file')     # file name of run script template to be read
    run_path = wsp.get('run_path')               # path to write run script file to

    try:
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
        template = env.loader.get_source(env, template_file)[0]

        template_ast = env.parse(template)
        var = meta.find_undeclared_variables(template_ast)

        var = var - set([name for name in __builtins__ if not name.startswith('_')])
        var = var - set(context.keys())
        
        # search for job specific args in job script template
        parser = argparse.ArgumentParser()
        for v in var:
            parser.add_argument('--%s' % v, required=True, type=ast.literal_eval)
        # parse job specific args from command line
        job_args = parser.parse_args(job_args)

        context.update(vars(job_args))

        # reload template file as template
        template = env.get_template(template_file)
        # render and write run script file
        with open(run_path, 'w') as script:
            script.write(template.render(**context))

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
            os.system(wsp['crun_cmd'])
        else:
            logger.error('cannot execute run script! Check previous warnings/errors')


if __name__ == '__main__':
    main()
