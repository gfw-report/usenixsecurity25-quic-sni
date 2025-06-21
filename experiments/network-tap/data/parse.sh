#!/bin/bash


jq -r '.parsed_tuple_conns.quic | to_entries[] | "\(.key),\(.value.tuple)"' tuple-count-2024-11-19-08-05.jsonl | sort -n -r -t, -k2,2 > tuple-count-2024-11-19-08-05.csv
awk -F',' '{sum += $2} END {print sum}' tuple-count-2024-11-19-08-05.csv
jq . < tuple-count-2024-11-19-08-05.jsonl | grep quic
