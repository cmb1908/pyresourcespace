.PHONY: requirements-dev requirements warehouse-stats filters

WAREHOUSE_PROJECTS := $(shell python -m pymediaflux.members 1193191)
WAREHOUSE_STATS := $(addsuffix .txt, $(WAREHOUSE_PROJECTS))

requirements:
	pip install -r requirements.txt

requirements-dev: requirements
	pip install -r requirements-dev.txt

stats: $(WAREHOUSE_STATS)

%.txt:
	python -m pymediaflux.stats $* > $@

filters:
	for f in `find filters -name \*xml -print | grep -v :`; do python -m pymediaflux.replace_filter_namespace $$f; done
	for f in filters/*:*.xml; do python -m pymediaflux.replace_filter $$f; done

clean:
	rm -f $(WAREHOUSE_STATS)
