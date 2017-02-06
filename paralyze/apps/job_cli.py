from paralyze.core import Workspace


CONTEXT_EXTENSIONS = {
    # export functions to context
    'rpath': Workspace.rel_path,  # TODO: rel_path must be static
    'apath': Workspace.abs_path,
}


def main():

    import argparse
    import os
    import sys
    import logging

    from jinja2 import meta
    import jinja2

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()

    # required arguments
    parser.add_argument('comp_case', type=str, help='a unique identifier for the simulation case')

    # optional arguments
    parser.add_argument('--comp_config', type=str, help='name of the simulation configuration')
    parser.add_argument('--workspace', default=os.getcwd())
    parser.add_argument('--schedule', action='store_true', default=False, help='schedule job after creation?')

    args = vars(parser.parse_args())

    # current work directory (should be a paralyze workspace)
    wsp = Workspace(args['workspace'], True)

    # update workspace settings directly with command line values
    wsp.update(args)

    # get all settings stored in workspace
    # template strings will all be replaced with values
    data = wsp.get_settings()

    # export custom extensions to jinja context
    # and make them accessible in the template files
    # e.g. to write something like:
    #   {% rpath( run_path ) %}
    data.update(CONTEXT_EXTENSIONS)
    data.update(wsp.get_context_extensions())

    paths_exist = wsp.perform_check()

    run_template_dir = wsp.abs_path('env_template_dir')
    run_template_file = wsp.get('env_template_file')
    run_path = wsp.get('env_run_path')

    try:
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(run_template_dir))
        template = env.get_template(run_template_file)

        ast = env.parse(template)
        var = meta.find_undeclared_variables(ast)
        for v in var:
            if v not in set(data.keys()):
                logger.warning('parameter "{0}" in run script template is undefined!'.format(v))

        with open(run_path, 'w') as script:
            script.write(template.render(**data))

    except jinja2.exceptions.UndefinedError as e:
        logger.error('usage of undefined parameter "{0}" in run script template!'.format(e.args[0]))
        sys.exit(1)
    except jinja2.exceptions.TemplateNotFound:
        sys.exit(1)

    logger.info('created run script: {}'.format(run_path))

    if args['schedule']:
        if paths_exist:
            logger.info('scheduling run script: {}'.format(run_path))
            os.system(wsp['comp_run_cmd'])
        else:
            logger.error('cannot execute run script! Check previous warnings/errors')


if __name__ == '__main__':
    main()
