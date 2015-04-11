# -*- coding: utf-8 -*-
#
#  IPTV Tools
#
#  $Id$
#
# 
###################################################
# LOCAL import
###################################################

###################################################
 
###################################################
# FOREIGN import
###################################################
from Components.config import config
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_CONFIG
from enigma import eConsoleAppContainer
from time import sleep as time_sleep, time
from urllib2 import Request, urlopen, URLError, HTTPError
from datetime import datetime
import urllib
import urllib2
import traceback
import re
import sys
import os
import stat
import codecs
try:    import json
except: import simplejson as json
###################################################
class eConnectCallbackObj:
    OBJ_ID = 0
    OBJ_NUM = 0
    def __init__(self, obj=None, connectHandler=None):
        eConnectCallbackObj.OBJ_ID += 1
        eConnectCallbackObj.OBJ_NUM += 1
        self.objID = eConnectCallbackObj.OBJ_ID
        printDBG("eConnectCallbackObj.__init__ objID[%d] OBJ_NUM[%d]" % (self.objID, eConnectCallbackObj.OBJ_NUM))
        self.connectHandler = connectHandler
        self.obj = obj
    
    def __del__(self):
        eConnectCallbackObj.OBJ_NUM -= 1
        printDBG("eConnectCallbackObj.__del__ objID[%d] OBJ_NUM[%d]" % (self.objID, eConnectCallbackObj.OBJ_NUM))
        try:
            if 'connect' not in dir(self.obj):
                if 'get' in dir(self.obj):
                    self.obj.get().remove(self.connectHandler)
                else:
                    self.obj.remove(self.connectHandler)
            else:
                del self.connectHandler
        except:
            printExc()
        self.connectHandler = None
        self.obj = None

def eConnectCallback(obj, callbackFun, withExcept=False):
    try:
        if 'connect' in dir(obj):
            return eConnectCallbackObj(obj, obj.connect(callbackFun))
        else:
            if 'get' in dir(obj):
                obj.get().append(callbackFun)
            else:
                obj.append(callbackFun)
            return eConnectCallbackObj(obj, callbackFun)
    except:
        printExc("eConnectCallback")
    return eConnectCallbackObj()
    
class iptv_system:
    '''
    Calling os.system is not recommended, it may fail due to lack of memory,
    please use iptv_system instead, this should be used as follow:
    self.handle = iptv_system("cmd", callBackFun)
    there is need to have reference to the obj created by iptv_system, 
    other ways behavior is undefined
    
    iptv_system must be used only inside MainThread context, please see 
    iptv_execute class from asynccall module which is dedicated to be
    used inside other threads
    '''
    def __init__(self, cmd, callBackFun=None):
        printDBG("iptv_system.__init__ ---------------------------------")
        self.callBackFun = callBackFun
        
        self.console = eConsoleAppContainer()
        if None != self.callBackFun:
            self.console_appClosed_conn = eConnectCallback(self.console.appClosed, self._cmdFinished)
            self.console_stdoutAvail_conn = eConnectCallback(self.console.stdoutAvail, self._dataAvail)
            self.outData     = ""
        self.console.execute( cmd )
        
    def terminate(self, doCallBackFun=False):
        self.kill(doCallBackFun)
        
    def kill(self, doCallBackFun=False):
        if None != self.console:
            if None != self.callBackFun:
                self.console_appClosed_conn = None
                self.console_stdoutAvail_conn = None
            else:
                doCallBackFun = False
            self.console.sendCtrlC()
            self.console = None
            if doCallBackFun:
                self.callBackFun(-1, self.outData)
                self.callBackFun = None

    def _dataAvail(self, data):
        if None != data:
            self.outData += data

    def _cmdFinished(self, code):
        printDBG("iptv_system._cmdFinished code[%r]---------------------------------" % code)
        self.console_appClosed_conn = None
        self.console_stdoutAvail_conn = None
        self.console = None
        self.callBackFun(code, self.outData)
        self.callBackFun = None

    def __del__(self):
        printDBG("iptv_system.__del__ ---------------------------------")

