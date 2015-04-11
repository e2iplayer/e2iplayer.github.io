# -*- coding: utf-8 -*-
# based on (root)/trunk/xbmc-addons/src/plugin.video.polishtv.live/ @ 635 - Wersja 668

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CDisplayListItem, RetHost, CUrlItem
import Plugins.Extensions.IPTVPlayer.libs.pCommon as pCommon
from Plugins.Extensions.IPTVPlayer.libs.youtubeparser import YouTubeParser
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, CSelOneLink, GetLogoDir

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
    return 'Kabarety Odpoczywam'

class Kabarety:
    MAINURL = 'http://www.kabarety.odpoczywam.net/'
    IMGURL = 'http://i.ytimg.com/vi/'

    NAJ_LINK = MAINURL + '/bestof/page:'
    NOW_LINK = MAINURL + '/index/page:'

    SERVICE_MENU_TABLE = {
        1: "Najnowsze",
        2: "Najlepsze",
        3: "Kategorie",
        4: "Wyszukaj",
    }
    def __init__(self):
        self.cm = pCommon.common()
        self.currList = []
        self.ytp = YouTubeParser()
        self.ytformats = config.plugins.iptvplayer.ytformat.value
        
    def _getFullUrl(self, url, baseUrl=None):
        if None == baseUrl: baseUrl = Kabarety.MAINURL
        if 0 < len(url) and not url.startswith('http'):
            url =  baseUrl + url
        return url
        
    def getCurrList(self):
        return self.currList

    def setCurrList(self, list):
        self.currList = list
        return 

    def setTable(self):
        return self.SERVICE_MENU_TABLE

    def listsMainMenu(self, table):
        printDBG("Kabarety.listsMainMenu")
        self.currList = []
        for num, val in table.items():
            item = {'type': 'dir', 'name': 'main-menu', 'category': val, 'title': val, 'icon': ''}
            self.currList.append(item)

    def getCategories(self, url):
        printDBG("Kabarety.getCategories")
        self.currList = []
        query_data = { 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        try:
            data = self.cm.getURLRequestData(query_data)
        except:
            printDBG("Kabarety.getCategories exception")
            return
            
        match = re.compile('<b>Kategorie</a><br><br>(.+?)<br><br>', re.DOTALL).findall(data)
        if len(match) > 0:
            match2 = re.compile('href="(.+?)">(.+?)</a>').findall(match[0])
            if len(match2) > 0:
                for i in range(len(match2)):
                    title = self.cm.html_entity_decode(match2[i][1])
                    item = {'type': 'dir', 'name': 'category', 'title': title, 'category': match2[i][0], 'icon': ''}
                    self.currList.append(item)

    def getFilmTab(self, url, page):
        printDBG("Kabarety.getFilmTab")
        self.currList = []
        query_data = { 'url': self._getFullUrl(url)+page, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True }
        try:
            data = self.cm.getURLRequestData(query_data)
        except:
            printDBG("Kabarety.getFilmTab exception")
            return
        link = data.replace('\n', '') #MOD
        match = re.compile('<a class="video-mini" title="(.+?)" href=".+?">.+?<span class="duration".+?<img class="video-mini-img".+?src="http://i.ytimg.com/vi/(.+?)/0.jpg" />').findall(link)
        if len(match) > 0:
            for i in range(len(match)):
                title = self.cm.html_entity_decode(match[i][0])
                img = self.IMGURL + match[i][1] + '/0.jpg'
                item = {'type': 'video', 'title': title, 'page': match[i][1], 'icon': img}
                self.currList.append(item)
        match = re.compile('<span><a href=".+?" class="next shadow-main">&raquo;</a></span>').findall(data)
        if len(match) > 0:
            newpage = str(int(page) + 1)
            item = {'type': 'dir', 'name': 'nextpage', 'title': 'Następna strona', 'category': url, 'page': newpage, 'icon': ''}
            self.currList.append(item)

    def getMovieUrls(self, vID):
        printDBG("Kabarety.getMovieUrls vID: " + vID)
        url = 'http://www.youtube.com/watch?v=' + vID
        tmpTab = self.ytp.getDirectLinks(url, self.ytformats)
        
        movieUrls = []
        for item in tmpTab:
            movieUrls.append({'name': item['format'] + '\t' + item['ext'] , 'url':item['url']})
        
        return movieUrls

    def handleService(self, index, refresh = 0, searchPattern = ''):
        printDBG("Kabarety.handleService")
        if 0 == refresh:
            if len(self.currList) <= index:
                printDBG( "handleService wrong index: %s, len(self.currList): %d" % (index, len(self.currList)) )
                return
            self.name = None
            self.title = ''
            self.category = ''
            self.page = ''
            self.icon = ''
            self.link = ''
            self.action = ''
            if -1 == index:
                printDBG( "Kinomaniak: handleService for first self.category" )
            else:
                item = self.currList[index]
                
                if "name" in item: self.name = item['name']
                if "title" in item: self.title = item['title']
                if "category" in item: self.category = item['category']
                if "page" in item: self.page = item['page']
                if "icon" in item: self.icon = item['icon']
                if "url" in item: self.link = item['url']
                if "action" in item: self.action = item['action']
                
                printDBG( "Kabarety: |||||||||||||||||||||||||||||||||||| %s " % item["name"] )
        self.currList = []
        name = self.name
        title = self.title
        category = self.category
        page = self.page
        icon = self.icon
        link = self.link
        action = self.action

        if str(page)=='None' or page=='': page = '1'

    #MAIN MENU
        if name == None:
            self.listsMainMenu(self.SERVICE_MENU_TABLE)
    #NAJNOWSZE
        elif category == self.setTable()[1]:
            self.getFilmTab(self.NOW_LINK, page)
    #NAJLEPSZE
        elif category == self.setTable()[2]:
            self.getFilmTab(self.NAJ_LINK, page)
    #KATEGORIE
        elif category == self.setTable()[3]:
            self.getCategories(self.MAINURL)
    #WYSZUKAJ
        elif category == self.setTable()[4]:
            self.getFilmTab(self.MAINURL + '/search/' + searchPattern + '/page:', page)
    #LISTA TYTULOW
        elif name == 'category' or  name == 'nextpage':
            url = category + '/page:'
            self.getFilmTab(url, page)
# end Kabarety


def _getLinkQuality( itemLink ):
    tab = itemLink['name'].split('x')
    return int(tab[0])
    
class IPTVHost(IHost):

    def __init__(self):
        self.host = None
        self.currIndex = -1
        self.listOfprevList = [] 
        
        self.searchPattern = ''
        self.searchType = ''
    
    # return firs available list of item category or video or link
    def getInitList(self):
        self.isSearch = False
        self.host = Kabarety()
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
            
        retlist = []
        urlList = self.host.getMovieUrls(self.host.currList[Index]["page"])
        if config.plugins.iptvplayer.ytUseDF.value:
            maxRes = int(config.plugins.iptvplayer.ytDefaultformat.value) * 1.1
            def __getLinkQuality( itemLink ):
                tab = itemLink['name'].split('x')
                return int(tab[0])
            urlList = CSelOneLink(urlList, __getLinkQuality, maxRes).getOneLink()
            
        for item in urlList:
            nameLink = item['name']
            url = item['url']
            retlist.append(CUrlItem(nameLink, url, 0))
            
        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
        
    # return resolved url
    # for given url
    def getResolvedURL(self, url):
        if url != None and url != '':
        
            ret = self.host.up.getVideoLink( url )
            list = []
            if ret:
                list.append(ret)
            
            return RetHost(RetHost.OK, value = list)
            
        else:
            return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
    # end getResolvedURL
            
    # return full path to player logo
    def getLogoPath(self):  
        return RetHost(RetHost.OK, value = [ GetLogoDir('kabaretylogo.png') ])


    def convertList(self, cList):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        
        for cItem in cList:
            hostLinks = []
                
            type = CDisplayListItem.TYPE_UNKNOWN
            possibleTypesOfSearch = None
            if cItem['type'] == 'dir':
                if cItem['title'] == 'Wyszukaj':
                    type = CDisplayListItem.TYPE_SEARCH
                    possibleTypesOfSearch = searchTypesOptions
                else:
                    type = CDisplayListItem.TYPE_CATEGORY
            elif cItem['type'] == 'video':
                type = CDisplayListItem.TYPE_VIDEO
                
            title = ''
            if 'title' in cItem: title = cItem['title']
            description = ''
            if 'plot' in cItem: description =  cItem['plot']
            icon = ''
            if 'icon' in cItem: icon =  cItem['icon']
            
            hostItem = CDisplayListItem(name = title,
                                        description = description,
                                        type = type,
                                        urlItems = hostLinks,
                                        urlSeparateRequest = 1,
                                        iconimage = icon,
                                        possibleTypesOfSearch = possibleTypesOfSearch)
            hostList.append(hostItem)
            
        return hostList
    # end convertList
        
    def getSearchResults(self, searchpattern, searchType = None):
        self.isSearch = True
        retList = []
        self.searchPattern = searchpattern
        self.searchType = searchType
        
        #4: Wyszukaj
        return self.getListForItem(3)
    # end getSearchResults
    
