import getopt
import sys
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.cm as cm
from matplotlib.colors import to_hex
import matplotlib.dates as mdates
import common
import pytz

FIGSIZE = (common.TEXTWIDTH, 1.5)

def usage(f=sys.stderr):
    program = sys.argv[0]
    f.write(f"""\
Usage: {program} [FILENAME...]
This script reads from CSV files and plots a heatmap. With no FILE, or when FILE is -, read standard input. By default, print results to stdout and log to stderr.

  -h, --help            show this help
  -o, --out             write to file (default: figure.pdf)
  -n, --no-show         do not show the plot, just save as file

Example:
  {program} input1.csv input2.csv --out figure.pdf
""")

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def input_files(args):
    """Yields DataFrames from provided file paths."""
    if not args:
        eprint("No input files specified.")
        sys.exit(1)
    for arg in args:
        for path in glob.glob(arg):
            try:
                df = pd.read_csv(path)
                yield path, df
            except Exception as e:
                eprint(f"Error reading file '{path}': {e}")


def plot_dirunal_timeseries(df, output_pdf, show_plot):
    fig, ax = plt.subplots(figsize=FIGSIZE)

    df['timestamp_rounded'] = pd.to_datetime(df['timestamp_rounded'], format='mixed').dt.tz_convert('Asia/Shanghai')
    
    # Get the first date
    start_date = df['timestamp_rounded'].min().normalize()

    # Start at 11/15
    start_date = start_date + pd.Timedelta(days=3)

    end_date = start_date + pd.Timedelta(days=7)

    # Filter DataFrame for the first 7 days
    df = df[(df['timestamp_rounded'] >= start_date) & (df['timestamp_rounded'] < end_date)]

    sns.lineplot(
        data=df,
        x='timestamp_rounded',
        y='percentage_censored_connections_per_interval',
        hue='Source',
        # hue_order=hour_slot_order,
        # palette=hour_slot_color_mapping,
        marker=None,
        # linewidth=1,
        ax=ax,
    )

    ax.legend(
        title='',
        bbox_to_anchor=(0.5, 1.35),
        loc='upper center',
        fontsize=9,
        title_fontsize=5.5,
        # markerscale=0.5,
        ncol=3,
        frameon=False,
        # handlelength=0.75
    )
    # sns.move_legend(ax, "upper center", bbox_to_anchor=(0.5, 1.15))


    # ax.xaxis.set_major_locator(mdates.HourLocator(interval=24))
    # ax.xaxis.set_minor_locator(mdates.HourLocator(interval=12))
    # ax.xaxis.set_major_formatter(
    #     mdates.DateFormatter('%m/%d \n %H:%M', tz=pytz.timezone('Asia/Shanghai'))
    # )

    # first_12_time = start_date + pd.Timedelta(hours=6)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d \n%H:%M', tz=pytz.timezone('Asia/Shanghai')))
    ax.xaxis.set_major_locator(mdates.HourLocator(byhour=range(4, 24, 12))) #start from 12 increment by 12

    # ax.set_xlim(start_date, end_date) # Ensure x-axis limits are set

    # ax.set_xticklabels(rotation=90)
    # ax.set_xticklabels(labels, rotation=45, ha='right')

    # plt.xticks(rotation=45, ha='right')

    ax.set_xlabel("")
    ax.set_ylabel("Percentage of Blocked \nConnections (%)")

    metadata = {"CreationDate": None, "Creator": None, "Producer": None} if output_pdf.endswith(".pdf") else None
    # fig.subplots_adjust(left=0.09, right=0.98, top=0.90, bottom=0.2)

    plt.tight_layout(pad=0.05)


    try:
        fig.savefig(output_pdf, format='pdf', dpi=300, metadata=metadata)
        eprint(f"Figure successfully saved to '{output_pdf}'.")
    except Exception as e:
        eprint(f"An error occurred while saving the PDF: {e}")

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
        if o in ("-h", "--help"):
            usage()
            sys.exit(0)
        if o in ("-o", "--out"):
            output_filename = a
        if o in ("-n", "--no-show"):
            show_plot = False

    dfs = []
    for file_path, df in input_files(args):
        eprint(f"Loaded file: {file_path} with {len(df)} rows.")
        dfs.append(df)

    if not dfs:
        eprint("No valid input files were loaded.")
        sys.exit(1)

    # Combine all DataFrames with a source identifier
    keys = [(x.split('-')[-1].split('.')[0]).capitalize() for x in args] 

    combined_df = pd.concat(dfs, keys=keys).reset_index(level=0).rename(columns={'level_0': 'Source'})

    # Generate and save the plot
    plot_dirunal_timeseries(combined_df, output_filename, show_plot)