def IsHttpsCertValidationEnabled():
    return config.plugins.iptvplayer.httpssslcertvalidation.value
    
#############################################################
# returns the directory path where specified resources are
# stored, in the future, it can be changed in the config
#############################################################
def GetLogoDir(file = ''):
    return resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/icons/logos/') + file
def GetCookieDir(file = ''):
    cookieDir = '/tmp/'
    tmpDir = config.plugins.iptvplayer.SciezkaCache.value + '/cookies/'
    try:
        if os.path.isdir(tmpDir) or mkdirs(tmpDir):
            cookieDir = tmpDir
    except:
        printExc()
    return cookieDir + file
    
def GetTmpDir(file = ''):
    path = config.plugins.iptvplayer.NaszaTMP.value
    path = path.replace('//', '/')
    try: mkdirs(path)
    except: printExc()
    return path + '/' + file
    
def GetCacheSubDir(dir, file = ''):
    path = config.plugins.iptvplayer.SciezkaCache.value + "/" + dir
    path = path.replace('//', '/')
    try: mkdirs(path)
    except: printExc()
    return path + '/' + file

def GetSearchHistoryDir(file = ''):
    return GetCacheSubDir('SearchHistory', file)
    
def GetFavouritesDir(file = ''):
    return GetCacheSubDir('IPTVFavourites', file)

def GetIPTVDMImgDir(file = ''):
    return resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/icons/') + file
def GetIconDir(file = ''):
    return resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/icons/') + file
def GetBinDir(file = '', platform=None):
    if None == platform: platform = config.plugins.iptvplayer.plarform.value
    return resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/bin/') + platform + '/' + file
def GetPluginDir(file = ''):
    return resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/') + file
def GetSkinsDir(path = ''):
    return resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/skins/') + path
def GetConfigDir(path = ''):
    return resolveFilename(SCOPE_CONFIG, path)
def IsExecutable(fpath):
    try:
        if '' != Which(fpath): return True
    except: printExc()
    return False
    
