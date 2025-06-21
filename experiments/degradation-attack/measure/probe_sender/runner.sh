#!/bin/bash

#tcpdump -n host 142.93.0.0 and udp -w cap.pcap &
#PID=$!

#sleep 3

for i in {1..80}
do 
	timeout 10 ./measure -src 172.16.0.0 -sleep 100000000 -vp 142.93.0.0 -ticks 10 -tick-sleep 0 -dstport $i -base-net 35.6.0.0
done

#sleep 3

#kill $PID
