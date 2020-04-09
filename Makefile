all:

install:
	python setup.py develop

test:
	pytest

profile:
	python -m cProfile -s tottime -o profile.prof -m sliceofpy.cli tests/ring.obj

clean:
	rm -rf .pytest_cache *.egg-info **/__pycache__/

# Can avoid phony rules breaking when a real file has the same name by
.PHONY: all clean install test profile
