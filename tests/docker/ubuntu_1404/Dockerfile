# Base image
FROM ubuntu:14.04
WORKDIR /pybombs

# Minimal package installation
RUN DEBIAN_FRONTEND=noninteractive apt-get update -qq -y
RUN DEBIAN_FRONTEND=noninteractive apt-get install -qq -y python-pip
# ruamel.yaml is a bit of a troublemaker. It's a dep of PyBOMBS itself
# (does not get installed by PyBOMBS, but by setup.py), so we'll make sure
# it's available manually. Everything else can cause additional errors.
RUN DEBIAN_FRONTEND=noninteractive apt-get install -qq -y python-dev
RUN pip install ruamel.yaml

# Install PyBOMBS using setuptools
COPY PyBOMBS*.tar.gz /pybombs
RUN tar zxf *.tar.gz
RUN cd * && python setup.py install -q

# Install something
RUN mkdir /prefix
RUN cd /prefix
RUN pybombs -v auto-config
RUN pybombs -v recipes add-defaults
RUN pybombs -v prefix init -a default default
RUN pybombs install gr-osmosdr

