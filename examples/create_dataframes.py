"""Creates pandas.DataFrame objects for each simulation case found in the
specified case file and saves the data frames to individual .csv files.

Parameters
----------
case_file: str
    case_id = {bed}_[...]
data_path: str
    data_path/volume_distributions/{case_id}.csv
    data_path/csb/beds/{bed}.csv
    data_path/csb/{case_id}_fill.tar.gz

results_path: str
"""

import os
import tarfile

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from paralyze.core.solids import CSBFile
from paralyze.core.stats import gm, gsd

DEPTH_SHIFT = {
    1.0: -2.062500,
    1.1: -1.687500,
    1.2: -1.562500,
    1.3: -1.187500,
    1.4: -1.562500,
    1.5: -1.187500,
    1.6: -1.78
}


def fit_func(x, f_f0, lambda_):
    return f_f0 * np.exp(-lambda_ * x)


def load_case(case_id, fit_bounds=(-np.inf, np.inf), data_path='/Users/tobs/sciebo/Diss/Data'):
    """Load simulation case into DataFrame row.
    """

    columns = [
        'c_n', 'c_psd_gm', 'c_psd_gsd',
        'c_v', 'c_gm'    , 'c_gsd'    ,
        'f_n', 'f_psd_gm', 'f_psd_gsd',
        'f_v', 'f_gm'    , 'f_gsd'    ,
        'g'  , 'q_f', 't', 'f_f0', 'lambda'
    ]

    coarse, fine, q_f, g = case_id.split("_")

    f_svd_path = os.path.join(data_path, 'volume_distributions', case_id+'.csv')
    c_csb_path = os.path.join(data_path, 'csb', 'beds', coarse+'.csv')
    f_csb_path = os.path.join(data_path, 'csb', case_id+'_fill.tar.gz')

    if not os.path.exists(f_svd_path):
        raise OSError('File {} does not exist!'.format(f_svd_path))
    if not os.path.exists(c_csb_path):
        raise OSError('File {} does not exist!'.format(c_csb_path))
    if not os.path.exists(f_csb_path):
        raise OSError('File {} does not exist!'.format(f_csb_path))

    bed = coarse.split('-')
    if bed[0] == 'uniform':
        c_gsd = 1.0
    else:
        c_gsd = float(bed[2])

    frame = pd.read_csv(f_svd_path, sep=',')
    # normalize and shift depth
    frame['depth'] = frame['depth']/8. + DEPTH_SHIFT[c_gsd]
    # drop inf and nan values
    frame.replace([np.inf, -np.inf], np.nan).dropna(inplace=True)
    # clip to fit_bounds
    frame = frame[fit_bounds[0] <= frame['depth']]
    frame = frame[frame['depth'] <= fit_bounds[1]]

    num_t = len(frame.columns[2:])
    with tarfile.open(f_csb_path) as tar:
        num_csb = sum([1 for member in tar.getmembers() if member.isfile()])
        if num_csb != num_t:
            raise ValueError('Number of fine csb files {:d} does not match number of volume distribution files {:d}'.format(num_csb, num_t))

    print('## starting to process {} time steps for case {} ##'.format(num_t, case_id))
    case_df = pd.DataFrame(np.full((num_t, len(columns)), np.nan), columns=columns)

    ############################################################################
    print('determine fitting parameters ...')

    for i, t in enumerate(frame.columns[2:]):
        try:
            popt, pcov = curve_fit(fit_func, frame['depth'], frame[t])
        except RuntimeError:
            print("Could not determine fittings constants (t={}, case={})".format(t, case_id))
        except ValueError:
            print("Could not determine fittings constants (t={}, case={})".format(t, case_id))
        except Exception as e:
            print("Unexpected error: {} (case={})".format(e, case_id))
        else:
            case_df['f_f0'][i] = popt[0]
            case_df['lambda'][i] = popt[1]

        case_df['t'][i] = int(t)

    ############################################################################
    print('determine coarse sediment parameters ...')

    solids = CSBFile.load(c_csb_path)
    s = np.array(list(map(lambda solid: solid.equivalent_mesh_size, solids)))
    v = np.array(list(map(lambda solid: solid.volume, solids)))

    case_df['c_n'] = len(solids)
    case_df['c_psd_gm'] = gm(s)
    case_df['c_psd_gsd'] = gsd(s)
    case_df['c_v'] = sum(v)
    case_df['c_gm'] = gm(s, v)
    case_df['c_gsd'] = gsd(s, v)

    ############################################################################
    print('determine fine sediment parameters ...')

    i = 0
    with tarfile.open(f_csb_path) as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue

            print(' processing member {} ({:d} of {:d})'.format(member.name, i+1, num_csb))

            f = tar.extractfile(member)
            solids = CSBFile.load(f)
            f.close()

            s = np.array(list(map(lambda solid: solid.equivalent_mesh_size, solids)))
            v = np.array(list(map(lambda solid: solid.volume, solids)))

            case_df['f_n'][i] = len(solids)
            case_df['f_psd_gm'][i] = gm(s)
            case_df['f_psd_gsd'][i] = gsd(s)
            case_df['f_v'][i] = sum(v)
            case_df['f_gm'][i] = gm(s, v)
            case_df['f_gsd'][i] = gsd(s, v)
            i += 1

    case_df['q_f'] = float(q_f)
    case_df['g'] = float(g)

    return case_df


def main():

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('case_file', type=str)
    parser.add_argument('data_path', type=str)
    parser.add_argument('results_path', type=str)
    args = parser.parse_args()

    casefile = open(args.case_file, 'r')
    cases = casefile.readlines()
    casefile.close()

    for case in cases:
        try:
            df = load_case(case, data_path=args.data_path)
            df.to_csv(os.path.join(results_path, case+'.csv', index=False))
        except Exception as e:
            print('Unexpected error for case {}: {}'.format(case, e.args[0]))
            continue

if __name__ == '__main__':
    main()
