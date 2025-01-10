.PHONY: requirements-dev requirements warehouse-stats

WAREHOUSE_PROJECTS := $(shell python -m pymediaflux.members 1193191)
WAREHOUSE_STATS := $(addsuffix .txt, $(WAREHOUSE_PROJECTS))

requirements:
	pip install -r requirements.txt

requirements-dev: requirements
	pip install -r requirements-dev.txt

stats: $(WAREHOUSE_STATS)

%.txt:
	python -m pymediaflux.stats $* > $@

clean:
	rm -f $(WAREHOUSE_STATS)