def Which(program):
    try:
        def is_exe(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                path = path.strip('"')
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return exe_file
    except: printExc()
    return ''
#############################################################
# class used to auto-select one link when video has several 
# links with different qualities
#############################################################
class CSelOneLink():

    def __init__(self, listOfLinks, getQualiyFun, maxRes):
       self.listOfLinks = listOfLinks
       self.getQualiyFun = getQualiyFun
       self.maxRes = maxRes
       
    def _cmpLinks(self, item1, item2):
        val1 = self.getQualiyFun(item1)
        val2 = self.getQualiyFun(item2)
        if val1 < val2:   return -1
        elif val1 > val2: return 1
        else:             return 0
        
    def getSortedLinks(self, defaultFirst=True):
        printDBG('getSortedLinks defaultFirst[%r]' % defaultFirst)
        sortList = self.listOfLinks[::-1]
        sortList.sort( self._cmpLinks )
        if len(self.listOfLinks) < 2 or None == self.maxRes:
            return self.listOfLinks

        defIdx = -1
        for idx in range(len(sortList)):
            linkRes = self.getQualiyFun( sortList[idx] )
            printDBG("=============== getOneLink [%r] res[%r] maxRes[%r]" % (sortList[idx], linkRes, self.maxRes))
            if linkRes <= self.maxRes:
                defIdx = idx
                printDBG('getOneLink use format %d/%d' % (linkRes, self.maxRes) )
                
        if defaultFirst and -1 < defIdx:
            item = sortList[defIdx]
            del sortList[defIdx]
            sortList.insert(0, item)
        return sortList
            
    def getOneLink(self):
        printDBG('getOneLink start')
        tab = self.getSortedLinks()
        if len(tab) == 0:
            return tab
        return [ tab[0] ]
# end CSelOneLink

#############################################################
# prints debugs on screen or to the file
#############################################################
# debugs
def printDBG( DBGtxt ):
    try:
        from Components.config import config
        DBG = config.plugins.iptvplayer.debugprint.value
    except:
        #nie zainicjowany modul Config, sprawdzamy wartosc bezposredio w pliku
        DBG=''
        file = open(resolveFilename(SCOPE_CONFIG, "settings"))
        for line in file:
            if line.startswith('config.plugins.iptvplayer.debugprint=' ) :
                DBG=line.split("=")[1].strip()
                break
        #print DBG
    if DBG == '':
        return
    elif DBG == 'console':
        print(DBGtxt)
    elif DBG == 'debugfile':
        try:
            f = open('/hdd/iptv.dbg', 'a')
            f.write(DBGtxt + '\n')
            f.close
        except:
            print("======================EXC printDBG======================")
            print("printDBG(I): %s" % traceback.format_exc())
            print("========================================================")
            try:
                msg = '%s' % traceback.format_exc()
                f = open('/tmp/iptv.dbg', 'a')
                f.write(DBGtxt + '\n')
                f.close
            except:
                print("======================EXC printDBG======================")
                print("printDBG(II): %s" % traceback.format_exc())
                print("========================================================")

#####################################################
# get host list based on files in /hosts folder
#####################################################
def GetHostsList():
    printDBG('getHostsList begin')
    HOST_PATH = resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/hosts/')
    lhosts = [] 
    
    try:
        fileList = os.listdir( HOST_PATH )
        for wholeFileName in fileList:
            # separate file name and file extension
            fileName, fileExt = os.path.splitext(wholeFileName)
            nameLen = len( fileName )
            if fileExt in ['.pyo', '.pyc', '.py'] and nameLen >  4 and fileName[:4] == 'host' and fileName.find('_blocked_') == -1:
                if fileName[4:] not in lhosts:
                    lhosts.append( fileName[4:] )
                    printDBG('getHostsList add host with fileName: "%s"' % fileName[4:])
        printDBG('getHostsList end')
        lhosts.sort()
    except:
        printDBG('GetHostsList EXCEPTION')
    return lhosts
    
def SortHostsList(hostsList):
    hostsList = list(hostsList)
    hostsOrderList = GetHostsOrderList()
    sortedList = []
    for item in hostsOrderList:
        if item in hostsList: 
            sortedList.append(item)
            hostsList.remove(item)
    sortedList.extend(hostsList)
    return sortedList

def SaveHostsOrderList(lhosts):
    printDBG('SaveHostsOrderList begin')
    fname = GetConfigDir("iptvplayerhostsorder")
    try:
        f = open(fname, 'w')
        for item in lhosts:
            f.write(item + '\n')
        f.close()
    except:
        printExc()
    
def GetHostsOrderList():
    printDBG('GetHostsOrderList begin')
    fname = GetConfigDir("iptvplayerhostsorder")
    lhosts = []
    try:
        with open(fname, 'r') as f:
            content = f.readlines()
        for item in content:
            item = item.strip()
            if len(item): lhosts.append(item)
    except:
        printExc()
    return lhosts

def GetSkinsList():
    printDBG('getSkinsList begin')
    skins = []
    SKINS_PATH = resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/skins/')
    fileList = os.listdir( SKINS_PATH )
    for filename in fileList: skins.append((filename, filename))
    skins.sort()
    skins.insert(0,("Default", "Default"))
    printDBG('getSkinsList end')
    return skins
    
def IsHostEnabled( hostName ):
    hostEnabled  = False
    try:
        exec('if config.plugins.iptvplayer.host' + hostName + '.value: hostEnabled = True')
    except:
        hostEnabled = False
    return hostEnabled

##############################################################
# check if we have enough free space
# if required == None return free space instead of comparing
# default unit = MB
##############################################################
def FreeSpace(katalog, requiredSpace, unitDiv=1024*1024):
    try:
        s = os.statvfs(katalog)
        freeSpace = s.f_bfree * s.f_frsize # all free space
        if 512 > (freeSpace / (1024 * 1024)):
            freeSpace = s.f_bavail * s.f_frsize
        freeSpace = freeSpace / unitDiv
    except:
        printExc()
        freeSpace = -1
    printDBG("FreeSpace freeSpace[%s] requiredSpace[%s] unitDiv[%s]" % (freeSpace, requiredSpace, unitDiv))
    if None == requiredSpace:
        return freeSpace
    else:    
        if freeSpace >= requiredSpace:
            return True
        else:
            return False

def IsValidFileName(name, NAME_MAX=255):
    prohibited_characters = ['/', "\000", '\\', ':', '*', '<', '>', '|', '"']
    if isinstance(name, basestring) and (1 <= len(name) <= NAME_MAX):
        for it in name:
            if it in prohibited_characters:
                return False
        return True
    return False
    
def touch(fname, times=None):
    try:
        with open(fname, 'a'):
            os.utime(fname, times)
        return True
    except:
        printExc()
        return False
        
        
def mkdir(newdir):
    """ Wrapper for the os.mkdir function
        returns status instead of raising exception
    """
    try:
        os.mkdir(newdir)
        sts = True
        msg = 'Katalog "%s" został utworzony poprawnie.' % newdir
    except:
        sts = False
        msg = 'Katalog "%s" nie może zostać utworzony.' % newdir
        printExc()
    return sts,msg

def mkdirs(newdir):
    """ Create a directory and all parent folders.
        Features:
        - parent directories will be created
        - if directory already exists, then do nothing
        - if there is another filsystem object with the same name, raise an exception
    """
    printDBG('mkdirs: "%s"' % newdir)
    try:
        if os.path.isdir(newdir):
            pass
        elif os.path.isfile(newdir):
            raise OSError("cannot create directory, file already exists: '%s'" % newdir)
        else:
            head, tail = os.path.split(newdir)
            if head and not os.path.isdir(head) and not os.path.ismount(head) and not os.path.islink(head):
                mkdirs(head)
            if tail:
                os.mkdir(newdir)
        return True
    except:
        printExc('!!!!!!!!!! EXCEPTION mkdirs["%s"]' % newdir)
        return False

def rmtree(path, ignore_errors=False, onerror=None):
    """Recursively delete a directory tree.
    If ignore_errors is set, errors are ignored; otherwise, if onerror
    is set, it is called to handle the error with arguments (func,
    path, exc_info) where func is os.listdir, os.remove, or os.rmdir;
    path is the argument to that function that caused it to fail; and
    exc_info is a tuple returned by sys.exc_info(). If ignore_errors
    is false and onerror is None, an exception is raised.
    """
    if ignore_errors:
        def onerror(*args):
            pass
    elif onerror is None:
        def onerror(*args):
            raise
    try:
        if os.path.islink(path):
            # symlinks to directories are forbidden, see bug #1669
            raise OSError("Cannot call rmtree on a symbolic link")
    except OSError:
        onerror(os.path.islink, path)
        # can't continue even if onerror hook returns
        return
    names = []
    try:
        names = os.listdir(path)
    except os.error, err:
        onerror(os.listdir, path)
    for name in names:
        fullname = os.path.join(path, name)
        try:
            mode = os.lstat(fullname).st_mode
        except os.error:
            mode = 0
        if stat.S_ISDIR(mode):
            rmtree(fullname, ignore_errors, onerror)
        else:
            try:
                os.remove(fullname)
            except os.error, err:
                onerror(os.remove, fullname)
    try:
        os.rmdir(path)
    except os.error:
        onerror(os.rmdir, path) 
       
def DownloadFile(url, filePath):
    printDBG('DownloadFile [%s] from [%s]' % (filePath, url) )
    try:
        downloadFile = urllib2.urlopen(url)
        output = open(filePath, 'wb')
        output.write(downloadFile.read())
        output.close()
        try:
            iptv_system('sync')
        except:
            printExc('DownloadFile sync exception')
        return True
    except:
        try:
            if os.path.exists(filePath):
                os.remove(filePath)
            return False
        except:
            printExc()
            return False

########################################################
#                     For icon manager
########################################################  
def GetLastDirNameFromPath(path):
    path = os.path.normcase(path)
    if path[-1] == '/':
        path = path[:-1]
    dirName = path.split('/')[-1]
    return dirName

def GetIconDirBaseName():
    return '.iptvplayer_icons_'
    
def CheckIconName(name):
    #check if name is correct 
    if 36 == len(name) and '.jpg' == name[-4:]:
        try:
            tmp = int(name[:-4], 16)
            return True
        except:
            pass
    return False

def GetNewIconsDirName():
    return "%s%f" % (GetIconDirBaseName(), float(time()))

def CheckIconsDirName(path):
    dirName = GetLastDirNameFromPath(path)
    baseName = GetIconDirBaseName()
    if dirName.startswith(baseName):
        try:
            test = float(dirName[len(baseName):])
            return True
        except:
            pass
    return False
    
def GetIconsDirs(basePath):
    iconsDirs = []
    try:
        list = os.listdir(basePath)
        for item in list:
            currPath = os.path.join(basePath, item)
            if os.path.isdir(currPath) and not os.path.islink(currPath) and CheckIconsDirName(item):
                iconsDirs.append(item)
    except:
        printExc()
    return iconsDirs
    
def GetIconsFilesFromDir(basePath):
    iconsFiles = []
    if CheckIconsDirName(basePath):
        try:
            list = os.listdir(basePath)
            for item in list:
                currPath = os.path.join(basePath, item)
                if os.path.isfile(currPath) and not os.path.islink(currPath) and CheckIconName(item):
                    iconsFiles.append(item)
        except:
            printExc()
    
    return iconsFiles
    
def GetCreationIconsDirTime(fullPath):
    try:
        dirName    = GetLastDirNameFromPath(fullPath)
        baseName   = GetIconDirBaseName()
        return float(dirName[len(baseName):])
    except:
        return None
        
def GetCreateIconsDirDeltaDateInDays(fullPath):
    ret = -1
    createTime = GetCreationIconsDirTime(fullPath)
    if None != createTime:
        try:
            currTime   = datetime.now()
            modTime    = datetime.fromtimestamp(createTime)
            deltaTime  = currTime - modTime
            ret = deltaTime.days
        except:
            printExc()
    return ret
    
def RemoveIconsDirByPath(path):
    printDBG("RemoveIconsDirByPath[%s]" % path)
    RemoveAllFilesIconsFromPath(path)
    try:
        os.rmdir(path)
    except:
        printExc('RemoveIconsDirByPath dir[%s] is not empty' % path) 
    
def RemoveOldDirsIcons(path, deltaInDays='7'):
    deltaInDays = int(deltaInDays)
    try:
        iconsDirs = GetIconsDirs(path)
        for item in iconsDirs:
            currDir = os.path.join(path, item)
            delta = GetCreateIconsDirDeltaDateInDays(currDir) # we will check only directory date
            if delta >= 0 and deltaInDays >= 0 and delta >= deltaInDays:
                RemoveIconsDirByPath(currDir)
    except:
        printExc()

def RemoveAllFilesIconsFromPath(path):
    printDBG( "RemoveAllFilesIconsFromPath" )
    try:
        list = os.listdir(path)
        for item in list:
            filePath = os.path.join(path, item)
            if CheckIconName(item) and os.path.isfile(filePath):
                printDBG( 'RemoveAllFilesIconsFromPath img: ' + filePath )
                try:
                    os.remove(filePath)
                except:
                    printDBG( "ERROR while removing file %s" % filePath )
    except:
        printExc('ERROR: in RemoveAllFilesIconsFromPath')
        
def RemoveAllDirsIconsFromPath(path, old=False):
    if old:
        RemoveAllFilesIconsFromPath(path)
    else:
        try:
            iconsDirs = GetIconsDirs(path)
            for item in iconsDirs:
                currDir = os.path.join(path, item)
                RemoveIconsDirByPath(currDir)
        except:
            printExc()
    
def formatBytes(bytes, precision = 2):
    import math
    units = ['B', 'KB', 'MB', 'GB', 'TB'] 
    bytes = max(bytes, 0); 
    if bytes:
        pow = math.log(bytes)
    else:
        pow = 0
    pow = math.floor(pow / math.log(1024)) 
    pow = min(pow, len(units) - 1) 
    bytes /= math.pow(1024, pow);
    return ("%s%s" % (str(round(bytes, precision)),units[int(pow)])) 
    
def remove_html_markup(s, replacement=''):
    tag = False
    quote = False
    out = ""
    for c in s:
            if c == '<' and not quote:
                tag = True
            elif c == '>' and not quote:
                tag = False
                out += replacement
            elif (c == '"' or c == "'") and tag:
                quote = not quote
            elif not tag:
                out = out + c
    return re.sub('&\w+;', ' ',out)

class CSearchHistoryHelper():
    TYPE_SEP = '|--TYPE--|'
    def __init__(self, name, storeTypes=False):
        printDBG('CSearchHistoryHelper.__init__')
        self.storeTypes = storeTypes
        try:
            printDBG('CSearchHistoryHelper.__init__ name = "%s"' % name)
            self.PATH_FILE = GetSearchHistoryDir(name + ".txt")
        except:
            printExc('CSearchHistoryHelper.__init__ EXCEPTION')

    def getHistoryList(self):
        printDBG('CSearchHistoryHelper.getHistoryList from file = "%s"' % self.PATH_FILE)
        historyList = []
    
        try:
            file = codecs.open(self.PATH_FILE, 'r', 'utf-8', 'ignore')
            for line in file:
                value = line.replace('\n', '').strip()
                if len(value) > 0:
                    try: historyList.insert(0, value.encode('utf-8', 'ignore'))
                    except: printExc()
            file.close()
        except:
            printExc()
            return []
        
        orgLen = len(historyList)
        # remove duplicates
        # last 50 searches patterns are stored
        historyList = historyList[:50]
        uniqHistoryList = []
        for i in historyList:
            if i not in uniqHistoryList:
                uniqHistoryList.append(i)
        historyList = uniqHistoryList

        # save file without duplicates
        if orgLen > len(historyList):
            self._saveHistoryList(historyList)
        
        # now type also can be stored
        #################################
        newList = []
        for histItem in historyList:
            fields = histItem.split(self.TYPE_SEP)
            if 2 == len(fields):
                newList.append({'pattern':fields[0], 'type':fields[1]})
            elif self.storeTypes:
                newList.append({'pattern':fields[0]})
        
        if len(newList) > 0:
            return newList
        #################################
            
        return historyList
    
    def addHistoryItem(self, itemValue, itemType = None):
        printDBG('CSearchHistoryHelper.addHistoryItem to file = "%s"' % self.PATH_FILE)
        try:
            file = codecs.open(self.PATH_FILE, 'a', 'utf-8', 'replace')
            value = itemValue
            if None != itemType:
                value = value + self.TYPE_SEP + itemType
            file.write(value + '\n')
            printDBG('Added pattern: "%s"' % itemValue) 
            file.close
        except:
            printExc('CSearchHistoryHelper.addHistoryItem EXCEPTION')


    def _saveHistoryList(self, list):
        printDBG('CSearchHistoryHelper._saveHistoryList to file = "%s"' % self.PATH_FILE)
        try:
            file = open( self.PATH_FILE, 'w' )
            l = len(list)
            for i in range( l ):
                file.write( list[l - 1 -i] + '\n' )
            file.close
        except:
            printExc('CSearchHistoryHelper._saveHistoryList EXCEPTION')
    
    @staticmethod
    def saveLastPattern(pattern):
        filePath = GetSearchHistoryDir("pattern")
        sts = False
        try:
            file = codecs.open(filePath, 'w', 'utf-8', 'replace')
            file.write(pattern)
            file.close
            sts = True
        except:
            printExc()
        return sts
        
    @staticmethod
    def loadLastPattern():
        filePath = GetSearchHistoryDir("pattern")
        sts, ret = False, ''
        try:
            file = codecs.open(filePath, 'r', 'utf-8', 'ignore')
            ret = file.read().encode('utf-8', 'ignore')
            file.close()
            sts = True
        except:
            printExc()
        return sts, ret
# end CSearchHistoryHelper

class CFakeMoviePlayerOption():
    def __init__(self, value, text):
        self.value = value
        self.text  = text
    def getText(self):
        return self.text

class CMoviePlayerPerHost():
    def __init__(self, hostName):
        self.filePath = GetCacheSubDir('MoviePlayer', hostName + '.json')
        self.activePlayer = {} # {buffering:True/False, 'player':''}
        self.load()
        
    def __del__(self):
        self.save()
        
    def load(self):
        sts, ret = False, ''
        try:
            if not os.path.isfile(self.filePath):
                sts = True
            else:
                file = codecs.open(self.filePath, 'r', 'utf-8', 'ignore')
                ret = file.read().encode('utf-8', 'ignore')
                file.close()
                activePlayer = {}
                ret = json.loads(ret)
                activePlayer['buffering'] = ret['buffering']
                activePlayer['player'] = CFakeMoviePlayerOption(ret['player']['value'].encode('utf-8'), ret['player']['text'].encode('utf-8'))
                self.activePlayer  = activePlayer
                sts = True
        except: printExc()
        return sts, ret
        
    def save(self):
        sts = False
        try:
            if {} == self.activePlayer and os.path.isfile(self.filePath):
                os.remove(self.filePath)
            else:
                data = {}
                data['buffering'] = self.activePlayer['buffering']
                data['player']    = {'value':self.activePlayer['player'].value, 'text':self.activePlayer['player'].getText()}
                data = json.dumps(data).encode('utf-8')
                file = codecs.open(self.filePath, 'w', 'utf-8', 'replace')
                file.write(data)
                file.close
                sts = True
        except: printExc()
        return sts
    
    def get(self, key, defval):
        return self.activePlayer.get(key, defval)
        
    def set(self, activePlayer):
        self.activePlayer = activePlayer
        
def byteify(input):
    if isinstance(input, dict):
        return dict([(byteify(key), byteify(value)) for key, value in input.iteritems()])
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

def printExc(msg=''):
    printDBG("===============================================")
    printDBG("                   EXCEPTION                   ")
    printDBG("===============================================")
    msg = msg + ': \n%s' % traceback.format_exc()
    printDBG(msg)
    printDBG("===============================================")

def GetIPTVPlayerVerstion():
    try: from Plugins.Extensions.IPTVPlayer.version import IPTV_VERSION
    except: IPTV_VERSION="XX.YY.ZZ"
    return IPTV_VERSION

def GetShortPythonVersion():
    return "%d.%d" % (sys.version_info[0], sys.version_info[1])
    
def GetVersionNum(ver):
    try:
        if None == re.match("[0-9][0-9]\.[0-9][0-9]\.[0-9][0-9]\.[0-9][0-9]", ver): raise Exception("Wrong version!")
        return int(ver.replace('.', ''))
    except:
        printExc('Version[%r]' % ver)
        return 0
