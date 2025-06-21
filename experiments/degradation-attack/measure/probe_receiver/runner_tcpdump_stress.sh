#!/bin/bash

full_date=$(date +%F_%H-%M)
dir=/root/abal/China_QUIC/"$full_date"_stress_quic
mkdir $dir
cd $dir

timeout 900 tcpdump -n host 8.147.0.0 and udp -w cap_stress_quic.pcap
