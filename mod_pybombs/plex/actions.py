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

Actions for use in token specifications
"""


class Action:

    def same_as(self, other):
        return self is other


class Return(Action):
    """
    Internal Plex action which causes |value| to
    be returned as the value of the associated token
    """

    value = None

    def __init__(self, value):
        self.value = value

    def perform(self, token_stream, text):
        return self.value

    def same_as(self, other):
        return isinstance(other, Return) and self.value == other.value

    def __repr__(self):
        return "Return(%s)" % repr(self.value)


class Call(Action):
    """
    Internal Plex action which causes a function to be called.
    """

    function = None

    def __init__(self, function):
        self.function = function

    def perform(self, token_stream, text):
        return self.function(token_stream, text)

    def __repr__(self):
        return "Call(%s)" % self.function.__name__

    def same_as(self, other):
        return isinstance(other, Call) and self.function is other.function


class Begin(Action):
    """
    Begin(state_name) is a Plex action which causes the Scanner to
    enter the state |state_name|. See the docstring of Plex.Lexicon
    for more information.
    """

    state_name = None

    def __init__(self, state_name):
        self.state_name = state_name

    def perform(self, token_stream, text):
        token_stream.begin(self.state_name)

    def __repr__(self):
        return "Begin(%s)" % self.state_name

    def same_as(self, other):
        return isinstance(other, Begin) and self.state_name == other.state_name


class Ignore(Action):
    """
    IGNORE is a Plex action which causes its associated token
    to be ignored. See the docstring of Plex.Lexicon  for more
    information.
    """

    def perform(self, token_stream, text):
        return None

    def __repr__(self):
        return "IGNORE"

IGNORE = Ignore()
IGNORE.__doc__ = Ignore.__doc__


class Text(Action):
    """
    TEXT is a Plex action which causes the text of a token to
    be returned as the value of the token. See the docstring of
    Plex.Lexicon  for more information.
    """

    def perform(self, token_stream, text):
        return text

    def __repr__(self):
        return "TEXT"

TEXT = Text()
TEXT.__doc__ = Text.__doc__
