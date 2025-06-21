PYTHON = python3

ALL = \
	quic_parse_heatmap.pdf \

.PHONY: all
all: $(ALL)

quic_parse_heatmap.pdf: parser.py results.txt
	$(PYTHON) $^

.PHONY: clean
clean:
	rm -f $(ALL)

.DELETE_ON_ERROR: