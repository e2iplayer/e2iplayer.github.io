# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from asynccall import AsyncMethod
from Plugins.Extensions.IPTVPlayer.libs.crypto.hash.md5Hash import MD5
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import mkdirs, \
                      FreeSpace as iptvtools_FreeSpace, \
                      printDBG, printExc, RemoveOldDirsIcons, RemoveAllFilesIconsFromPath, \
                      RemoveAllDirsIconsFromPath, GetIconsFilesFromDir, GetNewIconsDirName, \
                      GetIconsDirs, RemoveIconsDirByPath
###################################################

###################################################
# FOREIGN import
###################################################
import threading
from binascii import hexlify
from os import path as os_path, listdir, remove as removeFile, rename as os_rename, rmdir as os_rmdir
from Components.config import config
###################################################


#config.plugins.iptvplayer.showcover (true|false)
#config.plugins.iptvplayer.SciezkaCache = ConfigText(default = "/hdd/IPTVCache")

class IconMenager:
    HEADER = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.18) Gecko/20110621 Mandriva Linux/1.9.2.18-0.1mdv2010.2 (2010.2) Firefox/3.6.18', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}

    def __init__(self, updateFun = None, downloadNew = True):
        printDBG( "IconMenager.__init__" )
        self.DOWNLOADED_IMAGE_PATH_BASE = config.plugins.iptvplayer.SciezkaCache.value
        self.cm = common()

        # download queue
        self.queueDQ = []
        self.lockDQ = threading.Lock()
        self.workThread = None
        
        # already available
        self.queueAA = {}
        self.lockAA = threading.Lock()
        
        #this function will be called after a new icon will be available
        self.updateFun = None
        
        #new icons dir for each run
        self.currDownloadDir = self.DOWNLOADED_IMAGE_PATH_BASE + '/' + GetNewIconsDirName()
        if not os_path.exists(self.currDownloadDir):
            mkdirs(self.currDownloadDir)

        #load available icon from disk
        #will be runned in separeted thread to speed UP start plugin
        AsyncMethod(self.loadHistoryFromDisk)(self.currDownloadDir)

        # this is called to remove icons which are stored in old version
        AsyncMethod(RemoveAllFilesIconsFromPath)(self.DOWNLOADED_IMAGE_PATH_BASE)
        
        self.stopThread = False
        
        self.checkSpace = 0 # if 0 the left space on disk will be checked
        self.downloadNew = downloadNew

    def __del__(self):
        printDBG( "IconMenager.__del__ -------------------------------")
        self.clearDQueue()
        self.clearAAueue()
        
        if config.plugins.iptvplayer.SciezkaCache.value == self.DOWNLOADED_IMAGE_PATH_BASE and config.plugins.iptvplayer.showcover.value:
            AsyncMethod(RemoveOldDirsIcons)(self.DOWNLOADED_IMAGE_PATH_BASE, config.plugins.iptvplayer.deleteIcons.value)
        else:
            # remove all icons as they are not more needed due to config changes
            AsyncMethod(RemoveAllDirsIconsFromPath)(self.DOWNLOADED_IMAGE_PATH_BASE)
        printDBG( "IconMenager.__del__ end" )
        
    def setUpdateCallBack(self, updateFun):
        self.updateFun = updateFun
        
    def stopWorkThread(self):
        self.lockDQ.acquire()
        
        if self.workThread != None and self.workThread.Thread.isAlive():
            self.stopThread = True
        
        self.lockDQ.release()
        
    def runWorkThread(self):
        if self.workThread == None or not self.workThread.Thread.isAlive():
            self.workThread = AsyncMethod(self.processDQ)()
        
    def clearDQueue(self):
        self.lockDQ.acquire()
        self.queueDQ = []
        self.lockDQ.release()
        
    def addToDQueue(self, addQueue=[]):
        self.lockDQ.acquire()
        self.queueDQ.extend(addQueue)
        #self.queueDQ.append(addQueue)
        self.runWorkThread()
        self.lockDQ.release()
        
    ###############################################################
    #                                AA queue
    ###############################################################
    def loadHistoryFromDisk(self, currDownloadDir):
        path = self.DOWNLOADED_IMAGE_PATH_BASE
        printDBG('+++++++++++++++++++++++++++++++++++++++ IconMenager.loadHistoryFromDisk path[%s]' % path)
        iconsDirs = GetIconsDirs(path)
        for item in iconsDirs:
            if os_path.normcase(path + '/' + item + '/') != os_path.normcase(currDownloadDir + '/'):
                self.loadIconsFromPath(os_path.join(path, item))
    
    def loadIconsFromPath(self, path):
        printDBG('IconMenager.loadIconsFromPath path[%s]' % path)
        iconsFiles = GetIconsFilesFromDir(path)
        if 0 == len(iconsFiles):
            RemoveIconsDirByPath(path)  
        for item in iconsFiles:
            self.addItemToAAueue(path, item)
            #printDBG('IconMenager.loadIconsFromPath path[%s], name[%s] loaded' % (path, item))

    def addItemToAAueue(self, path, name):
        self.lockAA.acquire()
        self.queueAA[name] = path
        self.lockAA.release()
        
    def clearAAueue(self):
        self.lockAA.acquire()
        self.queueAA = {}
        self.lockAA.release()
        
    def isItemInAAueue(self, item, hashed = 0):
        if hashed == 0:
            hashAlg = MD5()
            name = hashAlg(item)
            file = hexlify(name) + '.jpg'
        else:
            file = item
        ret = False
        #without locking. Is it safety?
        self.lockAA.acquire()
        if  None != self.queueAA.get(file, None):
            ret = True
        self.lockAA.release()
        
        return ret
       
    def getIconPathFromAAueue(self, item):
        printDBG("getIconPathFromAAueue item[%s]" % item)
        hashAlg = MD5()
        name = hashAlg(item)
        filename = hexlify(name) + '.jpg'
        
        self.lockAA.acquire()
        file_path = self.queueAA.get(filename, '')
        if file_path != '':
            try:
                if os_path.normcase(self.currDownloadDir+'/') != os_path.normcase(file_path+'/'):
                    file_path = os_path.normcase(file_path + '/' + filename)
                    os_rename(file_path, os_path.normcase(self.currDownloadDir + '/' + filename))
                    self.queueAA[filename] = os_path.normcase(self.currDownloadDir + '/' )
                    file_path = os_path.normcase(self.currDownloadDir + '/' + filename)
                else:
                    file_path = os_path.normcase(file_path + '/' + filename)
            except:
                printExc()
        self.lockAA.release()
        
        printDBG("getIconPathFromAAueue A file_path[%s]" % file_path)
        return file_path
        
    def processDQ(self):
        printDBG( "IconMenager.processDQ: Thread started" )
        
        while 1:
            die = 0
            url = ''
            
            #getFirstFromDQueue
            self.lockDQ.acquire()
            
            if False == self.stopThread:
                if len(self.queueDQ):
                    url = self.queueDQ.pop(0)
                else:
                    self.workThread = None
                    die = 1
            else:
                self.stopThread = False
                self.workThread = None
                die = 1
            
            self.lockDQ.release()
            
            if die:
                return
            
            printDBG( "IconMenager.processDQ url: [%s]" % url )
            if url != '':
                hashAlg = MD5()
                name = hashAlg(url)
                file = hexlify(name) + '.jpg'
                
                #check if this image is not already available in cache AA list
                if self.isItemInAAueue(file, 1):
                    continue
                
                if self.download_img(url, file):
                    self.addItemToAAueue(self.currDownloadDir, file)
                    if self.updateFun: self.updateFun(url)

                # add to AA list

    def download_img(self, img_url, filename):
        # if at start there was NOT enough space on disk 
        # new icon will not be downloaded
        if False == self.downloadNew:
            return False
    
        if len(self.currDownloadDir) < 4:
            printDBG('IconMenager.download_img: wrong path for IPTVCache')
            return False
            
        path = self.currDownloadDir + '/'
        
        # if at start there was enough space on disk 
        # we will check if we still have free space 
        if 0 >= self.checkSpace:
            printDBG('IconMenager.download_img: checking space on device')
            if not iptvtools_FreeSpace(path, 10):
                printDBG('IconMenager.download_img: not enough space for new icons, new icons will not be downloaded any more')
                self.downloadNew = False
                return False
            else:
                # for another 50 check again
                self.checkSpace = 50
        else:
            self.checkSpace -= 1
        file_path = "%s%s" % (path, filename)
        return self.cm.saveWebFile(file_path, img_url, {'maintype': 'image'})['sts']
    