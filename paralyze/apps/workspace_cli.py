from paralyze.core import Workspace


def main():

    import argparse
    import logging
    import os
    import sys

    parser = argparse.ArgumentParser()

    # optional arguments
    parser.add_argument('--folder', default=os.getcwd())
    parser.add_argument('--auto-create', action='store_true', default=False, dest='auto_create')
    parser.add_argument('--create-folders', action='store_true', default=False, dest='create_folders')
    parser.add_argument('--verbose', action='store_true', default=False)

    args = parser.parse_args()

    if args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(stream=sys.stdout, level=log_level, format='[%(levelname)-7s] %(message)s')
    log = logging.getLogger(__name__)

    wsp = Workspace(args.folder, args.auto_create)

    if args.create_folders:
        wsp.create_folders()

