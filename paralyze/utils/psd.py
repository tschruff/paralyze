from scipy import interpolate
from .stats import log_mean
from .interpolate import log_interpolate

import numpy as np
import copy


class ParticleSizeDistribution(object):

    EPSILON = 1.E-6
    DEFAULT_BIN_SCALE = 'linear'

    StandardBinSets = {
        "ISO": [.002, .0063, .02, 0.063, .2, .63, 2., 6.3, 20., 63., 200., 630.],
        "Kru": [2**(-phi) for phi in range(10, -9, -1)]
    }

    def __init__(self, d, bins=10, range=None, bin_scale='linear', weights=1):
        """Initializes a new ParticleSizeDistribution instance.

        Parameters
        ----------
        d: array-like
            Input particle diameters. The particle size distribution is computed
            based on these values.
        bins: int or sequence of scalars or str, optional
            One of the standard bin sets names ('ISO', 'Kru'), the number of bins,
            or a list (array-like) of custom set of bin edges.
        bin_scale: str, optional
            One of 'linear' (Default), 'log' (equal to log10), 'log2', or 'log10'.
        """
        assert len(d) > 0, "len(d) must not be zero"

        if isinstance(bins, str):
            bins = ParticleSizeDistribution.StandardBinSets[bins]
            self._scale = 'linear'
            self._base = 1
        elif isinstance(bins, int):
            self._scale, self._base = self._parse_bin_scale(bin_scale)
            range = range or (-np.inf, np.inf)
            min_d = max(np.min(d), range[0])
            max_d = min(np.max(d), range[1])
            if self._scale == 'log':
                bins = np.logspace(np.log(min_d), np.log(max_d), num=bins, base=self._base)
            elif self._scale == 'linear':
                bins = np.linspace(min_d, max_d, num=bins)
            else:
                raise ValueError("bin_scale must be any of 'linear', 'log', 'log2', or 'log10', not %s" % bin_scale)
        else:
            self._scale = 'linear'
            self._base = 1

        if isinstance(weights, (int, float)):
            weights = np.full(len(d), weights)
        elif callable(weights):
            weights = np.array([weights(item) for item in d])

        # bin edges
        self._b = np.array(bins)
        # content finer values
        self._f = self._generate(d, bins=self._b, weights=weights)
        # not
        # self._f, self._b = np.histogram(d, bins=bins, weights=weights)
        # because np.histogram uses a half-open interval which includes the
        # lower edge and excludes the upper edge. We need exactly the opposite
        # because the bin 1.0-2.0 should include all values for which
        # 1.0 < v <= 2.0.
        # This is achieved by using np.digitize(d, bins, right=True)

    def _generate(self, d, bins, weights):
        f = np.zeros_like(bins)
        idx = np.digitize(d, bins, right=True)
        for i in range(len(d)):
            if 0 <= idx[i] < len(f):
                f[idx[i]] += weights[i]
        return f

    def _parse_bin_scale(self, bin_scale):
        if bin_scale == 'linear':
            return 'linear', 1.0
        if bin_scale.startswith('log'):
            try:
                return 'log', float(bin_scale.lstrip('log') or '10')
            except ValueError:
                pass
        raise ValueError("bin_scale must be any of 'linear', 'log', 'log2', or 'log10', not %s" % bin_scale)

    def __add__(self, other):
        if not isinstance(other, ParticleSizeDistribution):
            raise NotImplemented

        if not np.array_equal(self.bi, other.bi):
            raise ValueError("distributions must have equal sieves")

        s = copy.copy(self)
        s._f += other.fi
        return s

    def __iadd__(self, other):
        if not isinstance(other, ParticleSizeDistribution):
            raise NotImplemented

        if not np.array_equal(self.bi, other.bi):
            raise ValueError("distributions must have equal sieves")

        self._f += other.fi
        return self

    def __sub__(self, other):
        if not isinstance(other, ParticleSizeDistribution):
            raise NotImplemented

        if not np.array_equal(self.bi, other.bi):
            raise ValueError("distributions must have equal sieves")

        s = copy.copy(self)
        s._f -= other.fi
        return s

    def __isub__(self, other):
        if not isinstance(other, ParticleSizeDistribution):
            raise NotImplemented

        if not np.array_equal(self.bi, other.bi):
            raise ValueError("distributions must have equal sieves")

        self._f -= other.fi
        return self

    def __mul__(self, scalar):
        s = copy.copy(self)
        s._f *= float(scalar)
        return s

    def __rmul__(self, scalar):
        return self * float(scalar)

    def __imul__(self, scalar):
        self._f *= float(scalar)
        return self

    ##########################
    #
    # Member properties
    #
    ##########################

    @property
    def num_bins(self):
        return len(self._f) - 1

    @property
    def bi(self):
        """Returns the bin edges.
        """
        return self._b

    def bin_centers(self, bin_scale):
        """Returns the bin centers according to given scale.
        """
        if bin_scale == 'log':  # return log mean values
            return np.array([log_mean(self._b[i], self._b[i+1]) for i in range(len(self._b)-1)])
        if bin_scale == 'linear':  # return arithmetic mean values
            return np.array([(self._b[i]+self._b[i+1])/2.0 for i in range(len(self._b)-1)])
        raise ValueError("Unexpected bin_scale: '%s'! Supported values are 'log', 'linear'" % bin_scale)

    @property
    def di(self):
        """Returns the bin centers.
        """
        return self.bin_centers(ParticleSizeDistribution.DEFAULT_BIN_SCALE)

    @property
    def fi(self):
        """Returns the fraction finer (edge centered).
        """
        return self._f

    @property
    def fc(self):
        """Returns the cumulative fraction finer (edge centered).
        """
        a = np.zeros_like(self._f)
        a[0] = self._f[0]
        for i in range(1, len(self._f)):
            a[i] = a[i-1] + self._f[i]
        return a

    ##########################
    #
    # Statistical descriptors
    #
    ##########################

    def dc(self, c, bin_scale='linear'):
        """Returns the characteristic particle sizes with cum fraction content
        specified by ``c``, e.g. dc(c=0.5) yields d50.

        Parameters
        ----------
        c: float or sequence of scalars
            The percentile values for which the characteristic sizes are computed.
        bin_scale: str, optional
            The scale according to which the interpolation is performed. Either
            'linear' (Default) or 'log' are currently supported.
        """
        if self._scale == 'log':
            f = log_interpolate(self.fc, self.bi, assume_sorted=True)
        elif self._scale == 'linear':
            f = interpolate.interp1d(self.fc, self.bi, kind='linear', assume_sorted=True)
        else:
            raise ValueError('Unsupported bin_scale "%s"' % bin_scale)

        if isinstance(c, float):
            return float(f(c))
        return f(c)

    @property
    def dmin(self):
        """The minimum fraction size.
        """
        return self.di[np.where(self.fc > 0.0)[0][0]]

    @property
    def dmax(self):
        """The maximum fraction size.
        """
        return self.di[np.where(self.fc >= np.sum(self._f))[0][0]]

    @property
    def mean(self):
        """Arithmetic mean particle size.
        """
        return np.sum(self.di * self.fi[1:]) / np.sum(self.fi[1:])

    @property
    def sd(self):
        """Standard deviation of particle size distribution.
        """
        return np.sqrt(np.sum((self.di - self.mean)**2 * self.fi[1:]))

    @property
    def gm(self):
        """Geometric mean particle size.
        """
        return np.exp(np.sum(self.fi[1:] * np.log(self.di)) / np.sum(self.fi[1:]))

    @property
    def gsd(self):
        """Geometric standard deviation of particle size distribution.
        """
        return np.exp(np.sqrt(np.sum(self.fi[1:] * np.log(self.di/self.gm)**2)/np.sum(self.fi[1:])))

    ##########################
    #
    # I/O
    #
    ##########################

    @classmethod
    def __load(cls, f, dialect, **kwargs):
        import csv
        reader = csv.reader(f, dialect, **kwargs)
        d = []
        f = []
        try:
            for row in reader:
                try:
                    d.append(float(row[0]))
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
        psd = cls([], bins=d)  # create an empty ParticleSizeDistribution
        psd._f = f  # and set fraction content directly
        return psd

    @classmethod
    def load(cls, f, dialect='excel', **kwargs):
        """Loads a ParticleSizeDistribution from a csv file.

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
        writer.writerow(['particle_diameter', 'fraction_finer', 'cum_fraction_finer'])
        for d, fi, fc in zip(self.bi, self.fi, self.fc):
            writer.writerow([d, fi, fc])

    def save(self, f, dialect='excel', **kwargs):
        if isinstance(f, str):
            with open(f, 'w') as f:
                self.__save(f, dialect, **kwargs)
        else:
            self.__save(f, dialect, **kwargs)

    ##########################
    #
    # Plotting
    #
    ##########################

    def plot(self, fig=None, axi=None, axc=None, normalize=False):
        if fig is None:
            import matplotlib.pyplot as plt
            fig = plt.figure()
        if not axi:
            axi = fig.add_subplot(211)
        if not axc:
            axc = fig.add_subplot(212)

        di = self.di
        fi = self.fi if not normalize else self.fi/np.sum(self.fi)
        ds = self.bi
        fc = self.fc if not normalize else self.fc/np.sum(self.fi)
        gm = self.gm
        label = "GM={:.3f}, GSD={:.3f}".format(gm, self.gsd)

        axi.bar(di, fi[1:])
        axi.set_ylabel('Content [-]')

        p = axc.plot(ds, fc, '-')
        q = axc.plot(di, fi[1:], '-')
        axc.axvline(gm, linestyle='--', color=p[0].get_color(), label=label)
        axc.set_ylabel('Fraction finer [-]')
        axc.set_xlabel('Grain size')

        if self._scale == 'log':
            axc.set_xscale('log', basex=self._base)

        return axi, axc
