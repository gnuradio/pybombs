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
Utilities
"""

import sys
from copy import deepcopy
from six import iteritems
from builtins import input

def dict_merge(a, b):
    """
    Recursively merge b into a. b[k] will overwrite a[k] if it exists.
    """
    if not isinstance(b, dict):
        return b
    result = deepcopy(a)
    for k, v in iteritems(b):
        if k in result and isinstance(result[k], dict):
            result[k] = dict_merge(result[k], v)
        else:
            result[k] = deepcopy(v)
    return result

def confirm(question, default="N", timeout=0):
    """
    Ask the question, return True if answered positive, or False if
    answered with 'no'.
    """
    from pybombs.config_manager import config_manager
    if config_manager.yes:
        return True
    question = question.strip()
    # Remove the question mark
    if question[-1] == "?":
        question = question[:-1]
    if default.upper() == "Y":
        question = question + " [Y]/N?"
    elif default.upper() == "N":
        question = question + " Y/[N]?"
    else:
        raise ValueError("default must be either 'Y' or 'N'")
    question = question + ' '
    while True:
        inp = None
        if timeout == 0:
            inp = input(question)
        else:
            import select
            print(question)
            inp, o, e = select.select([sys.stdin], [], [], 10)
            if inp:
                inp = sys.stdin.readline()
            else:
                inp = ""
        ans = inp.strip().upper()[0:1] # use 0:1 to avoid index error even on empty response
        if ans == "":
            ans = default
        if ans == "Y":
            return True
        elif ans == "N":
            return False
        else:
            print("`{0}' is not a valid response.".format(inp))

if __name__ == "__main__":
    print(dict_merge(
        {'a': 1, 'b': 2},
        {'a': 5},
    ))

