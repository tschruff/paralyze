from paralyze.core import AABB, Vector
from paralyze.core import Storage, Sphere
from paralyze.solids.io import csb

import logging
import time
import os


def str_to_body_types(type_str):
    assert isinstance(type_str, str)

    types = []
    if ',' in type_str:
        type_names = type_str.split(',')
        for type_name in type_names:
            types.append(str_to_body_types(type_name))
    else:
        type_name = type_str.title()
        types.append(eval(type_name))
    return tuple(types)


class Command(object):

    def __init__(self):
        self.log = logging.getLogger(__name__)

        self.args = [
            ('--domain-filter', '-d', {
                'type': str,
                'default': None,
                'help': 'axis aligned bounding box used for filtering. Format: "[<x0,y0,z0>,<x1,y1,z1>]"',
                'dest': 'domain_filter'
            }),
            ('--strict', '-s', {
                'action'  : 'store_true',
                'default' : False,
                'help'    : 'if enabled, bodies have to be fully contained by the given domain',
                'dest'    : 'strict'
            })
        ]

        self.domain = None

    def load_bodies(self, args):
        bodies = Storage(solids=csb.load(args.path, args.delimiter))
        num_bodies = len(bodies)
        if not num_bodies:
            self.log.error('No bodies to edit! Aborting ...'.format(args.path))
            return []
        self.log.info('Loaded {:d} bodies from file {}'.format(num_bodies, args.path))

        # extract command line parameters
        if args.domain_filter is None:
            self.domain = AABB.inf()
        else:
            self.domain = AABB.parse(args.domain_filter)
            if self.domain.is_empty():
                self.log.error('Specified domain is empty! Aborting ...')
                return []
            # apply domain filter
            old_num_bodies = len(bodies)
            bodies = bodies.clipped(self.domain, args.strict)
            num_bodies = len(bodies)
            text = 'Strictly filtered' if args.strict else 'Filtered'
            self.log.info('{} {:d} bodies outside domain, {:d} bodies remain'.format(text, old_num_bodies-num_bodies, num_bodies))

        return bodies


class Mesh(Command):

    help = 'convert to vtk mesh file'

    def __init__(self):
        Command.__init__(self)

        self.args.extend((
            ('vtk_file', {
                'type': str,
                'help': 'absolute path to vtk mesh file'
            }),
            ('--invert-solids', '-i', {
                'action': 'store_true',
                'default': False,
                'help': 'flips solid and void space of the volume mesh',
                'dest': 'invert_solids'
            })
        ))

    def __call__(self, args):

        bodies = self.load_bodies(args)

        mesh = self.domain.csg()
        with ProgressBar(max_value=len(bodies)-1) as p:
            for i, body in enumerate(bodies):
                mesh = mesh.subtract(body.csg())
                p.update(i)

        if not args.invert_solids:
            mesh = mesh.inverse()

        mesh.saveVTK(args.vtk_file)
        return True


class Slice(Command):

    help = 'create slices along specified axis'

    def __init__(self):
        Command.__init__(self)

        self.args.extend((
            ('axis', {
                'type'    : str
            }),
            ('num_slices', {
                'type'    : int,
                'default' : 0
            }),
            ('out_folder', {
                'type'    : str,
                'default' : '',
                'help'    : 'path to output folder'
            })
        ))

    def __call__(self, args):

        bodies = self.load_bodies(args)

        if args.num_slices < 1:
            self.log.error('Number of slices must be greater than zero! Aborting ...')

        axes = ['x', 'y', 'z']
        if args.axis not in axes:
            self.log.error('Specified axis is not valid! Valid axes are: x, y, z. Aborting ...')
            return False
        axis = axes.index(args.axis)

        # create folder for slice files
        if not os.path.exists(args.out_folder):
            os.makedirs(args.out_folder)
            self.log.info('Created output folder %s' % args.out_folder)

        # create slices and save them
        slice_file = os.path.join(args.out_folder, 'slice_{axis}_{slice_min:f}-{slice_max:f}.csv')
        for slice in self.domain.iter_slices(axis, args.num_slices):
            slice_bodies = bodies.clipped(slice, args.strict)
            bodies -= slice_bodies
            filename = slice_file.format(axis=axes[axis], slice_min=slice.min[axis], slice_max=slice.max[axis])
            csb.save(filename, slice_bodies)
            self.log.info('Saved {:d} bodies to file {}'.format(len(slice_bodies), filename))

        return True


class Edit(Command):

    help = 'edit bodies in an existing csb file'

    def __init__(self):
        Command.__init__(self)

        self.args.extend((
            ('out', {
                'type'    : str,
                'help'    : 'path to file where bodies are saved to. Will be overridden if it already exists!'
            }),
            ('--type-filter', '-t', {
                'type'    : str,
                'default' : 'All',
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
            })
        ))

    def __call__(self, args):

        bodies = self.load_bodies(args)

        offset = Vector.parse(args.offset)

        # apply type filter
        if args.type_filter != 'All':
            try:
                types = str_to_body_types(args.type_filter)
                bodies = bodies.subset(lambda body: isinstance(body, types))
            except NameError as e:
                self.log.exception(e.args[0])
                return
            self.log.info('Filtered bodies not being of type(s): {}'.format(args.type_filter))

        # apply scale factor
        if args.scale_factor != 1.0:
            self.log.info('Applying scaling factor {} to bodies'.format(args.scale_factor))
            bodies.scale(args.scale_factor)

        # apply offset
        if offset != Vector(0):
            self.log.info('Applying offset {} to bodies'.format(offset))
            bodies.translate(offset)

        if self.log.getEffectiveLevel() <= logging.DEBUG:
            self.log.debug('Body space is {}'.format(bodies.aabb()))

        # save
        csb.save(args.out, bodies)
        self.log.info('Saved {:d} bodies to file {}'.format(len(bodies), args.out))


class Exec(Command):

    help = ''

    def __init__(self):
        Command.__init__(self)

        self.args.extend((
            ('expression', {}),
        ))

    def __call__(self, args):
        bodies = self.load_bodies(args)
        self.log.info('Execution result: {}'.format(eval(args.expression, globals(), {'bodies': bodies})))


def main():

    import argparse
    import sys

    commands = {
        'edit' : Edit(),
        'exec' : Exec(),
        'slice': Slice(),
        'mesh' : Mesh()
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
    commands[args.cmd_name](args)
    log.info('Finished command "{}". Took {:f} seconds'.format(args.cmd_name, time.time()-t0))


if __name__ == '__main__':
    main()
