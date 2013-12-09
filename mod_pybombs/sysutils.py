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

from threading import Thread,Event
#from subprocess import call;
import os,re,shutil,time,glob,copy,signal,operator,re,sys
import subprocess;
import globals;
import logging
from distutils.version import StrictVersion

RED = str('\033[91m');
ENDC = str('\033[0m');      
BOLD = str('\033[1m')

class ColoredConsoleHandler(logging.StreamHandler):
    def emit(self, record):
        # Need to make a actual copy of the record
        # to prevent altering the message for other loggers
        myrecord = copy.copy(record)
        levelno = myrecord.levelno
        if(levelno >= 50):  # CRITICAL / FATAL
            color = '\x1b[31m'  # red
        elif(levelno >= 40):  # ERROR
            color = '\x1b[31m'  # red
        elif(levelno >= 30):  # WARNING
            color = '\x1b[33m'  # yellow
        elif(levelno >= 20):  # INFO
            color = '\x1b[32m'  # green
        elif(levelno >= 10):  # DEBUG
            color = '\x1b[35m'  # pink
        else:  # NOTSET and anything else
            color = '\x1b[0m'  # normal
        myrecord.msg = BOLD + color + str(myrecord.msg) + '\x1b[0m'  # normal
        logging.StreamHandler.emit(self, myrecord)

logger = logging.getLogger('PyBombs.sysutils')
logger.setLevel(logging.INFO)
ch = ColoredConsoleHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)            

def shellexec(cmd):
#    print cmd;
    [pin,pout] = os.popen4( " ".join(cmd) );
    return pout.read();
    
def confirm(msg, default="N", timeout=0):
    # Remove the quesiton mark
    if msg[-1] == "?":
        msg = msg[:-1]
    if default.upper() == "Y":
        msg = msg + "[Y]/N? "
    elif default.upper() == "N":
        msg = msg + "Y/[N]? "
    else:
        raise ValueError("default must be either 'Y' or 'N'")

    while True:
        inp = None
        if(timeout == 0):
            inp = raw_input(msg)
        else:
            import select
            print msg;
            inp,o,e = select.select([sys.stdin], [], [], 10);
            if(inp):
                inp = sys.stdin.readline();
            else:
                inp = "";

        ans = inp.strip().upper()[0:1] # use 0:1 to avoid index error even on empty response
        if ans == "":
            ans = default
        if ans == "Y":
            return True;
        elif ans == "N":
            return False;
        else:
            print "'%s' is not a valid response" % inp

