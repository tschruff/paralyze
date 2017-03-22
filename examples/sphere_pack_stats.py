import pylab as p
import matplotlib.pyplot as pyplot
import numpy as np
import math
import scipy.stats
import os
import glob
import sys

from paralyze.core.algebra import AABB


########################################################################################################################
# USER PARAMETERS
########################################################################################################################

# === GENERAL ===

# absolute path to input csb file(s)
INPUT = '/Users/tobs/Programming/PlayGround/sandbox/csb_out/coarse/simulation_step_10000.csv'

# used to scale input to SI units, i.e. [m]
SCALING_FACTOR = .001

# sieves to classify the grain sizes, in mm
SIEVES = np.arange(0.25, 64.25, 0.5)
# SIEVES = [0.0625, 0.125, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0]

DOMAIN_FILTER = '[<0, 0, 0> , <256, 256, 256>]'


# === FIGURES ===

# grain size fractions used in figures
GSD_MODE = 'coarse'

# absolute path to output folder (will be set to INPUT folder if empty)
OUTPUT = ""

# file format of output figure
FIGURE_FORMAT = "png"

# change font size and type
FONT_SIZE = 10
FONT_FAMILY = 'Arial'
MARKER_SIZE = 5


########################################################################################################################
# UTILITIES
########################################################################################################################

GRAIN_SIZE_CLASSES = {
   'full':         ([0.004, 0.063, 2, 64, 256],
                    [2**x for x in range(-10, 9)]),

   'non-cohesive': ([2],
                    [2**x for x in range(-4, 7)]),

   'coarse':       ([2],
                    [2**x for x in range(-1, 7)]),

   'fine':         ([],
                    [2**x for x in range(-10, 0)]),

   'clay':         ([0.001, 0.004],
                    [2**x for x in range(-10, -7)]),

   'silt':         ([0.004, 0.063],
                    [2**x for x in range(-7, -3)]),

   'sand':         ([0.063, 2],
                    [2**x for x in range(-4, 2)]),

   'pebbles':      ([2, 64],
                    [2**x for x in range(1, 7)]),

   'cobbles':      ([64, 256],
                    [2**x for x in range(6, 9)]),

   'boulders':     ([],
                    [])
}


def classify(grain_size, sieves):
    sieves_count = len(sieves)
    sieves = reversed(sieves)
    for i, sieve_diameter in enumerate(sieves):
        if grain_size >= sieve_diameter:
            return sieves_count - 1 - i
    raise ValueError('Grain size %d is not contained in given sieves %s' % (grain_size, sieves))


def volume(diameter):
    """
    :param bodies:
    :return: The volume of the bodies in cubic-m
    """
    return 4.0/3 * math.pi * (diameter / 2.0) ** 3


def specific_surface(diameter):
    return 6.0 / diameter


def load_diameters(files, scaling_factor=1.0, separator=','):
    diameters = []
    files = glob.glob(files)
    for file in files:
        with open(file, 'r') as csb:
            for line in csb:
                line = line.split(separator)
                if int(line[0]) == 1:
                    diameters.append(float(line[4]) * scaling_factor)
    return diameters


########################################################################################################################
# SCRIPT
########################################################################################################################

# checking user defined variables
if INPUT == "" or len(glob.glob(INPUT)) == 0:
    print("ERROR: No such file or directory: %s" % INPUT)
    sys.exit()

if OUTPUT == "":
    OUTPUT = os.path.dirname(os.path.abspath(INPUT))

sieve_count = len(SIEVES)
class_count = sieve_count - 1  # convert sieves to m
sieves = [sieve * 0.001 for sieve in SIEVES]

# creates a list of Sphere objects found in INPUT
diameters = load_diameters(INPUT, SCALING_FACTOR)
# truncate all diameters smaller than the smallest sieve and larger than the largest sieve
diameters = [diameter for diameter in diameters if sieves[0] < diameter < sieves[-1]]
# list of sphere volumes, in cubic-m
volumes = [volume(diameter) for diameter in diameters]
# total solid volume of the spheres, in cubic-m
solid_volume = sum(volumes)

if solid_volume == 0.0:
    print('No bodies found larger than smallest given sieve %f' % sieves[0])
    sys.exit()

volume_fractions = [0.0 for _ in range(class_count)]
acc_volume_fractions = [0.0 for _ in range(class_count)]
avg_diameters = [0.0 for _ in range(class_count)]

# calculate volume fractions for each grain size class
for i in range(len(diameters)):
    d = diameters[i]
    v = volumes[i]
    cat = classify(d, sieves)
    volume_fractions[cat] += v

for i in range(class_count):
    avg_diameters[i] = math.sqrt(sieves[i] * sieves[i + 1])

# normalize volume
volume_fractions[0] /= solid_volume
acc_volume_fractions[0] = volume_fractions[0]
for i in range(1, class_count):
    volume_fractions[i] /= solid_volume
    acc_volume_fractions[i] = volume_fractions[i] + acc_volume_fractions[i - 1]

