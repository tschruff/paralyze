import numpy as np


def log_mean(x0, x1):
    if not x0 > 0.0 or not x1 > 0.0:
        raise ValueError('x0 and x1 must be greater than 0.0')
    log0 = np.log(x0)
    log1 = np.log(x1)
    if np.equal(log0, log1):
        return x0
    return (x0-x1)/(log0-log1)


def mean(x, weights=1.0):
    return np.sum(weights * x)/np.sum(weights)


def var(x, weights=1.0):
    return np.sum(weights * (x-mean(x, weights))**2)/np.sum(weights)


def std(x, weights=1.0):
    return np.sqrt(var(x, weights))


def sk(x, weights=1.0):
    return np.sum(weights * ((x-mean(x, weights))/std(x, weights))**3)/np.sum(weights)


def kur(x, weights=1.0):
    return np.sum(weights * ((x-mean(x, weights))/std(x, weights))**4)/np.sum(weights) - 3.0


def gmean(x, weights=1.0):
    return np.exp(np.sum(weights * np.log(x)) / np.sum(weights))


def gstd(x, weights=1.0):
    return np.exp(np.sqrt(np.sum(weights * np.log(x/gmean(x, weights))**2)/np.sum(weights)))
