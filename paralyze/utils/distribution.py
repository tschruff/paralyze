import numpy as np
import math
import copy
import os
import logging

from scipy import interpolate, stats, special


class Lognormal(object):

    def __init__(self, mu, sigma):
        """

        Parameters
        ----------
        mu: float (-inf, inf)
            The location parameter, equal to ln(gm).
        sigma: float (1, inf)
            The scale parameter, equal to ln(gsd).
        """
        self.mu = float(mu)
        self.sigma = float(sigma)

        assert sigma > 0.0, 'sigma must be greater than 0.0'

    @property
    def cv(self):
        """Coefficient of variation.
        """
        return np.sqrt(np.exp(self.sigma**2) - 1)

    @property
    def gm(self):
        """Geometric mean.
        """
        return self.median

    @property
    def gsd(self):
        """Geometic standard deviation.
        """
        return np.exp(self.sigma)

    @property
    def mean(self):
        return np.exp(self.mu + self.sigma**2 / 2.)

    @property
    def median(self):
        return np.exp(self.mu)

    @property
    def mode(self):
        return np.exp(self.mu - self.sigma**2)

    @property
    def sd(self):
        """Standard deviation.
        """
        return self.mean * self.cv

    @property
    def sk(self):
        """Skewness.
        """
        return (np.exp(self.sigma**2) + 2) * self.cv

    @property
    def var(self):
        """Variance.
        """
        return self.cv**2 * np.exp(2*self.mu + self.sigma**2)

    def pdf(self, x):
        """Probability density function.
        """
        return 1/(x*self.sigma*(2*math.pi)**(0.5))*np.exp(-(np.log(x)-self.mu)**2/(2*self.sigma**2))

    def cdf(self, x):
        """Cumulative distribution function.
        """
        return 0.5 + 0.5 * special.erf((np.log(x)-self.mu)/(np.sqrt(2)*self.sigma))


