from scipy import special

import numpy as np
import math
import copy
import warnings


class Uniform(object):

    def __init__(self, mu):
        self.mu = float(mu)

    @property
    def cv(self):
        """Coefficient of variation.
        """
        return 0.0

    @property
    def gm(self):
        """Geometric mean.
        """
        return self.mu

    @property
    def gsd(self):
        """Geometic standard deviation.
        """
        return 1.0

    @property
    def mean(self):
        return self.mu

    @property
    def median(self):
        return self.mu

    @property
    def mode(self):
        return self.mu

    @property
    def sd(self):
        """Standard deviation.
        """
        return 0.0

    @property
    def sk(self):
        """Skewness.
        """
        return 0.0

    @property
    def var(self):
        """Variance.
        """
        return 0.0

    def pdf(self, x):
        """Probability density function.
        """
        return 1.0 if x == self.mu else 0.0

    def cdf(self, x):
        """Cumulative distribution function.
        """
        return self.pdf(x)

    def inv(self, c):
        return self.mu


class Lognormal(object):

    def __init__(self, mu, sigma, scale=1.0):
        """

        Parameters
        ----------
        mu: float (-inf, inf)
            The location parameter, equal to ln(gm).
        sigma: float [0, inf)
            The scale parameter, equal to ln(gsd).
        """
        self.mu = mu
        self.sigma = sigma
        self.scale = scale

        if not np.all(sigma > np.zeros_like(sigma, np.float64)):
            warnings.warn('sigma must be > 0.0')

    def __mul__(self, scale):
        s = copy.copy(self)
        s.scale *= float(scale)
        return s

    def __rmul__(self, scale):
        return self * float(scale)

    def __imul__(self, scale):
        self.scale *= float(scale)
        return self

    @property
    def cv(self):
        """Coefficient of variation.
        """
        return np.sqrt(np.exp(self.sigma**2) - 1)

    @classmethod
    def fit(cls, x, y):
        popt, pcov = curve_fit(
            lambda x, mu, sigma: Lognormal(mu, sigma).pdf(x), x, y,
            bounds=((0, 1e-10), np.inf)
        )

        return Lognormal(*popt)

    @property
    def mean(self):
        return np.exp(self.mu + self.sigma**2/2.)

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
        p = 1./(x*self.sigma*np.sqrt(2*math.pi)) * np.exp(-(np.log(x)-self.mu)**2/(2.*self.sigma**2))
        return self.scale * p

    def cdf(self, x):
        """Cumulative distribution function.
        """
        c = (0.5 + 0.5 * special.erf((np.log(x)-self.mu)/(np.sqrt(2)*self.sigma)))
        return self.scale * c

    def inv(self, c):
        c /= self.scale
        return np.exp(np.sqrt(2)*self.sigma*special.erfinv((c-0.5)/0.5)+self.mu)
