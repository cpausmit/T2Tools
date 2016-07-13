#!/usr/bin/env python
#---------------------------------------------------------------------------------------------------
#
# Script defines core operations on our Tier-2 file system: ls, rm, up(load), down(load)  etc.
#
#                                                                         v0 - Mar 31, 2016 - C.Paus
#---------------------------------------------------------------------------------------------------
import os,sys,subprocess,getopt,re,ConfigParser,time
from subprocess import PIPE

#===================================================================================================
#  H E L P E R S
#===================================================================================================
def testLocalSetup(action,src,tgt,debug=0):
    # local setup needs a number of things to be present: make sure all is there, or complain

    # check environment variables
    base = os.environ.get('T2TOOLS_BASE','')
    if base == '':
        print '\n ERROR -- t2tools is not setup T2TOOLS_BASE environment not set.\n'
        sys.exit(1)

    server = os.environ.get('T2TOOLS_SERVER','')
    if server == '':
        print '\n ERROR -- t2tools is not setup T2TOOLS_SERVER environment not set.\n'
        sys.exit(1)

    # every action needs a source
    if src == '':
        print '\n ERROR - no source specified. EXIT!\n'
        print usage
        sys.exit(1)

    # some actions need a target
    if action == 'up' or action == 'down' or action == 'cp' or action == 'mv':
        if tgt == '':
            print '\n ERROR - no target specified. EXIT!\n'
            print usage
            sys.exit(1)

    if debug>1:
        print '\n INFO -- local setup looks ok.\n'
            
    return

def sshBase():
    # provide basic ssh command

    server = os.environ.get('T2TOOLS_SERVER')
    return 'ssh -x ' + os.environ.get('T2TOOLS_USER') + '@' + server
    
def sshCmd(action):
    # provide basic command to be executed remotely

    cmd = 'hdfs dfs ' + config.get('commands',action)
    return cmd

def getInternalRC(output):
    # find the return code from the command executed at thje remote site

    irc = -99 # default means it failed
    lines = output.split('\n')    

    # very carefully extracting the internal retrun code
    if len(lines) > 1:
        lastLine = lines[-2]
        f = lastLine.split(':')
        if len(f) > 1:
            if f[0] == 'IRC':
                lines = lines[:-2] # overwite output removing the IRC line
                output = "\n".join(lines)
                irc = int(f[1])

    return (irc,output)

