#!/bin/bash
set -e # Exit as soon as any command returns non-zero exit codes
echo "Running static code analysis (PyLint)..."
pylint -E pybombs \
	--disable=maybe-no-member \
	--disable=no-member

echo "Building source distribution package (sdist)..."
python setup.py -q sdist
