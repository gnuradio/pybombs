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
"""
Version comparison functions
"""

import operator
from distutils.version import LooseVersion

def vcompare(cmp_op, version_x, version_y):
    """
    Confirm if version x compares to y given an operator op.
    """
    operators = {'<=': operator.le, '==': operator.eq, '>=': operator.ge, '!=': operator.ne}
    try:
        return operators[cmp_op](LooseVersion(version_x), LooseVersion(version_y))
    except TypeError:
        return False

if __name__ == "__main__":
    print(vcompare(">=", "2.3.4", "1.2.3"))
