#
# A corrected version of the user's Makefile
#

# --- Configuration ---
# Set the main .tex file name (without the .tex extension)
TARGET := usenix25

# List all .tex source files. The PDF build will be triggered if any of these change.
TEX_SOURCES := \
    $(TARGET).tex \
    $(TARGET)-ae.tex

# List all your figure files here. This is important for the 'clean' rule.
# For example: FIGURES := fig/flowchart.eps fig/graph.pdf
FIGURES :=

# --- Targets ---

# The default target, executed when you just run 'make'
.PHONY: all
all: $(TARGET).pdf

# Rule for building the PDF
# This sequence (pdflatex -> bibtex -> pdflatex -> pdflatex) is required
# to correctly resolve citations and references.
$(TARGET).pdf: $(TEX_SOURCES)
	pdflatex $(TARGET).tex
	pdflatex $(TARGET).tex
	pdflatex $(TARGET).tex


.PHONY: clean
clean:
	rm -fv *.aux *.log *~ *.bbl *.toc *.out 
	rm -fv $(TARGET).pdf