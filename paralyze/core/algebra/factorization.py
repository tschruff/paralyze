import numpy as np

from .primes import primeFactors


def factors(number, numberOfFactors, weights=None):
    assert isinstance(number, int)
    assert numberOfFactors > 0
    assert weights is None or len(weights) == numberOfFactors

    fs = np.array([1 for i in range(numberOfFactors)])
    primes = primeFactors(number)

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
    assert isinstance(number, int)
    assert weights is None or len(weights) == 2
    return factors(number, 2, weights)


def factors3D(number, weights=None):
    assert isinstance(number, int)
    assert weights is None or len(weights) == 3
    return factors(number, 3, weights)
