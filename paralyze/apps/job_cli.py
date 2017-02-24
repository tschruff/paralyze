from paralyze import ARCH, VERSION
from paralyze.core import Workspace, type_cast

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
    '__paralyze_version__': VERSION,

    "app_dir": "apps",
    "app_file": "<not-set>",
    "app_path": "{app_dir}/{app_file}",

    # job settings
    "job_type": "",
    "job_name": "",

    # all files that should be parsed for a job
    "templates": {
        "job": "<not-set>.sh",
        "config": "<not-set>.prm"
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
    'schedule_cmd': "echo {files[job]}"
}


def get_template_variables(env, template_file):
    """ Read template_file as plain file and parse variables

    :param env:
    :param template_key: name of template
    :return: list of template variables (strings)
    """
    template = env.loader.get_source(env, template_file)[0]
    template_ast = env.parse(template)

    template_vars = meta.find_undeclared_variables(template_ast)

    for ref_template in meta.find_referenced_templates(template_ast):
        template_vars.update(get_template_variables(env, ref_template))

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
    # load template file
    template = env.get_template(context["templates"][template_key])

    out_file = context["files"][template_key]
    if os.path.exists(out_file):
        logger.warning('replacing existing file "{}"!'.format(out_file))

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


def create_env(wsp):
    return jinja2.Environment(loader=jinja2.FileSystemLoader(wsp.get('template_dir')))


def main():

    parser = argparse.ArgumentParser()
    # add job_cli arguments
    parser.add_argument('--create_workspace', action='store_true', default=False, dest='create_workspace')
    parser.add_argument('--schedule', action='store_true', default=False, help='schedule job after creation?')
    parser.add_argument('--verbose', action='store_true', default=False)

    args, custom_args = parser.parse_known_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO

    # create workspace and exit
    if args.create_workspace:
        wsp = Workspace(auto_create=True, settings=DEFAULTS)
        logger.info('created new workspace at {}'.format(wsp.root))
        sys.exit(0)

    # load workspace at CWD
    try:
        wsp = Workspace(auto_create=False, log_level=log_level)
        job_args = wsp.init_variables(custom_args)
    except IOError as e:
        logger.error('directory {} is not a paralyze workspace!\n '
                     'Note: run "{} --create-workspace" to create '
                     'a workspace at the current working directory'.format(wsp.root, sys.argv[0]))
        sys.exit(1)

    # generates a file path for each item in "templates" to the context
    generate_file_paths(wsp)

    # create jinja environemt for template loading
    env = create_env(wsp)

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

    # Collect and parse template variables
    template_vars = set([])
    for template_key in context['templates'].keys():
        template_file = context["templates"][template_key]
        var = get_template_variables(env, template_file)
        template_vars.update(var)

    # substract builtin names
    template_vars = template_vars - set([name for name in __builtins__ if not name.startswith('_')])
    # and names that already exist in the global context
    template_vars = template_vars - set(context.keys())

    parser = argparse.ArgumentParser(allow_abbrev=False)
    for var in template_vars:
        parser.add_argument('--%s' % var, required=True, type=type_cast)
    # parse template args from command line
    job_args = parser.parse_args(job_args)
    # and add them to the context
    context.update(vars(job_args))

    # Save template files
    for template_key in context['templates'].keys():
        try:
            save_job_file(job_args, env, template_key, context)
        except jinja2.exceptions.UndefinedError as e:
            logger.error('usage of undefined parameter "{}" in template "{}"!'.format(e.message, template_key))
            sys.exit(1)
        except jinja2.exceptions.TemplateNotFound as e:
            logger.error('template file "{}" not found for template "{}"!'.format(e.message, template_key))
            sys.exit(1)
        except jinja2.exceptions.TemplateSyntaxError as e:
            logger.error('syntak error in template "{}": {}'.format(template_key, e.message))
            sys.exit(1)

    # Schedule job
    if args.schedule:
        logger.info('scheduling job "{}" for execution'.format(context['job_name']))
        os.system(context['schedule_cmd'])


if __name__ == '__main__':
    main()
