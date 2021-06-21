XARGS := xargs -0 $(shell test $$(uname) = Linux && echo -r)
GREP_T_FLAG := $(shell test $$(uname) = Linux && echo -T)
BLACK_INSTALLED := $(shell python -m black --version 2>/dev/null)

all:
	@echo "\nThere is no default Makefile target right now. Try:\n"
	@echo "make clean - reset the project and remove auto-generated assets."
	@echo "make pyflakes - run the PyFlakes code checker."
	@echo "make pep8 - run the PEP8 style checker."
	@echo "make test - run the test suite."
	@echo "make coverage - view a report on test coverage."
	@echo "make check - run all the checkers and tests."
	@echo "make package - create a deployable package for the project."
	@echo "make rpm - create an rpm package for the project."
	@echo "make publish - publish the project to PyPI."
	@echo "make docs - run sphinx to create project documentation.\n"

clean:
	rm -rf build
	rm -rf dist
	rm -rf uflash.egg-info
	rm -rf .coverage
	rm -rf .tox
	rm -rf docs/_build
	rm -f tests/example.hex
	rm -rf deb_dist
	rm -f uflash-*.tar.gz
	find . \( -name '*.py[co]' -o -name dropin.cache \) -print0 | $(XARGS) rm
	find . \( -name '*.bak' -o -name dropin.cache \) -print0 | $(XARGS) rm
	find . \( -name '*.tgz' -o -name dropin.cache \) -print0 | $(XARGS) rm

pyflakes:
	find . \( -name _build -o -name var -o -path ./docs \) -type d -prune -o -name '*.py' -print0 | $(XARGS) pyflakes

pep8: clean
	find . \( -name _build -o -name var \) -type d -prune -o -name '*.py' -print0 | $(XARGS) -n 1 pycodestyle --repeat --exclude=build/*,docs/* --ignore=E731,E402,W504,W503,E203

test: clean
	py.test

coverage: clean
	py.test --cov-report term-missing --cov=uflash tests/

tidy:
ifdef BLACK_INSTALLED
	python -m black -l79 .
else
	@echo Black not present
endif

black:
ifdef BLACK_INSTALLED
	python -m black --check -l79 .
else
	@echo Black not present
endif

check: clean pep8 pyflakes black coverage

package: check
	python setup.py sdist

rpm: check
	python setup.py bdist_rpm

publish: check
	@echo "\nChecks pass, good to publish..."
	python setup.py sdist upload

docs: clean
	$(MAKE) -C docs html
	@echo "\nDocumentation can be found here:"
	@echo file://`pwd`/docs/_build/html/index.html
	@echo "\n"
