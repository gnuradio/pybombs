# Base image
FROM fedora:26
WORKDIR /pybombs

# Minimal package installation
RUN dnf install -y -q python-pip
RUN dnf install -y -q python2-ruamel-yaml
RUN dnf install -y -q tar

# Install PyBOMBS using setuptools
COPY PyBOMBS*.tar.gz /pybombs
RUN tar zxf *.tar.gz
RUN rm *.tar.gz
RUN ls
RUN cd * && python setup.py -q install


# Install something
RUN mkdir /prefix
RUN cd /prefix
RUN pybombs -v auto-config
RUN pybombs -v recipes add-defaults
RUN pybombs -v prefix init -a default -R gnuradio-default default
