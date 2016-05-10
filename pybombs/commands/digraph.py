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
""" PyBOMBS command: digraph """

import os
from pybombs.commands import CommandBase
from pybombs.requirer import Requirer
from pybombs import recipe_manager
from pybombs import recipe
from pybombs.utils import subproc

class Digraph(CommandBase, Requirer):
    """ Generate dependency graph """
    cmds = {
        'digraph': 'Write out package.dot digraph for graphviz',
    }
    host_sys_deps = ['graphviz']

    @staticmethod
    def setup_subparser(parser, cmd=None):
        """
        Set up a subparser for 'digraph'
        """
        parser.add_argument(
            '--all',
            help="Print dependency tree",
            action='store_true',
        )
        parser.add_argument(
            '--dotfile',
            help="Dotfile to write to",
            default="digraph.dot",
        )

    def __init__(self, cmd, args):
        CommandBase.__init__(self,
            cmd, args,
            load_recipes=True,
            require_prefix=True,
        )
        Requirer.__init__(self)
        self.packages = []
        if self.args.all:
            self.packages = recipe_manager.recipe_manager.list_all()
        else:
            self.packages = self.inventory.get_packages()
        self.assert_requirements()

    def run(self):
        """ Go, go, go! """
        self.graphviz(
            self.packages,
            self.args.dotfile,
            "digraph.png"
        )

    def graphviz(self, packages, dotfile, pngfile):
        """
        Create the graphviz file
        """
        self.log.info("Creating digraph file {0}".format(dotfile))
        f = open(dotfile, "w")
        f.write("digraph g {\n")
        for pkg in packages:
            pkg_safe = pkg.replace("-", "_")
            f.write('{pkg} [label="{pkg}"]\n'.format(pkg=pkg_safe))
            rec = recipe.get_recipe(pkg, fail_easy=True)
            if rec is None:
                continue
            for dep in rec.depends:
                if dep in packages:
                    f.write(" {pkg} -> {dep}\n".format(
                        pkg=pkg_safe,
                        dep=dep.replace("-", "_")
                    ))
        f.write("}\n")
        f.close()
        self.log.debug("{0} written".format(dotfile))
        if pngfile is None:
            return
        self.log.info("Creating png file {0}".format(pngfile))
        subproc.monitor_process(
            ['dot', dotfile, '-Tpng', '-o{0}'.format(pngfile)],
            env=os.environ,
        )
        #bashexec("eog digraph.png")

