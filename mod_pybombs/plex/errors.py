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

Exception classes
"""

import exceptions


class PlexError(exceptions.Exception):
    message = ""


class PlexTypeError(PlexError, TypeError):
    pass


class PlexValueError(PlexError, ValueError):
    pass


class InvalidRegex(PlexError):
    pass


class InvalidToken(PlexError):

    def __init__(self, token_number, message):
        PlexError.__init__(self, "Token number %d: %s" % (
                           token_number, message))


class InvalidScanner(PlexError):
    pass


class AmbiguousAction(PlexError):
    message = "Two tokens with different actions can match the same string"

    def __init__(self):
        pass


class UnrecognizedInput(PlexError):
    scanner = None
    position = None
    state_name = None

    def __init__(self, scanner, state_name):
        self.scanner = scanner
        self.position = scanner.position()
        self.state_name = state_name

    def __str__(self):
        return ("'%s', line %d, char %d: Token not recognised in state %s"
            % (self.position + (repr(self.state_name),)))
