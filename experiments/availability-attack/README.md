# Availability Attack using GFW's QUIC SNI-based Censorship

## Description

The GFW's implementation of QUIC SNI-based censorship can be exploited by an attacker to block UDP traffic between arbitrary hosts—one in China and another outside the country.

To execute this attack, an attacker sends a UDP datagram to the target IP and port,
spoofing the source IP to that of an intended victim.
This datagram contains a QUIC Client Initial packet with a blocked SNI.
A single such packet is sufficient to trigger the GFW's 180-second residual censorship.

While the GFW's trigger mechanism was previously bi-directional (allowing attackers outside China to initiate the block), it changed on March 13, 2025. GFW's QUIC SNI-based censorship is now only triggered by traffic outbound from China.
Nevertheless, it still allows the attack to be conducted from any host in China without egress filtering. (see the "Ethics Considerations" section for a detailed discussion).

## Usage

`send_udp.sh` - An example application to send benign data via UDP to
a server.
`spoof.py` - The attack script, sends a UDP datagram with a source IP set
to that of the victim with a payload known to trigger QUIC SNI censorship.
