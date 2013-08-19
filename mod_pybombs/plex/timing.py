#
# Copyright 2013 Tim O'Shea
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
#
#   Get time in platform-dependent way
#

import os
from sys import platform, exit, stderr

if platform == 'mac':
    import MacOS

    def time():
        return MacOS.GetTicks() / 60.0

    timekind = "real"
elif hasattr(os, 'times'):

    def time():
        t = os.times()
        return t[0] + t[1]

    timekind = "cpu"
else:
    stderr.write(
        "Don't know how to get time on platform %s\n" % repr(platform))
    exit(1)
