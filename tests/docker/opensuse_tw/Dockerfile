# Base image
FROM opensuse:tumbleweed
WORKDIR /pybombs

# Minimal package installation
RUN zypper refresh
RUN zypper -q install -y --no-recommends tar
# On a raw OpenSuse, setuptools will fail to compile ruamel, because compilers
# and Python headers are missing.
RUN zypper -q install -y --no-recommends python2-pip python2-ruamel.yaml

# Install PyBOMBS using setuptools
COPY PyBOMBS*.tar.gz /pybombs
RUN tar zxf *.tar.gz
RUN cd `ls --hide=*.gz` && python setup.py -q install

# Install something
RUN mkdir /prefix

RUN cd /prefix
# Disable sudo:
RUN pybombs -v auto-config
# Just for verbosity:
RUN pybombs config
RUN pybombs -v recipes add-defaults
RUN pybombs -v prefix init -a default -R gnuradio-default default
