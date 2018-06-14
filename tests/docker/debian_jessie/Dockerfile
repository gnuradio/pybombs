# Base image
FROM debian:jessie
WORKDIR /pybombs

# Minimal package installation
RUN apt-get update -qq -y
# ruamel will get installed by setup.py via pip, but this just makes the
# process smoother
RUN apt-get install -qq -y python-pip
# Debian Jessie does not have ruamel.yaml packaged, but pip install will fail
# unless we pre-install python-dev
RUN apt-get install -qq -y python-dev
# setup.py should really install this, but it fails. Somehow, this does not.
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

