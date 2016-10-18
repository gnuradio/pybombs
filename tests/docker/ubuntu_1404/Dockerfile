# Base image
FROM ubuntu:14.04
WORKDIR /pybombs

# Minimal package installation
RUN apt-get update -qq -y
RUN apt-get install -qq -y python-pip

# Install PyBOMBS using setuptools
COPY PyBOMBS*.tar.gz /pybombs
RUN tar zxf *.tar.gz
RUN cd * && python setup.py install -q

# Install something
RUN mkdir /prefix
RUN cd /prefix
RUN pybombs -v recipes add gr-recipes git+https://github.com/gnuradio/gr-recipes.git
RUN pybombs -v prefix init -a default default
RUN pybombs install gr-osmosdr

