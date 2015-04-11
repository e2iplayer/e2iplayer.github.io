# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, CSearchHistoryHelper, GetLogoDir, CSelOneLink
from Plugins.Extensions.IPTVPlayer.libs.youtubeparser import YouTubeParser
###################################################
# FOREIGN import
###################################################
import re
from Components.config import config
###################################################

###################################################
# Config options for HOST
###################################################

def GetConfigList():
    return []
###################################################

def gettytul():
    return 'FightTube'

class FightTube:
    MAINURL = 'http://www.fighttube.pl/'
    SEARCHURL = MAINURL + 'search/?keywords='

    def __init__(self):
        self.cm = common()
        self.history = CSearchHistoryHelper('fighttube')
        self.ytp = YouTubeParser()
        self.ytformats = config.plugins.iptvplayer.ytformat.value
        
        # temporary data
        self.currList = []
        self.currItem = {}

    def getCurrList(self):
        return self.currList

    def setCurrList(self, list):
        self.currList = list
        
    def getCurrItem(self):
        return self.currItem

    def setCurrItem(self, item):
        self.currItem = item

    @staticmethod
    def printDBG( strDBG ):
        printDBG('[IPTV FightTube] ' + strDBG)
        
    def getVideoUrl(self, url):
        FightTube.printDBG("getVideoUrl url[%s]" % url)

        query_data = {'url': url, 'return_data': True}
        try:
            data = self.cm.getURLRequestData(query_data)
        except:
            FightTube.printDBG('getVideoUrl exception')
            return []
            
        match = re.search('<embed src="([^"]+?)" type="application/x-shockwave-flash"', data)
        if match:
            return self.getYTVideoUrl(match.group(1))
        else:
            FightTube.printDBG('getVideoUrl YT embed not found!')
        
        return []

    def getYTVideoUrl(self, url):
        FightTube.printDBG("getYTVideoUrl url[%s]" % url)
        tmpTab = self.ytp.getDirectLinks(url, self.ytformats)
     
        movieUrls = []
        for item in tmpTab:
            movieUrls.append({'name': item['format'] + '\t' + item['ext'] , 'url':item['url']})
            
        return movieUrls

    def listsMainMenu(self):
        FightTube.printDBG('listsMainMenu start')
        query_data = {'url': self.MAINURL, 'return_data': True}
        try:
            data = self.cm.getURLRequestData(query_data)
        except:
            FightTube.printDBG('listsMainMenu exception')
            return
    
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, 'Kategorie video', '</ul>', False)
        if not sts:
            printDBG('listsMainMenu: menu marker cannot be found!')
            return
        match = re.compile("<a href='([^']+?)' class='level0'[^>]+?>([^<]+?)</a>").findall(data)
        if len(match) > 0:
            for i in range(len(match)):
                params = {'type': 'category', 'title': match[i][1], 'page': match[i][0], 'icon': ''}
                self.currList.append(params)
                
        params = {'type': 'category', 'title': 'Wyszukaj', 'page': self.SEARCHURL, 'icon': ''}
        self.currList.append(params)
        return
        
    def getMovieTab(self, url):
        FightTube.printDBG('getMovieTab start')
        query_data = { 'url': url, 'return_data': True }
        try:
            data = self.cm.getURLRequestData(query_data)
        except:
            FightTube.printDBG('getMovieTab exception')
            return            
        # get next page url
        nexPageUrl = ''
        sts, tmp = CParsingHelper.getDataBeetwenMarkers(data, "<nav class='pagination'>", "</nav>", False)
        if sts:
            match = re.search("<li><a href='([^']+?)'>&gt;</a></li>", tmp)
            if match: nexPageUrl = match.group(1)
                
        # separete vidTab
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, "<ul class='videos-listing'>", "</ul>", False)
        if not sts:
            printDBG('getMovieTab: main markers cannot be found!')
            return
            
        # separate videos data
        data = data.split('</li>')
        for vidItem in data:
            url = ''
            title = ''
            icon = ''
            ocena = ''
            wyswietlen = ''
            match = re.search("<a href='([^']+?)'", vidItem)
            if match: 
                url = match.group(1)
            match = re.search("<img src='([^']+?)' alt='([^']+?)'", vidItem)
            if match: 
                icon = match.group(1)
                title = match.group(2)
                
            if '' != url and '' != title:
                params = {'type': 'video', 'title': title, 'page': url, 'icon': icon}
                self.currList.append(params)
            

        if nexPageUrl.startswith("http://"):
            params = {'type': 'category', 'name': 'nextpage', 'title': 'Następna strona', 'page': nexPageUrl, 'icon': ''}
            self.currList.append(params)
        return
 
    def searchTab(self, text):
        FightTube.printDBG('searchTab start')
        self.getMovieTab(self.SEARCHURL + text)

    def handleService(self, index, refresh = 0, searchPattern = ''):
        FightTube.printDBG('handleService start')
        if 0 == refresh:
            if len(self.currList) <= index:
                FightTube.printDBG( "handleService wrong index: %s, len(self.currList): %d" % (index, len(self.currList)) )
                return
            if -1 == index:
                # use default value
                self.currItem = { "name": None }
                FightTube.printDBG( "handleService for first self.category" )
            else:
                self.currItem = self.currList[index]

        name     = self.currItem.get("name", '')
        title    = self.currItem.get("title", '')
        category = self.currItem.get("category", '')
        page     = self.currItem.get("page", '')
        icon     = self.currItem.get("icon", '')
        type     = self.currItem.get("type", '')

 
        FightTube.printDBG( "handleService: |||||||||||||||||||||||||||||||||||| [%s] " % name )
        self.currList = []


    #MAIN MENU == KATEGORIE
        if name == None:
            self.listsMainMenu()
        elif type != 'category':
            return
    #WYSZUKAJ
        elif title == 'Wyszukaj':
            if searchPattern != None:
                self.searchTab(searchPattern)
        else:
            self.getMovieTab(page)
            
