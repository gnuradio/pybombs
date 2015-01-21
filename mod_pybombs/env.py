#!/usr/bin/env python2
#
# Copyright 2013 Tim O'Shea
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

import os
import verbosity as v

def tryenv(k):
    try: 
        return os.environ[k]
    except:
        return ""

def env_init(vars, prefix_key='prefix'):
    print "Initializing environmental variables..."
    env = os.environ
    env["PATH"] = vars[prefix_key] + "/bin/:" + tryenv("PATH")
    env["PATH"] = tryenv("PATH") + ":/usr/lib64/qt4/bin/"
    env["PYTHONPATH"] = vars[prefix_key] + "/python/:"
    for pyname in ["python2.6","python2.7"]:
        for moddir in ["site-packages","dist-packages"]:
            env["PYTHONPATH"] = env["PYTHONPATH"] + vars[prefix_key] + "/lib/%s/%s/:"%(pyname,moddir)
            env["PYTHONPATH"] = env["PYTHONPATH"] + vars[prefix_key] + "/lib64/%s/%s/:"%(pyname,moddir)
    env["PYTHONPATH"] = env["PYTHONPATH"] + tryenv("PYTHONPATH")
    if env["PYTHONPATH"][-1] == ":":
        env["PYTHONPATH"] = env["PYTHONPATH"][:-1]
    v.print_v(v.DEBUG, "$PYTHONPATH = {0}".format(env["PYTHONPATH"]))
    
    env["ATLAS"] = vars[prefix_key] + "/lib/libatlas.so:/usr/local/lib/:/usr/lib/"
    env["BLAS"] = vars[prefix_key] + "/lib/libblas.so:/usr/local/lib/:/usr/lib/"
    env["LAPACK"] = vars[prefix_key] + "/lib/liblapack.so:/usr/local/lib:/usr/lib/"
    env["BOOST_ROOT"] = vars[prefix_key]
    env["BOOST_LIBRARYDIR"] = vars[prefix_key] + "/lib/:" + vars[prefix_key] + "/lib64/:"
    env["PREFIX"] = vars[prefix_key]
    env["GTEST_DIR"] = vars[prefix_key] + "/gtest"
    
    #env["PYTHONPATH"] = vars[prefix_key] + "/lib/python2.6/site-packages/:" + vars[prefix_key] + tryenv("PYTHONPATH")
    tryenv("PYTHONPATH")
    env["LD_LIBRARY_PATH"] = vars[prefix_key] + "/lib/:" + vars[prefix_key] + "/lib64/:" + tryenv("LD_LIBRARY_PATH")
    tryenv("LD_LIBRARY_PATH")
    env["PKG_CONFIG_PATH"] = vars[prefix_key] + "/lib/pkgconfig/:" + vars[prefix_key] + "/lib64/pkgconfig/:" + tryenv("PKG_CONFIG_PATH")
    tryenv("PKG_CONFIG_PATH")
    return env


