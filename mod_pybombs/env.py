#!/usr/bin/env python
import os

def tryenv(k):
    try: 
        return os.environ[k]
    except:
        return ""

def env_init(vars):
    print "Initializing environmental variables..."
    env = os.environ
    env["PATH"] = vars["prefix"] + "/bin/:" + tryenv("PATH")
    env["PATH"] = tryenv("PATH") + ":/usr/lib64/qt4/bin/"
    env["PYTHONPATH"] = vars["prefix"] + "/python/:"
    for pyname in ["python2.6","python2.7"]:
        for moddir in ["site-packages","dist-packages"]:
            env["PYTHONPATH"] = env["PYTHONPATH"] + vars["prefix"] + "/lib/%s/%s/:"%(pyname,moddir)
            env["PYTHONPATH"] = env["PYTHONPATH"] + vars["prefix"] + "/lib64/%s/%s/:"%(pyname,moddir)
    env["PYTHONPATH"] = env["PYTHONPATH"] + tryenv("PYTHONPATH")
    if env["PYTHONPATH"][-1] == ":":
        env["PYTHONPATH"] = env["PYTHONPATH"][:-1]
    print env["PYTHONPATH"]
    
    env["ATLAS"] = vars["prefix"] + "/lib/libatlas.so:/usr/local/lib/:/usr/lib/"
    env["BLAS"] = vars["prefix"] + "/lib/libblas.so:/usr/local/lib/:/usr/lib/"
    env["LAPACK"] = vars["prefix"] + "/lib/liblapack.so:/usr/local/lib:/usr/lib/"
    env["BOOST_ROOT"] = vars["prefix"]
    env["BOOST_LIBRARYDIR"] = vars["prefix"] + "/lib/:" + vars["prefix"] + "/lib64/:"
    env["PREFIX"] = vars["prefix"]
    env["GTEST_DIR"] = vars["prefix"] + "/gtest"
    
    #env["PYTHONPATH"] = vars["prefix"] + "/lib/python2.6/site-packages/:" + vars["prefix"] + tryenv("PYTHONPATH")
    tryenv("PYTHONPATH")
    env["LD_LIBRARY_PATH"] = vars["prefix"] + "/lib/:" + vars["prefix"] + "/lib64/:" + tryenv("LD_LIBRARY_PATH")
    tryenv("LD_LIBRARY_PATH")
    env["PKG_CONFIG_PATH"] = vars["prefix"] + "/lib/pkgconfig/:" + vars["prefix"] + "/lib64/pkgconfig/:" + tryenv("PKG_CONFIG_PATH")
    tryenv("PKG_CONFIG_PATH")
    return env


