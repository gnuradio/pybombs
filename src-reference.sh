#!/bin/bash

#
# This file is part of PyBOMBS
#
# PyBOMBS is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# PyBOMBS is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyBOMBS; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

C="src-reference"

if [ $# -ne 0 ] ; then
	echo "Usage: $0"
	echo ""
	echo "This script will use the contents of the src/ directory"
	echo "to create a reference repository in $C"
	echo ""
	echo "This reference will then be used to as the base for future"
	echo "source checkouts, reducing network load and time to fetch."
	echo ""
	echo "It may be re-run to update the reference."
	exit 1
fi

if [ -d $C ] ; then
	echo "NOTICE: cache directory exists. Assuming you want to update it."
elif [ -e $C ] ; then
	echo "ERROR: unexpected $C - remove it and try again"
	exit 1
else
	mkdir $C
fi

cd $C
# extract all the git projects and urls from current source directory
for g in ../src/*/.git ; do
	# XXX figure out if I can clone the repos from the source dir
	PROJECT=$(echo "$g" | sed -e 's,.*/\([^/]*\)/.git,\1,')
	REPO=$(git --git-dir="$g" remote -v | sed -re 's,.*\s((http|git).*)\s.*,\1,' | sort -u)
	git remote add $PROJECT $REPO
done

# check out all the sources
git remote update -p
cd ..

#add the new reference directory to the config
if [ -f config.dat ] ; then
	if ! grep -q "gitoptions.*--reference" config.dat ; then
		sed -i.old -re "s,(gitoptions.*),\1 --reference='${PWD}/$C'," config.dat
	fi
fi
