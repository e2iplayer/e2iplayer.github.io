# -*- coding: utf-8 -*-
#
#  IPTV download manager API
#
#  $Id$
#
#
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, eConnectCallback
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper,DMItemBase
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdownloadercreator import DownloaderCreator
###################################################

###################################################
# FOREIGN import
###################################################
from Tools.BoundFunction import boundFunction
from enigma import eTimer
from time import sleep
import datetime
import os
###################################################

class DMItem(DMItemBase): 
    def __init__(self, url, fileName):
        DMItemBase.__init__(self, url, fileName)

        self.processed = False
        self.downloadIdx = -1
        

class IPTVDMApi():
    
    def __init__(self, refreshDelay = 2, parallelDownloadNum = 1):
        self.running = False
        self.downloadIdx = 0
        self.downloading = False

        self.updateProgress = False
        self.sleepDelay = refreshDelay
        
        #self.currDMItem = None
        # under download queue
        self.queueUD = []
        self.MAX_DOWNLOAD_ITEM = parallelDownloadNum
        # already downloaded
        self.queueAA = []
        # waiting for download queue
        self.queueDQ = []
        
        self.onlistChanged = []
        
        #main Queue
        self.mainTimer = eTimer()
        self.mainTimer_conn = eConnectCallback(self.mainTimer.timeout, self.processDQ)
        return

    def __del__(self):
        printDBG("IPTVDMApi.__del__ -------------------")
        if True == self.running:
            self.running = False
            self.mainTimer.stop()
        self.stopAllDownloadItem()
        self.mainTimer_conn = None
        self.mainTimer = None
        return
    
    def setUpdateProgress(self, update=True):
        self.updateProgress = update
        return
    
    def isRunning(self):
        return self.running 
        
    def stopDownloadItem(self, downloadIdx):
        listUDIdx = self.findIdxInQueueUD(downloadIdx)
        if -1 < listUDIdx and None != self.queueUD[listUDIdx].downloader:
            self.queueUD[listUDIdx].downloader.terminate()
            # give some time to finish
            sleep(1)
            # manually run endCmd because when killed 
            # appClosed is not called
            self.cmdFinished(downloadIdx, -1)
            
        
    def stopAllDownloadItem(self):
            while len(self.queueUD) > 0:
                downloadIdx = self.queueUD[0].downloadIdx
                self.queueUD[0].downloader.terminate()
                self.cmdFinished(downloadIdx, -1)
        
    def moveToTopDownloadItem(self, downloadIdx):
        printDBG("moveToTopDownloadItem for downloadIdx[%d]" % downloadIdx)
        bRet = False
        listUDIdx = self.findIdxInQueueDQ(downloadIdx)
        if -1 < listUDIdx and 1 < len(self.queueDQ):
            # get item from self.queueDQ
            item = self.queueDQ[listUDIdx]
            # remove item from self.queueDQ
            del self.queueDQ[listUDIdx]
            # add to top of list
            self.queueDQ.insert(0, item)
            bRet = True
        
        if bRet:
            self.listChanged()
        
    def deleteDownloadItem(self, downloadIdx):
        printDBG("deleteDownloadItem for downloadIdx[%d]" % downloadIdx)
        bRet = False

        listUDIdx = self.findIdxInQueueDQ(downloadIdx)
        if -1 < listUDIdx:
            # get processed item from self.queueDQ
            item = self.queueDQ[listUDIdx]
            
            # generaly the file should not exist but when it 
            # tries == CONTINUE_DOWNLOAD it exist
            # delete file
            try:
                os.remove(item.fileName)
            except:
                printDBG("deleteDownloadItem removing file[%s] error" % item.fileName)
            
            # remove item from self.queueDQ
            del self.queueDQ[listUDIdx]
            bRet = True
        
        if bRet:
            self.listChanged()
        
    def removeDownloadItem(self, downloadIdx):
        printDBG("removeDownloadItem for downloadIdx[%d]" % downloadIdx)
        bRet = False
        listUDIdx = self.findIdxInQueueAA(downloadIdx)
        if -1 < listUDIdx:
            # get processed item from self.queueAA
            item = self.queueAA[listUDIdx]
            
            # delete file
            try:
                os.remove(item.fileName)
            except:
                printDBG("removeDownloadItem removing file[%s] error" % item.fileName)
            
            # remove item from self.queueAA
            del self.queueAA[listUDIdx]
            bRet = True
        
        if bRet:
            self.listChanged()
        
    def continueDownloadItem(self, downloadIdx):
        listUDIdx = self.findIdxInQueueAA(downloadIdx)
        if -1 < listUDIdx:
            # get processed item from self.queueAA
            item = self.queueAA[listUDIdx]
            
            item.status = DMHelper.STS.WAITING
            #item.fileSize = -1
            item.downloadedSize = 0
            item.downloadedProcent = -1
            item.downloadedSpeed = 0
            item.timeToFinish = -1
            
            item.processed = False
            item.tries = DMHelper.DOWNLOAD_TYPE.CONTINUE
            self.queueDQ.append(item)
            # remove processed item from self.queueAA
            del self.queueAA[listUDIdx]
        
    def retryDownloadItem(self, downloadIdx):
        listUDIdx = self.findIdxInQueueAA(downloadIdx)
        if -1 < listUDIdx:
            # get processed item from self.queueAA
            item = self.queueAA[listUDIdx]
            
            item.status = DMHelper.STS.WAITING
            item.fileSize = -1 
            item.downloadedSize = 0
            item.downloadedProcent = -1
            item.downloadedSpeed = 0
            item.timeToFinish = -1
        
            item.processed = False
            item.tries = DMHelper.DOWNLOAD_TYPE.RETRY
            self.queueDQ.append(item)
            # remove processed item from self.queueAA
            del self.queueAA[listUDIdx]
        
    def stopWorkThread(self):
        ''' Can be called only from main thread'''
        if True == self.running:
            self.running = False
            self.mainTimer.stop()
            
        self.stopAllDownloadItem()
 
    def runWorkThread(self):
        ''' Can be called only from main thread'''
        if False == self.running:
            self.running = True
            self.mainTimer.start(self.sleepDelay * 1000)

    def addToDQueue(self, newItem):
        bRet = False
        
        # check if there is no Item with this 
        # same url already in queue
        exist = False
        for item in self.queueDQ:
            if item.url == newItem.url:
                exist = True
        if False == exist:
            self.downloadIdx += 1
            newItem.downloadIdx = self.downloadIdx 
            newItem.statusFile = DMHelper.STATUS_FILE_PATH + str(newItem.downloadIdx) + DMHelper.STATUS_FILE_EXT
            self.queueDQ.append(newItem)
            bRet = True
        if bRet:
            self.listChanged()
        return bRet
    
    def processDQ(self):
            if False == self.running: return
            dListChanged = False
            if len(self.queueUD) < self.MAX_DOWNLOAD_ITEM and \
               0 < len(self.queueDQ):
                item = self.queueDQ.pop(0)
                self.queueUD.append(item)
                dListChanged = True
                
                # remove old sts file
                try:
                    os.remove(item.statusFile)
                except:
                    printExc("ERROR: while removing status file %s" % item.statusFile)
                    
                # start downloading
                self.runCMD(item)
                
            if 0 < len(self.queueUD):
                self.downloading = True
            else:
                self.downloading = False
            
            if dListChanged:
                self.listChanged()
                
            if self.downloading and self.updateProgress:
                self.updateDownloadItemsStatus()
            
    def makeUnikalFileName(self, fileName):
        # if this function is called
        # no more than once per second
        # date and time (with second)
        # is sufficient to provide a unique name
        from time import gmtime, strftime
        date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        newFileName = os.path.dirname(fileName) + os.sep + date.replace(':', '.') + "-" + os.path.basename(fileName)
        tmpFileName = os.path.dirname(fileName) + os.sep + "." + date.replace(':', '.') + "-" + os.path.basename(fileName)
        return newFileName, tmpFileName
    
    def runCMD(self, item):
        printDBG("runCMD for downloadIdx[%d]" % item.downloadIdx)
        
        if DMHelper.DOWNLOAD_TYPE.INITIAL == item.tries:
           item.fileName, item.tmpFileName = DMHelper.makeUnikalFileName(item.fileName, True)

        printDBG("Downloading started downloadIdx[%s] File[%s] URL[%s]" % (item.downloadIdx, item.fileName, item.url) )
      
        listUDIdx = self.findIdxInQueueUD(item.downloadIdx)
        self.queueUD[listUDIdx].status      = DMHelper.STS.DOWNLOADING
        self.queueUD[listUDIdx].fileName    = item.fileName
        self.queueUD[listUDIdx].tmpFileName = item.tmpFileName
        
        url, downloaderParams = DMHelper.getDownloaderParamFromUrl(item.url)
        self.queueUD[listUDIdx].downloader = DownloaderCreator(url)
        self.queueUD[listUDIdx].callback   = boundFunction(self.cmdFinished, item.downloadIdx)
        self.queueUD[listUDIdx].downloader.subscribeFor_Finish( self.queueUD[listUDIdx].callback )
        self.queueUD[listUDIdx].downloader.start(url, item.fileName, downloaderParams)
   
    def cmdFinished(self, downloadIdx, retval=None):
        printDBG("cmdFinished downloadIdx[%d]" % downloadIdx)
        
        listUDIdx = self.findIdxInQueueUD(downloadIdx)
        
        # listUDIdx must be > -1 
        if -1 >= listUDIdx:
            return
        
        self.updateDownloadedItemStatus(listUDIdx)
        self.queueUD[listUDIdx].processed  = True
        self.queueUD[listUDIdx].downloader.unsubscribeFor_Finish(self.queueUD[listUDIdx].callback)
        self.queueUD[listUDIdx].downloader = None
        self.queueUD[listUDIdx].callback   = None
        
        item = self.queueUD[listUDIdx]
        printDBG("Downloading finished idx[%s] File[%s] URL[%s]" % (downloadIdx, item.fileName, item.url) )        
        
        item = self.queueUD[listUDIdx]
        # add processed item to self.queueAA
        self.queueAA.append(item)
        # remove processed item from self.queueUD
        del self.queueUD[listUDIdx]
        self.listChanged()
        
    def findIdxInQueueDQ(self, downloadIdx):
        # function should be called from locked area
        for listIdx in range( len(self.queueDQ) ):
            if self.queueDQ[listIdx].downloadIdx == downloadIdx:
                return listIdx
        return -1
        
    def findIdxInQueueUD(self, downloadIdx):
        # function should be called from locked area
        for listIdx in range( len(self.queueUD) ):
            if self.queueUD[listIdx].downloadIdx == downloadIdx:
                return listIdx
        return -1
        
    def findIdxInQueueAA(self, downloadIdx):
        # function should be called from locked area
        for listIdx in range( len(self.queueAA) ):
            if self.queueAA[listIdx].downloadIdx == downloadIdx:
                return listIdx
        return -1
        
    def updateDownloadedItemStatus(self, listUDIdx):
        printDBG("updateDownloadedItemStatus listUDIdx[%d]" % listUDIdx)
        self.updateItemSTS(listUDIdx)
        # dItem - copy only for reading filed
        dItem = self.queueUD[listUDIdx]
                
        if 100 == dItem.downloadedProcent:
            self.queueUD[listUDIdx].status = DMHelper.STS.DOWNLOADED
        else:           
            if dItem.downloadedSize > 0:
                self.queueUD[listUDIdx].status = DMHelper.STS.INTERRUPTED
            else:
                self.queueUD[listUDIdx].status = DMHelper.STS.ERROR
        #dItem = self.queueUD[listUDIdx] 
        #print( dItem.fileName + ": "+ " status: " + dItem.status + dItem.downloadedSize + " " + dItem.downloadedProcent + " " + dItem.downloadedSpeed + " " + dItem.timeToFinish )
    # end updateEndItemStatus
    
    def updateItemSTS(self, listUDIdx):
        printDBG("updateItemSTS listUDIdx[%d]" % listUDIdx)
        self.queueUD[listUDIdx].downloader.updateStatistic()
        self.queueUD[listUDIdx].downloadedSize  = self.queueUD[listUDIdx].downloader.getLocalFileSize()
        self.queueUD[listUDIdx].fileSize        = self.queueUD[listUDIdx].downloader.getRemoteFileSize()
        self.queueUD[listUDIdx].downloadedSpeed = self.queueUD[listUDIdx].downloader.getDownloadSpeed()
        # calculate downloadedProcent
        if self.queueUD[listUDIdx].fileSize > 0 and self.queueUD[listUDIdx].downloadedSize > 0:
            self.queueUD[listUDIdx].downloadedProcent = (100 * self.queueUD[listUDIdx].downloadedSize) / self.queueUD[listUDIdx].fileSize
        return True
            
    def updateDownloadItemsStatus(self):
        stsChanged = False 
        printDBG("updateDownloadItemsStatus")
        for listUDIdx in range( len(self.queueUD) ):
            if self.updateItemSTS(listUDIdx):
                stsChanged = True
        if stsChanged:
            self.listChanged()
    # end updateDownloadItemsStatus
    
    def getList(self):
        list = []
        printDBG("getList")
        tmpList = []
        # under downloading
        tmpList.extend(self.queueUD)
        # waiting for dowlnoad
        tmpList.extend(self.queueDQ)
        # already processedupdateItemSTS
        tmpList.extend(self.queueAA)
        list = tmpList[:]
        return list

    def connectListChanged(self, fnc):
        if not fnc in self.onlistChanged:
            self.onlistChanged.append(fnc)

    def disconnectListChanged(self, fnc):
        if fnc in self.onlistChanged:
            self.onlistChanged.remove(fnc)

    def listChanged(self):
        printDBG("listChanged()")
        for x in self.onlistChanged:
            x()
