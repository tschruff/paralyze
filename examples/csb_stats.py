# -*- coding: utf-8 -*-
"""Determines the size distribution of each csb file in a tarball and writes the
results into a csv file.

Author:
    Tobias Schruff, <tobias.schruff@gmail.com>

Date:
    09.05.2017
"""

import tarfile
import os
import sys
import numpy as np
import argparse
import pandas as pd

from paralyze.core.solids.io import CSBFile
from paralyze.util.distribution import SizeDistribution


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('tarball', type=str)
    parser.add_argument('--n_sieves', type=float, default=10)
    parser.add_argument('--precision', type=int, default=3)
    args = parser.parse_args()

    TARFILE = args.tarball
    if TARFILE.endswith('.tar'):
        CSVFILE = TARFILE.replace('.tar', '.csv')
    elif TARFILE.endswith('.tar.gz'):
        CSVFILE = TARFILE.replace('.tar.gz', '.csv')
    else:
        CSVFILE = os.path.splitext(TARFILE)[0] + '.csv'

    if not os.path.exists(TARFILE):
        print('Error: file {} does not exist'.format(TARFILE))
        sys.exit(1)

    p = args.precision
    pp = p+3
    np.set_printoptions(precision=p)

    with open(CSVFILE, 'w') as csv:

        print('{0:^10}\t{1:^{pp}} {2:^{pp}}'.format("Member", "GM", "GSD", pp=pp))

        tar = tarfile.open(TARFILE)
        df = pd.DataFrame(np.full((len(tar.getnames()), 4), np.nan), columns=['case', 'time', 'gm', 'gsd'])

        for member in tar.getmembers():
            if not member.isfile():
                continue

            f = tar.extractfile(member)
            bodies = CSBFile.load(f)
            f.close()

            sizes = list(map(lambda body: 2.0 * body.radius, bodies))
            sieves = np.linspace(min(sizes), max(sizes) + SizeDistribution.EPSILON, args.n_sieves)
            s = SizeDistribution(sieves, sizes=sizes, volume_func=lambda size: 4/3. * np.pi * (size/2.)**3)
            if len(member.name) > 50:
                text = '[...]'+member.name[-45:]
            else:
                text = member.name
            print('{0:<50}\t{1:^{pp}.{p}f} {2:^{pp}.{p}f}'.format(text, s.gm, s.gsd, p=p, pp=pp))

            csv.write(str(member.name) + '\n')
            csv.write('gm,gsd,' + ','.join(map(str, sieves)) + '\n')
            csv.write('{0:.{p}f},{1:.{p}f},'.format(s.gm, s.gsd, p=p) + ','.join(map(str, s.fc)) + '\n')


if __name__ == '__main__':
    main()
