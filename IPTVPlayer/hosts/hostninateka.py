# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CHostBase, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, CSearchHistoryHelper, GetLogoDir
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import unescapeHTML
###################################################

###################################################
# FOREIGN import
###################################################
import re, urllib
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################

###################################################
# Config options for HOST
###################################################
# None

def GetConfigList():
    optionList = []
    # None
    return optionList
###################################################

def gettytul():
    return 'Ninateka'

class Ninateka:
    MAIN_URL = 'http://ninateka.pl/'
    VIDEOS_URL = MAIN_URL + 'filmy?MediaType=video&Paid=False&CategoryCodenames='
    SEARCH_URL = VIDEOS_URL + '&SearchQuery='
    
    DEFAULT_GET_PARAM = 'MediaType=video&Paid=False'
  
    MENU_TAB = {
        1: "Wszystkie",
        2: "Kategorie",
        3: "Wyszukaj",
        4: "Historia Wyszukiwania"
    }
    def __init__(self):
        self.menuHTML = ''
        self.refresh = False
        self.cm = common()
        self.history = CSearchHistoryHelper('ninateka')

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
        
    def getMenuHTML(self):
        printDBG("getMenuHTML start")
        
        if True == self.refresh or '' == self.menuHTML:
            self.menuHTML = ''
            sts, data = self.cm.getPage( self.MAIN_URL )
            if sts: self.menuHTML = CParsingHelper.getDataBeetwenMarkers(data, '<div class="nav-collapse collapse">', '<!--/.nav-collapse -->', False)[1]
        return self.menuHTML
        
    def setTable(self):
        return self.MENU_TAB
        
    def listsMainMenu(self, table):
        for num, val in table.items():
            params = {'type': 'category', 'name': 'main-menu', 'category': val, 'title': val}
            self.currList.append( params )
        
    def getMainCategory(self):
        menuHTML = self.getMenuHTML()
        
        match = re.compile('<li data-codename="([^"]+?)"><a href="/filmy/([^"^,^/]+?)">([^<]+?)</a>').findall( menuHTML )
        if len(match) > 0:
            for i in range(len(match)):
                params = {'type': 'category', 'name': 'main-category', 'page': match[i][0], 'title': match[i][2]}
                self.currList.append( params )
                
    def getSubCategory(self, cat):
        menuHTML = self.getMenuHTML()
        
        pattern = '<li data-codename="([^"]+?)"><a href="/filmy/(%s,[^"^,^/]+?)">([^<]+?)</a></li>' % cat
        match = re.compile( pattern ).findall( menuHTML )
        if len(match) > 0:
            for i in range(len(match)):
                params = {'type': 'category', 'name': 'sub-category', 'page': self.VIDEOS_URL + (match[i][1]).replace(',', '%2C'), 'title': match[i][2]}
                self.currList.append( params )

    def getVideoUrl(self, url):
        printDBG("getVideoUrl url[%s]" % url)
        linksTab = []
        sts, data = self.cm.getPage(url)
        if not sts:
            printDBG("getVideoUrl except")
            return linksTab
        
        match = re.search( '{"file":"([^"]+?.mp4)"}', data )
        if match: 
            linksTab.append( {'name': 'mp4', 'url': match.group(1)} )
        match = re.search( '{"file":"([^"]+?.m3u8)"}', data )
        if match: 
            m3u8Tab = getDirectM3U8Playlist( match.group(1))
            linksTab.extend(m3u8Tab)
        return linksTab

    def getVideosList(self, url):
        printDBG("getVideosList url[%s]" % url)
        sts, data = self.cm.getPage(url)
        if not sts:
            printDBG("getVideosList except")
            return
        
        # get pagination HTML part
        nextPageData = CParsingHelper.getDataBeetwenMarkers(data, 'class="pager"', '</div>', False)[1]
        # get Video HTML part
        data = CParsingHelper.getDataBeetwenMarkers(data, '<!-- ************ end user menu ************ -->', '</ul>', False)[1].split('<li>')
        del data[0]
        
        for videoItemData in data:
            printDBG('                              videoItemData')
            icon     = ''
            duration = ''
            gatunek  = ''
            plot     = ''
            title    = ''
            url      = ''
            
            if 'class="playIcon"' in videoItemData:
                # get icon src
                match = re.search('src="(http://[^"]+?)"', videoItemData)
                if match: icon = match.group(1).replace('&amp;', '&')
                # get duration
                match = re.search('class="duration"[^>]*?>([^<]+?)<', videoItemData)
                if match: duration = match.group(1).replace('&#39;', "'")
                # get gatunek
                match = re.search('"gatunek"[^>]*?>([^<]+?)<', videoItemData)
                if match: gatunek = match.group(1)
                # get plot
                match = re.search('class="text"[^>]*?>([^<]+?)<', videoItemData)
                if match: plot = match.group(1)
                # get title and url
                match = re.search('<a href="([^"]+?)" class="title"[^>]*?>([^<]+?)</a>', videoItemData)
                if match:
                    url   = self.MAIN_URL + match.group(1)
                    title = match.group(2)
                    params = {'type': 'video', 'page': url, 'title': title, 'icon': icon, 'duration': duration, 'gatunek': gatunek, 'plot': plot}
                    self.currList.append( params )

        # check next page
        nextPageUrl = ''
        match = re.search('href="([^"]+?)" class="nextPage"', nextPageData)
        if match: 
            nextPageUrl = match.group(1)
        else:
            match = re.search('href="([^"]+?)" class="lastPage"', nextPageData)
            if match:
                nextPageUrl = match.group(1)

        if '' != nextPageUrl:
            params = {'type': 'category', 'name': 'sub-category', 'page': self.MAIN_URL + nextPageUrl.replace('&amp;', '&'), 'title': 'Następna strona'}
            self.currList.append( params )
    # end getVideosList
    
    def listsHistory(self):
            list = self.history.getHistoryList()
            for item in list:
                params = { 'type': 'category', 'name': 'history', 'category': 'Wyszukaj', 'title': item, 'plot': 'Szukaj: "%s"' % item, 'icon': ''}
                self.currList.append( params )
            
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        if 0 == refresh:
            if len(self.currList) <= index:
                printDBG( "handleService wrong index: %s, len(self.currList): %d" % (index, len(self.currList)) )
                return
            if -1 == index:
                # use default value
                self.currItem = { "name": None }
                printDBG( "handleService for first self.category" )
            else:
                self.currItem = self.currList[index]

        name     = self.currItem.get("name", '')
        title    = self.currItem.get("title", '')
        category = self.currItem.get("category", '')
        page     = self.currItem.get("page", '')
        icon     = self.currItem.get("icon", '')

        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| [%s] " % name )
        self.currList = []

    #MAIN MENU
        if name == None:
            self.listsMainMenu(self.MENU_TAB)
    #WSZYSTKIE
        elif category == self.setTable()[1]:
            self.getVideosList(self.VIDEOS_URL)
    #KATEGORIE
        elif category == self.setTable()[2]:
            self.getMainCategory()
    #SUB-KATEGORIE
        elif name == 'main-category':
            self.getSubCategory(page)
        elif name == 'sub-category':
            self.getVideosList(page)
    #WYSZUKAJ
        elif category == self.setTable()[3]:
            text = searchPattern
            self.getVideosList(self.SEARCH_URL + urllib.quote_plus(text))
    #HISTORIA WYSZUKIWANIA
        elif category == self.setTable()[4]:
            self.listsHistory()
    #WRONG WAY
        else:
            printDBG('handleService WRONG WAY')

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Ninateka(), True)

    def getLogoPath(self):  
        return RetHost(RetHost.OK, value = [GetLogoDir('ninatekalogo.png')] )

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] != 'video':
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])

        retlist = []
        urlsTab = self.host.getVideoUrl(self.host.currList[Index]["page"])
        for item in urlsTab:
            retlist.append(CUrlItem(item['name'], item['url'], 0))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo

    def convertList(self, cList):
        hostList = []
        
        for cItem in cList:
            hostLinks = []
            type = CDisplayListItem.TYPE_UNKNOWN

            if cItem['type'] == 'category':
                if cItem['title'] == 'Wyszukaj':
                    type = CDisplayListItem.TYPE_SEARCH
                else:
                    type = CDisplayListItem.TYPE_CATEGORY
            elif cItem['type'] == 'video':
                type = CDisplayListItem.TYPE_VIDEO
                page = cItem.get('page', '')
                if '' != page:
                    hostLinks.append(CUrlItem("Link", page, 1))
                
            title     =  cItem.get('title',    '')
            icon      =  cItem.get('icon',     '')

            # prepar description
            descTab = ( (cItem.get('duration', ''), '|', '' ),
                        (cItem.get('gatunek',  ''), '|', '' ),
                        (cItem.get('plot',     ''), '|\t',  '' ) )
            description = ''
            for descItem in descTab:
                if '' != descItem[0]:
                    description += descItem[1] + descItem[0] + descItem[2] 
            
            hostItem = CDisplayListItem( name        = unescapeHTML(title.decode("utf-8")).encode("utf-8"),
                                         description = unescapeHTML(description.decode("utf-8")).encode("utf-8"),
                                         type        = type,
                                         urlItems    = hostLinks,
                                         urlSeparateRequest = 1,
                                         iconimage   = icon )
            hostList.append(hostItem)

        return hostList
    # end convertList

    def getSearchItemInx(self):
        # Find 'Wyszukaj' item
        try:
            list = self.host.getCurrList()
            for i in range( len(list) ):
                if list[i]['category'] == 'Wyszukaj':
                    return i
        except:
            printDBG('getSearchItemInx EXCEPTION')
            return -1

    def setSearchPattern(self):
        try:
            list = self.host.getCurrList()
            if 'history' == list[self.currIndex]['name']:
                pattern = list[self.currIndex]['title']
                self.host.history.addHistoryItem( pattern )
                self.searchPattern = pattern
        except:
            printDBG('setSearchPattern EXCEPTION')
            self.searchPattern = ''
        return
