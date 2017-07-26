import pandas as pd
import argparse
import os
from sqlalchemy import create_engine


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('folder', type=str)
    parser.add_argument('db_name', type=str)
    parser.add_argument('--fit_folder', type=str, default='fitting_results')
    parser.add_argument('--dist_folder', type=str, default='dist_results')
    parser.add_argument('--db_path', type=str, default='results.db')
    parser.add_argument('--if_exists', choices=['fail', 'replace', 'append'], default='fail')
    args = parser.parse_args()

    dist_folder = os.path.join(args.folder, args.dist_folder)
    fit_folder = os.path.join(args.folder, args.fit_folder)

    print("""
    Merging results from
        distributions: {}
        fitting:       {}
    to
        {}""".format(dist_folder, fit_folder, os.path.join(args.folder, args.db_path)))

    entries = set(filter(lambda entry: entry.endswith('.csv'), os.listdir(dist_folder)))
    comp_en = set(filter(lambda entry: entry.endswith('.csv'), os.listdir(fit_folder)))

    if entries != comp_en:
        print('Warning: unequal number of cases found in dist_results and fitting_results!')

    print('Found {} cases in folder {}'.format(len(entries), dist_folder))
    frames = []
    for f in entries:

        dist_path = os.path.join(dist_folder, f)
        fit_path = os.path.join(fit_folder, f)

        if not os.path.exists(fit_path) or not os.path.exists(dist_path):
            continue

        dist_frame = pd.read_csv(dist_path, header=0)
        dist_frame.set_index('t', drop=False, inplace=True)
        dist_frame['case_id'] = len(frames)

        fit_frame = pd.read_csv(fit_path, header=0)
        fit_frame.set_index('t', inplace=True)

        common_names = set(list(dist_frame)) & set(list(fit_frame))

        dist_frame.drop(common_names, axis=1, inplace=True)
        frame = pd.concat([dist_frame, fit_frame], axis=1)
        frames.append(frame)

    print('Loaded {} data frames'.format(len(frames)))
    frame = pd.concat(frames, ignore_index=True)

    engine = create_engine('sqlite:///{}'.format(args.db_path))
    frame.to_sql(args.db_name, engine, if_exists=args.if_exists)
    print('Saved merged data frames to {}'.format(args.db_path))


if __name__ == '__main__':
    main()
