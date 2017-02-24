from paralyze.core import Workspace


def main():

    import argparse
    import logging
    import os

    parser = argparse.ArgumentParser()

    # optional arguments
    parser.add_argument('--folder', default=os.getcwd())
    parser.add_argument('--auto-create', action='store_true', default=False, dest='auto_create')
    parser.add_argument('--verbose', action='store_true', default=False)

    args = parser.parse_args()

    if args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    wsp = Workspace(args.folder, args.auto_create, log_level=log_level)
