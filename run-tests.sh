#!/bin/bash
set -e # Exit as soon as any command returns non-zero exit codes

do_pylint="yes"
for arg in "$@"; do
    if [[ $arg == "--skip-pylint" ]]; then
        echo "Skipping PyLint."
        do_pylint=""
    fi
done


if [[ $do_pylint == "yes" ]]; then
	echo "Running static code analysis (PyLint)..."
	pylint -E pybombs \
		--disable=maybe-no-member \
		--disable=no-member
fi

echo "Building source distribution package (sdist)..."
python setup.py -q sdist

(cd tests && ./run-tests.sh $*)
