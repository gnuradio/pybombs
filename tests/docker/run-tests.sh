#!/bin/bash

function do_docker_build() {
	cp ../../dist/* $1
        docker build -t pybombs_$1 $1
	local retval=$?
	rm $1/PyBOMBS*
	echo $retval
}

do_full_test=""
container=""
for arg in "$@"; do
    if [[ $arg == "--full" ]]; then
        do_full_test="yes"
    elif [[ $arg =~ "--container="(.+) ]]; then
        container=${BASH_REMATCH[1]}
    fi
done

if [ "$do_full_test" == "yes" ]; then
	echo "Testing all containers..."
	CONTAINERS=`ls | grep -v run`
	echo $CONTAINERS
	for i in $CONTAINERS
	do
		if do_docker_build $i; then
			echo "==== SUCCESS! ===="
		else
			exit 1
		fi
	done
	exit 0
fi

if [ -z $container ]; then
	exit 0
fi

echo "Testing container ${container}..."
do_docker_build $container

