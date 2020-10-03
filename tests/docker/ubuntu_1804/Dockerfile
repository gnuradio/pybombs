# Base image
FROM ubuntu:18.04
WORKDIR /pybombs

# Some packages depend on tzdata, which gets stuck if timezone is not set.
# overrideable during build using `--build-arg TZ=America/New_York`.
ARG TZ=Etc/UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Minimal package installation
RUN apt-get update -qq -y
# ruamel will get installed by setup.py via pip, but this just makes the
# process smoother
RUN apt-get install -qq -y python-pip python-ruamel.yaml

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
