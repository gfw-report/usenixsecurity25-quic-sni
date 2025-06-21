# Common code for graph plotting, for a uniform look.

# paste this to the paper:
#
# the text width: \the\textwidth
#
# the column width: \the\columnwidth


# \the\textwidth → 505.89pt
TEXTWIDTH = 505.89 / 72.27

# \the\columnwidth → 241.14749pt
COLUMNWIDTH = 241.02039 / 72.27

# Set default plot style.
# https://seaborn.pydata.org/tutorial/aesthetics.html
# https://seaborn.pydata.org/generated/seaborn.set_theme.html
import seaborn as sns
sns.set_theme(style = "ticks", rc = {
    'font.family': 'serif',
    # 'font.serif': 'Linux Libertine O', # ACM and PETS: https://petsymposium.org/authors.php#fonts
    'font.serif': ['Nimbus Roman', 'Helvetica'], # USENIX and NDSS
    'font.size': 10,
    'legend.fontsize': 10,
    'axes.labelsize': 10,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'xtick.major.size': 2,
    'xtick.minor.size': 2,
    'ytick.major.size': 2,
    'ytick.minor.size': 2,
    'patch.force_edgecolor': False,
    'legend.fancybox': False,
    'mathtext.default': 'regular',
    'axes.linewidth': 1.0,
    'text.color': 'black',
    'xtick.color': 'black',
    'ytick.color': 'black',
    'xtick.bottom': True,
    'ytick.left': True,
    'axes.grid' : True,
    'grid.linewidth': 0.5,
    'grid.color': '#efefef',
})
