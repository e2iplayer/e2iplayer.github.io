# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CDisplayListItem, RetHost, CUrlItem
import Plugins.Extensions.IPTVPlayer.libs.pCommon as pCommon
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, GetLogoDir
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta

###################################################
# FOREIGN import
###################################################
import re, urllib    
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry, ConfigPIN
###################################################

###################################################
# Config options for HOST
###################################################
#config.plugins.iptvplayer.PIN = ConfigPIN(default = 6666 , censor='*')

def GetConfigList():
    optionList = []
    return optionList
###################################################

###################################################
# Title of HOST
###################################################
def gettytul():
    return 'Apple Trailers'

class IPTVHost(IHost):
    LOGO_NAME = 'appletrailerslogo.png'

    def __init__(self):
        printDBG( "init begin" )
        self.host = Host()
        self.prevIndex = []
        self.currList = []
        self.prevList = []
        printDBG( "init end" )
    
    def getLogoPath(self):  
        return RetHost(RetHost.OK, value = [GetLogoDir(self.LOGO_NAME)])

    def getInitList(self):
        printDBG( "getInitList begin" )
        self.prevIndex = []
        self.currList = self.host.getInitList()
        self.host.setCurrList(self.currList)
        self.prevList = []
        printDBG( "getInitList end" )
        return RetHost(RetHost.OK, value = self.currList)

    def getListForItem(self, Index = 0, refresh = 0, selItem = None):
        printDBG( "getListForItem begin" )
        self.prevIndex.append(Index)
        self.prevList.append(self.currList)
        self.currList = self.host.getListForItem(Index, refresh, selItem)
        #self.currList = [ self.prevList[-1][Index] ]
        printDBG( "getListForItem end" )
        return RetHost(RetHost.OK, value = self.currList)

    def getPrevList(self, refresh = 0):
        printDBG( "getPrevList begin" )
        if(len(self.prevList) > 0):
            self.prevIndex.pop()
            self.currList = self.prevList.pop()
            self.host.setCurrList(self.currList)
            printDBG( "getPrevList end OK" )
            return RetHost(RetHost.OK, value = self.currList)
        else:
            printDBG( "getPrevList end ERROR" )
            return RetHost(RetHost.ERROR, value = [])

    def getCurrentList(self, refresh = 0):
        printDBG( "getCurrentList begin" )
        #if refresh == 1
        #self.prevIndex[-1] #ostatni element prevIndex
        #self.prevList[-1]  #ostatni element prevList
        #tu pobranie listy dla dla elementu self.prevIndex[-1] z listy self.prevList[-1]  
        printDBG( "getCurrentList end" )
        return RetHost(RetHost.OK, value = self.currList)

    def getLinksForVideo(self, Index = 0, item = None):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    def getResolvedURL(self, url):
        printDBG( "getResolvedURL begin" )
        if url != None and url != '':        
            ret = self.host.getResolvedURL(url)
            if ret != None and ret != '':        
               printDBG( "getResolvedURL ret: "+ret)
               list = []
               list.append(ret)
               printDBG( "getResolvedURL end OK" )
               return RetHost(RetHost.OK, value = list)
            else:
               printDBG( "getResolvedURL end" )
               return RetHost(RetHost.NOT_IMPLEMENTED, value = [])                
        else:
            printDBG( "getResolvedURL end" )
            return RetHost(RetHost.NOT_IMPLEMENTED, value = [])

    def getSearchResults(self, pattern, searchType = None):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])

    ###################################################
    # Additional functions on class IPTVHost
    ###################################################

