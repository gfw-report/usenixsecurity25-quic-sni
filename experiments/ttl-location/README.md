
```check-dns.py```

* Sends DNS A queries for google.com to the target IP, incrementing IP TTL in each iteration until an injection is detected.

```check-quic.py```

* Sends QUIC Initial (sni=google.com) packets every 5 seconds with increasing TTL values to the target IP. After each QUIC Initial, it sends UDP payloads with a fixed TTL value (64).

To identify the blocking hop for DNS, examine the TTL values within the DNS injection results. These results are located in files corresponding to each city, found at ```./data/DNS/<city>-dns-and-traceroute-result.txt```. The blocking hop is indicated by the TTL value from which a DNS injection is first observed.

To identify the blocking hop for QUIC, run:

```bash
python3 parse_quic_pcaps.py -f ./data/QUIC/<city>-ttl_anon.pcap
```
