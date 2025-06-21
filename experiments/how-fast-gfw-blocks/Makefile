PYTHON = python3

ALL = \
	how-fast-the-gfw-blocks.pdf \
	how-fast-the-gfw-blocks-boxplot.pdf \

# These are large files that are not checked into the repository.
# Various filtered and reduced versions of them, created by makefile
# rules, are checked in, instead. Marking the source filenames as
# "secondary" means that Make will not insist on the source files being
# present even though they are part of the dependency chain; the
# graph-producing scripts can use the filtered and reduced input files
# directly.
.SECONDARY:
	./data/results.csv


.PHONY: all
all: $(ALL)

how-fast-the-gfw-blocks.pdf: plot-ecdf.py ./data/results.csv
	$(PYTHON) $^ --out "$@" --no-show

how-fast-the-gfw-blocks-boxplot.pdf: plot-boxplot.py ./data/results.csv
	$(PYTHON) $^ --out "$@" --no-show



.PHONY: clean
clean:
	rm -f $(ALL)

.DELETE_ON_ERROR: