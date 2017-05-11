import numpy as np


def gm(x, w=1.0):
    """Returns the (weighted) geometric mean of sample values ``x``.

    The weighted geometric mean can be calculated in two ways:

        1. np.power(np.prod(x**w), 1./np.sum(w))
        2. np.exp(np.sum(w * np.log(x)) / np.sum(w))

    The first version tends to produce numeric overflow due to the internal
    product, thus, we use the second (more robust) version.

    Parameters
    ----------
    x: array-like
        The sample values.
    w: array-like
        The weights. ``x`` and ``w`` must have equal dimensions.
    """
    if isinstance(w, float):
        w = np.full_like(x, w)
    return np.exp(np.sum(w * np.log(x)) / np.sum(w))


def gsd(x, w=1.0):
    """Returns the (weighted) geometric standard deviation of sample values ``x``.

    Parameters
    ----------
    x: array-like
        The sample values.
    w: array-like
        The weights. ``x`` and ``w`` must have equal dimensions.
    """
    if isinstance(w, float):
        w = np.full_like(x, w)
    return np.exp(np.sqrt(np.sum(w * np.log(x/gm(x, w))**2)/np.sum(w)))
