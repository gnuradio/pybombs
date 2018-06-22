# Using PyBOMBS on Debian

## Debian Jessie

### Failure to install ruamel.yaml from source

There is a known issue where installing PyBOMBS via setup.py fails to install
the ruamel.yaml dependency. See this issue: https://github.com/gnuradio/pybombs/issues/498

A workaround is to install ruamel.yaml manually before installing PyBOMBS.

    $ [sudo] apt install python-dev # Required to build ruamel.yaml
    $ [sudo] pip install ruamel.yaml
    $ [sudo] python ./setup.py install # Now proceed to install from source


