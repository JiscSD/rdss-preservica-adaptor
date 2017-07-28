PYTHON = python3.6
COVERAGE_MIN = 40

env:
	@python3 -m venv env

install:
	@pip install -e .

uninstall:
	cd ..; $(PYTHON) -m pip uninstall -y -v $(shell basename $(PWD))

name:
	@echo $(shell basename $(PWD))

deps-update:
	@pip install -r requirements-to-freeze.txt --upgrade
	@pip freeze > requirements.txt

deps:
	@pip install -r requirements.txt
	@pre-commit install

clean:
	@pip uninstall -yr requirements.txt
	@pip freeze > requirements.txt

lint:
	@pre-commit run \
		--allow-unstaged-config \
		--all-files \
		--verbose

autopep8:
	@autopep8 . --recursive --in-place --pep8-passes 2000 --verbose

autopep8-stats:
	@pep8 --quiet --statistics .

test:
	@BOTO_CONFIG=/dev/null pytest

coverage:
	@BOTO_CONFIG=/dev/null pytest --cov-fail-under $(COVERAGE_MIN) --cov=preservicaservice tests/

debug:
	@pytest --pdb

.PHONY: install deps lint test* debug clean
