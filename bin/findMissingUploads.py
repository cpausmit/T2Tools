#!/usr/bin/env python
#---------------------------------------------------------------------------------------------------
#
# Find missing files in all samples in a given book.
#
#---------------------------------------------------------------------------------------------------
import os,sys

MOUNT = "/mnt/hadoop"
TRUNC = "/cms"
DIR = "/store/user/paus"

def missingFilesInSample(book,sample,tmpDir):

    if os.path.exists(tmpDir +'/missing_'+sample+'.list'):
        print ' Missing file list already exists. ' + tmpDir + '/missing_'+sample+'.list'
        return

    os.system("date")
    print " Working on sample: " + sample
    allFiles = []
    print ' Find all files (T2).'
    cmd = 'list ' + MOUNT + TRUNC + DIR + "/" + book \
        + '/' + sample + " | grep .root"
    for line in os.popen(cmd).readlines():
        file = line[:-1]
        file = (file.split(" ")).pop()
        allFiles.append(file)
    
    doneFiles = []
    print ' Find done files (Dropbox).'
    cmd = "python "+ os.getenv("PYCOX_BASE", None) + "/pycox.py --action=ls --source=" \
        + TRUNC + DIR + '/'+ book + '/' + sample + "| grep root"
    for line in os.popen(cmd).readlines():
        file = line[:-1]
        file = (file.split(" ")).pop()
        file = (file.split("/")).pop()
        doneFiles.append(file)
    
    missingFiles = []
    print ' Find missing files (missing in Dropbox).'
    for file in allFiles:
        if file not in doneFiles:
            missingFiles.append(file)
            print TRUNC + DIR + "/" + book + '/' + sample + '/' + file        
    
    print ' Numbers all/done/missing:  %4d / %4d / %4d'%\
        (len(allFiles),len(doneFiles),len(missingFiles))

    with open(tmpDir + '/missing_'+sample+'.list','w') as fileH:
        for file in missingFiles:
            fileH.write(TRUNC + DIR + "/" + book + '/' + sample + '/' + file + '\n')

#---------------------------------------------------------------------------------------------------
#  M A I N
#---------------------------------------------------------------------------------------------------
book = sys.argv[1]
pattern = ''
if len(sys.argv) > 2:
    pattern = sys.argv[2]

# is everything setup?
pycox = os.getenv("PYCOX_BASE", None)
if not pycox:
    print ' ERROR - no pycox is setup'
    sys.exit(1)

# hi, here we are!
os.system("date")

# make a list of all samples in this book
allSamples = []
print ' Find all samples (T2).'
cmd = 'list ' + MOUNT + TRUNC + DIR + "/" + book + "| grep ^0"
if pattern != "":
    cmd += "| grep %s"%(pattern)
for line in os.popen(cmd).readlines():
    sample = (line[:-1].split(" ")).pop()
    allSamples.append(sample)

# say what we found
print ' Number of samples found: %d'%(len(allSamples))

# make a cache for the missing files
tmpDir = '/tmp/' + book.replace('/','_')
if not os.path.exists(tmpDir):
    cmd = 'mkdir -p ' + tmpDir
    print '\n Making cache for missing file summary (%s).\n'%(tmpDir)
    os.system('mkdir -p ' + tmpDir)
    
# now loop through all samples and find the missing files
for sample in allSamples:
    missingFilesInSample(book,sample,tmpDir)
