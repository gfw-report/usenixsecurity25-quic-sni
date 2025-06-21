PYTHON = python3

ALL = \
	diurnal-timeseries-three-sources.pdf \

.PHONY: all
all: $(ALL)

diurnal-timeseries-three-sources.pdf: plot.py ./data/2-weeks-beijing.csv ./data/2-weeks-shanghai.csv ./data/2-weeks-guangzhou.csv
	$(PYTHON) $^ --out "$@" --no-show

.PHONY: clean
clean:
	rm -f $(ALL)

.DELETE_ON_ERROR: