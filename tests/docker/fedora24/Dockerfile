# Base image
FROM fedora:24
WORKDIR /pybombs

# Minimal package installation
RUN dnf install -y -q python-pip
RUN dnf install -y -q tar

# Install PyBOMBS using setuptools
COPY PyBOMBS*.tar.gz /pybombs
RUN tar zxf *.tar.gz
RUN cd * && python setup.py -q install

# Install something
RUN mkdir /prefix
RUN cd /prefix
# Disable sudo:
RUN pybombs config elevate_pre_args ''
RUN pybombs recipes add gr-recipes git+https://github.com/gnuradio/gr-recipes.git
RUN pybombs -v prefix init -a default -R gnuradio-default default
