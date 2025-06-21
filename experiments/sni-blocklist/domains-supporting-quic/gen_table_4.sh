#!/usr/bin/env bash

# Tranco List for QUIC Support was tested on Jan 13 2025.
QUIC_XZ="tranco_domains_supporting_quic_results.txt.xz"
BLOCK_DIR="../daily_blocklist"

total_domains=$(
  xzcat "$QUIC_XZ" | wc -l
)

quic_supporting=$(
  xzcat "$QUIC_XZ" \
    | grep -F "true" \
    | sort -u \
    | wc -l
)

blocked_domains=$(
  cat "$BLOCK_DIR"/* \
    | sort -u \
    | wc -l
)

blocked_and_support=$(
  comm -12 \
       <(cat "$BLOCK_DIR"/* | sort -u) \
       <(xzcat "$QUIC_XZ" \
              | grep "true$" \
              | cut -d',' -f1 \
              | sort -u) \
   | wc -l
)

printf "\n%-28s %s\n" "FQDN" "Count"
printf "%-28s %'d\n" "Total domains"           "$total_domains"
printf "%-28s %'d\n" "Support QUIC "            "$quic_supporting"
printf "%-28s %'d\n" "Blocked via QUIC"        "$blocked_domains"
printf "%-28s %'d\n\n" "Blocked & support QUIC " "$blocked_and_support"
