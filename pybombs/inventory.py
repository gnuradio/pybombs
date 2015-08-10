#!/usr/bin/env python2
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
Inventory Manager
"""

import yaml
import pprint
from pybombs import pb_logging

class Inventory(object):
    """
    Inventory Manager.

    Every prefix has an inventory, a list of packages that are
    installed and in which state they current are.

    Except for save(), none of the methods actually writes to the
    inventory file.
    """
    STATE_FETCHED    = 10
    STATE_CONFIGURED = 20
    STATE_BUILT      = 30
    STATE_INSTALLED  = 40

    def __init__(
            self,
            inventory_file=None,
        ):
        self._filename = inventory_file
        self._contents = {}
        self.log = pb_logging.logger.getChild("Inventory")
        self.load()
        self._valid_states = {
            self.STATE_FETCHED:    'Package source is in prefix, but not installed.',
            self.STATE_CONFIGURED: 'Package is downloaded and configured.',
            self.STATE_BUILT:      'Package is compiled.',
            self.STATE_INSTALLED:  'Package is installed into current prefix.'
        }

    def load(self):
        """
        Load the inventory file.
        If the file does not exist, initialize the internal content
        with an empty dictionary.
        This will override any internal state.
        """
        try:
            self.log.debug("Trying to load inventory file {}...".format(self._filename))
            self._contents = yaml.safe_load(open(self._filename, 'r').read())
        except:
            self.log.debug("No success. Creating empty inventory.")
            self._contents = {}
        return

    def save(self):
        """
        Save current state of inventory to the inventory file.
        This will overwrite any existing file with the same name
        and without warning. If the file didn't exist, it will be
        created.
        """
        self.log.debug("Saving inventory to file {}...".format(self._filename))
        open(self._filename, 'wb').write(yaml.dump(self._contents, default_flow_style=False))

    def has(self, pkg):
        """
        Returns true if the package pkg is in the inventory.
        """
        return self._contents.has_key(pkg)

    def remove(self, pkg):
        """
        Remove package pkg from the inventory.
        """
        if self.has(pkg):
            del self._contents[pkg]

    def get_state(self, pkg):
        """
        Return a package's state.
        See the documentation for Inventory for a list of valid states.
        If pkg does not exist, returns None.
        """
        try:
            return self._contents[pkg]["state"]
        except KeyError:
            return None

    def set_state(self, pkg, state):
        """
        Sets the state of pkg to state.
        If pkg does not exist, add that package to the list.
        """
        if not state in self.get_valid_states():
            raise ValueError("Invalid state: {}".format(state))
        if not self.has(pkg):
            self._contents[pkg] = {}
        self.log.debug("Setting state to {}".format(state))
        self._contents[pkg]["state"] = state

    def get_version(self, pkg, default_version=None):
        """
        Return a package's version.
        This throws a PBException if the package doesn't exist.
        If no version was set, return default_version (defaults to None).
        """
        if not has(pkg):
            raise PBException("Cannot get version for package {} if it's not in the inventory!".format(pkg))
        try:
            return self._contents[pkg]["version"]
        except KeyError:
            return default_version

    def set_version(self, pkg, version):
        """
        Sets the version of pkg to version.
        This throws a PBException if the package doesn't exist.
        """
        if not has(pkg):
            raise PBException("Cannot set version for package {} if it's not in the inventory!".format(pkg))
        self.log.debug("Setting version to {}".format(version))
        self._contents[pkg]["version"] = version

    def get_valid_states(self):
        """
        Returns a list of valid arguments for set_state()
        """
        return self._valid_states.keys()

