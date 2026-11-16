#!/usr/bin/env python3
#---------------------------------------------------------------------------------------------------
#
# Script defines core operations on our Tier-2 file system: ls, rm, up(load), down(load)  etc.
#
# The Tier-2 storage is a Ceph filesystem which is POSIX mounted on a storage server. All operations
# are executed on that server through ssh. Users always deal with the logical name space (/cms/...)
# which is mapped to the physical mount point (root parameter in the configuration) on the server.
#
#                                                                         v0 - Mar 31, 2016 - C.Paus
#                                                                         v1 - Nov 16, 2026 - Ceph
#---------------------------------------------------------------------------------------------------
import os,sys,subprocess,getopt,re,time
import configparser

# keep our messages in order with the error messages
sys.stdout.reconfigure(line_buffering=True)

#===================================================================================================
#  H E L P E R S
#===================================================================================================
# characters allowed in a path and in options (protects the remote shell, globs are allowed)
VALID_PATH = re.compile(r'^[A-Za-z0-9_.\-+=,:@%/*?\[\]]+$')
VALID_OPTS = re.compile(r'^[A-Za-z0-9\-+=, ]*$')

# ls output format: permissions links user group size date time path (same 8 fields as hdfs)
LS_FORMAT  = '%M %n %u %g %s %TY-%Tm-%Td %TH:%TM %p\\n'
LS_FORMATD = '%M %n %u %g 0 %TY-%Tm-%Td %TH:%TM %p\\n'

def error(text,rc=1):
    # print error message and exit
    sys.stderr.write('\n ERROR -- %s\n\n'%(text))
    sys.exit(rc)

def debugPrint(text,level=1):
    if debug >= level:
        print(' DEBUG: ' + text)

def testLocalSetup(action,src,tgt):
    # local setup needs a number of things to be present: make sure all is there, or complain

    if os.environ.get('T2TOOLS_BASE','') == '':
        error('t2tools is not setup T2TOOLS_BASE environment not set.')

    # every action needs a source
    if src == '':
        print(usage)
        error('no source specified. EXIT!')

    # some actions need a target
    if action in ('up','down','cp','mv') and tgt == '':
        print(usage)
        error('no target specified. EXIT!')

    debugPrint('local setup looks ok.',2)

    return

def toLogical(path):
    # convert any known representation of a Tier-2 file into the logical name (/cms/...)

    root = config.get('cfg','root')
    if   path.startswith('root://'):                    # root://server//store/... -> /cms/store/...
        path = '/cms/' + '/'.join(path.split('/')[3:]).lstrip('/')
    elif path.startswith('/mnt/hadoop/cms'):            # legacy hadoop mount
        path = path[len('/mnt/hadoop'):]
    elif path.startswith(root + '/cms'):                # physical path on the server
        path = path[len(root):]

    return re.sub('/+','/',path)

def toPhysical(path):
    # convert a logical name into the physical name on the server, refuse anything suspicious

    if not (path == '/cms' or path.startswith('/cms/')):
        error('path not on Tier-2 (has to start with /cms/): ' + path)
    if not VALID_PATH.match(path) or '..' in path.split('/'):
        error('invalid characters or components in path: ' + path)

    return config.get('cfg','root') + path

def stripRoot(text):
    # convert physical names in output from the server back to logical names
    return text.replace(config.get('cfg','root') + '/cms','/cms')

def sshBase():
    # provide basic ssh command
    return ['ssh','-x','-o','BatchMode=yes',config.get('cfg','user') + '@' + config.get('cfg','server')]

