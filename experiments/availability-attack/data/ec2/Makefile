PYTHON = python3

ALL = \
	ip_density_map.html \
	table_6.txt \


.PHONY: all
all: $(ALL)

ip_density_map.html: density_map.py 
	$(PYTHON) $^ 

table_6.txt: table_gen.py
	$(PYTHON) $^ > $@
.PHONY: clean
clean:
	rm -f $(ALL)

.DELETE_ON_ERROR: