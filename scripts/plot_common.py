"""Shared labels and publication styling for analysis figures."""
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable
import matplotlib.pyplot as plt

VERSIONS = ('lambda', 'omega')
TASKS = ('T01', 'T02', 'T04', 'T05')
LABELS = {'lambda': 'With Atom', 'omega': 'Without Atom'}
SLUGS = {'lambda': 'with_atom', 'omega': 'without_atom'}
COLORS = {'With Atom': '#ed7867', 'Without Atom': '#609fc4'}
HEAT_CMAP = LinearSegmentedColormap.from_list(
    'fixation_time', [(1, 1, 1, 0), (1, .78, .63, .35), (.92, .25, .13, .7), (.55, .02, .04, .9)])


def case_label(task):
    return f'Case {int(task[1:])}'


def heat_scale(fig, axes, maximum):
    scale = ScalarMappable(norm=Normalize(0, max(maximum, 1e-12)), cmap=HEAT_CMAP)
    bar = fig.colorbar(scale, ax=axes, shrink=.78, pad=.025)
    bar.set_label('Accumulated fixation-time density (ms/pixel²)')
    return bar
