#!/usr/bin/env python
#
# Copyright 2015 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# PyBOMBS is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# PyBOMBS is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyBOMBS; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#
"""
PyBOMBS
~~~~~~~

PyBOMBS (the Python Bundles Overlay Managed Build System) is a meta-package
manager that can install packages from source or using the local package
manager(s).

It was mainly designed for use by users of the `GNU Radio project`_, which
is extended by a large number of out-of-tree modules (OOTs).

PyBOMBS is a recipe-based system and can easily mix and match installations
from different sources. Cross-compilation works transparently.


Basic commands
--------------

With PyBOMBS installed, you might want to install GNU Radio into a directory
called `my_gnuradio`. First, you create a /prefix/ there:

    $ pybombs prefix init my_gnuradio

Then, you call PyBOMBS to do the installation:

    $ pybombs install gnuradio

PyBOMBS will determine the dependency tree for GNU Radio, and install
dependencies either through the local system's package manager (e.g.
apt-get, yum, pip...) or pull the source files and build them in the
prefix.

With slight modifications, the same commands would have worked to create
a cross-compile environment and cross-compile GNU Radio:

    $ pybombs prefix init my_gnuradio --sdk e300
    $ pybombs install gnuradio

For more informations see the `documentation`_.

.. _GNU Radio project: http://gnuradio.org/
.. _documentation: http://gnuradio.org/pybombs/
"""

try:
    import setuptools
except ImportError:
    import ez_setup
    try:
        ez_setup.use_setuptools()
    except AttributeError:
        print("=========================================================")
        print("Detected incompatibility between ez_setup and setuptools.")
        print("Re-running this script might fix things.")
        print("If not, install setuptools separately and try again.")
        print("=========================================================")
        exit(1)

from setuptools import setup
import pybombs

packages = [
    "pybombs",
    "pybombs.commands",
    "pybombs.fetchers",
    "pybombs.packagers",
    "pybombs.utils",
]

package_data = {
    'pybombs': [
        'templates/*.lwt',
        'recipes/*.lwr',
    ],
}

deps = [
    "setuptools",
    "PyYAML",
    "requests",
    "six",
    "future",
]

setup(
    name="PyBOMBS",
    version=pybombs.__version__,
    description="A meta-package manager to install software from source, or whatever "
                  "the local package manager is. Designed for easy install of source "
                  "trees for the GNU Radio project.",
    long_description=__doc__,
    url="http://gnuradio.org/pybombs/",
    download_url="https://github.com/gnuradio/pybombs/tarball/v{version}".format(version=pybombs.__version__),
    author="Martin Braun",
    author_email="martin.braun@ettus.com",
    maintainer="Martin Braun",
    maintainer_email="martin.braun@ettus.com",
    license="GPLv3",
    packages=packages,
    package_data=package_data,
    entry_points={
        "console_scripts": ["pybombs=pybombs.main:main"],
    },
    install_requires=deps,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Telecommunications Industry",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2.7",
        "Topic :: Communications :: Ham Radio",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: System :: Archiving :: Packaging",
        "Topic :: System :: Installation/Setup",
        "Topic :: System :: Software Distribution",
        "Topic :: Utilities",
    ],
    #zip_safe=False,
)
