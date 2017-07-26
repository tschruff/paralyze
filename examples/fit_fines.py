import os
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from paralyze.utils import get_fitting_parameters

import seaborn
import inshore

style = inshore.get('rwth-a5', 'thesis')
seaborn.set(**style)
mpl.rcParams['text.usetex'] = True

# 2.2  2.35 2.4  2.15 2.45 2.15 2.4
DEPTH_SHIFT = {
    1.0: -2.7,
    1.1: -2.85,
    1.2: -2.9,
    1.3: -2.65,
    1.4: -2.95,
    1.5: -2.65,
    1.6: -2.9
}

def f_beta(z, f0, beta):
    return f0 * np.exp(-beta * z)

def f_alpha(z, f0, alpha):
    return f0 * alpha**z

def fit_case(case_id, data_path, z_bounds, num_obs, decay_param='alpha'):

    f_svd_path = os.path.join(data_path, case_id+'.csv')

    coarse, fine, q_f, g = case_id.split('_')
    bed = coarse.split('-')
    c_gm = float(bed[1])
    if bed[0] == 'uniform':
        c_gsd = 1.0
    else:
        c_gsd = float(bed[2])
    f_gm, f_gsd = map(float, fine.split('-'))

    frame = pd.read_csv(f_svd_path, sep=',')
    # apply rolling mean
    if num_obs > 0:
        frame = frame.rolling(num_obs, center=True).mean()
    # drop inf and nan values
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna()

    cols = ('t', 'c_f0', 'f_f0', decay_param, 'R2', 'RMSE')
    if decay_param == 'alpha':
        fit_func = f_alpha
        fit_bounds = (0, 1)
    elif decay_param == 'beta':
        fit_func = f_beta
        fit_bounds = (0, np.inf)

    num_t = len(frame.columns[2:])
    case_df = pd.DataFrame(np.full((num_t, len(cols)), np.nan), columns=cols)

    # apply depth shift (0 = surface-layer-bed interface) and clip to fit_bounds
    frame['depth'] += DEPTH_SHIFT[c_gsd]
    frame = frame[(z_bounds[0] <= frame['depth']) & (frame['depth'] <= z_bounds[1])]
    frame = frame.reset_index(drop=True)

    print('Fitting {} curves for case {}'.format(num_t, case_id))
    popt = None
    for i, t in enumerate(frame.columns[2:]):

        try:
            popt, pcov = curve_fit(fit_func, frame['depth'], frame[t], bounds=fit_bounds)
        except RuntimeError:
            print("Could not determine fittings constants (t={}, case={})".format(t, case_id))
            popt = (0.0, np.nan)
        except ValueError:
            print("Could not determine fittings constants (t={}, case={})".format(t, case_id))
            popt = (0.0, np.nan)
        except Exception as e:
            print("Unexpected error: {} (case={})".format(e, case_id))
            sys.exit(1)

        p = get_fitting_parameters(fit_func, frame['depth'], frame[t], popt)

        case_df.loc[i, 'c_f0'] = frame.loc[0, 'bed']
        case_df.loc[i, 'f_f0'] = popt[0]
        case_df.loc[i, decay_param] = popt[1]
        case_df.loc[i, 't'] = int(t)
        case_df.loc[i, 'R2'] = p.r_sq
        case_df.loc[i, 'RMSE'] = p.rmse

    fig = plt.figure()
    ax = fig.add_subplot(111)
    frame.plot(x='depth', ax=ax, colormap='copper', legend=False)
    if popt is not None:
        ax.step(frame['depth'], fit_func(frame['depth'], *popt), where='mid', lw=2., linestyle='--', color='k')
        ax.text(0.97*z_bounds[1], 0.95, r'$f_0 = {0:.3f}, \{2} = {1:.3f}$'.format(*popt, decay_param), ha='right', va='top')
        ax.text(0.97*z_bounds[1], 0.85, r'$\mathrm{{ R }}^2 = {:.3f}, \mathrm{{ RMSE }} = {:.3f}$'.format(p.r_sq, p.rmse), ha='right', va='top')
    ax.set_xlim(*z_bounds)
    ax.set_xlabel('Relative depth $z^*$')
    ax.set_ylim(0, 1)
    ax.set_ylabel('Solid volume fraction')

    return case_df, fig


def create_fit_cases(data_path, results_path, z_bounds, num_obs, decay_param, fig_path):

    entries = os.listdir(data_path)

    if not os.path.exists(results_path):
        os.mkdir(results_path)
    fig_path = os.path.join(results_path, fig_path)
    if not os.path.exists(fig_path):
        os.mkdir(fig_path)

    print('Found {} entries in data_path: {}'.format(len(entries), data_path))
    for entry in entries:

        if not entry.endswith('.csv'):
            continue

        case_df, fig = fit_case(entry.replace('.csv', ''), data_path, z_bounds, num_obs, decay_param)
        case_df.to_csv(os.path.join(results_path, entry), index=False)
        fig.tight_layout()
        fig.savefig(os.path.join(fig_path, entry.replace('.csv', '.pdf')))
        plt.close(fig)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('data_path', type=str)
    parser.add_argument('results_path', type=str)
    parser.add_argument('--z_bounds', type=float, nargs=2, default=(0, 16))
    parser.add_argument('--num_obs', type=int, default=0)
    parser.add_argument('--fig_path', type=str, default='figures')
    parser.add_argument('--decay_param', type=str, default='alpha')

    args = vars(parser.parse_args())
    create_fit_cases(**args)


if __name__ == '__main__':
    main()
