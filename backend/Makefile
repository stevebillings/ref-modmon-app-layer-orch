all: check test


check:
	mypy --strict --explicit-package-bases application domain infrastructure

test:
	python -m pytest
