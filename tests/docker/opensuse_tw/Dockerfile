# Base image
FROM opensuse:tumbleweed
WORKDIR /pybombs

# Minimal package installation
RUN zypper refresh
RUN zypper install -y --no-recommends python2-pip
RUN zypper install -y --no-recommends tar

# Install PyBOMBS using setuptools
COPY PyBOMBS*.tar.gz /pybombs
RUN tar zxf *.tar.gz
RUN cd `ls --hide=*.gz` && python setup.py -q install

# Install something
RUN mkdir /prefix

RUN cd /prefix
# Disable sudo:
RUN pybombs config elevate_pre_args ''
RUN pybombs recipes add gr-recipes git+https://github.com/jaredd/gr-recipes.git
RUN pybombs -v prefix init -a default -R gnuradio-default default
