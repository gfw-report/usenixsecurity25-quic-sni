#!/usr/bin/env python3
import glob
import datetime
import pandas as pd
import os

blocklist_dir = "daily_blocklist"

pattern = os.path.join(blocklist_dir, "*_blocklist.txt")

all_data = []

for filename in glob.glob(pattern):
    base = os.path.basename(filename)  # get filename without path
    date_str = base.split("_")[0]
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        continue

    iso_year, iso_week, _ = dt.isocalendar()

    df = pd.read_csv(filename, header=None, names=['domain'], dtype=str)
    df = df[df['domain'].notna() & (df['domain'] != '')].copy()

    df['year'] = iso_year
    df['week'] = iso_week

    all_data.append(df)

if not all_data:
    print("No blocklist files found.")
    exit()

# Combine all data into a single DataFrame
data = pd.concat(all_data, ignore_index=True)

# Drop duplicates by year, week, and domain
data = data.drop_duplicates(subset=['year', 'week', 'domain'])

# Group by year and week to count unique domains
weekly_grouped = data.groupby(['year', 'week'])['domain'].apply(set).reset_index()
weekly_grouped.rename(columns={'domain': 'domains'}, inplace=True)

# Sort by year and week
weekly_grouped = weekly_grouped.sort_values(by=['year', 'week']).reset_index(drop=True)

# Calculate added and removed domains
weekly_grouped['added_domains'] = weekly_grouped['domains'] \
        .combine(
            weekly_grouped['domains'].shift(1), 
            lambda curr_set, prev_set: len(curr_set - prev_set) if prev_set is not None else len(curr_set)
        )
    
# Calculate domains removed compared to the previous period
weekly_grouped['removed_domains'] = weekly_grouped['domains'] \
        .combine(
            weekly_grouped['domains'].shift(1), 
            lambda curr_set, prev_set: len(prev_set - curr_set) if prev_set is not None else 0
        )

# Handle the first week separately
if not weekly_grouped.empty:
    weekly_grouped.loc[0, 'added_domains'] = 0
    weekly_grouped.loc[0, 'removed_domains'] = 0

# Calculate the count of unique domains per week
weekly_grouped['unique_domains'] = weekly_grouped['domains'].apply(len)

# Add a Week column for formatted year-week
weekly_grouped['Week'] = weekly_grouped.apply(lambda row: f"{int(row['year'])}-W{int(row['week']):02}", axis=1)

# Prepare final output DataFrame
output_df = weekly_grouped[['Week', 'unique_domains', 'added_domains', 'removed_domains']].copy()

# Save the result to a CSV file
output_csv_path = "aggregated_weekly.csv"
output_df.to_csv(output_csv_path, index=False)

print(f"Aggregated weekly data with changes saved to {output_csv_path}")
