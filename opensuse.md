# Using PyBOMBS on OpenSUSE

- A raw OpenSUSE is not able to run setuptools to install modules that require
  compilation, e.g. ruamel.yaml. If `pip install pybombs` or installing PyBOMBS
  via setup.py fails, try manually install ruamel.yaml, or install compilers
  and Python development headers manually before starting to use PyBOMBS.
