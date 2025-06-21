### Tested on Jan 13 2025

```
# Decompress data file:
xz -d tranco_domains_supporting_quic_results.txt.xz

# Count total domains:
wc -l tranco_domains_supporting_quic_results.txt

# Count all supporting quic:
grep true tranco_domains_supporting_quic_results.txt | sort -u | wc -l

# Count all blocked via QUIC
cat ../daily_blocklist/* | sort -u | wc -l

# Count all blocked via QUIC and support QUIC
comm -12 <(cat ../daily_blocklist/* | sort -u) <(grep "true$" tranco_domains_supporting_quic_results.txt | cut -d, -f1| sort -u) | wc -l

```


