from scapy.all import *
import sys

for pkt in PcapReader(sys.argv[1]):
    if pkt.haslayer(IP) and pkt.haslayer(UDP):
        if pkt[IP].dst == "142.93.0.0":
            print(pkt[UDP].sport)