def monitor(cmd,event):                
    
    def kill_process_tree(process, pid):
        children = subprocess.Popen("ps -o pid --ppid %d --noheaders" % (pid), shell=True, stdout=subprocess.PIPE).communicate()[0]
        if len(children) > 0:
            children = children.strip().split("\n")
            for child in children:
                kill_process_tree(None, int(child))
        if process:
            process.terminate()
        else:
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError: pass
            
    # get the artifact to look for
    artifact = None
    if cmd[0:4] == "wget": 
        r = re.search(r'.+/(.+)',cmd)
        artifact = r.group(1)
    elif cmd[0:9] == "git clone" or cmd[0:6] == "svn co":
        r = re.search(r'.+ (.+)',cmd) 
        artifact = r.group(1)
    
    for tries in range(10):
        logger.info("monitor: Tried command %d time(s)" % (tries))
        if tries > 0:
            if cmd[0:4] == "wget":
                # clean up any truncated files
                [try_unlink(f) for f in glob.glob("%s.*" % (cmd.split('/')[-1:][0])) + [cmd.split('/')[-1:][0]]]
            elif cmd[0:9] == "git clone":
                rmrf(cmd.split(' ')[-1])
            elif cmd[0:6] == "svn co":
                svnclean(cmd.split(' ')[-1])
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, env=globals.env)
        pid = p.pid
        parentPid = pid
        while p.poll() == None:
            event.wait(1)
        if event.isSet():
            logger.info("monitor: Caught the quit Event. Killing Subprocess...")
            kill_process_tree(p, pid)
            return
        if cmd[0:9] == "git clone":
            # check for subprocess started by the git subprocess
            try:
                child = subprocess.Popen("ps -o pid --ppid %d --noheaders" % (pid), shell=True, stdout=subprocess.PIPE).communicate()[0]
                if len(child) > 0:
                    pid = int(child.strip().split("\n")[0])
                    grandchild = subprocess.Popen("ps -o pid --ppid %d --noheaders" % (pid), shell=True, stdout=subprocess.PIPE).communicate()[0]
                    if len(grandchild) > 0:
                        pid = int(grandchild.strip().split("\n")[0])
            except subprocess.CalledProcessError:
                pass
        monitorCmd = "ps --noheaders -p %d -o time" % (pid)
        cpuUsageCmd = "ps --noheaders -p %d -o pcpu" % (pid)
        wgetCheckCmd = "ls -s %s" % (artifact)
        gitCheckCmd = "du -s %s" % (artifact)
        oldCpuTime = oldWgetSize = oldGitSize = "0"

        while True:
            retcode = p.poll()
            if retcode is not None:
                if retcode != 0 and tries < 10:
                    break
                else:
                    monitor.result = retcode
                    event.set()
                    return
            try:
                newCpuTime = subprocess.Popen(monitorCmd, shell=True, stdout=subprocess.PIPE).communicate()[0]
            except subprocess.CalledProcessError:
                retcode  = p.poll()
                if retcode != 0 and tries < 10:
                    break
                else:
                    monitor.result = retcode
                    event.set()
                    return
            
            if newCpuTime > oldCpuTime:
                oldCpuTime = newCpuTime
                event.wait(int(globals.vars['timeout']))
                if event.isSet():
                    logger.info("monitor: Caught the quit Event. Killing Subprocess. Please wait...")
                    kill_process_tree(p, parentPid)
                    return
                else: continue 
                
            else:
                logger.info("monitor: No CPU Time accumulated. Check for pulse...")
                if cmd[0:4] == "wget":
                    try:
                        newWgetSize = (subprocess.Popen(wgetCheckCmd, shell=True, stdout=subprocess.PIPE).communicate()[0]).strip().split(' ')[0]
                    except subprocess.CalledProcessError:
                        retcode  = p.poll()
                        if retcode != 0 and tries < 10:
                            break
                        else:
                            monitor.result = retcode
                            event.set()
                            return    
                    try:            
                        if int(newWgetSize) > int(oldWgetSize):
                            oldWgetSize = newWgetSize
                            event.wait(int(globals.vars['timeout']))
                            if event.isSet():
                                logger.info("monitor: Caught the quit Event. Killing Subprocess. Please wait...")
                                kill_process_tree(p, parentPid)
                                return
                            else: continue                        
                    except ValueError: pass                
                elif cmd[0:9] == "git clone" or cmd[0:6] == "svn co":
                    try:
                        newGitSize = (subprocess.Popen(gitCheckCmd, shell=True, stdout=subprocess.PIPE).communicate()[0]).strip().split('\t')[0]
                    except subprocess.CalledProcessError:
                        retcode  = p.poll()
                        if retcode != 0 and tries < 10:
                            break
                        else:
                            monitor.result = retcode
                            event.set()
                            return   
                    try:                 
                        if int(newGitSize) > int(oldGitSize):
                            oldGitSize = newGitSize
                            event.wait(int(globals.vars['timeout']))
                            if event.isSet():
                                logger.info("monitor: Caught the quit Event. Killing Subprocess. Please wait...")
                                kill_process_tree(p, parentPid)
                                return
                            else: continue
                    except ValueError: pass
                else:
                    try:
                        cpuUsage = (subprocess.Popen(cpuUsageCmd, shell=True, stdout=subprocess.PIPE).communicate()[0]).strip()
                    except subprocess.CalledProcessError:
                        retcode  = p.poll()
                        if retcode != 0 and tries < 10:
                            break
                        else:
                            monitor.result = retcode
                            event.set()
                            return                    
                    if float(cpuUsage) > 0:
                        event.wait(int(globals.vars['timeout']))
                        if event.isSet():
                            logger.info("monitor: Caught the quit Event. Killing Subprocess. Please wait...")
                            kill_process_tree(p, parentPid)
                            return
                        else: continue
                        
                # if we get here, no pulse was detected                        
                logger.info("monitor: No pulse detected!")
                kill_process_tree(p, parentPid)
                if tries < 10:
                    logger.info("monitor: Restarting Subprocess...")
                    break
                else:
                    monitor.result = 2
                    event.set()
                    return       

    # tried 10 times
    monitor.result = 2
    event.set()
    return                    


