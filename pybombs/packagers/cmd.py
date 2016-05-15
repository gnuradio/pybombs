#
# Copyright 2015-2016 Free Software Foundation, Inc.
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
Pseudo-Packager: Test command
"""

import re
import subprocess
from pybombs.packagers.extern import ExternCmdPackagerBase, ExternReadOnlyPackager
from pybombs.utils import subproc

class ExternalTestCmd(ExternReadOnlyPackager):
    " Wrapper around running a command "
    def __init__(self, logger):
        ExternReadOnlyPackager.__init__(self, logger)

    def get_installed_version(self, command):
        """
        Run command, see if it works. If the output has a version number in
        x.y.z format, return that. If it doesn't, but the command ran, return
        True. If it fails, return False. ezpz.
        """
        try:
            # If this fails, it almost always throws.
            # NOTE: the split is to handle multi-argument commands. There's
            # cases where this is not intended, e.g. it won't handle arguments
            # with spaces! But currently this is preferable to running the
            # command in a shell.
            ver = subproc.match_output(
                command.split(),
                r'(?P<ver>[0-9]+\.[0-9]+(\.[0-9]+)?)',
                'ver'
            )
            if ver is None:
                self.log.debug("Could run, but couldn't find a version number.")
                return True
            self.log.debug("Found version number: {0}".format(ver))
            return ver
        except (subprocess.CalledProcessError, OSError):
            # We'll assume it's not installed
            return False
        except Exception as e:
            self.log.error("Running `{0}` failed.".format(command))
            self.log.obnoxious(str(e))
        return False


class TestCommand(ExternCmdPackagerBase):
    """
    Checks if something is installed by running a command.
    Can't really install stuff, but is useful for finding out if something is
    already installed, e.g. from source.
    """
    name = 'cmd'
    pkgtype = 'cmd'

    def __init__(self):
        ExternCmdPackagerBase.__init__(self)
        self.packager = ExternalTestCmd(self.log)

    def supported(self):
        " We can always run commands. "
        return True

