#---------------------------------------------------------------------------------------------------
# Python Module File to translate storage/computing elements into meta site names
#
# Author: C.Paus                                                                      (Jun 16, 2010)
#---------------------------------------------------------------------------------------------------
import os,sys,re,string

def convertToUrl(dir,debug):
    if   re.search('/castor/cern.ch/',     dir):
        storageEle  = 'srm-cms.cern.ch'
        storagePath = '/srm/managerv2?SFN='
    elif re.search('/mnt/hadoop/cms/store',dir):
        storageEle  = 'se01.cmsaf.mit.edu'
        storagePath = '/srm/v2/server?SFN='
    else:
        storageEle  = ''
        storagePath = ''

    if storageEle == '':
        storageUrl = dir
    else:
        storageUrl = 'srm://' + storageEle + ':8443' + storagePath + dir

    if debug:
        print " DEBUG (srm.py): " + storageUrl

    return storageUrl

def convertToHdfs(dir,debug):

    if re.search('/mnt/hadoop/cms/store',dir):
        dir = dir.replace('/mnt/hadoop','')        

    if debug:
        print " DEBUG (srm.py): " + dir

    return dir