class IPTVHost(IHost):

    def __init__(self):
        self.host = None
        self.currIndex = -1
        self.listOfprevList = [] 
        self.listOfprevItems = [] 
        
        self.searchPattern = ''
    
    # return firs available list of item category or video or link
    def getInitList(self):
        self.isSearch = False
        self.host = FightTube()
        self.currIndex = -1
        self.listOfprevList = [] 
        self.listOfprevItems = []
        
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
        self.listOfprevItems.append(self.host.getCurrItem())
        
        self.currIndex = Index
        self.host.handleService(Index, refresh, self.searchPattern)
        convList = self.convertList(self.host.getCurrList())
        
        return RetHost(RetHost.OK, value = convList)
        
    # return prev requested List of item 
    # for given Index
    # 1 == refresh - force to read data from 
    #                server if possible
    def getPrevList(self, refresh = 0):
        if(len(self.listOfprevList) > 0):
            hostList = self.listOfprevList.pop()
            hostCurrItem = self.listOfprevItems.pop()
            self.host.setCurrList(hostList)
            self.host.setCurrItem(hostCurrItem)
            
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
            self.host.handleService(self.currIndex, refresh, self.searchPattern)
        convList = self.convertList(self.host.getCurrList())
        return RetHost(RetHost.OK, value = convList)
        
    # return list of links for VIDEO with given Index
    # for given Index
    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] != 'video':
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])
            
        
        
        urlsTab = self.host.getVideoUrl(self.host.currList[Index]["page"])
        if config.plugins.iptvplayer.ytUseDF.value:
            maxRes = int(config.plugins.iptvplayer.ytDefaultformat.value) * 1.1
            def __getLinkQuality( itemLink ):
                tab = itemLink['name'].split('x')
                return int(tab[0])
            urlsTab = CSelOneLink(urlsTab, __getLinkQuality, maxRes).getOneLink()
        retlist = []
        for urlItem in urlsTab:
            retlist.append(CUrlItem(urlItem['name'], urlItem['url'], 0))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
        
    # return resolved url
    # for given url
    def getResolvedURL(self, url):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
    # end getResolvedURL
            
    # return full path to player logo
    def getLogoPath(self):  
        return RetHost(RetHost.OK, value = [ GetLogoDir('fighttubelogo.png') ])

    def convertList(self, cList):
        hostList = []
        
        for cItem in cList:
            hostLinks = []
                
            type = CDisplayListItem.TYPE_UNKNOWN
            possibleTypesOfSearch = None
            if cItem['type'] == 'category':
                if cItem['title'] == 'Wyszukaj':
                    type = CDisplayListItem.TYPE_SEARCH
                else:
                    type = CDisplayListItem.TYPE_CATEGORY
            elif cItem['type'] == 'video':
                type = CDisplayListItem.TYPE_VIDEO
                
            title       =  cItem.get('title', '')
            description =  cItem.get('plot', '')
            icon        =  cItem.get('icon', '')
            
            hostItem = CDisplayListItem(name = title,
                                        description = description,
                                        type = type,
                                        urlItems = hostLinks,
                                        urlSeparateRequest = 1,
                                        iconimage = icon )
            hostList.append(hostItem)
            
        return hostList
    # end convertList
        
    def getSearchResults(self, searchpattern, searchType = None):
        self.isSearch = True
        retList = []
        self.searchPattern = searchpattern
        
        # Find 'Wyszukaj' item
        list = self.host.getCurrList()
        try:
            for i in range( len(list) ):
                if list[i]['title'] == 'Wyszukaj':
                    return self.getListForItem( i )
        except:
            printDBG('getSearchResults EXCEPTION')
            
        return RetHost(RetHost.ERROR, value = [])
            
    # end getSearchResults
    


    
