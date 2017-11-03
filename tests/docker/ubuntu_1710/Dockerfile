# Base image
FROM ubuntu:17.10
WORKDIR /pybombs

# Minimal package installation
RUN apt-get update -qq -y
RUN apt-get install -qq -y python-pip
RUN apt-get install -qq -y python-apt apt-utils
# ruamel will get installed by setup.py via pip, but this just makes the
# process smoother. If it were to be installed by PyBOMBS itselfs, this would
# be a different story and we'd not include it here.
RUN apt-get install -qq -y python-ruamel.yaml

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

