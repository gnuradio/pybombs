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
