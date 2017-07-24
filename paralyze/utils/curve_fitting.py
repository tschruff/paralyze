import numpy as np
import collections

FittingParams = collections.namedtuple('FittingParams', 'r_sq rmse')


def get_fitting_parameters(fit_func, fit_x, fit_y, popt=()):
    """Returns R^2 and RMSE of fitting function.
    """
    # residuum^2
    res_sq = (fit_y - fit_func(fit_x, *popt))**2
    sum_res_sq = np.sum(res_sq)
    # denominator
    diff_sq = (fit_y - np.mean(fit_y))**2
    sum_diff_sq = np.sum(diff_sq)

    r_sq = 1.0 - sum_res_sq / sum_diff_sq
    rmse = (sum_res_sq/res_sq.size)**0.5

    return FittingParams(r_sq=r_sq, rmse=rmse)
