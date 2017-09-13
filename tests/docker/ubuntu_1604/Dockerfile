# Base image
FROM ubuntu:16.04
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
RUN pybombs config elevate_pre_args ''
RUN pybombs -v recipes add-defaults
RUN pybombs -v prefix init -a default default
RUN pybombs install gr-osmosdr

