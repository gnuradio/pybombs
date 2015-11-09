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

import re
import sys
from subprocess import Popen, PIPE, STDOUT
from threading  import Thread
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x


READ_TIMEOUT = 0.1 # s

ROTATION_ANIM = ('-', '\\', '|', '/',)

def get_console_width():
    '''
    http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
    '''
    import os
    env = os.environ
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,
        '1234'))
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
        print "\n"

class OutputProcessorDots(OutputProcessor):
    """ Shows progress """
    def __init__(self):
        OutputProcessor.__init__(self)

    def process_output(self, stdoutdata, stderrdata):
        sys.stdout.write('.')
        print '.',

class OutputProcessorMake(OutputProcessor):
    """ Shows progress """
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
            print self._make_percentage_line(),
            return
        self._check_for_percentage(stdoutdata)
        print self._make_generic_progress_line(),

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
        print self.status_line


def run_with_output_processing(p, o_proc):
    """
    Run a previously created process p through
    an output processor o_proc.
    """
    def enqueue_output(stdout_data, stdout_queue, stderr_data, stderr_queue):
        " Puts the output from the process into the queue "
        for line in iter(stdout_data.readline, b''):
            stdout_queue.put(line)
        stdout_data.close()
        if stderr_data is not None:
            for line in iter(stderr_data.readline, b''):
                stderr_queue.put(line)
            stderr_data.close()
    def poll_queue(q):
        " Safe polling from queue "
        line = ""
        try:
            line = q.get(timeout=READ_TIMEOUT)
        except Empty:
            return ""
        # Got line:
        return line
    # Init thread and queue
    q_stdout = Queue()
    q_stderr = Queue()
    t = Thread(target=enqueue_output, args=(p.stdout, q_stdout, p.stderr, q_stderr))
    # End the thread when the program terminates
    t.daemon = True
    t.start()
    # Run loop
    while p.poll() is None: # Run while process is alive
        line_stdout = poll_queue(q_stdout)
        line_stderr = poll_queue(q_stderr)
        o_proc.process_output(line_stdout, line_stderr)
    o_proc.process_final()
    return p.returncode
