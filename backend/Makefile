all: check test


check:
	mypy --strict --explicit-package-bases application domain infrastructure
	lint-imports

test:
	python -m pytest