def executeAction(action,src,opt='',tgt=''):
    # execute the defined action and return rc  - return code
    #                                       out - standard output
    #                                       err - standard error
    
    list = sshBase().split(' ')
    list.append(sshCmd(action))
    if opt != '':
        list.append(opt)
    list.append(src)
    if tgt != '':
        list.append(tgt)
    list.append('; echo IRC:$?') # this will make sure that we know the internal return code

    # show what we do
    if debug>1:
        print ' CMD String: ' + " ".join(list)
        print ' CMD List: '
        print list
    
    p = subprocess.Popen(list,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (out, err) = p.communicate()
    rc = p.returncode
    (irc, out) = getInternalRC(out) # get the internal retrun code and clean the output

    if irc != 0:
        print " ERROR on remote end: %d"%(int(irc))
        print " "
        print " " + err
            
    return (irc,rc,out,err)
    
def t2Exists(config,src,debug=0):
    # Test whether path is file (0: not a file, 1: is a file)
    # CAREFUL this is a little twisted as I invert the logic, but t2IsFile should be one if 'yes'

    # execute the requested action
    (irc,rc,out,err) = executeAction('test',src)
    #print " RC, IRC: %d %d"%(rc,irc)

    lines = out.split('\n')
    if irc == 0:
        return 1
    else:
        if debug>0:
            lines = err.split('\n')
            if len(lines) > 0 and err != '':
                print 'ERROR -- %s: %d\n%s'%('test',len(lines),err)
            lines = out.split('\n')
            print 'OUTPUT -- %s: %d\n%s'%('test',len(lines),out)
        return 0

def t2IsDir(config,src,debug=0):
    # Test whether path is directory (0: not a directory, 1: is directory)
    # CAREFUL this is a little twisted as I invert the logic, but t2IsDir should be one if 'yes'

    # execute the requested action
    (irc,rc,out,err) = executeAction('testDir',src)

    lines = out.split('\n')
    if irc == 0:
        return 1
    else:
        if debug>0:
            lines = err.split('\n')
            if len(lines) > 0 and err != '':
                print 'ERROR -- %s: %d\n%s'%('testDir',len(lines),err)
            lines = out.split('\n')
            print 'OUTPUT -- %s: %d\n%s'%('testDir',len(lines),out)
        return 0

def t2Ls(config,src,debug=0):
    # List the given path (src)

    if debug>0:
        print "# o List o  " + src

    # execute the requested action
    (irc,rc,out,err) = executeAction('ls',src)

    if debug > 0:
        print ' Return code: %d'%(rc)
        print ' Std Output : \n%s'%(out)
        print ' Std Error  : \n%s'%(err)
        print ''
        
    # deal with error
    if rc != 0:
        print ' RC: %d\n'%(rc)
        lines = err.split('\n')
        if len(lines) > 0 and err != '':
            print 'ERROR -- %s: %d\n%s'%('ls',len(lines),err)
        sys.exit(rc)

    # analyze the output
    lines = out.split('\n')
    for line in lines:
        line = re.sub(' +',' ',line)
        f = line.split(' ')
        if debug>1:
            print ' LINE(%d): %s'%(len(f),line)

        if len(f) == 8:
            type = 'F'
            if (f[0])[0] == 'd':
                type = 'D'
            size = int(f[4])
            path = f[7]
            baseFile = (path.split('/')).pop()
            #print '%d %s'%(size,baseFile)
            print '%s:%d %s'%(type,size,path)
            
    return irc

def t2Du(config,src,debug=0):

    # loop through the content and show each entry we find

    # execute the requested action
    (irc,rc,out,err) = executeAction('du',src)

    if debug > 0:
        print ' Return code: %d'%(rc)
        print ' Std Output : \n%s'%(out)
        print ' Std Error  : \n%s'%(err)
        print ''
        
    # deal with error
    if rc != 0:
        print ' RC: %d\n'%(rc)
        lines = err.split('\n')
        if len(lines) > 0 and err != '':
            print 'ERROR -- %s: %d\n%s'%('ls',len(lines),err)
        sys.exit(rc)

    # analyze the output
    lines = out.split('\n')
    for line in lines:
        print line

    return irc

def t2Cp(config,src,tgt,debug=0):
    # copy a given remote source file (src) to remote target file (tgt)

    print "# o Copy o  " + src + "  -->  " + tgt

    # execute the requested action
    (irc,rc,out,err) = executeAction('cp',src,'',tgt)

    if debug > 0:
        print ' Return code: %d'%(rc)
        print ' Std Output : \n%s'%(out)
        print ' Std Error  : \n%s'%(err)
        print ''
        
    # deal with error
    if rc != 0:
        print ' RC: %d\n'%(rc)
        lines = err.split('\n')
        if len(lines) > 0 and err != '':
            print 'ERROR -- %s: %d\n%s'%('cp',len(lines),err)
        sys.exit(rc)
    
    return irc

def t2Mv(config,src,tgt,debug=0):
    # move a given remote source file (src) to remote target file (tgt)

    print "# o Move o  " + src + "  -->  " + tgt

    # execute the requested action
    (irc,rc,out,err) = executeAction('mv',src,'',tgt)

    if debug > 0:
        print ' Return code: %d'%(rc)
        print ' Std Output : \n%s'%(out)
        print ' Std Error  : \n%s'%(err)
        print ''
        
    # deal with error
    if rc != 0:
        print ' RC: %d\n'%(rc)
        lines = err.split('\n')
        if len(lines) > 0 and err != '':
            print 'ERROR -- %s: %d\n%s'%('mv',len(lines),err)
        sys.exit(rc)
    
    return irc
    
def t2Up(config,src,tgt,debug=0):
    # upload a given local source file (src) to dropbox target file (tgt)

    print "# o Upload o  " + src + "  -->  " + tgt
    print '\n NOT YET IMPLEMENTED \n'

    tStart = time.time()

    # size determines whether in one shot or by chunks
    statinfo = os.stat(src)
    size = statinfo.st_size
  
    tEnd = time.time()

    print " transfered: %.0f MB in %.2f sec at %.2f MB/sec"%\
        (size/1000./1000.,tEnd-tStart,size/1000./1000./(tEnd-tStart))

    return irc

def t2Down(config,src,tgt,debug=0):
    # upload a given local source file (src) to dropbox target file (tgt)

    print "# o Download o  " + src + "  -->  " + tgt

    # is it a directory or file
    if os.path.isdir(tgt):
        dtarget = tgt
        ftarget = src.split("/").pop()
    else:
        dtarget =  "/".join(tgt.split("/").pop())
        ftarget = src.split("/").pop() 
        
    
    xrdSrc = "/" + "/".join((src.split("/"))[2:])
    cmd = "xrdcp root://xrootd.cmsaf.mit.edu/" + xrdSrc + " " + dtarget + "/" + ftarget + ".partial"
    list = cmd.split(' ')
    p = subprocess.Popen(list,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (out, err) = p.communicate()
    rc = p.returncode

    if rc != 0:
        print " ERROR: %d"%(int(rc))
        print " "
        print " " + err

    cmd = "mv " + dtarget + "/" + ftarget + ".partial " + dtarget + "/" + ftarget
    os.system(cmd)

    return rc

def t2Rm(config,src,debug=0):
    # Remove the given path if it is a file

    print "# o RemoveFile o  " + src

    # execute the requested action
    (irc,rc,out,err) = executeAction('rm',src)

    if debug > 0:
        print ' Return code: %d'%(rc)
        print ' Std Output : \n%s'%(out)
        print ' Std Error  : \n%s'%(err)
        print ''
        
    # deal with error
    if rc != 0:
        print ' RC: %d\n'%(rc)
        lines = err.split('\n')
        if len(lines) > 0 and err != '':
            print 'ERROR -- %s: %d\n%s'%('rm',len(lines),err)
        sys.exit(rc)

    return irc

def t2RmDir(config,src,debug=0):
    # Remove the given path if it is a directory (maybe ? show contents and ask for confirmation)

    print "# o RemoveDir o  " + src

    # execute the requested action
    (irc,rc,out,err) = executeAction('rmdir',src)

    if debug > 0:
        print ' Return code: %d'%(rc)
        print ' Std Output : \n%s'%(out)
        print ' Std Error  : \n%s'%(err)
        print ''
        
    # deal with error
    if rc != 0:
        print ' RC: %d\n'%(rc)
        lines = err.split('\n')
        if len(lines) > 0 and err != '':
            print 'ERROR -- %s: %d\n%s'%('rmdir',len(lines),err)
        sys.exit(rc)

    return irc

def t2MkDir(config,src,debug=0):
    # Make given path as a directory

    print "# o MakeDir o  " + src

    # execute the requested action
    (irc,rc,out,err) = executeAction('mkdir',src)

    if debug > 0:
        print ' Return code: %d'%(rc)
        print ' Std Output : \n%s'%(out)
        print ' Std Error  : \n%s'%(err)
        print ''
        
    # deal with error
    if rc != 0:
        print ' RC: %d\n'%(rc)
        lines = err.split('\n')
        if len(lines) > 0 and err != '':
            print 'ERROR -- %s: %d\n%s'%('mkdir',len(lines),err)
        sys.exit(rc)

    return

#===================================================================================================
#  M A I N
#===================================================================================================
# define string to explain usage of the script
usage =  " Usage: t2tools.py  --action=<what do you want to do?>\n"
usage += "                    --source=<the source the action should apply to>\n"
usage += "                  [ --target=<the target where data should go> ]\n"
usage += "                  [ --debug=0 ]  <-- see various levels of debug output\n"
usage += "                  [ --help ]\n"

# define valid options which can be specified and check out the command line
valid = ['configFile=','action=','source=','target=','debug=','help']
try:
    opts, args = getopt.getopt(sys.argv[1:], "", valid)
except getopt.GetoptError, ex:
    print usage
    print str(ex)
    sys.exit(1)

# get all configuration parameters
# --------------------------------
# set defaults for each command line parameter/option
configFile = os.environ.get('T2TOOLS_BASE','NOT-DEFINED') + '/config/' + 't2tools.cfg'

action = 'ls'
src = ''
tgt = ''
debug = 0

# read new values from the command line
for opt, arg in opts:
    if   opt == "--help":
        print usage
        sys.exit(0)
    elif opt == "--action":
        action = arg
    elif opt == "--configFile":
        configFile = arg
    elif opt == "--source":
        src = arg
    elif opt == "--target":
        tgt = arg
    elif opt == "--debug":
        debug = int(arg)

# remove the '/mnt/hadoop' mount point
if src.startswith('/mnt/hadoop/'):
    src = '/' + '/'.join(src.split('/')[3:])
if tgt.startswith('/mnt/hadoop/'):
    tgt = '/' + '/'.join(tgt.split('/')[3:])

# inspecting the local setup
#---------------------------
testLocalSetup(action,src,tgt,debug)

# read the configuration file
#----------------------------
config = ConfigParser.RawConfigParser()
config.read(configFile)

# looks like we have a valid request
#-----------------------------------
if   action == 'ls':
    rc = t2Ls(config,src,debug)
elif action == 'rm':
    rc = t2Rm(config,src,debug)
elif action == 'rmdir':
    rc = t2RmDir(config,src,debug)
elif action == 'mkdir':
    rc = t2MkDir(config,src,debug)
elif action == 'du':
    rc = t2Du(config,src,debug)
elif action == 'cp':
    rc = t2Cp(config,src,tgt,debug)
elif action == 'mv':
    rc = t2Mv(config,src,tgt,debug)
elif action == 'up':
    rc = t2Up(config,src,tgt,debug)
elif action == 'down':
    rc = t2Down(config,src,tgt,debug)
elif action == 'testDir':
    rc = t2IsDir(config,src,debug)
    if int(rc) == 0: # make sure if it is not a directory to return non-zero code
        sys.exit(1)
elif action == 'test':
    rc = t2Exists(config,src,debug)
    if int(rc) == 0: # make sure if it is not a file to return non-zero code
        sys.exit(1)
else:
    print "\n ERROR - Action is undefined: " + action + "\n"
    sys.exit(1)

# if we arrive here, the action was a success :-)
#------------------------------------------------
sys.exit(rc)
