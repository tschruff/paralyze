import numpy as np


class SizeDistribution(object):

    CLAY     = [0.0     , 2.**(-4)]
    SILT     = [2.**(-8), 2.**(-7), 2.**(-6), 2.**(-5), 2.**(-4)]
    SAND     = [2.**(-4), 2.**(-3), 2.**(-2), 2.**(-1), 2.**( 0), 2.**( 1)]
    GRAVEL   = [2.**( 1), 2.**( 2), 2.**( 3), 2.**( 4), 2.**( 5), 2.**( 6), 2.**( 7), 2.**( 8)]
    BOULDERS = [2.**( 8), ]

    EPSILON = 1.e-6

    def __init__(self, sieves, **kwargs):
        self.__validate_keys(list(kwargs.keys()))
        self._s = np.array(sieves, dtype=np.float64)

        keys = kwargs.keys()
        if 'passage' in keys:
            cum = self.__normalize(kwargs['passage'], cum=True)
            self._f = [cum[i+1]-cum[i] for i in range(len(cum)-1)]
        elif 'residue' in keys:
            self._f = self.__normalize(kwargs['residue'], cum=False)
        elif 'volumes' in keys:
            self._f = self.from_sample(kwargs['volumes'], kwargs['sizes'], self._s)
        elif 'gm' and 'gsd' in keys:
            self._f = self.generate(kwargs['gm'], kwargs['gsd'], self._s)

        self._f = np.array(self._f, dtype=np.float64)
        assert abs(1.0 - np.sum(self._f)) < self.EPSILON, 'Sum of fraction contents must be 1.0'
        assert len(self._s) == len(self._f), 'Sieves and passage/residue must have same size'
        assert self._f[-1] == 0.0, 'Largest sieve must not contain any grains'

    def characteristic_size(self, index):
        index /= 100.0
        if 0. < index < 1.:
            fc = self.fc
            for i in range(self.num_fractions):
                if fc[i] >= index:
                    # TODO: Interpolate size
                    return self.fraction_sizes[i]
        else:
            raise IndexError('Given index "{}" is not covered by volume distribution'.format(index))

    def mixed(self, other, volume_ratio=.5):
        """Mixes two volume distributions with a given ratio of volumes.

        Parameters
        ----------
        other: SizeDistribution
            The other SizeDistribution
        volume_ratio: float
            The ratio of volumes of the two distributions (0 < volume_ratio < 1).
            A volume_ratio of 0.5 (default) means that both distributions will
            represent 50 % of the resulting distribution.

        Returns
        -------
        combination: SizeDistribution
            The combination of ``self`` and ``other``.
        """
        if 0. < volume_ratio < 1.:
            sieves = set(self.sieves + other.sieves)
            f = np.zeros(len(sieves), np.float64)

            pvr = volume_ratio
            nvr = 1.0 - volume_ratio
            # iter over all sieves
            for i, sieve in enumerate(sieves):
                idx, = np.where(sieve == self.sieves)
                f[i] += pvr * self.fi[idx]
                idx, = np.where(sieve == other.sieves)
                f[i] += nvr * other.fi[idx]
            return SizeDistribution(sieves, residue=f)
        else:
            raise ValueError("volume_ratio must be in the range (0-1)")

    def refined(self, nv, scale='log'):
        ft = self._f / nv
        s = []
        f = []
        for i in range(self.num_fractions):
            if scale == 'log':
                ispace = np.logspace(self._s[i], self._s[i+1], nv+1, base=2)
            else:
                ispace = np.linspace(self._s[i], self._s[i+1], nv+1)
            for j in range(nv):
                f.append(self.interpolate(ispace[0], ft[i], ispace[nv], ft[i+1], ispace[j]))

            if i < self.num_fractions - 1:
                s.extend(ispace[:-1])
            else:
                s.extend(ispace)

        s = np.array(s, dtype=np.float64)
        s = np.log2(s) if scale == 'log' else s
        f.append(0.)
        f = np.array(f, dtype=np.float64)

        return GrainSizeDistribution(s, residue=f)

    def iter_sizes(self):
        return iter(self.fraction_sizes(self._s))

    def iter_contents(self, cum=False):
        if cum:
            return iter(self.fc)
        return iter(self.fi)

    def figure(self, **kwargs):
        fig = plt.figure(**kwargs)
        axt = fig.add_subplot(211)
        axb = fig.add_subplot(212, sharex=axt)

        Di = self.di
        Fi = self.fi[:-1]
        Ds = self.sieves
        Fc = self.fc
        gm = self.gm

        axt.step(Di, Fi, where='mid', color='C0')
        axt.axvline(gm, linestyle='--', color='0.5')
        axb.scatter(Ds, Fc, facecolors='none', edgecolors='C1')
        axb.plot(Ds, Fc, '--', color='C1')
        axb.axvline(gm, linestyle='--', color='0.5')
        axb.text(gm*1.1, 0.4, '$d_{50}$', size='small', weight='bold', ha='left')

        axt.set_ylabel('Rel. Anteil [-]')
        axb.set_ylabel('Kum. Anteil [-]')
        axb.set_xlabel('Korngröße [m]')
        axb.set_xscale('log')

        return fig

    @property
    def num_sieves(self):
        """Returns the number of sieves.
        """
        return len(self._s)

    @property
    def num_fractions(self):
        """Returns the number of sieve fractions.
        """
        return len(self._s) - 1

    @property
    def di(self):
        """Returns the size of each sieve fraction.

        The size of a sieve fraction ``i`` is the
        log-interpolated mean value of sieve ``i`` and ``i+1``.
        """
        return self.fraction_sizes(self._s)

    @property
    def fi(self):
        """Returns the relative content ``fi`` of each sieve fraction.
        """
        return self._f

    @property
    def fc(self):
        """Returns the cumulated content ``fc`` of each sieve fraction.
        """
        return [sum(self._f[:i]) for i in range(self.num_sieves)]

    @property
    def gm(self):
        return np.prod([self.di[i]**self._f[i] for i in range(self.num_fractions)])**(1/sum(self.fi))

    @property
    def sieves(self):
        return self._s

    @staticmethod
    def fraction_sizes(sieves):
        return np.array([10**((math.log10(sieves[i])+math.log10(sieves[i+1]))/2) for i in range(len(sieves)-1)])

    @staticmethod
    def generate(gm, gsd, sieves):
        # TODO: Implement generate method
        return []

    @staticmethod
    def from_sample(volumes, sizes, sieves):
        """Returns the realtive content ``f`` for each sieve fraction.
        """
        assert len(volumes) == len(sizes)
        assert list(sieves) == list(sorted(sieves))

        f = np.zeros(len(sieves), np.float64)
        for k in range(len(volumes)):
            for i in range(1, len(sieves)):
                if 0. < (sieves[i] - sizes[k]) < self.EPSILON:
                    f[i-1] += volumes[k]
        f /= sum(volumes)
        return f

    @staticmethod
    def interpolate(s0, f0, s1, f1, sx):
        return f0 + (f1-f0) * (sx-s0)/(s1-s0)

    @staticmethod
    def __validate_keys(keys):
        if 'sieves' and 'sizes' in keys:
            raise KeyError('')

    @staticmethod
    def __normalize(f, cum=False):
        if cum:
            return [(fi-f[0])/(f[-1]-f[0]) for fi in f]
        total = sum(f)
        return [fi/total for fi in f]
