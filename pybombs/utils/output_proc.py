#!/usr/bin/env python
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
Output Processors
"""

from __future__ import print_function
import os
import re
import sys
from subprocess import PIPE, STDOUT

ROTATION_ANIM = ('-', '\\', '|', '/',)
DEFAULT_CONSOLE_WIDTH = 80

def get_console_width():
    '''
    http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
    '''
    env = os.environ
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
        except:
            return
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        cr = (env.get('LINES', 25), env.get('COLUMNS', 80))
    return cr[1]

class OutputProcessor(object):
    """ Output processor. Meant to parse output from a running command. """
    def __init__(self):
        self.extra_popen_args = {'stdout': PIPE, 'stderr': PIPE}

    def process_output(self, stdoutdata, stderrdata):
        """
        This is called every time there's new output. May contain
        multiple lines.
        """
        raise NotImplementedError("process_output() not overridden.")

    def process_final(self):
        print("\n")

class OutputProcessorDots(OutputProcessor):
    """ Shows progress by printing ... when stuff happens. """
    def __init__(self):
        OutputProcessor.__init__(self)

    def process_output(self, stdoutdata, stderrdata):
        sys.stdout.write('.')

class OutputProcessorMake(OutputProcessor):
    """
    Shows progress when running 'make'
    If CMake's make is run, grep the progress from the output
    """
    def __init__(self, preamble="Progress: "):
        OutputProcessor.__init__(self)
        self.extra_popen_args = {'stdout': PIPE, 'stderr': STDOUT}
        self.preamble = preamble
        self.percent_found = False
        self.percentage = 0
        self.call_count = 0
        self.percent_regex = re.compile(r'(?<=\[)[ 0-9]{3}(?=%\])')

    def process_output(self, stdoutdata, stderrdata):
        self.call_count += 1
        if self.percent_found:
            self._update_percentage(stdoutdata)
            sys.stdout.write(self._make_percentage_line())
            return
        self._check_for_percentage(stdoutdata)
        sys.stdout.write(self._make_generic_progress_line())

    def _check_for_percentage(self, strdata):
        " Check if strdata contains a percentage string. "
        if self.percent_regex.search(strdata) is not None:
            self.percent_found = True

    def _update_percentage(self, strdata):
        """
        Scan strdata for percentage strings and update self.percentage
        with the largest found value.
        """
        results = self.percent_regex.findall(strdata)
        for result in results:
            self.percentage = max(self.percentage, int(result))
        self.percentage = min(100, self.percentage)
        self.status_line = ' ' * get_console_width()

    def _make_percentage_line(self):
        preamble = self.preamble
        # 2 for '[*]', 7 for '(xxx%) '
        progress_bar_len = get_console_width() - len(preamble) - 2 - 7
        # subtract 1 to account for the rotation animation
        chars_left  = int((progress_bar_len-1) * .01 * self.percentage)
        chars_right = progress_bar_len - chars_left - 2
        self.status_line = '\r{0}({1:>3}%) [{2}{3}{4}]\r'.format(
                preamble,
                self.percentage,
                '=' * chars_left,
                ROTATION_ANIM[self.call_count % len(ROTATION_ANIM)],
                ' ' * chars_right
        )
        return self.status_line

    def _make_generic_progress_line(self):
        preamble = self.preamble
        progress_bar_len = get_console_width() - len(preamble) - 2
        fraction = float(int((self.call_count / 10) % progress_bar_len)) / progress_bar_len
        chars_left = int(progress_bar_len * fraction)
        chars_right = progress_bar_len - chars_left - 2
        self.status_line = '\r{0}[{1}{2}{3}]'.format(
                preamble,
                ' ' * chars_left,
                ROTATION_ANIM[self.call_count % len(ROTATION_ANIM)],
                ' ' * chars_right
        )
        return self.status_line

    def process_final(self):
        progress_bar_len = get_console_width() - len(self.preamble) - 2 - 7
        self.status_line = '\r{0}({1:>3}%) [{2}]'.format(
                self.preamble,
                100,
                '=' * (progress_bar_len-1),
        )
        print(self.status_line)