# stdout -> shell
def shellexec_shell(cmd, throw_ex):
    print "shellexec_long: " + cmd
    try:    
        result = None
        quitEvent = Event()
        monitorThread = Thread(target=monitor, args=(cmd,quitEvent,))
        monitorThread.start()
        while monitorThread.isAlive:
            monitorThread.join(1)
            if quitEvent.isSet():
                logger.info("shellexec_shell: Caught the quit Event")
                break
        return monitor.result
    except KeyboardInterrupt:
        logger.info("shellexec_shell: Caught Ctl+C. Killing all threads. Patience...")
        quitEvent.set()
        time.sleep(10)
        exit(0)
    except Exception, e:
        if(throw_ex):
            raise e;
        else:
            return -1;

# stdout -> return
def shellexec_getout(cmd, throw_ex=True):
    print "shellexec_long: " + str(cmd);
    try:
        #p = subprocess.call([cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=globals.env);
        p = subprocess.Popen([cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=globals.env);
        (out,err) = p.communicate();
        return out;
    except Exception, e:
        if(throw_ex):
            raise e;
        else:
            return -1;

def bashexec(cmd):
    if cmd.strip() == "": return 0
    print "bash exec (%s):: %s"%(os.getcwd(),cmd);
    from subprocess import Popen, PIPE
    p = subprocess.Popen(["bash"], stdin=subprocess.PIPE, shell=True, env=globals.env)
    p.stdin.write(cmd)
    if(cmd[-1] != "\n"):
        p.stdin.write("\n")
    p.stdin.close()
    st = p.wait() # unless background execution preferred
    return st;

enable_sudo = True;
def sudorun(cmd):
    if(os.geteuid() == 0):
        rv = bashexec("%s"%(cmd));
    elif(enable_sudo):
        rv = bashexec("sudo %s"%(cmd));
    else:
        print(RED + " *** ERROR: re-run as root to apt-get install %s! *** "%(nlj) + ENDC);
        return False;
    return rv==0;
 
   
def try_unlink(path):
    try:
        os.unlink(path);
    except:
        pass

def rmrf(path):
    try:
        shutil.rmtree(path);
    except:
        pass

def svnclean(path):
    try:
        bashexec("svn cleanup " + path)
    except:
        pass

def which(program):
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None
    

def deb_exists(name, comparator=None, version=None):
    comparatorDict = {'<=':operator.le, '==':operator.eq, '>=':operator.ge, '!=':operator.ne}
    cmp = lambda x, y, z: z(StrictVersion(x),StrictVersion(y))
    a = shellexec(["apt-cache","showpkg",name])
    if len(a) == 0:
        logger.warning("deb_exists: could not find a downloadable version of %s" % (name))
        return False
    if re.search(r'Unable to locate package', a):
        logger.warning("deb_exists: could not find a downloadable version of %s" % (name))
        return False
    m = re.search(r'Versions: \n(\d+:)?([0-9]+\.[0-9]+\.[0-9]+|[0-9]+\.[0-9]+|[0-9]+[a-z]+).*\n', a)
    if(m):
        if not comparator:
            logger.info("deb_exists: Satisfies requirement...found downloadable version of %s" % (name))
            return True
        try:
            if cmp(m.group(2), version, comparatorDict[comparator]):
                if comparator == '==':
                    logger.info("deb_exists: Satisfies requirement...downloadable version of %s (%s) is %s" % (name, m.group(2), version))
                else:
                    logger.info("deb_exists: Satisfies requirement...downloadable version of %s (%s) is %s than %s" % (name, m.group(2), comparator, version))
                return True
            else:
                if comparator == '==':
                    logger.warning("deb_exists: Does not satisfy requirement...downloadable version of %s (%s) is not %s" % (name, m.group(2), version))
                else:
                    logger.warning("deb_exists: Does not satisfy requirement...downloadable version of %s (%s) is not %s than %s" % (name, m.group(2), comparator, version))
                return False
        except ValueError, e:
            logger.error("deb_exists: fatal error: %s" % (e))
            globals.die("Please check the recipe for %s" % (name))
    else: return False
    print a;
    globals.die("This should be unreachable: in deb_exists()");
    
    
def rpm_exists(name, comparator=None, version=None):
    comparatorDict = {'<=':operator.le, '==':operator.eq, '>=':operator.ge, '!=':operator.ne}
    cmp = lambda x, y, z: z(StrictVersion(x),StrictVersion(y))
    a = shellexec(["yum","info",name])
    if len(a) == 0:
        logger.warning("rpm_exists: could not find a downloadable version of %s" % (name))
        return False
    if re.search(r'No matching Packages to list', a):
        logger.warning("rpm_exists: could not find a downloadable version of %s" % (name))
        return False
    m = re.search(r'Version *: (\d+:)?([0-9]+\.[0-9]+\.*[0-9]*|[0-9]+[a-z]+).*\n', a)
    if(m):
        if not comparator:
            logger.info("rpm_exists: Satisfies requirement...found downloadable version of %s" % (name))
            return True
        try:
            if cmp(m.group(2), version, comparatorDict[comparator]):
                if comparator == '==':
                    logger.info("rpm_exists: Satisfies requirement...downloadable version of %s (%s) is %s" % (name, m.group(2), version))
                else:
                    logger.info("rpm_exists: Satisfies requirement...downloadable version of %s (%s) is %s than %s" % (name, m.group(2), comparator, version))
                return True
            else:
                if comparator == '==':
                    logger.warning("rpm_exists: Does not satisfy requirement...downloadable version of %s (%s) is not %s" % (name, m.group(2), version))
                else:
                    logger.warning("rpm_exists: Does not satisfy requirement...downloadable version of %s (%s) is not %s than %s" % (name, m.group(2), comparator, version))
                return False
        except ValueError, e:
            logger.error("rpm_exists: fatal error: %s" % (e))
            globals.die("Please check the recipe for %s" % (name))
    else: return False
    print a;
    globals.die("This should be unreachable: in rpm_exists()");    
    

def have_deb(name, comparator=None, version=None):
    comparatorDict = {'<=':operator.le, '==':operator.eq, '>=':operator.ge, '!=':operator.ne}
    cmp = lambda x, y, z: z(StrictVersion(x),StrictVersion(y))
    #print "have_deb: %s , %s, %s" % (name, comparator, version)
    devnull = open(os.devnull,"w")
    notfound = subprocess.call(["dpkg","-s",name],stdout=devnull,stderr=subprocess.STDOUT)
    devnull.close()
    if notfound:
        return False;
    a = shellexec(["dpkg","-s",name]);
    m = re.search(r'Version: (\d+:)?([0-9]+\.[0-9]+\.[0-9]+|[0-9]+\.[0-9]+|[0-9]+[a-z]+).*\n', a);
#    print "MATCH:" + "1" + str( m.group(1) )  + "2" + str( m.group(2) )
    if(m):
        #print "Deb Version: " + m.group(2);
        if not comparator:
            return True
        try:
            if cmp(m.group(2), version, comparatorDict[comparator]):
                if comparator == '==':
                    logger.info("have_deb: Satisfies requirement...installed version of %s (%s) is %s" % (name, m.group(2), version))
                else:
                    logger.info("have_deb: Satisfies requirement...installed version of %s (%s) is %s than %s" % (name, m.group(2), comparator, version))
                return True
            else:
                if comparator == '==':
                    logger.warning("have_deb: Does not satisfy requirement...installed version of %s (%s) is not %s" % (name, m.group(2), version))
                else:
                    logger.warning("have_deb: Does not satisfy requirement...installed version of %s (%s) is not %s than %s" % (name, m.group(2), comparator, version))
                return False
        except ValueError, e:
            logger.error("have_deb: fatal error: %s" % (e))
            globals.die("Please check the recipe for %s" % (name))
    print a;
    globals.die("This should be unreachable: in have_deb()");


def have_rpm(name, comparator=None, version=None):
    comparatorDict = {'<=':operator.le, '==':operator.eq, '>=':operator.ge, '!=':operator.ne}
    cmp = lambda x, y, z: z(StrictVersion(x),StrictVersion(y))
    #print "have_rpm: %s , %s, %s" % (name, comparator, version)
    a = shellexec(["rpm","-q",name]);
    if(re.search(r'is not installed', a)):
        return False;
    #m = re.search(r'-([\d\.]+)', a);
    m = re.search(r'-([0-9]+\.[0-9]+\.*[0-9]*|[0-9]+[a-z]+).*\n', a)
    if(m):
        #print "RPM Version: " + m.group(1);
        if not comparator:
            return True
        try:
            if cmp(m.group(1), version, comparatorDict[comparator]):
                if comparator == '==':
                    logger.info("have_rpm: Satisfies requirement...installed version of %s (%s) is %s" % (name, m.group(1), version))
                else:
                    logger.info("have_rpm: Satisfies requirement...installed version of %s (%s) is %s than %s" % (name, m.group(1), comparator, version))
                return True
            else:
                if comparator == '==':
                    logger.warning("have_rpm: Does not satisfy requirement...installed version of %s (%s) is not %s" % (name, m.group(1), version))
                else:
                    logger.warning("have_rpm: Does not satisfy requirement...installed version of %s (%s) is not %s than %s" % (name, m.group(1), comparator, version))
                return False
        except ValueError, e:
            logger.error("have_rpm: fatal error: %s" % (e))
            globals.die("Please check the recipe for %s" % (name))
    print a;
    globals.die("This should be unreachable: in have_rpm()");
        

def have_debs(pkg_expr_tree):
    if(which("dpkg") == None):
        return False;
    if(pkg_expr_tree):
        return pkg_expr_tree.ev(have_deb);
    return False;

def have_rpms(pkg_expr_tree):
    if(which("rpm") == None):
        return False;
    if(pkg_expr_tree):
        return pkg_expr_tree.ev(have_rpm);
    return False;
    
def debs_exist(pkg_expr_tree):
    if(which("apt-cache") == None):
        return False
    if(pkg_expr_tree):
        return pkg_expr_tree.ev(deb_exists);
    return False
    
def rpms_exist(pkg_expr_tree):
    if(which("yum") == None):
        return False
    if(pkg_expr_tree):
        return pkg_expr_tree.ev(rpm_exists);
    return False

def rpm_install(namelist):
    print "rpm install: "+str(namelist);
    try:
        nlj = namelist.name;
    except:
        return True;
    if(namelist is list):
        nlj = " ".join(namelist);
    return sudorun("yum -y install %s"%(nlj));

def rpm_install(namelist):
    print "rpm install: "+str(namelist);
    try:
        nlj = namelist.name;
    except:
        if(namelist.combiner == "&&"):
            return rpm_install(namelist.first) and rpm_install(namelist.second);
        elif(namelist.combiner == "||"):
            return rpm_install(namelist.first) or rpm_install(namelist.second);
        else:
            print "invalid combiner logic."
            return false;
#    if(namelist is list):
#        nlj = " ".join(namelist);
    return sudorun("yum -y install %s"%(nlj));

def deb_install(namelist):
    print "deb install: "+str(namelist);
    try:
        nlj = namelist.name;
    except:
        if(namelist.combiner == "&&"):
            return deb_install(namelist.first) and deb_install(namelist.second);
        elif(namelist.combiner == "||"):
            return deb_install(namelist.first) or deb_install(namelist.second);
        else:
            print "invalid combiner logic."
            return false;
#    if(namelist is list):
#        nlj = " ".join(namelist);
    return sudorun("apt-get -y install %s"%(nlj));

def mkchdir(p):
    try:
        os.mkdir(p);
    except:
        pass
    os.chdir(p);


def filemd5(path):
    shellout = shellexec(["md5sum",path]);
    rm = re.search("([a-f0-9]+)\w+.*", shellout);
    hashval = rm.group(1);
    return hashval;


def validate_write_perm(d):
    try:
        tmpfile = os.tempnam(d);
        print "TMPFILE = %s"%(tmpfile)
        f1 = open(tmpfile,"w")
        f1.close()
        os.unlink(tmpfile);
        print "WRITE PERMS OK %s"%(tmpfile)
    except:
        logger.error("Can not write to prefix (%s)! please fix your permissions or choose another prefix!"%(d));
        sys.exit(-10)
