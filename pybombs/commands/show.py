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
""" PyBOMBS command: show """

from pybombs.commands import CommandBase
from pybombs import package_manager

RECIPE_INFO_TPL = """
Recipe name:    {rname}
Is installed:   {installed}
Is installable: {installable}
""".strip()

class Show(CommandBase):
    """ Show information about a package """
    cmds = {
        'show': 'Show information about a recipe',
    }

    @staticmethod
    def setup_subparser(parser, cmd=None):
        """
        Set up a subparser for 'show'
        """
        parser.add_argument(
                'packages',
                help="List of packages to display information on",
                action='append',
                default=[],
                nargs='*'
        )
        parser.add_argument(
                '-a', '--all',
                help="Display info on all packages. Warning: Prints a lot of output",
                action='store_true',
        )

    def __init__(self, cmd, args):
        CommandBase.__init__(self,
                cmd, args,
                load_recipes=True,
                require_prefix=False,
        )
        self.package_manager = package_manager.PackageManager()
        if args.all:
            self.args.packages = recipe_manager.list_all()
        else:
            self.args.packages = args.packages[0] # wat?
        if len(self.args.packages) == 0:
            self.log.error("No packages specified.")
            exit(1)

    def run(self):
        """ Go, go, go! """
        for r in self.args.packages:
            self.show_one_recipe(r)
            print "\n"

    def show_one_recipe(self, recipe_name):
        """
        Gather info for one recipe and display it.
        """
        self.log.debug("Displaying info for package {}".format(recipe_name))
        installed   = "Yes" if self.package_manager.installed(recipe_name) else "No"
        installable = "Yes" if self.package_manager.exists(recipe_name) else "No"
        print(RECIPE_INFO_TPL.format(
                rname=recipe_name,
                installed=installed,
                installable=installable,
        ))
