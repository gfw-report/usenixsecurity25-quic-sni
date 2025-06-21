import pandas as pd
import argparse
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from common import *

ip_to_name = {
    # Inside China
    "43.143.0.0": "Tencent Beijing",#"Tencent 10",
    "101.42.0.0": "Tencent 9",
    "8.134.0.0":  "Guangzhou",#"Alibaba Guangzhou",
    "59.110.0.0": "Beijing 1",
    "8.147.0.0": "Beijing 2",
    "101.132.0.0": "Shanghai",
    # Outside China
    "103.152.0.0": "San Jose",#"Aperture San Jose",
    "134.122.0.0": "DigitalOcean NYC1",
    "52.91.0.0": "N. Virginia", #"AWS us-east-1d",
    "137.184.0.0": "San Francisco", #"DigitalOcean SFO3",
    "10.216.0.0": "Stanford",
    "128.138.0.0": "CU Boulder",
    "165.227.0.0": "Frankfurt",
    "13.244.0.0": "Capetown",

}

outside_ips = [
    "103.152.0.0",
    "134.122.0.0",
    "52.91.0.0",
    "137.184.0.0",
    "10.216.0.0",
    "128.138.0.0",
    "165.227.0.0",
    "13.244.0.0"
    ]

# true experiment number: paper experiment number
experiment_map = {
    1: 1,
    3: 2,
    4: 3,
    8: 4,
    9: 5,
    10: 6,
    11: 7,
    13: 8,
    14: 9,
    16: 10,
}

# Set up argument parser
parser = argparse.ArgumentParser(description="Process a CSV file of packet data.")
parser.add_argument("csv_file", help="Path to the CSV file containing the data.")

# Parse the CLI arguments
args = parser.parse_args()

try:
    df = pd.read_csv(args.csv_file)
except FileNotFoundError:
    print(f"Error: File '{args.csv_file}' not found.")
    exit(1)

# Calculate success rate as percentages
df["success_rate"] = (df["packets_received"] / df["packet_count"]) * 100

# Extract experiment number from payload
df["true_experiment"] = df["payload"].str.extract(r'exp(\d+)').astype(int)
df["Experiment"] = df["true_experiment"].map(experiment_map)

# Map IPs to names
df["src_name"] = df["src"].map(ip_to_name)
df["dst_name"] = df["dst"].map(ip_to_name)

# Create src-dst pair
df["Source -> Destination"] = df["src_name"] + " -> " + df["dst_name"]

# Drop Rows we are not interested in
for index, row in df.iterrows():
    if row["src_name"] == "Tencent 9" or row["dst_name"] == "Tencent 9":
        df.drop(index, inplace=True)
    elif row["src_name"] == "CU Boulder" or row["dst_name"] == "CU Boulder":
        df.drop(index, inplace=True)
    elif row["src_name"] == "DigitalOcean NYC1" or row["dst_name"] == "DigitalOcean NYC1":
        df.drop(index, inplace=True)
    elif row["src_name"] == "Stanford" or row["dst_name"] == "Stanford":
        df.drop(index, inplace=True)
    elif row["src_name"] == "Frankfurt" or row["dst_name"] == "Frankfurt":
        df.drop(index, inplace=True)
    elif row["src_name"] == "Tencent Beijing" or row["dst_name"] == "Tencent Beijing":
        df.drop(index, inplace=True)

df["inside"] = False
# Drop rows going outside in
for index, row in df.iterrows():
    if row["src"] in outside_ips:
        if row["dst_name"] != "Guangzhou" and row["dst_name"] != "Beijing 2" and row["dst_name"] != "Beijing 1":
            df.drop(index, inplace=True)
        else:
            df.at[index, "inside"] = True

df.sort_values(by=["inside", "Source -> Destination"], inplace=True)

# Capture the sorted order of 'Source -> Destination'
sorted_order = df["Source -> Destination"].unique()


df.sort_values(by=["Experiment"], inplace=True)
exp_order = df["Experiment"].unique()

# Pivot table with experiments as columns and src-dst as rows
pivot_table = df.pivot_table(
    index="Source -> Destination", columns="Experiment", values="success_rate", aggfunc="first"
)
# Reorder the pivot table index to match the sorted order
pivot_table = pivot_table.reindex(sorted_order)


plt.figure(figsize=(1*TEXTWIDTH, 0.75 * TEXTWIDTH))
ax = sns.heatmap(pivot_table, annot=True, fmt=".0f", cmap="RdYlGn", cbar=False, cbar_kws={'label': 'Success Rate (%)'})
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x + 1)}'))
plt.title("Success Rate (%) of QUIC-like Payloads per Source -> Destination Pair", loc="right")
plt.xlabel("Payload Number")
plt.ylabel("Source -> Destination")
plt.tight_layout()
plt.savefig("quic_parse_heatmap.pdf")