def executeRemote(script):
    # execute the given shell script on the server and return rc  - return code
    #                                                         out - standard output
    #                                                         err - standard error
    # ssh returns the exit code of the remote script (255 is reserved for ssh problems)

    debugPrint('server script:\n' + script,2)

    p = subprocess.Popen(sshBase() + ['bash','-s'],stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (out,err) = p.communicate(script.encode())
    rc = p.returncode
    out = stripRoot(out.decode())
    err = stripRoot(err.decode())

    if debug > 0:
        print(' Return code: %d'%(rc))
        print(' Std Output : \n%s'%(out))
        print(' Std Error  : \n%s'%(err))
    if rc == 255:
        sys.stderr.write(' ERROR -- ssh to %s failed.\n'%(config.get('cfg','server')))

    return (rc,out,err)

def executeAction(name,script):
    # execute remote action and deal with the errors (exit on failure)

    (rc,out,err) = executeRemote(script)
    if rc != 0:
        sys.stderr.write(' ERROR -- %s failed (rc=%d)\n%s'%(name,rc,err))
        sys.exit(rc)

    return out

def humanSize(size):
    # make size human readable (similar to hdfs dfs -du -h)
    for unit in ('','K','M','G','T'):
        if size < 1024 or unit == 'T':
            break
        size /= 1024.
    if unit == '':
        return '%d'%(size)
    return '%.1f %s'%(size,unit)

def transferCmd(direction,local,logical):
    # command to transfer a file between local and the server (direction: up or down)

    method = config.get('cfg','transfer')
    if   method == 'ssh':
        remote = config.get('cfg','user') + '@' + config.get('cfg','server') + ':' + toPhysical(logical)
        cmd = ['scp','-q','-o','BatchMode=yes']
    elif method == 'xrootd':
        remote = config.get('cfg','xrootd').rstrip('/') + '/' + logical[len('/cms'):]
        cmd = ['xrdcp','-s']
    else:
        error('unknown transfer method in configuration: ' + method)

    if direction == 'up':
        return cmd + [local,remote]
    return cmd + [remote,local]

#===================================================================================================
#  A C T I O N S
#===================================================================================================
def t2Exists(src):
    # Test whether path exists (1: exists, 0: does not exist)

    (rc,out,err) = executeRemote('test -e "%s"\n'%(toPhysical(src)))
    return 1 if rc == 0 else 0

def t2IsDir(src):
    # Test whether path is directory (1: is directory, 0: not a directory)

    (rc,out,err) = executeRemote('test -d "%s"\n'%(toPhysical(src)))
    return 1 if rc == 0 else 0

def t2Ls(src,options):
    # List the given path (src), directories show their content, globs are expanded on the server

    debugPrint("# o List o  " + src)

    script  = 'rc=0\n'
    script += 'for p in %s; do\n'%(toPhysical(src))
    script += '  if   [ -d "$p" ]; then find "$p" -mindepth 1 -maxdepth 1 \\( -type d -printf "%s" \\) -o -printf "%s"\n'%(LS_FORMATD,LS_FORMAT)
    script += '  elif [ -e "$p" ]; then find "$p" -maxdepth 0 -printf "%s"\n'%(LS_FORMAT)
    script += '  else echo "ls: $p: No such file or directory" >&2; rc=1; fi\n'
    script += 'done\n'
    script += 'exit $rc\n'
    out = executeAction('ls',script)

    # analyze the output (sorted by path as hdfs used to do)
    entries = []
    for line in out.split('\n'):
        f = line.split(' ')
        if len(f) < 8:
            continue
        path = ' '.join(f[7:])
        entries.append((path,f))
    for path,f in sorted(entries):
        if options == '-l':
            print(' '.join(f[:7]) + ' ' + path)
        else:
            type = 'D' if f[0].startswith('d') else 'F'
            print('%s:%d %s'%(type,int(f[4]),path))

    return 0

def t2Du(src):
    # Show the size of all entries in the given path (src), nothing is shown for an empty directory
    # On Ceph the recursive size of a directory is available as an extended attribute (fast).

    script  = 'size() { if [ -d "$1" ]; then\n'
    script += '    s=$(getfattr --only-values -n ceph.dir.rbytes "$1" 2> /dev/null) || s=$(du -sb "$1" | cut -f1)\n'
    script += '  else s=$(stat -c %s "$1"); fi; echo "$s $1"; }\n'
    script += 'rc=0\n'
    script += 'for p in %s; do\n'%(toPhysical(src))
    script += '  if   [ -d "$p" ]; then while read -r c; do size "$c"; done < <(find "$p" -mindepth 1 -maxdepth 1)\n'
    script += '  elif [ -e "$p" ]; then size "$p"\n'
    script += '  else echo "du: $p: No such file or directory" >&2; rc=1; fi\n'
    script += 'done\n'
    script += 'exit $rc\n'
    out = executeAction('du',script)

    entries = []
    for line in out.split('\n'):
        f = line.split(' ',1)
        if len(f) == 2 and f[0].isdigit():
            entries.append((f[1],int(f[0])))
    for path,size in sorted(entries):
        print('%s  %s'%(humanSize(size),path))

    return 0

def t2Simple(name,command,src,tgt='',options=''):
    # Run a simple command (rm, mv, mkdir ...) on the server

    if not VALID_OPTS.match(options):
        error('invalid options: ' + options)
    script = '%s %s -- %s'%(command,options,toPhysical(src))
    if tgt != '':
        script += ' ' + toPhysical(tgt)
    executeAction(name,script + '\n')

    return 0

def t2Cp(src,tgt):
    # copy a given remote source file (src) to remote target file (tgt)
    print("# o Copy o  " + src + "  -->  " + tgt)
    return t2Simple('cp','cp',src,tgt)

def t2Mv(src,tgt):
    # move a given remote source file (src) to remote target file (tgt)
    print("# o Move o  " + src + "  -->  " + tgt)
    return t2Simple('mv','mv',src,tgt)

def t2Rm(src):
    # Remove the given path if it is a file
    print("# o RemoveFile o  " + src)
    return t2Simple('rm','rm',src)

def t2Rmr(src):
    # Remove the given path recursively, protect the upper part of the tree
    print("# o RemoveRecursive o  " + src)
    if len([ d for d in src.split('/') if d != '' ]) < int(config.get('cfg','minRmrDepth')):
        error('refusing to remove recursively, path is too high up in the tree: ' + src)
    return t2Simple('rmr','rm -r',src)

def t2RmDir(src):
    # Remove the given path if it is an empty directory
    print("# o RemoveDir o  " + src)
    return t2Simple('rmdir','rmdir',src)

def t2MkDir(src,options):
    # Make given path as a directory (options: -p)
    print("# o MakeDir o  " + src)
    return t2Simple('mkdir','mkdir',src,'',options)

def t2Chmod(src,options):
    # Change the permissions of the given path (options: ex. "-R a+r")
    print("# o ChangeMod o  " + src)
    return t2Simple('chmod','chmod',src,'',options)

def t2Up(src,tgt):
    # upload a given local source file (src) to Tier-2 target file (tgt)

    print("# o Upload o  " + src + "  -->  " + tgt)

    tStart = time.time()
    size = os.stat(src).st_size
    toPhysical(tgt)                     # make sure target is valid before we start

    cmd = transferCmd('up',src,tgt + '.partial')
    debugPrint(' '.join(cmd))
    rc = subprocess.call(cmd)
    if rc != 0:
        sys.stderr.write(' ERROR -- upload failed (rc=%d): %s\n'%(rc,' '.join(cmd)))
        executeRemote('rm -f -- %s.partial\n'%(toPhysical(tgt)))
        return rc

    print("#   upload 'partial' completed. Move into final location.")
    rc = t2Mv(tgt + '.partial',tgt)

    dt = max(time.time() - tStart,0.001)
    print(" uploaded: %.0f MB in %.2f sec at %.2f MB/sec"%(size/1.e6,dt,size/1.e6/dt))

    return rc

def t2Down(src,tgt):
    # download a given remote source file (src) to a local target file (tgt)

    print("# o Download o  " + src + "  -->  " + tgt)

    if os.path.isdir(tgt):
        tgt = tgt + '/' + src.split('/')[-1]

    cmd = transferCmd('down',tgt + '.partial',src)
    debugPrint(' '.join(cmd))
    rc = subprocess.call(cmd)
    if rc != 0:
        sys.stderr.write(' ERROR -- download failed (rc=%d): %s\n'%(rc,' '.join(cmd)))
        if os.path.exists(tgt + '.partial'):
            os.remove(tgt + '.partial')
        return rc

    os.rename(tgt + '.partial',tgt)

    return 0

#===================================================================================================
#  M A I N
#===================================================================================================
# define string to explain usage of the script
usage =  " Usage: t2tools.py  --action=<ls,du,test,testDir,rm,rmr,rmdir,mkdir,chmod,cp,mv,up,down>\n"
usage += "                    --source=<the source the action should apply to>\n"
usage += "                  [ --target=<the target where data should go> ]\n"
usage += "                  [ --options=<options: ls '-l', mkdir '-p', chmod '-R a+r'> ]\n"
usage += "                  [ --configFile=<alternative configuration file> ]\n"
usage += "                  [ --debug=0 ]  <-- see various levels of debug output\n"
usage += "                  [ --help ]\n"

# define valid options which can be specified and check out the command line
valid = ['configFile=','options=','action=','source=','target=','debug=','help']
try:
    opts, args = getopt.getopt(sys.argv[1:], "", valid)
except getopt.GetoptError as ex:
    print(usage)
    print(str(ex))
    sys.exit(1)

# get all configuration parameters
# --------------------------------
# set defaults for each command line parameter/option
configFile = os.environ.get('T2TOOLS_BASE','NOT-DEFINED') + '/config/' + 't2tools.cfg'

action = 'ls'
options = ''
src = ''
tgt = ''
debug = 0

# read new values from the command line
for opt, arg in opts:
    if   opt == "--help":
        print(usage)
        sys.exit(0)
    elif opt == "--action":
        action = arg
    elif opt == "--options":
        options = arg
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
testLocalSetup(action,src,tgt)

# read the configuration file
#----------------------------
config = configparser.RawConfigParser(defaults={'transfer': 'ssh', 'minRmrDepth': '5',
                                                'xrootd': 'root://xrootd.cmsaf.mit.edu/'})
if config.read(configFile) == []:
    error('configuration file not found: ' + configFile)

# local files (up: source, down: target) stay as they are, the rest is a Tier-2 path
if action != 'up':
    src = toLogical(src)
if action != 'down':
    tgt = toLogical(tgt)

# looks like we have a valid request
#-----------------------------------
if   action == 'ls':
    rc = t2Ls(src,options)
elif action == 'rm':
    rc = t2Rm(src)
elif action == 'rmr':
    rc = t2Rmr(src)
elif action == 'rmdir':
    rc = t2RmDir(src)
elif action == 'mkdir':
    rc = t2MkDir(src,options)
elif action == 'chmod':
    rc = t2Chmod(src,options)
elif action == 'du':
    rc = t2Du(src)
elif action == 'cp':
    rc = t2Cp(src,tgt)
elif action == 'mv':
    rc = t2Mv(src,tgt)
elif action == 'up':
    rc = t2Up(src,tgt)
elif action == 'down':
    rc = t2Down(src,tgt)
elif action == 'testDir':
    rc = 0 if t2IsDir(src) == 1 else 1
elif action == 'test':
    rc = 0 if t2Exists(src) == 1 else 1
else:
    error("Action is undefined: " + action)

# if we arrive here, the action was executed, hand back the return code
#----------------------------------------------------------------------
sys.exit(rc)