class Host:
    currList = []
    MAIN_URL = ''
    
    def __init__(self):
        printDBG( 'Host __init__ begin' )
        self.cm = pCommon.common()
        self.currList = []
        printDBG( 'Host __init__ begin' )
        
    def setCurrList(self, list):
        printDBG( 'Host setCurrList begin' )
        self.currList = list
        printDBG( 'Host setCurrList begin' )
        return 

    def getInitList(self):
        printDBG( 'Host getInitList begin' )
        #self.currList = self.MAIN_MENU
        self.currList = self.listsItems(-1, '', 'main-menu')
        printDBG( 'Host getInitList end' )
        return self.currList

    def getListForItem(self, Index = 0, refresh = 0, selItem = None):
        printDBG( 'Host getListForItem begin' )
        valTab = []
        if len(self.currList[Index].urlItems) == 0:
           return valTab
        valTab = self.listsItems(Index, self.currList[Index].urlItems[0], self.currList[Index].urlSeparateRequest)
        self.currList = valTab
        printDBG( 'Host getListForItem end' )
        return self.currList

    def listsItems(self, Index, url, name = ''):
        printDBG( 'Host listsItems begin' )
        printDBG( 'Host listsItems url: '+url )
        valTab = []
        if name == 'main-menu':
           printDBG( 'Host listsItems begin name='+name )
           #valTab.append(CDisplayListItem("Newest (HD-1080p)",  "Newest (HD-1080p)",  CDisplayListItem.TYPE_CATEGORY, ['http://trailers.apple.com/trailers/home/xml/newest_1080p.xml'],  'appletrailers-movies', '', None)) 
           #valTab.append(CDisplayListItem("Current (HD-1080p)", "Current (HD-1080p)", CDisplayListItem.TYPE_CATEGORY, ['http://trailers.apple.com/trailers/home/xml/current_1080p.xml'], 'appletrailers-movies', '', None)) 
           valTab.append(CDisplayListItem("Newest (HD-720p)",   "Newest (HD-720p)",   CDisplayListItem.TYPE_CATEGORY, ['http://trailers.apple.com/trailers/home/xml/newest_720p.xml'],   'appletrailers-movies', '', None)) 
           valTab.append(CDisplayListItem("Current (HD-720p)",  "Current (HD-720p)",  CDisplayListItem.TYPE_CATEGORY, ['http://trailers.apple.com/trailers/home/xml/current_720p.xml'],  'appletrailers-movies', '', None)) 
           valTab.append(CDisplayListItem("Newest (HD-480p)",   "Newest (HD-480p)",   CDisplayListItem.TYPE_CATEGORY, ['http://trailers.apple.com/trailers/home/xml/newest_480p.xml'],   'appletrailers-movies', '', None)) 
           valTab.append(CDisplayListItem("Current (HD-480p)",  "Current (HD-480p)",  CDisplayListItem.TYPE_CATEGORY, ['http://trailers.apple.com/trailers/home/xml/current_480p.xml'],  'appletrailers-movies', '', None)) 
           valTab.append(CDisplayListItem("Newest (SD)",        "Newest (SD)",        CDisplayListItem.TYPE_CATEGORY, ['http://trailers.apple.com/trailers/home/xml/newest.xml'],        'appletrailers-movies', '', None)) 
           valTab.append(CDisplayListItem("Current (SD)",       "Current (SD)",       CDisplayListItem.TYPE_CATEGORY, ['http://trailers.apple.com/trailers/home/xml/current.xml'],       'appletrailers-movies', '', None)) 
           printDBG( 'Host listsItems end' )
           return valTab
        
        # ########## #
        if 'appletrailers-movies' == name:
           printDBG( 'Host listsItems begin name='+name )
           self.MAIN_URL = 'http://trailers.apple.com' 
           query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
           try:
              data = self.cm.getURLRequestData(query_data)
           except:
              printDBG( 'Host listsItems query error' )
              printDBG( 'Host listsItems query error url:'+url )
              return valTab
           printDBG( 'Host listsItems data: '+data )
           phMovies = re.findall('<movieinfo.*?<title>(.*?)</title>.*?<runtime>(.*?)</runtime>.*?<location>(.*?)</location>.*?<large filesize=".*?">(.*?)</large>', data, re.S)
           if phMovies:
              for (phTitle, phRuntime, phImage, phUrl) in phMovies:
                  phUrl = urlparser.decorateUrl(phUrl, {'User-Agent':'QuickTime/7.6.2'})
                  printDBG( 'Host listsItems phTitle:   ' +phTitle )
                  printDBG( 'Host listsItems phRuntime: ' +phRuntime )
                  printDBG( 'Host listsItems phImage:   ' +phImage )
                  printDBG( 'Host listsItems phUrl:     ' +phUrl )
                  valTab.append(CDisplayListItem(phTitle,'['+phRuntime+'] '+phTitle,CDisplayListItem.TYPE_VIDEO, [CUrlItem('', phUrl, 1)], 0, phImage, None)) 
           printDBG( 'Host listsItems end' )
           return valTab

        return valTab

    def getResolvedURL(self, url):
        printDBG( 'Host getResolvedURL begin' )
        printDBG( 'Host getResolvedURL url: '+url )
        videoUrl = ''
        valTab = []

        if self.MAIN_URL == 'http://trailers.apple.com':
           printDBG( 'Host getResolvedURL mainurl: '+self.MAIN_URL )
           return url

        printDBG( 'Host getResolvedURL end' )
        return videoUrl
