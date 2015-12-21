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
A requirer is a class that has requirements.
"""

import argparse

def require_hostsys_dependencies(deps):
    """
    Require a dependency 'dep' to be installed. Try to install if not.
    Fail if not possible.
    """
    if not deps:
        return
    from pybombs.commands import Install
    from pybombs.config_manager import config_manager
    s_order = config_manager.get('satisfy_order')
    # These are host system dependencies, so disallow source package manager
    config_manager.set('satisfy_order', 'native')
    args = argparse.Namespace(
        packages=[deps],
        update=False,
        static=False,
        no_deps=False,
        print_tree=False,
        quiet_install=True,
    )
    Install('install', args).run()
    # Restore previous settings
    config_manager.set('satisfy_order', s_order)

class Requirer(object):
    """
    Any child class of this can operate with a guarantee that certain
    packets will have been installed.
    """
    host_sys_deps = []

    def __init__(self):
        pass

    def assert_requirements(self):
        """
        Make sure this class' requirements are met, whatever necessary,
        and fail if not.
        """
        if getattr(self, 'log', None) is not None:
            logger = self.log
        else:
            from pybombs import pb_logging
            logger = pb_logging.logger.getChild("Requirer")
        if self.host_sys_deps:
            logger.debug("Requiring packages on host system: {deps}".format(deps=self.host_sys_deps))
            require_hostsys_dependencies(self.host_sys_deps)
            logger.debug("Requirements met.")

