PYTHON = python3

ALL = \
	venn-intersection-between-lists.pdf \

.PHONY: all table5
all: $(ALL) table5

venn-intersection-between-lists.pdf: plot.py ./data/http-blocklist.txt ./data/https-blocklist.txt \
                                      ./data/quic-blocklist.txt ./data/dns-blocklist.txt 
	$(PYTHON) $^ --out "$@" --no-show


table5:
	$(PYTHON) gen_table_5.py

.PHONY: clean
clean:
	rm -f $(ALL)

.DELETE_ON_ERROR: