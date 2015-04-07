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
""" PyBOMBS dispatcher. This will figure out which module to call
    and call it. """

from pybombs.commands import *
from pybombs.commands.cmd_help import get_command_from_argv

def main():
    """ Here we go. Parse command, choose class and run. """
    cmd_dict = get_class_dict(globals().values())
    command = get_command_from_argv(cmd_dict.keys())
    if command is None:
        print 'Usage:' + PyBombsHelp.usage
        exit(2)
    pb_cmd = cmd_dict[command]()
    try:
        (options, args) = pb_cmd.parser.parse_args()
        args.pop(0)
        pb_cmd.setup(options, args)
        pb_cmd.run()
    except PBException as err:
        print >> sys.stderr, err
        exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

### Old stuff:
#import os,re,sys;
#from optparse import OptionParser
#from mod_pybombs import verbosity as v

#parser = OptionParser(USAGE)
#parser.add_option("-c", "--continue", dest="_continue", default=False, action="store_true", help="Attempt to continue in-spite of failures")
#parser.add_option("-f", "--force", default=False, action="store_true", help="Force operation to occur")
#parser.add_option("-a", "--all", default=False, action="store_true", help="Apply operation to all packages")
#parser.add_option("-v", "--verbose", default=False, action="count", help="Increase verbosity")
#opts,args = parser.parse_args()

#"""
#Handle commands don't require loading the PyBombs modules & subsytem.
#"""
## Set up verbosity level
#v.VERBOSITY_LEVEL = v.INFO + opts.verbose

#"""
#Load the PyBomb modules & subsystem. 
#"""

##from mod_pybombs import *
#import mod_pybombs.pybombs_ops as pybombs_ops
#import mod_pybombs.recipe_loader as recipe_loader
#import mod_pybombs.sysutils as sysutils
##from mod_pybombs import recipe,update,fetch,inventory
##from mod_pybombs import cfg,vars,globals


#from mod_pybombs import *
#sysutils.set_logger()
