#!/bin/bash
echo "Running static code analysis..."
pylint -E pybombs \
	--disable=maybe-no-member \
	--disable=no-member \
	|| exit 1
