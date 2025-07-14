# Exposing and Circumventing SNI-based QUIC Censorship of the Great Firewall of China

This repository contains the source code, experiment data and documentation for the paper: [*Exposing and Circumventing SNI-based QUIC Censorship of the Great Firewall of China*](https://gfw.report/publications/usenixsecurity25/en/) (USENIX Security 2025).

It is intended for two purposes:
1. To enable reproducibility of all figures and results presented in the paper.
2. To facilitate independent verification of our claims regarding the GFW's QUIC-SNI blocking.

## Repository Structure
The repository is structured as follows:
```
.
├── ae-appendix
├── experiments
│   ├── availability-attack
│   ├── diurnal-blocking
│   ├── flow-tracking-time
│   ├── how-fast-gfw-blocks
│   ├── network-tap
│   ├── overlap-between-blocklists
│   ├── rule-srcport-greater-than-dst-port
│   ├── sni-blocklist
│   ├── degradation-attack
│   ├── ttl-location
│   └── what-triggers-blocking
└── utils
    ├── quic-packet-builder
    ├── quic-sni-sender
    └── server-parser
```
* `ae-appendix`: contains the materials for the artifact evaluation appendix.
* `experiments`: Each subdirectory in this folder corresponds to a specific experiment or analysis conducted in the paper.
* `utils`: Contains common scripts used across experiments.


## Reproducing Paper Resources
To reproduce the figures and data presented in the paper, follow these instructions:

First, set up your Python environment:
```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

Each figure in the paper can be reproduced individually via the `make` command in their respective experiment directories.
The table below lists the figures and the command to produce them. The commands are to be executed in the `experiments` directory.

| Section | Figure | Command | Output file |
|--- |--- |--- |---
| 3.2 GFW's Blocking Latency | Figure 2 & 10 | `cd how-fast-gfw-blocks; make clean; make` |  `how-fast-the-gfw-blocks.pdf`, `how-fast-the-gfw-blocks-boxplot.pdf`
| 3.3 Blocking Rule: Source Port >= Destination Port | Figure 3 & 11 | `cd rule-srcport-greater-than-dst-port; make clean; make` | `heatmap-ports-401-450-step-1_heatmap.pdf`, `heatmap-ports-1-65000-step-1000_heatmap.pdf`
| 3.4 Diurnal Blocking Pattern | Figure 4 | `cd diurnal-blocking; make clean; make` | `diurnal-timeseries-three-sources.pdf`
| 3.6 Parsing Idiosyncrasies | Figure 5 | `cd what-triggers-blocking; make clean; make`| `quic_parse_heatmap.pdf`
| 4. Monitoring the Blocklist over Time | Figure 6 | `cd sni-blocklist; make clean; make`| `domains-blocked-over-quic-weekly.pdf`
| 4.1. Comparison with Other Blocklists | Figure 7 |  `cd overlap-between-blocklists; make clean; make` | `venn-intersection-between-lists.pdf`
| 5. GFW Degradation Attack | Figure 8 | `cd degradation-attack/Figure_8_experiments/AVG_exp23-22-20_sensitive-stressing_and_exp25-26-27_random-stressing; make clean; make` | `stressing_rates.eps`|


The data files for each table in the paper are listed below:

| Table | Data sources                                                                                                                                             | Command |
| :---: | :------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------------------- |
| **1** | `./network-tap/data/tuple-count-2025-01-22-16-00.statistics-quic-conn.txt`,`./network-tap/data/tuple-count-2025-01-22-16-00.statistics-udp-pkt.txt`      | —                        |
| **2** | `./ttl-location/data/DNS/{city}-dns-and-traceroute-result.txt`,`./ttl-location/data/QUIC/{city}-ttl_anon.pcap`                                                                                           | —                        |
| **3** | `./what-triggers-blocking/payloads`, `./what-triggers-blocking/results.txt`                                                                              | —                        |
| **4** | `./sni-blocklist/`                                                                                                                                       | `make clean && make`       |
| **5** | `./overlap-between-blocklists`                                                                                                                           | `make clean && make` |
| **6** | `./availability-attack/data/ec2/`                                                                                                                        | `make clean && make`     |


## Running Experiments
Running experiments requires at least two servers: one located in China and one outside of China. For USENIX artifact reviewers, we provide the necessary servers to conduct these experiments listed below. If you are not a reviewer, you will have to set up your own machines.


| SSH Hostname                              | Location                              | ASN     | CPU Model                | # Core(s) | RAM  | OS                                                      |
|---------------------------------------|---------------------------------------|---------|--------------------------|-----------|------|---------------------------------------------------------|
| usenix-ae-cn | Tencent Cloud Guangzhou Datacenter | AS45090 | Intel(R) Xeon(R) Platinum 8255C CPU @ 2.50GHz | 1 | 2GB  | Ubuntu 22.04 LTS (GNU/Linux 5.15.0-139-generic x86_64)   |
| usenix-ae-us | AWS Oregon | AS16509 | Intel(R) Xeon(R) CPU E5-2686 v4 @ 2.30GHz | 1 | 2GB | Ubuntu 22.04 LTS (GNU/Linux 6.8.0-1024-aws x86_64) |


## Setup:
To set up the machines, navigate to the `utils` directory and run `make` (requires `Docker`). This will compile the necessary tools and copy them to the servers. Additionally, `iptables` rule will be configured on the server to block outgoing ICMP packets to the client. To add the rule manually, use the following command on usenix-ae-us machine:

```bash
iptables -A OUTPUT -p icmp -d $USENIX_AE_CN -j DROP
```

Once the setup is complete, you can proceed with the following experiments:

### Experiment 1: Testing QUIC SNI-based blocking

* Using `quic-sni-sender`:
The `make` command executed in the `utils` folder transfers the `quic-sni-sender` and `server-parser` binaries to both the client (usenix-ae-cn) and server (usenix-ae-us).

On the server (usenix-ae-us), run:
```bash
sudo tcpdump udp and host $USENIX_AE_CN -Uw - | ./server-parser
```

On the client (usenix-ae-cn), run the following command to send a QUIC probe. This probe consists of a Client Initial packet, followed by a 5 second delay, and then subsequent 10-byte UDP payloads.

```bash
echo google.com | ./quic-sni-sender  -p 443 --socket-pool-size 1 --dip=$USENIX_AE_US --sport=55000

# Note: Other SNIs that trigger blocking include cloudflare-dns.com and youtube.com.
```

Wait for 10 seconds to see output on the server:
```
# 2025/06/04 03:01:34 Started parsing: /dev/stdin
# tcpdump: listening on eth0, link-type EN10MB (Ethernet), snapshot length 262144 bytes
# 2025-06-04T03:02:08Z,{usenix-ae-cn_IP_ADDRESS},{usenix-ae-us_IP_ADDRESS},55001,4437,google.com,true
```
The `true` value in the last column indicates that blocking was triggered for the SNI google.com. Similarly, test other SNI values like `baidu.com` (to verify behavior for exempt domains) and `cloudflare-dns.com, youtube.com` (to verify blocking for other domains).


* Using `netcat` (alternative method):

On the server:
Capture any udp packets from the client using `tcpdump`:

```bash
sudo tcpdump udp and host $USENIX_AE_CN
```

On the client:
```bash
echo "c1000000010000004055f5de2bedfa3f92b1b6c9566bb0fdd4cd655379bc549f9383046e110d3ec5af79f977950f7357c9af27587d2ca63da6f931afd48e211cbbb364d99a3363d60e23bbf8064b36e7294572c4a210e895c752cadc168441" | xxd -r -p | nc -u -q 0 -p 60001 $USENIX_AE_US 444
```
This payload is a truncated QUIC packet with the SNI set to `google.com`. After a few seconds, attempt to send it again. If no subsequent packets are received on the server, it indicates successful triggering of the GFW's QUIC SNI-based blocking.

### Experiment 2: Testing Rule: SourcePort > Destination Port
This experiment tests the GFW's blocking rule that blocks QUIC packets where the source port is greater than the destination port.

On the client (usenix-ae-cn), run the following commands and observe the output on the server (usenix-ae-us):

```bash
# Source port (4000) < Destination port (5000) -> NOT BLOCKED
echo google.com | ./quic-sni-sender  -p 5000 --socket-pool-size 1  --dip=$USENIX_AE_US --followup-payloads=10 --bind-ip=0.0.0.0 --sport=4000 --no-use-greater-srcports


# Source port (65000) > Destination port (443) -> BLOCKED
echo google.com | ./quic-sni-sender  -p 443 --socket-pool-size 1  --dip=$USENIX_AE_US --followup-payloads=10 --bind-ip=0.0.0.0 --sport=65000
```


### Experiment 3: Testing QUIC Payloads (listed in Table 3 of the paper)

This experiment evaluates the GFW's blocking behavior based on various QUIC payloads as detailed in Table 3 of the paper.
The payloads can be generated using the `quic-packet-builder` utility in the `utils` directory.

On the client (usenix-ae-cn), run the following commands using the payloads [here](./experiments/what-triggers-blocking/payloads/).
```
# For each payload, run the following command:
nc -u -q 0 -p 60001 $USENIX_AE_US 444 < exp1.bin
```

| Payload No. | Description | Blocked? | Payload |
|:-------:|-------------|:--------:|:---------:|
| 1 | One‑byte QUIC packet number. | ✓ | [link](./experiments/what-triggers-blocking/payloads/exp1.bin) |
| 2 | Remove last byte from QUIC packet. | ✗ | [link](./experiments/what-triggers-blocking/payloads/exp3.bin) |
| 3 | Bad Version Number with incorrect tag. Version Number: `0x00000002` | ✗ | [link](./experiments/what-triggers-blocking/payloads/exp4.bin) |
| 4 | Both connection IDs have a length of `0x0`. | ✓ | [link](./experiments/what-triggers-blocking/payloads/exp8.bin) |
| 5 | Source connection ID has a length of `0x255`. | ✗ | [link](./experiments/what-triggers-blocking/payloads/exp9.bin) |
| 6 | `CRYPTO` frame has a length of `0x00` but still contains a payload. | ✓ | [link](./experiments/what-triggers-blocking/payloads/exp10.bin) |
| 7 | Sensitive domain in an extension other than the SNI extension. In this case, ALPN contains `google.com`. | ✗ | [link](./experiments/what-triggers-blocking/payloads/exp11.bin) |
| 8 | A QUIC packet with a payload containing a single `CRYPTO` frame along with multiple `PING` and `PADDING` frames. | ✗ | [link](./experiments/what-triggers-blocking/payloads/exp13.bin) |
| 9 | A QUIC Initial packet whose TLS Client Hello contained an Encrypted Client Hello extension with an outer SNI of `cloudflare-ech.com`. | ✗ | [link](./experiments/what-triggers-blocking/payloads/exp14.bin) |
| 10 | A QUIC Version 2 packet. | ✗ | [link](./experiments/what-triggers-blocking/payloads/exp16.bin) |



### Experiment 4: Random Payload Before Client Initial Bypasses Blocking

This experiment shows how sending a random UDP payload before the Client Initial packet can bypass the GFW's blocking.

On the client (usenix-ae-cn), run the following commands:

```bash
# Send an arbitrary UDP payload to the server
echo "0000000000000000000000000000" | xxd -r -p | nc -u -q 0 -p 65535 $USENIX_AE_US 6126
```

Wait a few seconds and then send the QUIC packet containing a forbidden SNI (google.com in this example):
```bash
echo "c1000000010000004055f5de2bedfa3f92b1b6c9566bb0fdd4cd655379bc549f9383046e110d3ec5af79f977950f7357c9af27587d2ca63da6f931afd48e211cbbb364d99a3363d60e23bbf8064b36e7294572c4a210e895c752cadc168441" | xxd -r -p | nc -u -q 0 -p 65535 $USENIX_AE_US 6126
```

Successful receipt of all subsequent packets on the 4-tuple <src_ip, 65535, dst_ip, 6126> by the server confirms the bypass.
