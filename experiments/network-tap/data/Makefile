# Python interpreter
PYTHON=python3

# Define variables
JSONL_FILES := $(wildcard *.jsonl)
QUIC_CONN_CSV_FILES := $(JSONL_FILES:.jsonl=.quic-conn.csv)
UDP_PKT_CSV_FILES := $(JSONL_FILES:.jsonl=.udp-pkt.csv)
QUIC_CONN_HEATMAP_FILES := $(JSONL_FILES:.jsonl=.heatmap-quic-conn.png) $(JSONL_FILES:.jsonl=.heatmap-quic-conn.pdf)
UDP_PKT_HEATMAP_FILES := $(JSONL_FILES:.jsonl=.heatmap-udp-pkt.png) $(JSONL_FILES:.jsonl=.heatmap-udp-pkt.pdf)
QUIC_CONN_STATS_FILES := $(JSONL_FILES:.jsonl=.statistics-quic-conn.txt)
UDP_PKT_STATS_FILES := $(JSONL_FILES:.jsonl=.statistics-udp-pkt.txt)

# Default target
ALL: \
	$(QUIC_CONN_CSV_FILES) \
	$(UDP_PKT_CSV_FILES) \
	$(QUIC_CONN_HEATMAP_FILES) \
	$(UDP_PKT_HEATMAP_FILES) \
	$(QUIC_CONN_STATS_FILES) \
	$(UDP_PKT_STATS_FILES)

debug:
	@echo "JSONL_FILES: $(JSONL_FILES)"
	@echo "QUIC_CONN_CSV_FILES: $(QUIC_CONN_CSV_FILES)"
	@echo "UDP_PKT_CSV_FILES: $(UDP_PKT_CSV_FILES)"
	@echo "QUIC_CONN_HEATMAP_FILES: $(QUIC_CONN_HEATMAP_FILES)"
	@echo "UDP_PKT_HEATMAP_FILES: $(UDP_PKT_HEATMAP_FILES)"
	@echo "QUIC_CONN_STATS_FILES: $(QUIC_CONN_STATS_FILES)"
	@echo "UDP_PKT_STATS_FILES: $(UDP_PKT_STATS_FILES)"

# Rule to generate .quic-conn.csv from .jsonl
%.quic-conn.csv: %.jsonl
	@echo "Processing $< to generate $@"
	jq -r '.parsed_tuple_conns.quic | to_entries[] | "\(.key),\(.value.tuple)"' $< \
		| sed 's#:#,#g' \
		| sort -n -r -t, -k3,3 > $@
	@echo "Calculating sum for $@"
	awk -F',' '{sum += $$3} END {print sum}' $@

# Rule to generate .udp-pkt.csv from .jsonl
%.udp-pkt.csv: %.jsonl
	@echo "Processing $< to generate $@"
	jq -r '.udp_tuple_pkts | to_entries[] | "\(.key | split(":")[0]),\(.key | split(":")[1]),\(.value.tuple)"' $< \
		| sed 's#:#,#g' \
		| sort -n -r -t, -k3,3 > $@
	@echo "Calculating sum for $@"
	awk -F',' '{sum += $$3} END {print sum}' $@

# Rules to generate heatmaps from CSV files
# %.heatmap-quic-conn.png: %.quic-conn.csv plot.py
# 	$(PYTHON) plot.py --step 1000 --out "$@" --no-show $<

# %.heatmap-quic-conn.pdf: %.quic-conn.csv plot.py
# 	$(PYTHON) plot.py --step 1000 --out "$@" --no-show $<

# %.heatmap-udp-pkt.png: %.udp-pkt.csv plot.py
# 	$(PYTHON) plot.py --step 1000 --out "$@" --no-show $<

# %.heatmap-udp-pkt.pdf: %.udp-pkt.csv plot.py
# 	$(PYTHON) plot.py --step 1000 --out "$@" --no-show $<

%.statistics-quic-conn.txt: count.py %.quic-conn.csv
	$(PYTHON) $^ > "$@"

%.statistics-udp-pkt.txt: count.py %.udp-pkt.csv
	$(PYTHON) $^ > "$@"

# Clean generated files
clean:
	@echo "Cleaning up generated files"
	rm -f $(QUIC_CONN_CSV_FILES) $(UDP_PKT_CSV_FILES) \
		$(QUIC_CONN_HEATMAP_FILES) $(UDP_PKT_HEATMAP_FILES) \
		$(QUIC_CONN_STATS_FILES) $(UDP_PKT_STATS_FILES)

# Phony targets
.PHONY: all clean
