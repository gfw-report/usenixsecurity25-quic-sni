#!/bin/bash

./measure -src 172.16.0.0 -sleep 100000000 -vp 142.93.0.0 -base-net 35.6.0.0 -simultaneous -sim-threads-sleep 1000000 -simprobes-data-pkts 100 -simprobes-end 2000 -simprobes-start 1000 -simsleep-quic 1000000 -sim-threads 5 -simsleep 1000

