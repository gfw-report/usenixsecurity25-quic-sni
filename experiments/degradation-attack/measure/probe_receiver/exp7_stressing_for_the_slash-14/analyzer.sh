#!/bin/bash

if [ $# -eq 0 ]; then
    echo "No arguments provided. Please specify the QUIC Initial payload"
    exit 1
fi

tmpfile=$(mktemp)

# Ensure the temporary file is deleted when the script exits
trap "rm -f $tmpfile" EXIT

for file in 202*
do

    python3 /root/abal/China_QUIC/process_pcap.py -f $file/*.pcap -s 8.147.0.0 -d 142.93.0.0 -p $1 > $tmpfile
    not_censored=$(awk '$2>=855 && $3=="True" {print $0}' $tmpfile | wc -l)
    partially_censored=$(awk '$2<855 && $2>=450 && $3=="True" {print $0}' $tmpfile | wc -l)
    censored_loose=$(awk '$2<450 {print $0}' $tmpfile | wc -l)
    censored_strict=$(awk '$2==1 {print $0}' $tmpfile | wc -l)
    all=$(cat $tmpfile| wc -l)

    #echo $file $not_censored $all | awk '{print $1, fraction_uncensored $2/$3}'
    # fraction_uncensored and other lables won't be printed. They are used for a reference here
    echo $file $not_censored $all $censored_strict $censored_loose $partially_censored | awk '{print $1, fraction_uncensored $2/79, censored_strict $4/79, censored_loose $5/79, partially_censored $6/79, all $3}'

done
