from .primes import prime_factors

import numpy as np


def factors(number, numberOfFactors, weights=None):
    """Factorizes given ``number`` into ``numberOfFactors`` prime numbers.

    Parameters
    ----------
    numbers: int
        The int that is factorized.
    numberOfFactors: int
        The number of factors into which ``number`` is factorized.
    weights: list
        An optional list of weights that a length of ``numberOfFactors``.

    Returns
    -------
    factors: list
        The list of factors with len(factors) == numberOfFactors.
    """
    assert isinstance(number, int)
    assert isinstance(numberOfFactors, int) and numberOfFactors > 0
    assert weights is None or len(weights) == numberOfFactors

    fs = np.array([1 for i in range(numberOfFactors)])
    primes = prime_factors(number)

    if weights is None:
        weights = fs

    for prime in reversed(primes):
        smallestWeighted = 0
        for factor in range(1, numberOfFactors):
            if fs[factor] / weights[factor] < fs[smallestWeighted] / weights[smallestWeighted]:
                smallestWeighted = factor
        fs[smallestWeighted] *= prime

    return fs


def factors2D(number, weights=None):
    """Convenience method of ``factors`` with numberOfFactors == 2.
    """
    assert isinstance(number, int)
    assert weights is None or len(weights) == 2
    return factors(number, 2, weights)


def factors3D(number, weights=None):
    """Convenience method of ``factors`` with numberOfFactors == 3.
    """
    assert isinstance(number, int)
    assert weights is None or len(weights) == 3
    return factors(number, 3, weights)
