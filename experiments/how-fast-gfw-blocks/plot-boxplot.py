#!/usr/bin/env python3

import getopt
import sys
import glob
import os

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.dates as mdates
import pytz
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import StrMethodFormatter, NullFormatter
import matplotlib.cm as cm
from matplotlib.colors import to_hex
import re


import common


FIGSIZE = (common.COLUMNWIDTH, 3.3)




def usage(f=sys.stderr):
    program = sys.argv[0]
    f.write(f"""\
Usage: {program} [FILENAME...]
This script reads from CSV files and plots a heatmap. With no FILE, or when FILE is -, read standard input. By default, print results to stdout and log to stderr.

  -h, --help            show this help
  -o, --out             write to file (default: figure.pdf)
  -n, --no-show         do not show the plot, just save as file

Example:
  {program} input.csv --out figure.pdf
""")


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

eprint(f"columnwidth: {common.COLUMNWIDTH}")

def format_time(s, spacing='  '):
    match = re.match(r"(\d{1,2})(AM|PM)", s)
    if match:
        return f"{match.group(1)}{spacing}{match.group(2)}"
    else:
        return s
    
def input_files(args, binary=False):
    STDIN = sys.stdin.buffer if binary else sys.stdin
    MODE = 'rb' if binary else 'r'
    if not args:
        yield STDIN
    else:
        for arg in args:
            if arg == "-":
                yield STDIN
            else:
                for path in glob.glob(arg):
                    with open(path, MODE) as f:
                        yield f


def plot_portgroup_prob_graph(df, output_pdf, show_plot):
    """
    Generates a heatmap of censored counts based on source and destination ports
    and saves the heatmap as a PDF file.

    Parameters:
    - df (DataFrame): DataFrame containing input data.
    - output_pdf (str): Path to the output PDF file.
    - show_plot (bool): Whether to display the plot interactively.
    """

    # # Initialize the matplotlib figure
    fig, ax = plt.subplots(figsize=FIGSIZE)

    # Boxplot on the first axis
    sns.boxplot(data=df,palette='gray',
                meanprops={
                    'marker': '^',       # shape of the marker (triangle up as an example)
                    # 'markerfacecolor': 'red',  # fill color for the marker
                    # 'markeredgecolor': 'black',# edge color of the marker
                    'markersize': 3      # size of the marker (smaller than default)
                },
                width=0.5,
                boxprops={'linewidth': 0.5},
                whiskerprops={'linewidth': 0.5},
                capprops={'linewidth': 0.5},
                medianprops={'linewidth': 0.5},
                x="time_difference_ms", y='hour_slot',ax=ax, whis=(0, 100), showmeans=True,linewidth=0.2)
    ax.set_xlabel('Time to Block (ms)')
    ax.set_ylabel('Time of Day (Beijing Time, UTC+8)')
    ax.set_xscale('log')

    new_labels = [format_time(tick.get_text().split('-')[0]) for tick in ax.get_yticklabels()]

    # Set the new tick labels
    # plt.xticks(fontsize=8)  # set x-axis tick label font size to 8
    plt.yticks(fontsize=7)  # set x-axis tick label font size to 8
    plt.xticks(fontsize=7)  # set x-axis tick label font size to 8
    plt.xlim(50, 10000)
    ax.set_yticklabels(new_labels)

    # Custom x-tick values for log scale
    # tick_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
    # ax.set_xticks(tick_values)
    # ax.set_xticklabels([f"{v}" for v in tick_values], rotation=90)
    # ax.xclip
    ax.xaxis.set_major_formatter(StrMethodFormatter('{x:.0f}'))

    # Remove PDF metadata
    metadata = (
        {"CreationDate": None, "Creator": None, "Producer": None}
        if output_pdf.endswith(".pdf")
        else None
    )


    fig.subplots_adjust(left=0.18, right=0.96, top=0.99, bottom=0.13)

    # fig.tight_layout()


    # Save the figure as a PDF
    try:
        fig.savefig(output_pdf, format='pdf', dpi=300, metadata=metadata)
        eprint(f"Figure successfully saved to '{output_pdf}'.")
    except Exception as e:
        eprint(f"An error occurred while saving the PDF: {e}")

    # Show plot if required
    if show_plot:
        plt.show()
    plt.close()


if __name__ == '__main__':
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "ho:n", ["help", "out=", "no-show"])
    except getopt.GetoptError as err:
        eprint(err)
        usage()
        sys.exit(2)

    output_filename = "figure.pdf"
    show_plot = True
    for o, a in opts:
        if o == "-h" or o == "--help":
            usage()
            sys.exit(0)
        if o == "-o" or o == "--out":
            output_filename = a
        if o == "-n" or o == "--no-show":
            show_plot = False

    for f in input_files(args):
        # Read the CSV file
        try:
            df = pd.read_csv(f)
        except FileNotFoundError:
            eprint(f"Error: The file '{f.name}' does not exist.")
            continue
        except pd.errors.EmptyDataError:
            eprint(f"Error: The file '{f.name}' is empty.")
            continue
        except Exception as e:
            eprint(f"An error occurred while reading '{f.name}': {e}")
            continue

        # Generate and save the heatmap
        plot_portgroup_prob_graph(df, output_filename, show_plot)
