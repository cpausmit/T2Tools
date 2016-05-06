#!/usr/bin/env python
#---------------------------------------------------------------------------------------------------
#
# Script defines core operations on our Tier-2 file system: ls, rm, up(load), down(load)  etc.
#
#                                                                         v0 - Mar 31, 2016 - C.Paus
#---------------------------------------------------------------------------------------------------
import os,sys,subprocess,getopt,re,ConfigParser,time
from subprocess import PIPE
from io import BytesIO

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
    return 'ssh -x ' + server
    
def sshCmd(action):
    # provide basic command to be executed remotely

    cmd = 'hdfs dfs ' + config.get('commands',action)
    return cmd

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

    # show what we do
    if debug>1:
        print ' CMD String: ' + " ".join(list)
        print ' CMD List: '
        print list
    
    p = subprocess.Popen(list,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (out, err) = p.communicate()
    rc = p.returncode

    return (rc,out,err)
    
def t2IsDir(config,src,debug=0):
    # Test whether path is directory (-1: inquery failed, 0: not directory, 1: is directory)

    print '\n NOT YET IMPLEMENTED \n'

    return 0

def t2Ls(config,src,debug=0):
    # List the given path (src)

    print "# o List o  " + src

    # execute the requested action
    (rc,out,err) = executeAction('ls',src)

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
        print ' LINE: ' + line
        f = line.split(' ')
        if len(f) == 8:
            type = 'F'
            if (f[0])[0] == 'd':
                type = 'D'
            size = int(f[4])
            path = f[7]
            print '%s:%d %s'%(type,size,path)
            
    return


def t2Du(config,src,debug=0):

    # loop through the content and show each entry we find
    totalBytes = 0

    print '\n NOT YET IMPLEMENTED \n'

#    if isDir == 1:
#        for entry in data["contents"]:
#            isEntryDir = t2IsDir(config,src,debug)
#            if isEntryDir == 1:
#                # this is a directory
#                subsrc = entry["path"]
#                if subsrc == src:
#                    continue
#                totalBytes += t2Du(config,subsrc,debug)
#            elif isEntryDir == 0:
#                # this is a simple file
#                file = entry["path"]
#                sizeBytes = entry["bytes"]
#                totalBytes += sizeBytes
#                #print  "%10d  "%(sizeBytes) + file
#        print  "%10d -"%(totalBytes) + src
#    elif isDir == 0:
#        totalBytes = data["bytes"]
#    else:
#        print ' ERROR - Requested object does not exist.'
#
    # return the measured size
    return totalBytes

def t2Du1(config,src,debug=0):
    # List disk usage for the given entry but only at most 1 level deep (for directories)

    if debug>-1:
        print "# o DiskUsage -1 o  " + src
    
    print '\n NOT YET IMPLEMENTED \n'

    # loop through the content and show each entry we find
    totalBytes = 0


    # summarize our findings
    if debug>-1:
        print ' %s %.3f'%('Total [GB]:',totalBytes/1000./1000./1000.)

    return totalBytes

def t2Du2(config,src,debug=0):
    # List disk usage for the given entry but only at most 2 level deep (for directories)

    print "# o DiskUsage -2 o  " + src

    print '\n NOT YET IMPLEMENTED \n'

    spaceSubdirs = { src : 0 }
    
    # loop through the content
    totalBytes = 0

    # summarize our findings
    print ' %.3f == %s'%(totalBytes/1000./1000./1000.,'Total [GB]')

    return
    
def t2Cp(config,src,tgt,debug=0):
    # copy a given remote source file (src) to remote target file (tgt)

    print "# o Copy o  " + src + "  -->  " + tgt

    # execute the requested action
    (rc,out,err) = executeAction('cp',src,'',tgt)

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
    
    return

def t2Mv(config,src,tgt,debug=0):
    # move a given remote source file (src) to remote target file (tgt)

    print "# o Move o  " + src + "  -->  " + tgt

    # execute the requested action
    (rc,out,err) = executeAction('mv',src,'',tgt)

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
    
    return
    
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

    return

def t2Down(config,src,tgt,debug=0):
    # upload a given local source file (src) to dropbox target file (tgt)

    print "# o Download o  " + src + "  -->  " + tgt
    print '\n NOT YET IMPLEMENTED \n'
    
    return

def t2Rm(config,src,debug=0):
    # Remove the given path if it is a file

    print "# o RemoveFile o  " + src

    # execute the requested action
    (rc,out,err) = executeAction('rm',src)

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

    return

def t2RmDir(config,src,debug=0):
    # Remove the given path if it is a directory (maybe ? show contents and ask for confirmation)

    print "# o RemoveDir o  " + src

    # execute the requested action
    (rc,out,err) = executeAction('rmdir',src)

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

    return

def t2MkDir(config,src,debug=0):
    # Make given path as a directory

    print "# o MakeDir o  " + src

    # execute the requested action
    (rc,out,err) = executeAction('mkdir',src)

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
    t2Ls(config,src,debug)
elif action == 'rm':
    t2Rm(config,src,debug)
elif action == 'rmdir':
    t2RmDir(config,src,debug)
elif action == 'mkdir':
    t2MkDir(config,src,debug)
elif action == 'du':
    t2Du(config,src,debug)
elif action == 'du1':
    t2Du1(config,src,debug)
elif action == 'du2':
    t2Du2(config,src,debug)
elif action == 'cp':
    t2Cp(config,src,tgt,debug)
elif action == 'mv':
    t2Mv(config,src,tgt,debug)
elif action == 'up':
    t2Up(config,src,tgt,debug)
elif action == 'down':
    t2Down(config,src,tgt,debug)
else:
    print "\n ERROR - Action is undefined: " + action + "\n"
    sys.exit(1)

# if we arrive here, the action was a success :-)
#------------------------------------------------
sys.exit(0)
