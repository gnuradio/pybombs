#
# Copyright 2015 Free Software Foundation, Inc.
#
# This file is part of PyBOMBS
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
Utils for handling archives
"""

import os
import zipfile
import tarfile
import tempfile
import shutil
from pybombs import pb_logging

def extract_to(filename, path):
    """
    Extract an archive into a directory. Return the prefix for the extracted files.
    """
    log = pb_logging.logger.getChild("extract_to")
    if tarfile.is_tarfile(filename):
        archive = tarfile.open(filename)
    elif zipfile.is_zipfile(filename):
        archive = zipfile.ZipFile(filename)
    else:
        raise RuntimeError("Cannot extract {}: Unknown archive type")
    log.debug("Unpacking {}".format(filename))
    if len(archive.getnames()) == 1:
        prefix = os.path.split(archive.getnames()[0])[0]
    else:
        prefix = os.path.commonprefix(archive.getnames())
    if not prefix:
        prefix = '.'
    log.debug("Common prefix: {}".format(prefix))
    if prefix == '.':
        if not os.path.isdir(path):
            os.mkdir(path)
        archive.extractall(path=path)
    else:
        tmp_dir = os.path.normpath(tempfile.mkdtemp())
        log.debug("Moving {0} -> {1}".format(os.path.normpath(os.path.join(tmp_dir, prefix)), path))
        archive.extractall(path=tmp_dir)
        shutil.move(os.path.normpath(os.path.join(tmp_dir, prefix)), path) # Will work if arguments are equal
    archive.close()
    return True

def is_archive(filename):
    """
    Return True if 'filename' is a zipped archive.
    """
    return os.path.isfile(filename) and \
            (tarfile.is_tarfile(filename) or zipfile.is_zipfile(filename))

