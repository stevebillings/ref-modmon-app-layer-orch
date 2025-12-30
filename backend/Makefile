all: check test


check:
	mypy --explicit-package-bases application domain infrastructure

test:
	python -m pytest
