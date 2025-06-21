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

import common

FIGSIZE = (common.COLUMNWIDTH, common.COLUMNWIDTH)



# Define column names
COLNAMES = ['timestamp', 'srcip', 'dstip', 'srcport', 'dstport', 'domain', 'censored']


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


def plot_heatmap(df, output_pdf, show_plot, step):
    """
    Generates a heatmap of censored counts based on source and destination ports
    and saves the heatmap as a PDF file.

    Parameters:
    - df (DataFrame): DataFrame containing input data.
    - output_pdf (str): Path to the output PDF file.
    - show_plot (bool): Whether to display the plot interactively.
    """
    # Convert 'censored' column to boolean
    df['censored'] = df['censored'].astype(bool)

    # Create a pivot table with counts of censored entries
    all_port_counts = df.pivot_table(
        index='dstport',
        columns='srcport',
        values='censored',
        aggfunc=np.sum,
        fill_value=0  # Replace NaN with 0
    )

    # Initialize the matplotlib figure
    fig, ax = plt.subplots(figsize=FIGSIZE)

    # Generate a heatmap with seaborn
    res = sns.heatmap(
        all_port_counts,
        cmap='coolwarm',
        # square=True,
        cbar_kws={'pad': 0.03,"shrink": 1, "aspect": 40},
        linewidths=0,
        linecolor='gray',
        ax=ax
    )

    for _, spine in res.spines.items():
        spine.set_visible(True)
        spine.set_linewidth(1)

    ax.tick_params(axis='both', which='both', direction='out', length=1.5, width=1, pad=2)
    cbar = ax.collections[0].colorbar
    cbar.ax.tick_params(labelsize=6, direction='out', length=1, width=1)

    # Customize the outline of the colorbar
    cbar.outline.set_edgecolor('black')  # Set the outline color to black
    cbar.outline.set_linewidth(1)      # Set the outline thickness


    # Set the labels
    ax.set_xlabel("Source Port")
    ax.set_ylabel("Destination Port")

    # Configure x and y ticks
    if step == 1:
        ax.set_xticks(np.arange(all_port_counts.columns.size) + 0.5)
        ax.set_yticks(np.arange(all_port_counts.index.size) + 0.5)
        ax.set_xticklabels(all_port_counts.columns, rotation=90, fontsize=4)
        ax.set_yticklabels(all_port_counts.index, rotation=0, fontsize=4)
        fig.subplots_adjust(left=0.10, right=1.05, top=0.98, bottom=0.10)
    else:
        ax.set_xticks(np.arange(0,all_port_counts.columns.size, 2) + 0.5)
        ax.set_yticks(np.arange(0,all_port_counts.index.size,2) + 0.5)
        ax.set_xticklabels(all_port_counts.columns[::2], rotation=90, fontsize=4)
        ax.set_yticklabels(all_port_counts.index[::2], rotation=0, fontsize=4)
        fig.subplots_adjust(left=0.12, right=1.05, top=0.98, bottom=0.12)

    # xticks_labels = all_port_counts.columns[::step]
    # ax.set_xticklabels(xticks_labels, rotation=90, fontsize=4)

    # yticks_labels = all_port_counts.index[::step]
    # Invert y-axis to have the first row at the top
    ax.invert_yaxis()

    # Remove PDF metadata
    metadata = (
        {"CreationDate": None, "Creator": None, "Producer": None}
        if output_pdf.endswith(".pdf")
        else None
    )


    # Save the figure as a PDF
    try:
        fig.savefig(output_pdf, format='pdf', dpi=300, metadata=metadata)
        eprint(f"Heatmap successfully saved to '{output_pdf}'.")
    except Exception as e:
        eprint(f"An error occurred while saving the PDF: {e}")

    # Show plot if required
    if show_plot:
        plt.show()
    plt.close()


if __name__ == '__main__':
    try:
        opts, args = getopt.gnu_getopt(
            sys.argv[1:], "ho:n", ["help", "out=", "no-show", "step="]
        )
    except getopt.GetoptError as err:
        eprint(err)
        usage()
        sys.exit(2)

    output_filename = "figure.pdf"
    show_plot = True
    step = 1  # Default step value

    for o, a in opts:
        if o == "-h" or o == "--help":
            usage()
            sys.exit(0)
        if o == "-o" or o == "--out":
            output_filename = a
        if o == "-n" or o == "--no-show":
            show_plot = False
        if o == "--step":
            try:
                step = int(a)
            except ValueError:
                eprint("Error: Step value must be an integer.")
                sys.exit(2)
    for f in input_files(args):
        # Read the CSV file
        try:
            df = pd.read_csv(f, header=None, names=COLNAMES)
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
        plot_heatmap(df, output_filename, show_plot, step)
