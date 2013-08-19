#!/bin/bash
#
# Copyright 2013 Tim O'Shea
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

rm -rf /target
mkdir /target
touch config.dat
echo "[config]" > config.dat
echo "gituser = hudson" >> config.dat
echo "prefix = /target" >> config.dat
echo "satisfy_order = $satisfy_order"  >> config.dat
echo "timeout = 30" >> config.dat
./pybombs inv gr-baz installed           # CMake Error at CMakeLists.txt:135 (message): Gruel required to compile baz
./pybombs inv gr-osmosdr installed      # CMake Error at CMakeLists.txt:123 (message): Gruel required to build gr-osmosdr
./pybombs inv gnss-sdr installed         # CMake Error at CMakeLists.txt:125 (message): Please install GNU Radio and all its dependencies.
./pybombs inv kal installed              # bash: line 2: ./configure: No such file or directory
./pybombs install all
./pybombs env
