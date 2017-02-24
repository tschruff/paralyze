from paralyze.core.bodies import Sphere
from paralyze.core.algebra import Interval

import numpy as np


class WentworthScale:

    Clay = np.array([1./1024000, 1./512000])
    Silt = np.array([1./256000, 1./128000, 1./64000, 1./32000])
    Sand = np.array([1./16000, 1./8000, 1./4000, 1./2000, 1./1000])
    Gravel = np.array([2./1000, 4./1000, 8./1000, 16./1000, 32./1000])
    Boulders = np.array([64./1000, ])
    All = Clay + Silt + Sand + Gravel + Boulders

    def __init__(self, sieves=WentworthScale.All):
        self._classes = []
        sieves = sorted(sieves)
        for i in range(len(sieves)-1):
            self._classes.append(Interval(sieves[i], sieves[i+1], Interval.Open, Interval.Closed))

    def __iter__(self):
        return iter(self._classes)


def sieveEquivalentBodySize(body):
    if isinstance(body, Sphere):
        return 2. * body.radius()
    else:
        raise NotImplemented('sieveEquivalentBodySize not implemented for bodies of type %s' % type(body))


def createSizeDistribution(bodies, sieves, mapping_func=lambda body: 1):
    """

    :param bodies: Set of bodies to create size distribution for
    :param sieves: Set of sieves to use for classification
    :param mapping_func: Function that adds the bodies dependend numeric value to the size class
    :return:
    """
    sieves_count = len(sieves)
    sieves = reversed(sieves)
    mapped_values = np.array([0. for _ in sieves])

    for body in bodies:
        for i, sieve_size in enumerate(sieves):
            if sieveEquivalentBodySize(body) >= sieve_size:
                mapped_values[sieves_count-1-i] += mapping_func(body)

    return mapped_values
