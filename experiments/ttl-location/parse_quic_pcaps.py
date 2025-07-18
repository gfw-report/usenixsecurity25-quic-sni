#!/usr/bin/env python3
"""
parse_quic_pcaps.py
==============

Scan a pcap for **gaps of > 3 minutes** between consecutive frames and
dump each surrounding pair:

Usage
-----
    python parse_quic_pcaps.py -f beijing-ttl_anon.pcap
"""

import argparse
import sys
from scapy.all import PcapReader, raw  # type: ignore

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------
MIN_GAP      = 180     # seconds (3 min)
MAX_GAP      = 1000     # seconds
HEADER_SKIP  = 42      # bytes to skip from start of frame (Ether+IP+UDP)
TRIM_BYTES   = 5       # bytes to drop from the tail
LINE_WIDTH   = 16      # bytes per line for hex / ASCII
# ---------------------------------------------------------------------------


def ascii_only(data: bytes, width: int = LINE_WIDTH) -> str:
    """Printable ASCII, dots for others, wrapped every <width> chars."""
    s = "".join(chr(b) if 32 <= b <= 126 else "." for b in data)
    return "\n".join(s[i:i + width] for i in range(0, len(s), width)) or "[empty payload]"


def hex_bytes(data: bytes, width: int = LINE_WIDTH) -> str:
    """Hex pairs separated by spaces, wrapped every <width> bytes."""
    return (
        "\n".join(
            " ".join(f"{b:02x}" for b in data[i:i + width])
            for i in range(0, len(data), width)
        )
        or "[empty payload]"
    )


def extract_payload(packet: bytes) -> bytes:
    """Return payload[HEADER_SKIP : -TRIM_BYTES], guarding against short frames."""
    if len(packet) <= HEADER_SKIP + TRIM_BYTES:
        return b""
    return packet[HEADER_SKIP:-TRIM_BYTES]


def main(pcap_file: str) -> None:
    reader = PcapReader(pcap_file)

    prev_pkt = prev_idx = prev_rel_time = first_time = None

    results = []
    for idx, pkt in enumerate(reader, start=1):
        if first_time is None:
            first_time = pkt.time
        rel_time = pkt.time - first_time

        # ---------------- gap detection ----------------
        if prev_pkt is not None:
            gap = rel_time - prev_rel_time
            if MIN_GAP <= gap < MAX_GAP:
                prev_payload = extract_payload(raw(prev_pkt))
                cur_payload  = extract_payload(raw(pkt))

                # We do not use any gaps between subequent runs (20 iterations == 1 run)
                if 'Experiment 20' in ascii_only(prev_payload) or 'Experiment' not in ascii_only(prev_payload):
                    continue

                # print("=" * 72)
                # print(">>> GAP DETECTED <<<")
                # print(f"  Current Packet Number : {idx}")
                # print(f"  Previous Packet Number: {prev_idx}")
                # print(f"  Exact Time Gap       : {gap:.6f} seconds\n")

                # ---- previous packet ----
                # print(f"--- HEX payload for PREVIOUS Packet ({prev_idx}) ---")
                # print(hex_bytes(prev_payload))
                # print(f"\n--- ASCII payload for PREVIOUS Packet ({prev_idx}) ---")
                # print(ascii_only(prev_payload))

                results.append(ascii_only(prev_payload))

                # print()

                # # ---- current packet ----
                # print(f"--- HEX payload for CURRENT Packet ({idx}) ---")
                # print(hex_bytes(cur_payload))
                # print(f"\n--- ASCII payload for CURRENT Packet ({idx}) ---")
                # print(ascii_only(cur_payload))
                # print()

        # Slide window
        prev_pkt, prev_idx, prev_rel_time = pkt, idx, rel_time

    reader.close()
    last_seen_hop = min(int("".join(c for c in x if c.isdigit())) for x in results)


    # print(last_seen_hop)
    print("Blocking Hop", last_seen_hop+1)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Find > 3 minute gaps in a pcap and dump payload bytes "
            f"(skip first {HEADER_SKIP}, trim last {TRIM_BYTES})."
        )
    )
    parser.add_argument("-f", "--file", required=True, help="PCAP file to scan")
    args = parser.parse_args()

    try:
        main(args.file)
    except KeyboardInterrupt:
        sys.exit("\nInterrupted by user")
