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
""" PyBOMBS command: deploy """

from __future__ import print_function
import re
import os
import tarfile
from pybombs.commands import CommandBase
from pybombs.requirer import Requirer
from pybombs.pb_exception import PBException
from pybombs.utils import subproc

class Deployer(object):
    """
    Deployer base class
    """
    ttype = None

    def __init__(self, skip_names=None):
        self.skip_names = skip_names or []

    def deploy(self, target, prefix_dir):
        """
        Override this.
        """
        raise NotImplementedError

class TarfileDeployer(Deployer):
    """
    Deploy to tarfile (.tar)
    """
    mode = ''

    def __init__(self, skip_names=None):
        Deployer.__init__(self, skip_names)

    def deploy(self, target, prefix_dir):
        """
        Create tar file
        """
        tf = tarfile.open(
            name=target,
            mode='w:{mode}'.format(mode=self.mode),
        )
        tf.add(prefix_dir, filter=self.filter)
        tf.close()

    def filter(self, tiobject):
        """ Filter callback """
        if tiobject.name in self.skip_names:
            return None
        return tiobject

class GZipDeployer(TarfileDeployer):
    """
    Deploy to .tar.gz
    """
    ttype = 'gzip'
    mode = 'gz'
    def __init__(self, skip_names=None):
        TarfileDeployer.__init__(self, skip_names)

class BZip2Deployer(TarfileDeployer):
    """
    Deploy to .tar.bz2
    """
    ttype = 'bzip2'
    mode = 'bz2'
    def __init__(self, skip_names=None):
        TarfileDeployer.__init__(self, skip_names)

class XZDeployer(Deployer, Requirer):
    """
    Deploy to .tar.xz
    """
    ttype = 'xz'
    host_sys_deps = ['xz']
    def __init__(self, skip_names=None):
        Requirer.__init__(self)
        Deployer.__init__(self, skip_names)
        self.tarfiledeployer = TarfileDeployer(skip_names)

    def deploy(self, target, prefix_dir):
        """
        Call TarfileDeployer to make a .tar file, then use xz
        to zip that
        """
        tarfilename = target
        if os.path.splitext(target)[1] == '.xz':
            tarfilename = os.path.splitext(target)[0]
        elif os.path.splitext(target)[1] == '.txz':
            tarfilename = os.path.splitext(target)[0] + '.tar'
        result_filename = tarfilename + '.xz'
        self.tarfiledeployer.deploy(tarfilename, prefix_dir)
        subproc.monitor_process(['xz', tarfilename], throw_ex=True)
        if result_filename != target:
            os.rename(result_filename, target)

class SSHDeployer(Deployer):
    """ Deploy via scp """
    def __init__(self, skip_names=None):
        Deployer.__init__(self, skip_names)

    def deploy(self, target, prefix_dir):
        """
        docstring for deploy
        """
        prefix_content = [
            x for x in os.listdir(prefix_dir) \
            if not os.path.join(prefix_dir, x) in self.skip_names \
        ]
        os.chdir(prefix_dir)
        cmd = ['scp', '-r', '-q'] + prefix_content + [target]
        subproc.monitor_process(cmd, throw_ex=True)

def choose_deployer(ttype, target):
    """
    Return the best match for the deployer class.

    throws KeyError if class can't be determined.
    """
    if ttype is not None:
        return {
            'tar': TarfileDeployer,
            'gzip': GZipDeployer,
            'bzip2': BZip2Deployer,
            'xz': XZDeployer,
            #'ssh': SSHDeployer
        }[ttype]
    if re.match(r'.*\.tar\.gz$', target):
        return GZipDeployer
    if re.match(r'.*\.tar\.bz2$', target):
        return BZip2Deployer
    if re.match(r'.*\.tar\.xz$', target):
        return XZDeployer
    if re.match(r'.*\.tar$', target):
        return TarfileDeployer
    if target.find('@') != -1:
        return SSHDeployer
    raise PBException("Cannot determine deployment type for target `{0}'".format(target))

class Deploy(CommandBase):
    """ Package and deploy the prefix """
    cmds = {
        'deploy': 'Deploy a prefix',
    }

    @staticmethod
    def setup_subparser(parser, cmd=None):
        """
        Set up a subparser for 'deploy'
        """
        parser.add_argument(
            'target', help="Deployment destination",
        )
        parser.add_argument(
            '-t', '--tar',
            help="Deploy to .tar",
            dest="ttype",
            action='store_const',
            const='tar',
        )
        parser.add_argument(
            '-z', '--gzip',
            help="Deploy to .tar.gz",
            dest="ttype",
            action='store_const',
            const='gzip',
        )
        parser.add_argument(
            '-j', '--bzip2',
            help="Deploy to .tar.bz2",
            dest="ttype",
            action='store_const',
            const='bzip2',
        )
        parser.add_argument(
            '-J', '--xz',
            help="Deploy to .tar.xz",
            dest="ttype",
            action='store_const',
            const='xz',
        )
        parser.add_argument(
            '-s', '--ssh',
            help="Deploy to remote target",
            dest="ttype",
            action='store_const',
            const='ssh',
        )
        parser.add_argument(
            '--keep-src',
            help="Include the source directory",
            action='store_true',
        )
        parser.add_argument(
            '--keep-config',
            help="Include the config directory",
            action='store_true',
        )

    def __init__(self, cmd, args):
        CommandBase.__init__(
            self,
            cmd, args,
            load_recipes=False,
            require_prefix=True,
        )

    def run(self):
        """ Go, go, go! """
        ### Identify deployment target type
        deployer = choose_deployer(self.args.ttype, self.args.target)
        self.log.debug("Using deployer: {0}".format(deployer))
        ### Setup paths and make archive
        prefix_base, prefix_path = os.path.split(os.path.normpath(self.prefix.prefix_dir))
        os.chdir(prefix_base)
        skip_names = []
        if not self.args.keep_src:
            self.log.debug("Excluding source directory")
            skip_names.append(os.path.join(
                prefix_path,
                os.path.split(self.prefix.src_dir)[1]
            ))
        if not self.args.keep_config:
            self.log.debug("Excluding config directory")
            skip_names.append(os.path.join(
                prefix_path,
                os.path.split(self.prefix.prefix_cfg_dir)[1]
            ))
        try:
            self.log.info("Deploying prefix to {0}...".format(self.args.target))
            deployer(skip_names).deploy(self.args.target, prefix_path)
        except PBException as ex:
            self.log.error("Failed to deploy: {0}".format(str(ex)))
            return 1
