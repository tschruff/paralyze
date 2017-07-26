from paralyze.utils.distribution import GrainSizeDistribution, Lognormal
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

%matplotlib inline

def sk(sigma):
    (np.exp(sigma**2) + 2)*np.sqrt(np.exp(sigma**2) - 1)

s = np.logspace(-4, 7, 50, base=2)
sigma = np.linspace(0.01, 3.0)
skewness = sk(sigma)
y = []
for x in sigma:
    gsd = GrainSizeDistribution(s, mu=np.log(6), sigma=x, dist='lognorm')
    psd = gsd.to_psd(lambda d: 4/3. * np.pi * (d/2.0)**3)
    y.append(psd.gm/gsd.gm)
y = np.array(y)

def fit_func(x, a):
    return 1./np.exp(a*x**2)

popt, pcov = curve_fit(fit_func, sigma, y)

plt.plot(sigma, y)
plt.plot(sigma, fit_func(sigma, *popt), '--')
plt.title('1/(e^{:.3}x^2)'.format(*popt))
