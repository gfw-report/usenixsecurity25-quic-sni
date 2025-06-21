#!/usr/bin/env python3

import getopt
import sys
import os
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from venny4py.venny4py import *

import common

FIGSIZE = (common.COLUMNWIDTH, 2.5)

def usage(f=sys.stderr):
    program = sys.argv[0]
    f.write(f"""\
Usage: {program} FILE1 FILE2 FILE3 FILE4 [options]
This script reads four domain blocklist files and plots an venn diagram for
the overlap between the blocklists for different protocols.

Required arguments:
  FILE1  Path to the first blocklist file (e.g., HTTP)
  FILE2  Path to the second blocklist file (e.g., HTTPS)
  FILE3  Path to the third blocklist file (e.g., QUIC)
  FILE4  Path to the fourth blocklist file (e.g., DNS)

Options:
  -h, --help            show this help
  -o, --out FILE        write output plot to FILE (default: figure.pdf)
  -n, --no-show         do not display the plot interactively

Example:
  {program} 2025-01-05_http_blocklist.txt 2025-01-05_https_blocklist.txt \\
           2025-01-05_quic_blocklist.txt 2025-01-05_dns_blocklist.txt --out overlap.pdf
""")

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def read_domains(filename):
    """Reads a file and returns a set of domains (stripping whitespace)."""
    domains = set()
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            domain = line.strip()
            if domain:
                domains.add(domain)
    return domains

def thousands_formatter(x, pos):
    """Convert a number into k format."""
    if x >= 1000:
        return f'{int(x / 1000)}K'
    return str(int(x))

def plot_venn(protocol_domains, output_pdf, show_plot):

    # Build a membership mapping for each domain across protocols

    fig, ax = plt.subplots(figsize=FIGSIZE)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.grid(False)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

    

    venny4py(sets=protocol_domains, asax=ax, 
            colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'] ,
            column_spacing=1,
            line_width=0, font_size=9,
            legend_cols=4,
            edge_color='black')

    # for ax in plt.gcf().axes:
    #     ax.xaxis.set_major_formatter(ticker.FuncFormatter(thousands_formatter))


    #     for artist in ax.get_children():
    #         if isinstance(artist, matplotlib.collections.PathCollection):
    #             # Adjust the size of the circles 
    #             sizes = artist.get_sizes()
    #             new_sizes = sizes * 0.25  # Scale down the sizes
    #             artist.set_sizes(new_sizes)
    #             plt.draw()  # Redraw the figure to reflect changes
        
    
    
    # plt.tick_params(axis='y', pad=5)  # Increase padding for y-axis ticks
    # plt.gca().spines['left'].set_position(('outward', 3))  # Move the y-axis spine outward

    fig.subplots_adjust(left=0.01, right=0.99, top=1.03, bottom=-0.03)


    for ax in fig.axes:
        for text in ax.texts:
            try:
                # Convert the text to number (removing commas)
                value = int(text.get_text().replace(',', ''))
                # Format with k if ≥1000, otherwise leave as is
                if value >= 1000:
                    text.set_text(f'{value/1000:.1f}K')
                else:
                    text.set_text(str(value))
            except ValueError:
                continue
    
    
    
    
    # Remove PDF metadata
    metadata = (
        {"CreationDate": None, "Creator": None, "Producer": None}
        if output_pdf.endswith(".pdf")
        else None
    )

    # Save the figure
    try:
        fig.savefig(output_pdf, format='pdf', dpi=300, metadata=metadata)
        eprint(f"Figure successfully saved to '{output_pdf}'.")
    except Exception as e:
        eprint(f"An error occurred while saving the PDF: {e}")

    # Show plot interactively if requested
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

    if len(args) != 4:
        eprint("Error: Exactly four input files are required.")
        usage()
        sys.exit(1)

    # Map each input file to a protocol label for clarity
    protocol_labels = ["HTTP", "HTTPS", "QUIC", "DNS"]
    protocol_files = dict(zip(protocol_labels, args))

    # Read domains from each file into a dictionary
    protocol_domains = {}
    for protocol, filename in protocol_files.items():
        try:
            protocol_domains[protocol] = read_domains(filename)
        except Exception as e:
            eprint(f"Error reading file '{filename}': {e}")
            sys.exit(1)

    plot_venn(protocol_domains, output_filename, show_plot)


    