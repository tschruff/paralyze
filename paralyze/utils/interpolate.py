from scipy.interpolate import interp1d

import numpy as np


def log_interpolate(x, y, kind='linear', assume_sorted=True):
    logx = np.log10(x)
    logy = np.log10(y)
    lin_interp = interp1d(logx, logy, kind=kind, assume_sorted=assume_sorted)

    def log_interp(z):
        return np.power(10.0, lin_interp(np.log10(z)))

    return log_interp
