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
    not_censored=$(awk '$2>=95 && $3=="True" {print $0}' $tmpfile | wc -l)
    partially_censored=$(awk '$2<95 && $2>=45 && $3=="True" {print $0}' $tmpfile | wc -l)
    censored_loose=$(awk '$2<45 {print $0}' $tmpfile | wc -l)
    censored_strict=$(awk '$2==1 {print $0}' $tmpfile | wc -l)
    all=$(cat $tmpfile| wc -l)

    #echo $file $not_censored $all | awk '{print $1, fraction_uncensored $2/$3}'
    echo $file $not_censored $all $censored_strict $censored_loose $partially_censored | awk '{print $1, fraction_uncensored $2/$3, censored_strict $4/$3, censored_loose $5/$3, partially_censored $6/$3, all $3}'

done
