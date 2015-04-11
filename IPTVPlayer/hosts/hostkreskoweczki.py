# -*- coding: utf-8 -*-
# Based on (root)/trunk/xbmc-addons/src/plugin.video.polishtv.live/self.HOSTs/ @ 419 - Wersja 636

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, CSearchHistoryHelper, GetLogoDir
import Plugins.Extensions.IPTVPlayer.libs.pCommon as pCommon
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
###################################################

###################################################
# FOREIGN import
###################################################
import re, urllib
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, fileExists
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
    return 'Kreskóweczki'

class Kreskoweczki(CBaseHostClass):
    MAINURL = 'http://www.kreskoweczki.pl'

    MENU_TAB = {
        1: "Kreskówki alfabetycznie",
        2: "Ostatnio uzupełnione",
        3: "Wyszukaj",
        4: "Historia Wyszukiwania"
    }
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'kreskoweczki'})

    def setTable(self):
        return self.MENU_TAB

    def listsMainMenu(self, table):
        for num, val in table.items():
            params = { 'name': 'main-menu','category': val, 'title': val, 'icon': ''}
            self.addDir(params)

    def listsABCMenu(self, table):
        for i in range(len(table)):
            params = { 'name': 'abc-menu','category': table[i], 'title': table[i], 'icon': ''}
            self.addDir(params)

    def showTitles(self, letter):
        query_data = {'url': self.MAINURL, 'return_data': True}
        try:
            data = self.cm.getURLRequestData(query_data)
        except:
            printDBG('showTitles EXCEPTION')
            return
        matchAll = re.compile('<ul class="menu" id="categories_block">(.+?)</ul>', re.DOTALL).findall(data)
        if len(matchAll) > 0:
            match = re.compile('<a href=.(.+?). class=.level0. alt=.(.+?) \(([0-9]+?)\).>').findall(matchAll[1])
            if len(match) > 0:
                for i in range(len(match)):
                    addItem = False
                    title = match[i][1].strip()

                    if letter == '0 - 9' and (ord(title[0]) < 65 or ord(title[0]) > 91): addItem = True
                    if (letter == title[0].upper()): addItem = True
                    if int(match[i][2]) == 0: addItem = False
                    if (addItem):
                        params = { 'name': 'episode', 'title': title, 'page': match[i][0], 'icon': ''}
                        self.addDir(params)

    def showParts(self, url):
        query_data = {'url': url, 'return_data': True}
        try:
            data = self.cm.getURLRequestData(query_data)
        except:
            printDBG('showParts EXCEPTION')
            return

        matchAll = re.compile("<div class='list-videos'>(.+?)<br />", re.DOTALL).findall(data)
        if len(matchAll) > 0:
            match = re.compile("<a href='(.+?)' title='(.+?)'><img src='(.+?)'.+?<dt class='series'>.+?title='(.+?)'>", re.DOTALL).findall(matchAll[0])
            if len(match) > 0:
                for i in range(len(match)):
                    serial = match[i][3]
                    title = '%s - %s' % (serial, match[i][1])
                    link = match[i][0]
                    params = {'title': title, 'page': link, 'icon': match[i][2]}
                    self.addVideo(params)
        match2 = re.compile("class='active'>.+?</a>  <a href='(.+?)'").findall(data)
        printDBG(str(match2))
        if len(match2) > 0:
            params = { 'name': 'nextpage', 'title': 'Następna strona', 'page': match2[0], 'icon': ''}
            self.addDir(params)

    def getVideoUrl(self, url):
        videoUrl = ''
        videosTab = []
        vid = re.compile("kreskowka/(.+?)/").findall(url)
        HEADER = {'Referer' : url}
        query_data = {'url': 'http://www.kreskoweczki.pl/fullscreen/', 'header': HEADER, 'return_data': True}
        postdata = {'v_id' : vid[0]}
        try:
            data = self.cm.getURLRequestData(query_data, postdata)
        except:
            printDBG('getVideoUrl EXCEPTION')
            return videosTab
        matchAll = re.compile("Loader.skipBanners(.+?)Loader.skipBanners", re.DOTALL).findall(data)
        printDBG(str(matchAll))
        if len(matchAll) > 0:
            match = re.compile('Loader.loadFlashFile."(.+?)"').findall(matchAll[0])
            if len(match) > 0:
                videoUrl = match[0]
            else:
                match = re.compile('src="(.+?)"').findall(matchAll[0])
                if len(match) > 0:
                    videoUrl = match[0]
                    
        match = re.search('src="(http[^"]+?)"', videoUrl )
        if match:
            videoUrl = match.group(1)
            
        match = re.search("/embed/proxy[^.]+?.php", videoUrl)
        if match:
            sts,data = self.cm.getPage(videoUrl)
            if sts:
                match = re.search('url: "[^?^"]+?\?url=([^"]+?)"', data)
                if match:
                    url = match.group(1)
                    if url.endswith('.m3u8'):
                        return getDirectM3U8Playlist(url)
        else: return self.up.getVideoLinkExt(videoUrl)
        return []
        
    def getFavouriteData(self, cItem):
        return cItem['page']
        
    def getLinksForFavourite(self, fav_data):
        return self.getVideoUrl(fav_data)

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

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
    #KRESKÓWKI ALFABETYCZNIE
        elif category == self.setTable()[1]:
            self.listsABCMenu(self.cm.makeABCList())
        elif name == 'abc-menu':
            self.showTitles(category)
        elif name == 'episode' or name == 'nextpage':
            self.showParts(page)
    #OSTATNIO UZUPEŁNIONE
        elif category == self.setTable()[2]:
            self.showParts(self.MAINURL)
    #WYSZUKAJ
        elif category == self.setTable()[3]:
            text = searchPattern
            self.showParts(self.MAINURL+"/search/?keywords="+urllib.quote_plus(text))
    #HISTORIA WYSZUKIWANIA
        elif category == self.setTable()[4]:
            self.listsHistory()
        
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Kreskoweczki(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):  
        return RetHost(RetHost.OK, value = [ GetLogoDir('kreskoweczkilogo.png') ])

    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): RetHost(retCode, value=retlist)

        urlList = self.host.getVideoUrl(self.host.currList[Index]["page"])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], 0))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo

    def converItem(self, cItem):
        hostList = []        
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
            
        title       =  cItem.get('title', '')
        description =  cItem.get('plot', '')
        icon        =  cItem.get('icon', '')
        
        return CDisplayListItem(name = title,
                                description = description,
                                type = type,
                                urlItems = hostLinks,
                                urlSeparateRequest = 1,
                                iconimage = icon )
    # end converItem

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
