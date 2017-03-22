import numpy as np


def get_fitting_parameters(fit_func, fit_y, fit_frame, popt=None):
    """Returns R^2 and RMSE of fitting.
    """
    # residuum^2
    if popt is not None:
        res_sq = (fit_y - fit_func(fit_frame, *popt))**2
    else:
        res_sq = (fit_y - fit_func(fit_frame))**2
    sum_res_sq = np.sum(res_sq)
    # denominator
    diff_sq = (fit_y - np.mean(fit_y))**2
    sum_diff_sq = np.sum(diff_sq)

    r_sq = 1.0 - sum_res_sq / sum_diff_sq
    rmse = (sum_res_sq/res_sq.size)**0.5

    return r_sq, rmse
