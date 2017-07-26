"""
"""
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
from sqlalchemy import create_engine
from paralyze.utils.distribution import Lognormal, Uniform, GradingCurve
from paralyze.utils import get_fitting_parameters

DB_FILE = '/Users/tobs/sciebo/Diss/Data/results.db'
DB_NAME = 'infiltration'

def max_t_indices(df):
    max_idx = []
    cases = df['case_id'].unique()
    for cid in cases:
        max_idx.append(df[df['case_id'] == cid].idxmax()['t'])
    return max_idx

def dc(mode, c, psd=False):
    gm = '{}_psd_gm'.format(mode) if psd else '{}_gm'.format(mode)
    gsd = '{}_psd_gsd'.format(mode) if psd else '{}_gsd'.format(mode)
    return np.where(
        df[gsd] > 1.0,
        Lognormal(mu=np.log(df[gm]), sigma=np.log(df[gsd])).xc(c),
        df[gm]
    )

def d(c, psd=False):
    return dc('f', c, psd)

def D(c, psd=False):
    return dc('c', c, psd)

def max_bin_f(c_f, f_gsd):
    return (1-c_f)*(1-(0.5-2/15*f_gsd))

def mean(gm, gsd):
    mu = np.log(gm)
    sigma = np.log(gsd)
    return np.exp(mu + sigma**2/2)


# %%
db = create_engine('sqlite:///{}'.format(DB_FILE))
df_raw = pd.read_sql(DB_NAME, db, index_col='index')
#df.head()

# %%
mi = list(map(int, max_t_indices(df_raw)))
df_tmax = df_raw.iloc[mi]
df_tmax.set_index('case_id', inplace=True)
#df_tmax.head()

# %%
import matplotlib.pyplot as plt
%matplotlib inline
plt.set_cmap('nipy_spectral')

# %%
df = df_tmax.copy()
#df = df[df['RMSE'] < 0.015]
#df = df[df['t'] > 159999]
#df = df[df['f_gsd'] < 1.01]
df = df[np.isclose(df['q_f'], 0.01)]
df = df[np.isclose(df['g'], 0.241)]

df['F0'] = df['f_f0']/max_bin_f(df['c_f0'], df['f_gsd'])
df['X'] = (df['f_gm']*df['f_psd_gm'])/(df['c_gm']*df['c_psd_gm'])

df = df.replace([-np.inf, np.inf], np.nan).dropna()

# In[ ]:
def fit_r(x, b, c):
    return 1/(1+np.exp(b-c*x))
    #return 1/np.exp(a*(x-0.05)**2+b) # 0.918
    #return np.exp(-a*(x+b)**2) # 0.919

def fit_l(x, b, c):
    #return a*np.exp(-np.exp(b-c*x)) # 0.639
    return 1/(1+np.exp(b-c*x)) # 0.594
    #return a/(d+np.exp(b-c*x)) # 0.643
    #return a*(1-np.exp(-b*x))**c # 0.639
    #return 1 - np.exp(-a*x**b) # 0.592
    #return a*x**b # 0.558

xl = 0.056
xr = 0.054
df_r = df[df['X'] >= xr].sort_values('X').reset_index(drop=True)
df_l = df[df['X'] <= xl].sort_values('X').reset_index(drop=True)

X_r = np.linspace(xr, 1.0, 100)
X_l = np.linspace(0.0, xl, 100)

df_r = df_r.replace([-np.inf, np.inf], np.nan).dropna()
df_l = df_l.replace([-np.inf, np.inf], np.nan).dropna()

popt_r, pcov_r = curve_fit(fit_r, df_r['X'], df_r['F0'])
p_r = get_fitting_parameters(fit_r, df_r['X'], df_r['F0'], popt_r)

popt_l, pcov_l = curve_fit(fit_l, df_l['X'], df_l['F0'])
p_l = get_fitting_parameters(fit_l, df_l['X'], df_l['F0'], popt_l)

plt.figure(figsize=(10,6))
plt.scatter(df_l['X'], df_l['F0'], facecolors='none', edgecolors='C0')
plt.scatter(df_r['X'], df_r['F0'], facecolors='none', edgecolors='C1')
plt.plot(X_l, fit_l(X_l, *popt_l), c='C0')
plt.plot(X_r, fit_r(X_r, *popt_r), c='C1')
plt.title('Rl$^2$ = {:.3f}, popt = {}, Rr$^2$ = {:.3f}, popt = {}'.format(p_l.r_sq, popt_l, p_r.r_sq, popt_r))
plt.savefig('/Users/tobs/sciebo/Diss/Data/x-f_f0.pdf')

# In[ ]:
plt.figure(figsize=(10,6))
plt.scatter(df['X'], np.log(2)/df['lambda'], s=df['g']*100, c=df['c_gsd'])
plt.ylim(0, 10)
plt.savefig('/Users/tobs/sciebo/Diss/Data/x-z50.pdf')

# In[ ]:
plt.figure(figsize=(10,6))
plt.scatter(df['X'], df['f_f0']/df['lambda'])
plt.ylim(0, 0.1)
plt.savefig('/Users/tobs/sciebo/Diss/Data/x-V.pdf')
