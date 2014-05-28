#!/bin/bash

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
