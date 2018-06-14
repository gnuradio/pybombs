# Base image
FROM centos:7
WORKDIR /pybombs

# Minimal package installation
RUN yum install -y -q epel-release
RUN yum install -y -q python-pip

# Install PyBOMBS using setuptools
COPY PyBOMBS*.tar.gz /pybombs
RUN tar zxf *.tar.gz
RUN cd * && python setup.py -q install

# Install something
RUN mkdir /prefix
RUN cd /prefix
# Disable sudo:
RUN pybombs -v auto-config
RUN pybombs -v recipes add-defaults
RUN pybombs -v prefix init -a default -R gnuradio-default default