# calculate geometric mean (GM)
gm = 1.0
for i in range(class_count):
    if volume_fractions[i] > 0.0:
        gm *= avg_diameters[i] ** volume_fractions[i]
gm **= (1.0 / sum(volume_fractions))

# calculate geometric standard deviation (GSD)
gsd = 0.0
for i in range(class_count):
    gsd += volume_fractions[i] * math.log(avg_diameters[i] / gm) ** 2
gsd = math.exp(math.sqrt(gsd))

# calculate skewness (SK)
if gsd > 1.0:
    sk = 0.0
    for i in range(class_count):
        sk += volume_fractions[i] * (math.log(avg_diameters[i]) - math.log(gm)) ** 3
    sk /= 100 * math.log(gsd ** 3)
else:
    sk = 0.0

nobs, min_max, mean, variance, skewness, kurtosis = scipy.stats.describe(diameters)
print('# bodies : %d' % nobs)
print('min. d   : %.3f mm' % (min_max[0] * 1000.0))
print('max. d   : %.3f mm' % (min_max[1] * 1000.0))
print('GM       : %.3f mm' % (gm * 1000.0))
print('GSD      : %.3f' % gsd)
print('Skewness : %.3f' % sk)

##################
# PLOTTING FIGURES

p.rcParams['font.size'] = FONT_SIZE
p.rcParams['font.family'] = FONT_FAMILY

fig = pyplot.figure(figsize=(8, 8), dpi=300)

major_xticks = GRAIN_SIZE_CLASSES[GSD_MODE][0]
minor_xticks = GRAIN_SIZE_CLASSES[GSD_MODE][1]
minor_xtick_labels = [str(int(-math.log(c, 2))) for c in GRAIN_SIZE_CLASSES[GSD_MODE][1]]

ax0 = fig.add_subplot(3, 1, 1)
counts, bins, patches = ax0.hist(list(map(lambda d: d * 1000.0, diameters)), bins=list(map(lambda sieve: sieve * 1000.0, sieves)),
                                 color='k')
ax0.axvline(gm * 1000.0, color='b', linewidth=1, linestyle='--')
[i.set_linewidth(1.5) for i in ax0.spines.values()]
ax0.set_xscale('log')
ax0.set_xlim(min(minor_xticks), max(minor_xticks))
ax0.set_xticks(major_xticks)
ax0.set_xticks(minor_xticks, minor=True)
ax0.set_xticklabels(minor_xtick_labels, minor=True)
ax0.xaxis.grid(b=True, which='major', color='0.1', linestyle='-', lw=1.5)
ax0.set_yscale('log')
ax0.set_ylabel('Count')

ax1 = fig.add_subplot(3, 1, 2)
ax1.plot(list(map(lambda d: d * 1000.0, avg_diameters)), volume_fractions, color='k', marker='x', markersize=MARKER_SIZE, lw=1)
ax1.axvline(gm * 1000.0, color='b', linewidth=1, linestyle='--')
[i.set_linewidth(1.5) for i in ax1.spines.values()]
ax1.set_xscale('log')
ax1.set_xlim(min(minor_xticks), max(minor_xticks))
ax1.set_xticks(major_xticks)
ax1.set_xticks(minor_xticks, minor=True)
ax1.set_xticklabels(minor_xtick_labels, minor=True)
ax1.xaxis.grid(b=True, which='major', color='0.1', linestyle='-', lw=1.5)
# ax1.yaxis.grid(b=True, which='major', color='k', linestyle='-')
ax1.set_ylabel('Fraction finer, in mass-%')

ax2 = fig.add_subplot(3, 1, 3)
ax2.plot(list(map(lambda d: d * 1000.0, sieves[1:])), acc_volume_fractions, color='k', marker='x', markersize=MARKER_SIZE, lw=1)
ax2.axvline(gm * 1000.0, color='b', linewidth=1, linestyle='--')
[i.set_linewidth(1.5) for i in ax2.spines.values()]
ax2.set_xscale('log')
ax2.set_xlim(min(minor_xticks), max(minor_xticks))
ax2.set_xticks(major_xticks)
ax2.set_xticks(minor_xticks, minor=True)
ax2.set_xticklabels(minor_xtick_labels, minor=True)
ax2.xaxis.grid(b=True, which='major', color='0.1', linestyle='-', lw=1.5)
ax2.yaxis.grid(b=True, which='major', color='k', linestyle='-')
ax2.set_xlabel(r'Grain diameter, in $\phi$')
ax2.set_ylim(0.0, 1.0)
ax2.set_yticks(np.arange(0.0, 1.1, 0.1))

ax2.text(0.03, 0.8, 'GM = {0:.2f}\nGSD = {1:.2f}'.format(-math.log(gm * 1000, 2), gsd), bbox=dict(facecolor='white'),
         transform=ax2.transAxes)

ax2.set_ylabel('Acc. fraction finer, in mass-%')

pyplot.subplots_adjust(left=0.08, right=0.95, top=0.95, bottom=0.08)

fig.savefig(OUTPUT + "/gsd." + FIGURE_FORMAT)