class GradingCurve(object):

    EPSILON = 1.e-5

    StandardSieveSets = {
        "ISO": [.002, .0063, .02, 0.063, .2, .63, 2., 6.3, 20., 63., 200., 630.],
        "Kru": [2**(-phi) for phi in range(10, -9, -1)]
    }

    def __init__(self, sieves, **kwargs):
        """Initializes a GradingCurve instance.

        Parameters
        ----------
        sieves: array-like
            An ascendingly sorted list of sieves.

        Valid kwargs combinations are
        passage: array-like
        residue: array-like
        sizes and volume_func (function):
        solids: array-like
            A set/list of solids
        mu (float), sigma (float), and distr (str):
        volume (float):
        """
        self._s = np.array(sieves, dtype=np.float64)
        assert self._s[0] > 0.0, 'The smallest sieve must be greater than 0.0'
        self._v = kwargs.get("volume", 1.0)

        keys = kwargs.keys()
        if 'passage' in keys:
            a = self.__normalize(np.array(kwargs['passage']), cum=True)
            self._f = [a[i+1]-a[i] for i in range(len(a)-1)]
        elif 'residue' in keys:
            self._f = self.__normalize(np.array(kwargs['residue']))
        elif 'sizes' and 'volume_func' in keys:
            a = self.__classify(self._s, np.array(kwargs['sizes']), kwargs['volume_func'])
            self._v = np.sum(a)
            self._f = self.__normalize(a)
        elif 'solids' in keys:
            a = self.__classify(self._s, kwargs['solids'], volume_func=lambda solid: solid.volume, size_func=lambda solid: solid.equivalent_mesh_size)
            self._v = np.sum(a)
            self._f = self.__normalize(a)
        elif 'mu' and 'sigma' in keys:
            a = self.__generate(self._s, kwargs['mu'], kwargs['sigma'], kwargs.get('distr', 'lognorm'))
            self._f = self.__normalize(a)
        else:
            raise ValueError('Unexpected kwargs: {}'.format(kwargs.keys()))

        f_sum = sum(self._f)
        sum_check = abs(1.0 - f_sum) < self.EPSILON or f_sum < self.EPSILON
        len_check = len(self._s) - 1 == len(self._f)
        assert sum_check, 'sum(f) must be either 1.0 or 0.0, not {:.3f}'.format(f_sum)
        assert len_check, '{:d} - 1 != {:d}'.format(len(self._s), len(self._f))

    def __add__(self, other):
        if not isinstance(other, GradingCurve):
            raise NotImplemented

        if not np.array_equal(self._s, other._s):
            raise ValueError("GradingCurves must have equal sieves")

        s = copy.copy(self)
        s._f = self.__normalize(self._f + other._v/s._v * other._f)
        s._v += other._v
        return s

    def __iadd__(self, other):
        if not isinstance(other, GradingCurve):
            raise NotImplemented

        if not np.array_equal(self._s, other._s):
            raise ValueError("GradingCurves must have equal sieves")

        self._f = self.__normalize(self._f + other._v/self._v * other._f)
        self._v += other._v

    def __mul__(self, scalar):
        s = copy.copy(self)
        s._v *= float(scalar)
        return s

    def __rmul__(self, scalar):
        return self * float(scalar)

    def __imul__(self, scalar):
        self._v *= float(scalar)

    def __classify(self, sieves, items, volume_func, size_func=lambda item: item):
        """Performs size classification of the particles given by ``items`` into
        the size fractions given by ``sieves``.

        Returns
        -------
        ndarray:
            The residue per sieve.
        """
        residues = np.zeros(len(sieves)-1)
        for item in items:
            size = size_func(item)
            for i, sieve in enumerate(reversed(sieves[:-1])):
                if size >= sieve:
                    residues[i] += volume_func(item)
                    break
        return np.flip(residues, 0)

    def __fraction_sizes(self, sieves):
        return np.array([self.__log_mean(sieves[i], sieves[i+1]) for i in range(len(sieves)-1)])

    def __log_mean(self, x0, x1):
        if not x0 > 0.0 or not x1 > 0.0:
            raise ValueError('x0 and x1 must be greater than 0.0')
        logx0 = np.log(x0)
        logx1 = np.log(x1)
        if np.equal(logx0, logx1):
            return x0
        return (x0-x1)/(logx0-logx1)

    def __log_interp(self, x, y):
        logx = np.log(x)
        logy = np.log(y)
        lin_interp = interpolate.interp1d(logx, logy)
        log_interp = lambda z: np.exp(lin_interp(np.log(z)))
        return log_interp

    def __generate(self, sieves, mu, sigma, distr='lognorm'):
        x = self.__fraction_sizes(sieves)
        if distr == 'lognorm':
            return Lognormal(mu, sigma).pdf(x)
        elif distr == 'norm':
            return stats.norm.pdf(x, mu, sigma)
        else:
            raise ValueError('Unexpected distribution type: {}'.format(distr))

    def __normalize(self, f, cum=False):
        if cum:
            fabs = f[-1]-f[0]
            return np.array([(fi-f[0])/fabs for fi in f])
        total = np.sum(f)
        return np.array([fi/total for fi in f])

    @property
    def num_sieves(self):
        return len(self._s)

    @property
    def num_fractions(self):
        return len(self._s) - 1

    @property
    def sieves(self):
        return self._s

    @property
    def volume(self):
        return self._v

    def dc(self, c, interp='linear'):
        """Returns the characteristic particle sizes with cum. fraction content
        specified by ``c``, e.g. d50 (c=0.5).

        Parameters
        ----------
        c: float or array-like
            The cum. fraction content values for which the sizes are returned.
        interp: str, optional
            One of ('linear', 'log', ‘nearest’, ‘zero’, ‘slinear’, ‘quadratic’,
            ‘cubic’ where ‘zero’, ‘slinear’, ‘quadratic’ and ‘cubic’ refer to a
            spline interpolation of zeroth, first, second or third order).
            Default is 'linear'.
        """
        if interp == 'log':
            f = self.__log_interp(self.fc, self.sieves)
        else:
            f = interpolate.interp1d(self.fc, self.sieves, kind=interp, assume_sorted=True)

        if isinstance(c, float):
            return float(f(c))
        return f(c)

    @property
    def dmin(self):
        return self.di[np.where(self.fc > 0.0)[0][0]]

    @property
    def dmax(self):
        return self.di[np.where(self.fc >= 1.0)[0][0]]

    @property
    def di(self):
        """Characteristic fraction sizes.
        """
        return self.__fraction_sizes(self._s)

    @property
    def fi(self):
        """Fraction content.
        """
        return self._f

    @property
    def fc(self):
        """Cumulative fraction content.
        """
        return np.array([sum(self._f[:i]) for i in range(self.num_sieves)])

    @property
    def mean(self):
        """Arithmetic mean particle size.
        """
        return np.sum(self.di * self.fi)

    @property
    def sd(self):
        """Standard deviation of particle size distribution.
        """
        return np.sqrt(np.sum((self.di - self.mean)**2 * self.fi))

    @property
    def gm(self):
        """Geometric mean particle size.
        """
        return np.prod(self.di**self.fi)

    @property
    def gsd(self):
        """Geometric standard deviation of size distribution.
        """
        return np.exp(np.sqrt(np.sum(self.fi * np.log(self.di/self.gm)**2)))

    @classmethod
    def __load(cls, f, dialect, **kwargs):
        import csv
        reader = csv.reader(f, dialect, **kwargs)
        s = []; f = []
        try:
            for row in reader:
                try:
                    s.append(float(row[0]))
                    f.append(float(row[1]))
                except ValueError as e:
                    # first row might be the header
                    if reader.line_num == 1:
                        continue
                    else:
                        raise e
        except csv.Error as e:
            msg = 'file {}, line {}: {}'.format(str(f), reader.line_num, e)
            raise OSError(msg)
        return cls(s, passage=f)

    @classmethod
    def load(cls, f, dialect='excel', **kwargs):
        """Loads a GradingCurve from a csv file.

        Parameters
        ----------
        f: file-like or str
            The path to the csv file if str, otherwise a file-like object as required
            by :class:`csv.reader`.
        dialect:
            A subclass of :class:`csv.Dialect` or one of the str returned by
            :func:`csv.list_dialects`.
        """
        if isinstance(f, str):
            with open(f, 'r', newline='') as f:
                return cls.__load(f, dialect, **kwargs)
        else:
            return cls.__load(f, dialect, **kwargs)

    def __save(self, f, dialect, **kwargs):
        import csv
        writer = csv.writer(f, dialect, **kwargs)
        writer.writerow(['sieve', 'passage'])
        for s, f in zip(self.sieves, self.fc):
            writer.writerow([s, f])

    def save(self, f, dialect='excel', **kwargs):
        if isinstance(f, str):
            with open(f, 'w') as f:
                self.__save(f, dialect, **kwargs)
        else:
            self.__save(f, dialect, **kwargs)

    def plot(self, fig=None, axi=None, axc=None):
        if not axi or not axc:
            axi = fig.add_subplot(211)
            axc = fig.add_subplot(212, sharex=axt)

        Di = self.di
        Fi = self.fi
        Ds = self.sieves
        Fc = self.fc
        gm = self.gm
        label = "GM={:.3f}, GSD={:.3f}".format(gm, self.gsd)

        axi.step(Di, Fi, where='mid')
        axi.set_ylabel('Fraction finer [-]')
        axi.set_xscale('log', basex=2)

        p = axc.plot(Ds, Fc, '-')
        axc.axvline(gm, linestyle='--', color=p[0].get_color(), label=label)
        axc.set_ylabel('Cum. fraction finer [-]')
        axc.set_xlabel('Particle size [m]')
        axc.set_xscale('log', basex=2)

        return axi, axc
