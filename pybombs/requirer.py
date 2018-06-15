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
A requirer is a class that itself has dependencies on packages.
"""

REQUIRER_CHECKED_CACHE = []

def require_hostsys_dependencies(deps):
    """
    Require a dependency 'dep' to be installed. Try to install if not.
    Fail if not possible.
    """
    if not deps:
        return
    global REQUIRER_CHECKED_CACHE
    deps_to_check = [d for d in deps if d not in REQUIRER_CHECKED_CACHE]
    if not deps_to_check:
        return
    from pybombs import install_manager
    from pybombs.config_manager import config_manager
    REQUIRER_CHECKED_CACHE += deps_to_check
    try:
        config_manager.set_config_reference('pybombs')
        install_manager.InstallManager().install(
            deps_to_check,
            'install', # install / update
            fail_if_not_exists=False,
            update_if_exists=False,
            quiet=True,
            print_tree=False,
            install_type="binary", # Requirers may not request source packages
        )
    finally:
        config_manager.set_config_reference('prefix')

class Requirer(object):
    """
    Any child class of this can operate with a guarantee that certain
    packets will have been installed.
    """
    host_sys_deps = []

    def __init__(self):
        # There's a pretty good reason assert_requirements() is not called
        # here, in fact, it used to be, but I can't remember why not. Probably
        # to avoid infinite loops.
        pass

    def assert_requirements(self, requirements=None):
        """
        Make sure this class' requirements are met, whatever necessary,
        and fail if not.
        """
        if requirements is None:
            requirements = self.host_sys_deps
        if getattr(self, 'log', None) is not None:
            logger = self.log
        else:
            from pybombs import pb_logging
            logger = pb_logging.logger.getChild("Requirer")
        if requirements:
            logger.debug("Requiring packages on host system: {deps}".format(deps=self.host_sys_deps))
            require_hostsys_dependencies(requirements)
            logger.debug("Requirements met.")

