#!/bin/bash
#

while true; do timeout 5 bmon -o ascii -p enp1s0 >> /home/aaa/QUIC/bmon_res; date >> /home/aaa/QUIC/bmon_res; done
