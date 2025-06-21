#!/bin/bash

# Enable debugging and stop on error
set -xe

# Navigate to the script's directory
cd "$(dirname "$0")" || exit 1

# Get the current datetime in UTC
datetime=$(date -u "+%Y-%m-%d-%H-%M")

# Set the LD_LIBRARY_PATH
export LD_LIBRARY_PATH="/home/gerryw/dpdk/dpdk-21.08/lib/x86_64-linux-gnu"

# Execute the command with proper logging
binary="./target/release/tuple_count"
config_file="configs/online.toml"
output_file="tuple-count-${datetime}.jsonl"

if [[ -x "$binary" ]]; then
    "$binary" --config "$config_file" --outfile "$output_file"
else
    echo "Error: Binary $binary not found or not executable"
    exit 1
fi
