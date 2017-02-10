from paralyze import ARCH, VERSION
from paralyze.core import Workspace

from jinja2 import meta
import os
import ast
import argparse
import sys
import logging
import jinja2

logger = logging.getLogger(__name__)


# default workspace settings
DEFAULTS = {

    # general settings
    '__paralyze_version': VERSION,

    "app_dir": "apps",
    "app_file": "<not-set>",
    "app_path": "{app_dir}/{app_file}",

    # job settings
    "job_type": "",
    "job_name": "",

    "example_job_type": {
        "app_file": "example_app",
        "templates": {
            "job": "example_job.sh",
            "data": "example_data.dat"
        }
    },

    # all files that should be parsed for a job
    "templates": {
        "job": "job.sh",
        "config": "config.prm"
    },

    # the paths of files specified by template
    # paths will be filled out during the file generation process automatically
    # you can access them in template files like so
    # {{ files.job }} or {{ files['job'] }}
    "files": {
        "job": "",
        "config": ""
    },

    # optional folder to store template files to
    "template_dir": "",

    # optional folder to store files for execution
    "run_dir": "",
    # job execution command (may depend on system architecture)
    'run_cmd': "echo {files[job]}"
}


def get_template_variables(env, template_key, context):
    """ Read template_file as plain file and parse variables

    :param env:
    :param template_key: name of template
    :param context:
    :return: list of template variables (strings)
    """
    template_file = context["templates"][template_key]
    template = env.loader.get_source(env, template_file)[0]
    template_ast = env.parse(template)

    template_vars = meta.find_undeclared_variables(template_ast)
    # substract builtin names
    template_vars = template_vars - set([name for name in __builtins__ if not name.startswith('_')])
    # and names that already exist in the global context
    template_vars = template_vars - set(context.keys())

    return template_vars


def save_job_file(args, env, template_key, context):
    """ Parses template variables from template_file and
    adds them as argument to the command line. Rendered files
    will be saved to <run_dir>/<job_name>.<suffix_of_template_file>

    Note: Existing files will be overridden.

    :param env:
    :param template_key: name of template
    :param context:
    :return: None
    """
    template_vars = get_template_variables(env, template_key, context)
    # search for job specific args in job script template
    parser = argparse.ArgumentParser()
    for var in template_vars:
        parser.add_argument('--%s' % var, required=True, type=ast.literal_eval)
    # parse job specific args from command line
    job_args, other_args = parser.parse_known_args(args)

    context.update(vars(job_args))

    # load template file
    template = env.get_template(context["templates"][template_key])

    out_file = context["files"][template_key]
    if os.path.exists(out_file):
        logger.warning('Replacing existing file "{}"!'.format(out_file))

    # render and write file
    with open(out_file, 'w') as job:
        job.write(template.render(**context))

    # log progress
    logger.info('Created file "{}"'.format(out_file))


def generate_file_paths(wsp):
    wsp['files'] = {}
    for key in wsp['templates'].keys():
        template_file = wsp['templates'][key]
        suffix = template_file[template_file.rfind('.'):]
        wsp['files'][key] = os.path.join(wsp['run_dir'], wsp['job_name'] + suffix)


def main():

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

    # generates a file path for each item in "templates" to the context
    generate_file_paths(wsp)

    # export all workspace settings to a dict
    # where variables are replaced with values
    # NOTE: No more updates of workspace variables hereafter!
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

    # add app specific context extensions
    context.update(context_extensions)
    # add user specific context extensions
    context.update(wsp.get_context_extensions())

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(wsp.abs_path('template_dir')))

    for template_key in context['templates'].keys():
        try:
            save_job_file(job_args, env, template_key, context)
        except jinja2.exceptions.UndefinedError as e:
            logger.error('usage of undefined parameter "{}" in template "{}"!'.format(e.message(), template_key))
            sys.exit(1)
        except jinja2.exceptions.TemplateNotFound as e:
            logger.error('template file "{}" not found for template "{}"!'.format(e.message, template_key))
            sys.exit(1)

    if args.schedule:
        logger.info('scheduling job "{}" for execution'.format(context['job_name']))
        os.system(context['run_cmd'])


if __name__ == '__main__':
    main()
