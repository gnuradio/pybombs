#
# Copyright 2015-2016 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
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
""" PyBOMBS command: git """

from __future__ import print_function
import os
from six import iteritems
from pybombs.pb_exception import PBException
from pybombs import recipe
from pybombs import fetcher
from pybombs.utils import sysutils
from pybombs.utils import subproc
from pybombs.commands import SubCommandBase

#############################################################################
# Subcommand arg parsers
#############################################################################
def setup_subsubparser_makeref(parser):
    " argparse for pybombs git make-ref "
    parser.add_argument(
        'packages',
        help="List of packages to add to git reference",
        nargs='*',
    )

#############################################################################
# Command class
#############################################################################
class Git(SubCommandBase):
    """
    pybombs git <foo>
    """
    cmds = {
        'git': 'git tools',
    }
    subcommands = {
        'make-ref': {
            'help': 'Create a git reference.',
            'subparser': setup_subsubparser_makeref,
            'run': lambda x: x.run_make_ref
        },
    }

    @staticmethod
    def setup_subparser(parser, cmd=None):
        """
        Set up a subparser for a specific command
        """
        return SubCommandBase.setup_subcommandparser(
            parser,
            'Git tool Commands:',
            Git.subcommands
        )

    def __init__(self, cmd, args):
        SubCommandBase.__init__(
            self,
            cmd, args,
            load_recipes=False,
            require_prefix=False,
        )

    #########################################################################
    # Subcommands
    #########################################################################
    def run_make_ref(self):
        """
        pybombs git make-ref [foo]
        """
        if not self.create_git_ref(self.args):
            return -1

    #########################################################################
    # Helpers
    #########################################################################
    def create_git_ref(self, args):
        " Create a git reference repo "
        def _get_packages(args):
            " Return list of packages that go into ref from args "
            packages = args.packages
            if self.prefix.inventory is not None:
                for pkg in self.prefix.inventory.get_packages():
                    src = self.prefix.inventory.get_key(pkg, 'source')
                    if src is not None:
                        packages.append(pkg)
            return packages
        def _get_repo_path(path):
            " Return path to the git cache dir "
            if path is None:
                return os.path.join(self.cfg.local_cfg_dir, 'gitcache')
            return path
        def _get_git_remotes(packages):
            """ Return a dict pkgname -> git remote for every package that has
            a git remote given. """
            the_fetcher = fetcher.Fetcher()
            recipes = {pkg: recipe.get_recipe(pkg, fail_easy=True) for pkg in packages}
            sources = {pkg: recipes[pkg].source for pkg in recipes if recipes[pkg] is not None}
            git_sources = {}
            for pkg in sources:
                try:
                    for src in sources[pkg]:
                        url_type, url = the_fetcher.parse_uri(src)
                        if url_type == 'git':
                            git_sources[pkg] = url
                            break
                except PBException:
                    pass
            return git_sources
        def _chdir_to_repo(path):
            " Will always chdir to the repo, even if it has to be created. "
            if not sysutils.dir_is_writable(path):
                sysutils.mkdir_writable(path)
                os.chdir(path)
                subproc.check_output(['git', 'init', '--bare'])
            else:
                os.chdir(path)
            return
        def _get_existing_remotes():
            " Return dict remotename->url from current git repo "
            return {
                remote.strip(): subproc.check_output(['git', 'remote', 'get-url', remote.strip()]).strip()
                for remote in subproc.check_output(['git', 'remote']).split()
            }
        def _add_git_remotes(git_sources, existing_remotes):
            " Add dict remotename->url safely into current git repo "
            for remote, url in iteritems(git_sources):
                while remote in existing_remotes:
                    remote += '_'
                existing_remotes.add(remote)
                cmd = ['git', 'remote', 'add', remote, url]
                self.log.debug("Adding remote: {0}".format(" ".join(cmd)))
                subproc.check_output(cmd)
        # Go, go, go!
        packages = _get_packages(args)
        self.log.debug("Packages to add to git ref: {0}".format(packages))
        gitcachedir = _get_repo_path(None)
        git_sources = _get_git_remotes(packages)
        _chdir_to_repo(gitcachedir)
        existing_remotes = _get_existing_remotes()
        print(existing_remotes)
        git_sources = {remote: url for remote, url in iteritems(git_sources)
                       if url not in existing_remotes.values()}
        print(git_sources)
        _add_git_remotes(git_sources, set(existing_remotes.keys()))
        self.log.debug("Updating remotes")
        subproc.check_output(['git', 'fetch', '--all', '--prune'])
        self.cfg.update_cfg_file({'config': {'git-cache': gitcachedir}})

