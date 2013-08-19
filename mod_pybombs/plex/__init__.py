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
"""
Python Lexical Analyser
=======================

The Plex module provides lexical analysers with similar capabilities
to GNU Flex. The following classes and functions are exported;
see the attached docstrings for more information.

   Scanner          For scanning a character stream under the
                    direction of a Lexicon.

   Lexicon          For constructing a lexical definition
                    to be used by a Scanner.

   Str, Any, AnyBut, AnyChar, Seq, Alt, Opt, Rep, Rep1,
   Bol, Eol, Eof, Empty

                    Regular expression constructors, for building pattern
                    definitions for a Lexicon.

   State            For defining scanner states when creating a
                    Lexicon.

   TEXT, IGNORE, Begin

                    Actions for associating with patterns when
                    creating a Lexicon.
"""

__version__ = '2.0.0'

from actions import TEXT, IGNORE, Begin
from lexicons import Lexicon, State
from regexps import RE, Seq, Alt, Rep1, Empty, Str, Any, AnyBut, AnyChar, Range
from regexps import Opt, Rep, Bol, Eol, Eof, Case, NoCase
from scanners import Scanner
