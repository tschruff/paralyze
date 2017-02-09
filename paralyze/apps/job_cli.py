from paralyze import ARCH, VERSION
from paralyze.core import Workspace


RUN_COMMANDS = {
    'bluegene': 'llsubmit {job_path}',
    'lsf': 'bsub < {job_path}',
    'windows': '{job_path}',
    'unix': '{job_path}',
    'macOS': './{job_path}'
}

# default workspace settings
DEFAULTS = {

    # general settings
    '__paralyze_version': VERSION,

    # job settings
    "job_type": "",
    "job_name": "",
    "job_path": "",

    # all files that should be parsed for a job
    "templates": [],
    "exec_template": "",

    # optional folder to store template files to
    "template_dir": "",

    # optional folder to store files for execution
    "run_dir": "",

    # job execution command (may depend on system architecture)
    'run_cmd': RUN_COMMANDS[ARCH]
}


def get_template_variables(env, template_file, context):
    """ Read template_file as plain file and parse variables

    :param env:
    :param template_file: path to template file
    :param context:
    :return: list of template variables (strings)
    """
    template = env.loader.get_source(env, template_file)[0]
    template_ast = env.parse(job_template)

    template_vars = meta.find_undeclared_variables(template_ast)
    # substract builtin names
    template_vars = template_vars - set([name for name in __builtins__ if not name.startswith('_')])
    # and names that already exist in the global context
    template_vars = template_vars - set(context.keys())

    return template_vars


def save_job_file(env, template_file, context):
    """ Parses template variables from template_file and
    adds them as argument to the command line. Rendered files
    will be saved to <run_dir>/<job_name>.<suffix_of_template_file>

    Note: Existing files will be overridden.

    :param env:
    :param template_file: path to template file
    :param context:
    :return: None
    """
    template_vars = get_template_variables(env, template_file, context)
    # search for job specific args in job script template
    parser = argparse.ArgumentParser()
    for var in template_vars:
        parser.add_argument('--%s' % var, required=True, type=ast.literal_eval)
    # parse job specific args from command line
    job_args, other_args = parser.parse_known_args(job_args)

    context.update(vars(job_args))

    # load template file
    template = env.get_template(job_template_path)

    suffix = template_file[template_file.rfind('.'):]
    out_file = os.path.join(wsp.get('run_dir'), wsp.get('job_name') + suffix)
    if os.path.exists(out_file):
        logger.warning('Replacing existing file "{}"!'.format(out_file))

    # render and write file
    with open(out_file, 'w') as job:
        job.write(template.render(**context))

    # log progress
    logger.info('Created file "{}"'.format(out_file))


def main():

    import ast
    import argparse
    import os
    import sys
    import logging

    from jinja2 import meta
    import jinja2

    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()

    # add job_cli arguments
    parser.add_argument('--job-type', default="", dest='job_type')
    parser.add_argument('--create-workspace', action='store_true', default=False, dest='create_workspace')
    parser.add_argument('--schedule', action='store_true', default=False, help='schedule job after creation?')
    parser.add_argument('--verbose', action='store_true', default=False)

    args, custom_args = parser.parse_known_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO

    # create workspace and exit
    if args.create_workspace:
        wsp = Workspace(os.getcwd(), True, DEFAULTS)
        print('Info: created new workspace at {}'.format(wsp.root))
        sys.exit(0)
    elif not args.job_type:
        print('Error: either --job-type or --create-workspace must be given')
        sys.exit(1)

    # load existing workspace
    try:
        wsp = Workspace(os.getcwd(), False, main_logger=logger, log_level=log_level)
    except RuntimeError as e:
        print('Error: Directory {} is not a paralyze workspace'.format(os.getcwd()))
        print('Run "{} --create-workspace" first to create a workspace here'.format(sys.argv[0]))
        sys.exit(1)

    if args.job_type:
        # add job_type to workspace
        wsp.update({'job_type': args.job_type})
        # and export job_type specific settings to global settings namespace
        # possibly overriding global settings!
        wsp.update(wsp.get(args.job_type, default={}))

    parser = argparse.ArgumentParser()
    # add workspace variables as required command line arguments
    for var in wsp.variables():
        parser.add_argument('--%s' % var, required=True, type=ast.literal_eval)
    # add workspace keys as optional command line arguments
    for var in wsp.keys(private=False):
        parser.add_argument('--%s' % var, default=wsp.get(var, raw=True))
    wsp_args, job_args = parser.parse_known_args(custom_args)

    # update workspace settings directly with command line values
    wsp.update(vars(wsp_args))

    # store all workspace settings in a dict
    # where variables are replaced with values
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
    template_files = wsp.get('templates')

    if wsp.get('exec_template', default=None):
        template_files.append(wsp.get('exec_template'))

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))

    for template_file in template_files:
        try:
            save_job_file(env, template_file, context.copy())
        except jinja2.exceptions.UndefinedError as e:
            logger.error('usage of undefined parameter "{}" in template!'.format(e.message()))
            sys.exit(1)
        except jinja2.exceptions.TemplateNotFound as e:
            logger.error('template file "{}" not found!'.format(e.message))
            sys.exit(1)

    if args.schedule:
        logger.info('scheduling job "{}" for execution'.format(wsp.get('job_name')))
        os.system(wsp.get('run_cmd'))


if __name__ == '__main__':
    main()
