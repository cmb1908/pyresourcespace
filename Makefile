.PHONY: requirements-dev requirements

requirements:
	pip install -r requirements.txt

requirements-dev: requirements
	pip install -r requirements-dev.txt
