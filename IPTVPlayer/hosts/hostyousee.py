# based on sd-xbmc-plugin.video.polishtv.live.r649

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CDisplayListItem, RetHost, CUrlItem
import Plugins.Extensions.IPTVPlayer.libs.pCommon as pCommon
import Plugins.Extensions.IPTVPlayer.libs.youseeapi as youseeapi
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetLogoDir
import re
###################################################
# FOREIGN import
###################################################
from Components.config import config

###################################################
def gettytul():
    return 'YouSee player'
    
class CListItem:
    TYPE_CATEGORY = "CATEGORY"
    TYPE_VIDEO = "VIDEO"
    def __init__(self,
                name = None,
                title = '',
                category = '',
                page = '',
                videoUrl = '',
                description = '',
                type = TYPE_CATEGORY):
                
        self.name = name
        self.title = title
        self.category = category
        self.page = page
        self.videoUrl = videoUrl
        self.description = description
        self.type = type

class YouSee:    
    LIVE_TV    = 0

    def __init__(self):
        self.cm = pCommon.common()
        self.api_ys = youseeapi.YouSeeLiveTVApi()
        
        self.valTab = None
        self.currList = []
        
    def getCurrList(self):
        return self.currList

    def setCurrList(self, list):
        self.currList = list
        return 

    def getMenuTable(self):
        valTab = []
        
        if None == self.valTab:
            valTab.append('YouSee Live TV')
            self.valTab = valTab
        
        return self.valTab

    def getYouSeeChannelsTab(self):
        strTab = []
        valTab = []
        
        try:
            programs = self.api_ys.allowedChannels()
            for program in programs:
                strTab = []
                strTab.append(program['id'])
                strTab.append(program['nicename'])
                print strTab
                valTab.append(strTab)
        except: printExc()
        return valTab

    def addList(self, table, category):

        if category == 'main-menu':
            for i in range(len(table)):
                item = CListItem(   name = table[i].encode('UTF-8'),
                                    title = table[i].encode('UTF-8'),
                                    category = category,
                                    description = 'For danish YouSee cable TV customers only',
                                    type = CListItem.TYPE_CATEGORY)

                self.currList.append(item)

        elif category == 'yousee-channels':
            for i in range(len(table)):
                item = CListItem(   name = table[i][0],
                                    title = table[i][1].encode('UTF-8'),
                                    category = category,
                                    videoUrl = 'yousee-channel-id:' + str(table[i][0]),
                                    type = CListItem.TYPE_VIDEO)
                
                self.currList.append(item)

    def handleService(self, index, refresh = 0):
    
        if 0 == refresh:
            if len(self.currList) <= index:
                print( "handleService wrong index: %s, len(self.currList): %d" % (index, len(self.currList)) )
                return
        
            if -1 == index:               
                self.name = None
                self.title = ''
                self.category = ''
                self.page = 0
                self.description = ''
                self.videoUrl = ''
                print( "yousee: handleService for first self.category" )
            else:
                item = self.currList[index]
                self.name = item.name
                self.title = item.title
                self.category = item.category
                self.page = item.page
                self.description = item.description
                self.videoUrl = item.videoUrl
                print( "yousee: |||||||||||||||||||||||||||||||||||| %s " % item.name )
        
        self.currList = []

        if self.name == None:
            self.addList(self.getMenuTable(),'main-menu')
        if self.category == 'main-menu' and self.LIVE_TV == index:
            self.addList(self.getYouSeeChannelsTab(),'yousee-channels')
        return
        
class IPTVHost(IHost):

    def __init__(self):
        self.host = None
        self.currIndex = -1
        self.listOfprevList = [] 
    
    # return firs available list of item category or video or link
    def getInitList(self):
        self.host = YouSee()
        self.currIndex = -1
        self.listOfprevList = [] 
        
        self.host.handleService(self.currIndex)
        
        convList = self.convertList(self.host.getCurrList())
        
        return RetHost(RetHost.OK, value = convList)
    
    # return List of item from current List
    # for given Index
    # 1 == refresh - force to read data from 
    #                server if possible 
    # server instead of cache 
    def getListForItem(self, Index = 0, refresh = 0, selItem = None):
        self.listOfprevList.append(self.host.getCurrList())
        
        self.currIndex = Index
        self.host.handleService(Index, refresh)
        convList = self.convertList(self.host.getCurrList())
        
        return RetHost(RetHost.OK, value = convList)
        
    # return prev requested List of item 
    # for given Index
    # 1 == refresh - force to read data from 
    #                server if possible
    def getPrevList(self, refresh = 0):
        if(len(self.listOfprevList) > 0):
            hostList = self.listOfprevList.pop()
            self.host.setCurrList(hostList)
            convList = self.convertList(hostList)
            return RetHost(RetHost.OK, value = convList)
        else:
            return RetHost(RetHost.ERROR, value = [])
        
    # return current List
    # for given Index
    # 1 == refresh - force to read data from 
    #                server if possible
    def getCurrentList(self, refresh = 0):      
        if refresh == 1:
            self.host.handleService(self.currIndex, refresh)
        convList = self.convertList(self.host.getCurrList())
        return RetHost(RetHost.OK, value = convList)
    
    # return resolved url
    # for given url
    def getResolvedURL(self, url):
        printDBG("yousee.getResolvedURL: %s" % url)
        list = []
        if url not in [None, '']:
            if url.startswith('yousee-channel-id:'):
                id = url.split(':')[1]
                ret = self.host.api_ys.streamUrl(id)
                rtmpUrl = ret['url'].encode('UTF-8')
                printDBG(rtmpUrl)
                if rtmpUrl:
                    printDBG("yousee.getResolvedurl.append: %s" % rtmpUrl)
                if rtmpUrl.find('://') >= 0 :
                    list.append(rtmpUrl)
        return RetHost(RetHost.OK, value = list)
            
    # return full path to player logo
    def getLogoPath(self):  
        return RetHost(RetHost.OK, value = [ GetLogoDir('youseelogo.png') ])

    def convertList(self, cList):
        hostList = []
        
        for cItem in cList:
            hostLinks = []
            description = cItem.description
            type = CDisplayListItem.TYPE_UNKNOWN
            if cItem.type == CListItem.TYPE_CATEGORY:
                type = CDisplayListItem.TYPE_CATEGORY
            elif cItem.type == CListItem.TYPE_VIDEO:
                type = CDisplayListItem.TYPE_VIDEO
                hostLinks.append(CUrlItem('', cItem.videoUrl, 1))

            hostItem = CDisplayListItem(name = cItem.title,
                                        description = description,
                                        type = type,
                                        urlItems = hostLinks,
                                        urlSeparateRequest = 0,
                                        iconimage = '')
            hostList.append(hostItem)
            
        return hostList
