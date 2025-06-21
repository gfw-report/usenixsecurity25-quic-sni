# Makefile for running Gnuplot on plot.gnu

GNUPLOT := gnuplot
SCRIPT   := plot.gnu

all: plot

plot: $(SCRIPT)
	$(GNUPLOT) $(SCRIPT)

.PHONY: clean
clean:
	rm -f *.eps