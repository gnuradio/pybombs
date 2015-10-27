#
# Copyright 2015 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#
""" PyBOMBS command: install """

import os
import shutil
from pybombs.commands import CommandBase
from pybombs import package_manager
from pybombs import dep_manager

class Remove(CommandBase):
    """ Remove a package from this prefix """
    cmds = {
        'remove': 'Remove listed packages',
    }

    @staticmethod
    def setup_subparser(parser, cmd=None):
        """
        Set up a subparser for 'remove'
        """
        parser.add_argument(
                'packages',
                help="List of packages to remove",
                action='append',
                default=[],
                nargs='*'
        )

    def __init__(self, cmd, args):
        CommandBase.__init__(self,
                cmd, args,
                load_recipes=False,
                require_prefix=True,
                require_inventory=True,
        )
        self.args.packages = args.packages[0]
        # Do not allow any non-source packagers for this:
        self.cfg.set('packagers', '')
        self.pm = package_manager.PackageManager()

    def run(self):
        """ Go, go, go! """
        ### Sanity checks
        for pkg in self.args.packages:
            if not self.pm.installed(pkg):
                self.log.error("Package {0} is not installed. Aborting.".format(pkg))
                exit(1)
        ### Remove packages
        for pkg in self.args.packages:
            self.log.info("Removing package {0}.".format(pkg))
            # Uninstall:
            self.log.debug("Uninstalling.")
            if not self.pm.uninstall(pkg):
                self.log.warn("Could not uninstall {0} from prefix.".format(pkg))
            # Remove source dir:
            pkg_src_dir = os.path.join(self.prefix.src_dir, pkg)
            self.log.debug("Removing directory {0}.".format(pkg_src_dir))
            shutil.rmtree(pkg_src_dir)
            # Remove entry from inventory:
            self.log.debug("Removing package from inventory.")
            self.inventory.remove(pkg)
            self.inventory.save()

