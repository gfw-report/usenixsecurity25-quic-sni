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
from matplotlib.ticker import StrMethodFormatter, NullFormatter, FuncFormatter
import matplotlib.cm as cm
from matplotlib.colors import to_hex




import common


FIGSIZE = (common.COLUMNWIDTH, 1.5)


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

def format_k(x, pos):
    if x == 0:
        return '0'
    return f'{int(x/1000)}k'

def plot_blocked_domain_over_time(df, output_pdf, show_plot):
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

    # if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        # df["date"] = pd.to_datetime(df["date"], errors='coerce')

    # Sort the DataFrame by date
    # df = df.sort_values("date")

    # df_weekly = (
    #     df.set_index("date")
    #       .resample("W")["num_of_domains_blocked"]
    #       .mean()
    #       .reset_index()
    # )
    # Boxplot on the first axis
    # sns.ecdfplot(data=df, x="time_difference_ms", ax=ax)

    df['WeekStart'] = pd.to_datetime(df['Week'] + '-1', format='%G-W%V-%u')


    # Sort the DataFrame by the new datetime column to ensure correct plotting order
    df = df.sort_values('WeekStart')


    sns.lineplot(data=df, x="WeekStart", y="unique_domains", ax=ax, marker="")

    plt.bar(df['WeekStart'], df['added_domains'], color='green', label='Added Domains', alpha=0.7)
    plt.bar(df['WeekStart'], -df['removed_domains'], color='red', label='Removed Domains', alpha=0.7)
    

    ax.set_xlabel('')
    ax.set_ylabel('Domains Blocked\nover QUIC')
    # ax.set_yscale('log')
    plt.ylim(top=50000)
    # plt.ylim(0, 50000)
    plt.xticks(rotation=45, ha='right', fontsize=8)

    plt.gca().yaxis.set_major_formatter(FuncFormatter(format_k))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%y-%m-%d'))

        # Set the x-axis ticks to start at the beginning of each week
    locator = mdates.WeekdayLocator(byweekday=0, interval=2)  # 0 = Monday
    formatter = mdates.DateFormatter('%Y-%m-%d')
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)

    # Remove PDF metadata
    metadata = (
        {"CreationDate": None, "Creator": None, "Producer": None}
        if output_pdf.endswith(".pdf")
        else None
    )


    fig.subplots_adjust(left=0.21, right=0.98, top=0.9, bottom=0.38)

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
        plot_blocked_domain_over_time(df, output_filename, show_plot)
