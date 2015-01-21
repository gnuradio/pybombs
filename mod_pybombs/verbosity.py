#
# Copyright 2014 Martin Braun
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

PDEBUG = 5
DEBUG  = 4
INFO   = 3
WARN   = 2
ERROR  = 1

VERBOSITY_LEVELS = {
    'PDEBUG': PDEBUG,
    'DEBUG': DEBUG,
    'INFO': INFO,
    'WARN': WARN,
    'ERROR': ERROR,
}

VERBOSITY_LEVEL = INFO

def print_v(level, strdata):
    " Print strdata iv level is smaller or equal to VERBOSITY_LEVEL "
    if level <= VERBOSITY_LEVEL:
        print strdata

def print_v_select(choices):
    """
    choices is a map of the form {verb_level: message}.
    It will print the message with the highest verb_level that
    is smaller than VERBOSITY_LEVEL.
    """
    levels = sorted(choices.keys())
    levels.reverse()
    for level in levels:
        if level <= VERBOSITY_LEVEL:
            print choices[level]
            return
