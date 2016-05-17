#!/usr/bin/env python2
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
""" PyBOMBS dispatcher. This will figure out which module to call
    and call it. """

from __future__ import print_function
from pybombs.commands import dispatch
from pybombs.pb_exception import PBException

def main():
    " Go, go, go! "
    try:
        return dispatch() or 0
    except PBException as ex:
        from pybombs import pb_logging
        if pb_logging.logger.getEffectiveLevel() <= pb_logging.DEBUG:
            pb_logging.logger.debug(str(ex))
        return 1
    except KeyboardInterrupt:
        pass
    return 0

if __name__ == '__main__':
    exit(main())

