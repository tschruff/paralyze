from paralyze.core import AABB, CSBFile, Vector
from paralyze.core import Capsule, Plane, Sphere

import logging
import time


def str_to_types(type_str):
    assert isinstance(type_str, str)

    types = []
    if ',' in type_str:
        type_names = type_str.split(',')
        for type_name in type_names:
            types.append(str_to_types(type_name))
    else:
        type_name = type_str.title()
        types.append(eval(type_name))
    return tuple(types)


class Command(object):
    def __init__(self):
        self.log = logging.getLogger(__name__)
    def load_bodies(self, args):
        bodies = CSBFile.load(args.path, args.delimiter)
        num_bodies = len(bodies)
        if not num_bodies:
            self.log.error('No bodies to edit! Aborting ...'.format(args.path))
            return
        self.log.info('Loaded {:d} bodies from file {}'.format(num_bodies, args.path))
        return bodies


class Edit(Command):

    help = 'edit bodies in an existing csb file'

    args = (('out', {
                'type'    : str,
                'help'    : 'path to file where filtered bodies are saved to. Will be overridden if it already exists!'
            }),
            ('--type-filter', '-t', {
                'type'    : str,
                'default' : 'all',
                'help'    : '',
                'dest'    : 'type_filter'
            }),
            ('--scale-factor', {
                'type'    : float,
                'default' : 1.0,
                'help'    : '',
                'dest'    : 'scale_factor'
            }),
            ('--offset', '-o', {
                'type'    : str,
                'default' : '<0,0,0>',
                'help'    : '',
                'dest'    : 'offset'
            }),
            ('--domain-filter', '-d', {
                'type'    : str,
                'default' : None,
                'help'    : 'axis aligned bounding box used for filtering. Format: "[<x0,y0,z0>,<x1,y1,z1>]"',
                'dest'    : 'domain_filter'
            }),
            ('--strict', '-s', {
                'action'  : 'store_true',
                'default' : False,
                'help'    : 'if enabled, bodies have to be fully inside the given domain, otherwise only body center',
                'dest'    : 'strict'
            }))

    def __call__(self, args):

        bodies = self.load_bodies(args)

        # extract command line parameters
        if args.domain_filter is not None:
            domain_filter = AABB.parse(args.domain_filter)
            if domain_filter.isEmpty():
                self.log.error('Specified domain is empty! Aborting ...')
                return
        else:
            domain_filter = None

        offset = Vector.parse(args.offset)

        # apply type filter
        if args.type_filter != 'all':
            try:
                types = str_to_types(args.type_filter)
                bodies = bodies.subset(lambda body: isinstance(body, types))
            except NameError as e:
                self.log.exception(e.args[0])
                return
            self.log.info('Filtered bodies not being of type(s): {}'.format(args.type_filter))

        # apply scale factor
        if args.scale_factor != 1.0:
            bodies.scale(args.scale_factor)
            self.log.info('Scaled bodies by factor {:f}'.format(args.scale_factor))

        # apply offset
        if offset != Vector(0):
            bodies.translate(offset)
            self.log.info('Moved bodies by {}'.format(offset))

        if self.log.getEffectiveLevel() <= logging.DEBUG:
            self.log.debug('Body space is {}'.format(bodies.aabb()))

        # apply domain filter
        if domain_filter is not None:
            bodies = bodies.clipped(domain_filter, args.strict)
            text = 'Strictly filtered' if args.strict else 'Filtered'
            self.log.info('{} {:d} bodies outside domain'.format(text, num_bodies-len(bodies)))

        # save
        CSBFile.save(args.out, bodies)
        self.log.info('Saved {:d} bodies to file {}'.format(len(bodies), args.out))


class Exec(Command):

    help = ''

    args = (('expression', {}),)

    def __call__(self, args):
        bodies = self.load_bodies(args)
        self.log.info('Execution result: {}'.format(eval(args.expression, globals(), {'bodies': bodies})))


if __name__ == '__main__':

    import argparse
    import sys

    commands = {
        'edit': Edit,
        'exec': Exec
    }

    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='Path to input csb file(s). May contain wildcards')
    parser.add_argument('--delimiter', default=',', help='character that delimits csv file columns. Default: ","',)
    parser.add_argument('--verbose', '-v', default=False, action='store_true')

    cmd_parsers = parser.add_subparsers(title='commands', dest='cmd_name')

    for name, command in commands.items():
        cmd_parser = cmd_parsers.add_parser(name, help=command.help)
        for args in command.args:
            cmd_parser.add_argument(*args[0:-1], **args[-1])

    args = parser.parse_args()

    if args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(stream=sys.stdout, level=log_level, format='[%(levelname)-7s] %(message)s')

    log = logging.getLogger(__name__)

    # the user has typed in an unknown command
    if args.cmd_name is None:
        parser.print_help()
        sys.exit()

    # execute command
    t0 = time.time()
    log.info('Running "{}" command'.format(args.cmd_name))
    commands[args.cmd_name]()(args)
    log.info('Finished command "{}". Took {:f} seconds'.format(args.cmd_name, time.time()-t0))
