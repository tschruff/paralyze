from paralyze import ARCH, VERSION
from paralyze.core import Workspace

import os
import ast


RUN_COMMANDS = {
    'bluegene': 'llsubmit {job_path}',
    'lsf': 'bsub < {job_path}',
    'windows': '{job_path}',
    'unix': '{job_path}',
    'macOS': './{job_path}'
}

# default workspace settings
DEFAULTS = {

    # job name
    "job_name": "<not-set>",

    # general settings
    'paralyze_version': VERSION,

    # environment settings
    'app_dir': 'apps',  # application folder
    'app_file': '<not-set>',
    'app_path': '{app_dir}/{app_file}',

    'run_dir'     : 'run',        # run folder
    'template_dir': 'templates',  # job script templates folder

    # config file settings
    'config_dir': 'configs',
    'config_path': "{run_dir}/{config_dir}/{job_name}.prm",

    # job file settings
    "job_dir"     : 'jobs',
    "job_path"    : '{run_dir}/{job_dir}/{job_name}.sh',

    "job_template_path": '{template_dir}/{job_dir}/{job_type}.sh',
    "config_template_path": '{template_dir}/{config_dir}/{job_type}.sh',

    # log file settings
    'log_dir': '{run_dir}/logs',
    'log_path': '{log_dir}/{job_name}.txt',
    'log_error_path': '{log_dir}/{job_name}_errors.txt',

    # computational settings
    'cores_per_node': 16,
    'nodes': 4096,
    'memory_per_process': 512,
    'wc_limit': '4:00',

    # notifications
    'notify_start': False,
    'notify_end': False,
    'notify_error': False,
    'notify_user': '',

    # job execution command (may depend on system architecture)
    'run_cmd': RUN_COMMANDS[ARCH]
}


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
        wsp.init_logger(logger, level=logging.DEBUG)
    else:
        wsp.init_logger(logger, level=logging.INFO)

    parser = argparse.ArgumentParser()
    # add workspace variables as required command line arguments
    for var in wsp.variables():
        parser.add_argument('--%s' % var, required=True, type=ast.literal_eval)
    # add workspace keys as optional command line arguments
    for var in wsp.keys():
        parser.add_argument('--%s' % var, default=wsp.get(var, raw=True))
    wsp_args, job_args = parser.parse_known_args(custom_args)

    # update workspace settings directly with command line values
    wsp.update(vars(wsp_args))

    # get all workspace settings stored in a dict
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

    template_dir = wsp.abs_path('template_dir')

    job_template_file = wsp.get('job_template_file')
    job_template_path = os.path.join('jobs', job_template_file)

    config_template_file = wsp.get('config_template_file')
    config_template_path = os.path.join('configs', config_template_file)

    try:
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))

        # read job template as plain file and parse variables
        job_template = env.loader.get_source(env, job_template_path)[0]
        job_template_ast = env.parse(job_template)
        # read config template as plain file and parse variables
        config_template = env.loader.get_source(env, config_template_path)[0]
        config_template_ast = env.parse(config_template)

        job_vars    = meta.find_undeclared_variables(job_template_ast)
        config_vars = meta.find_undeclared_variables(config_template_ast)
        custom_vars = job_vars.union(config_vars)
        custom_vars = custom_vars - set([name for name in __builtins__ if not name.startswith('_')])
        custom_vars = custom_vars - set(context.keys())
        
        # search for job specific args in job script template
        parser = argparse.ArgumentParser()
        for var in custom_vars:
            parser.add_argument('--%s' % var, required=True, type=ast.literal_eval)
        # parse job specific args from command line
        job_args = parser.parse_args(job_args)

        context.update(vars(job_args))

        # reload template file as template
        job_template = env.get_template(job_template_path)
        config_template = env.get_template(config_template_path)

        if os.path.exists(wsp.get('job_path')):
            logger.warning('replacing existing job script "{}"!'.format(wsp.get('job_path')))
        if os.path.exists(wsp.get('config_path')):
            logger.warning('replacing existing job config "{}"!'.format(wsp.get('config_path')))

        # render and write job script file
        with open(wsp.get('job_path'), 'w') as job:
            job.write(job_template.render(**context))
        # render and write config file
        with open(wsp.get('config_path'), 'w') as config:
            config.write(config_template.render(**context))

    except jinja2.exceptions.UndefinedError as e:
        logger.error('usage of undefined parameter "{}" in template!'.format(e.args[0]))
        sys.exit(1)
    except jinja2.exceptions.TemplateNotFound as e:
        logger.error('template file "{}" not found!'.format(e.message))
        sys.exit(1)

    logger.info('created job script "{}"'.format(wsp.get('job_path')))
    logger.info('created job config "{}"'.format(wsp.get('config_path')))

    if args.schedule:
        logger.info('scheduling run script "{}" for execution'.format(wsp.get('job_path')))
        os.system(wsp['run_cmd'])


if __name__ == '__main__':
    main()
