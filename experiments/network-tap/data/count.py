#!/usr/bin/env python3

import sys
import getopt
import glob
import csv

def usage(f=sys.stderr):
    program = sys.argv[0]
    f.write(f"""\
Usage: {program} [FILENAME...]
This script reads from files and write output. With no FILE, or when FILE is -, read standard input. By default, print results to stdout and log to stderr.

  -h, --help            show this help
  -o, --out             write to file
  -b, --binary          read input as binary (default: False)

Example:
  {program} < input.txt > output.txt
""")

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def input_files(args, binary=False):
    STDIN =  sys.stdin.buffer if binary else sys.stdin
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

if __name__ == '__main__':
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "ho:b", ["help", "out=", "binary"])
    except getopt.GetoptError as err:
        eprint(err)
        usage()
        sys.exit(2)

    output_file = sys.stdout
    binary_input = False
    for o, a in opts:
        if o == "-h" or o == "--help":
            usage()
            sys.exit(0)
        if o == "-o" or o == "--out":
            output_file = open(a, 'a+')
        if o == "-b" or o == "--binary":
            binary_input = True

    sum_sport_gt_dport = 0
    sum_sport_lt_dport = 0
    sum_sport_eq_dport = 0

    for f in input_files(args, binary=binary_input):
        csv_reader = csv.reader(f)
        for row in csv_reader:
            sport = int(row[0])
            dport = int(row[1])
            count = int(row[2])

            if sport > dport:
                sum_sport_gt_dport += count
            elif sport < dport:
                sum_sport_lt_dport += count
            else:
                sum_sport_eq_dport += count
                eprint(f"Found sport == dport: {sport}")
                eprint(f"row: {row}")


    total = sum_sport_gt_dport + sum_sport_lt_dport + sum_sport_eq_dport

    print(f"Sum of count where sport > dport: {sum_sport_gt_dport}, {sum_sport_gt_dport / total * 100:.2f}% of total", file=output_file)
    print(f"Sum of count where sport < dport: {sum_sport_lt_dport}, {sum_sport_lt_dport / total * 100:.2f}% of total", file=output_file)
    print(f"Sum of count where sport == dport: {sum_sport_eq_dport}, {sum_sport_eq_dport / total * 100:.2f}% of total", file=output_file)
    output_file.close()
