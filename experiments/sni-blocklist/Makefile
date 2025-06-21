PYTHON = python3

INTERMEDIATE = aggregated_weekly.csv
FINAL_PDF = domains-blocked-over-quic-weekly.pdf
ALL = $(FINAL_PDF)

.PHONY: all clean table4

all: $(ALL) table4

# Rule to create the intermediate CSV from daily blocklist text files
$(INTERMEDIATE): aggregate-weekly.py
	@echo "Generating Weekly CSV file from daily blocklists..."
	$(PYTHON) $^

# Rule to create the final PDF using plot.py and the intermediate CSV
$(FINAL_PDF): plot.py $(INTERMEDIATE)
	$(PYTHON) $^ --out "$@" --no-show

table4: ./domains-supporting-quic/gen_table_4.sh
	@echo "Generating Table 4..."
	cd ./domains-supporting-quic; ./gen_table_4.sh

clean:
	rm -f $(ALL) $(INTERMEDIATE)

.DELETE_ON_ERROR:
