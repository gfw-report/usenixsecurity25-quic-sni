PYTHON = python3

ALL = \
	heatmap-ports-401-450-step-1_heatmap.pdf \
	heatmap-ports-1-65000-step-1000_heatmap.pdf \

# These are large files that are not checked into the repository.
# Various filtered and reduced versions of them, created by makefile
# rules, are checked in, instead. Marking the source filenames as
# "secondary" means that Make will not insist on the source files being
# present even though they are part of the dependency chain; the
# graph-producing scripts can use the filtered and reduced input files
# directly.
.SECONDARY:

.PHONY: all
all: $(ALL)

heatmap-ports-401-450-step-1_heatmap.pdf: plot.py heatmap-ports-401-450-step-1-date-2024-10-17.csv
	$(PYTHON) $^ --out "$@" --no-show

heatmap-ports-1-65000-step-1000_heatmap.pdf: plot.py heatmap-ports-1-65000-step-1000.csv
	$(PYTHON) $^ --out "$@" --step 1000 --no-show

.PHONY: clean
clean:
	rm -f $(ALL)

.DELETE_ON_ERROR: