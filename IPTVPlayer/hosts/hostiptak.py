# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, CSearchHistoryHelper, GetLogoDir
import Plugins.Extensions.IPTVPlayer.libs.pCommon as pCommon
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
###################################################

###################################################
# Config options for HOST
###################################################
# None

def GetConfigList():
    return []
###################################################

def gettytul():
    return 'iPtak'

class iPtak:
    MAINURL = 'http://iptak.pl/'
    
    M_NOWOSCI          = "Nowo dodane"
    M_POLECAMY         = "Polecamy"
    M_DISIAJ_NAJLEPSZE = "Najlepsze z tygodnia"
    M_KATRGORIE_FILMOW = "Kategorie filmów"
    M_WYSZUKAJ         = "Wyszukaj"
    M_HISTORIA         = "Historia wyszukiwania"
    
    SERVICE_MENU_TABLE = [
        M_NOWOSCI,
        M_POLECAMY,
        M_DISIAJ_NAJLEPSZE,
        M_KATRGORIE_FILMOW,
        M_WYSZUKAJ,
        M_HISTORIA
    ]
    def __init__(self):
        self.up = urlparser.urlparser()
        self.cm = pCommon.common()
        self.history = CSearchHistoryHelper('iptak')
        # temporary data
        self.currList = []
        self.currItem = {}
        
        # for cache to speedUp
        self.menuData = None

    def getCurrList(self):
        return self.currList

    def setCurrList(self, list):
        self.currList = list
        
    def getCurrItem(self):
        return self.currItem

    def setCurrItem(self, item):
        self.currItem = item

    def addDir(self, params):
        params['type'] = 'category'
        self.currList.append(params)
        return
        
    def addVideo(self, params):
        params['type'] = 'video'
        self.currList.append(params)
        return
        
    def getMenuData(self):
        printDBG("getMenuData start")
        if self.menuData == None:
            sts, self.menuData = self.cm.getPage( self.MAINURL )
            if False == sts:
                printDBG("getMenuData problem")
                self.menuData = None
        return self.menuData
        
    def getPropertiesValues(self, properties, data):
        retDict = dict()
        for prop in properties:
            match = re.search(prop + '="([^"]+?)"', data)
            if match: 
                retDict[prop] = match.group(1)
        return retDict

    def listsMainMenu(self, table):
        for val in table:
            params = { 'name': 'main-menu','category': val, 'title': val, 'icon': ''}
            self.addDir(params)
    
    def listMainBase(self, addMethod, category, mark1, mark2, splitMark):
        printDBG('listMainBase category[%s]: mark1[%s], mark2[%s], splitMark[%s]' % (category, mark1, mark2, splitMark) )
        data = self.getMenuData()
        if data == None: return
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, mark1, mark2)
        
        if False == sts: return
        data = data.split(splitMark)
        del data[0]
        printDBG('listMainBase len(data)[%r]' % len(data))
        for item in data:
            retDict = self.getPropertiesValues(['href', 'src', 'title'], item) 
            if 'href' in retDict:
                img = retDict.get('src', '')
                if not img.startswith('http://'):
                    img = self.MAINURL + img.replace('../', '')
                params = {'name': 'sub', 'category': category, 'title': retDict.get('title', ''), 'page': retDict['href'], 'icon': img}
                addMethod( params )
    # end listMainBase
    
    def listsMenuNowosci(self):
        printDBG("listsMenuNowosci start")
        self.listMainBase(addMethod=self.addVideo, category=self.M_NOWOSCI, mark1='<h3>Nowo dodane:</h3>', mark2='<div id="footer">', splitMark='<div id="item"')
    # end listsMenuNowosci
        
    def listsMenuPolecamy(self):
        printDBG("listsMenuPolecamy start")
        self.listMainBase(addMethod=self.addVideo, category=self.M_POLECAMY, mark1='<div class="banner">', mark2='<script', splitMark='<a')
    # end listsMenuPolecamy
    
    def listsMenuDzisiajNajlepsze(self):
        printDBG("listsMenuDzisiajNajlepsze start")
        data = self.getMenuData()
        if data == None:
            return
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'Najlepsze z tygodnia', '</ul>')
        if False == sts:
            return
        data = data.split('<li')
        del data[0]
        for item in data:
            retDict = self.getPropertiesValues(['href'], item) 
            if 'href' in retDict:
                # title
                match = re.search('>([^<]+?)<span', item)
                if match: title = match.group(1)
                else: title = ''
                # vote
                match = re.search('>([^<]+?)</span', item)
                if match: vote = match.group(1)
                else: vote = ''
                params = {'name': 'sub', 'category': self.M_DISIAJ_NAJLEPSZE, 'title': title, 'plot': ' Ocena: ' + vote, 'page': retDict['href']}
                self.addVideo( params )
    # end listsMenuDzisiajNajlepsze
    
    def listsMenuKategorieFilmow(self):
        printDBG("listsMenuKategorieFilmow start")
        data = self.getMenuData()
        if data == None:
            return
        sts, data = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('<a[^>]+?href="http://iptak.pl/kategoria/wszystkie/"[^>]*?>'), re.compile('<script>'))
        if False == sts: return
        data = data.split('</li>')
        for item in data:
            retDict = self.getPropertiesValues(['href'], item) 
            if 'href' in retDict:
                # title
                match = re.search('<h5>([^<]+?)</h5>', item)
                if match: title = match.group(1)
                else: title = ''
                params = {'name': 'sub', 'category': self.M_KATRGORIE_FILMOW, 'title': title, 'page': retDict['href']}
                self.addDir( params )
        #self.listMainBase(addMethod=self.addDir, category=self.M_KATRGORIE_FILMOW, mark1='<div id="category" style="border:none !important">', mark2='</ul>', splitMark='<li>')
    # end listsMenuKategorieFilmow
    
    def listsVideosForCategory(self, catUrl):
        printDBG("listsVideosForCategory start catUrl[%s]" % catUrl)
        sts, data = self.cm.getPage( catUrl )
        if not sts: return
        
        #next Page
        match = re.search('<a class="next page-numbers" href="([^"]+?)">', data)
        if match:
            nextPageParams = {'name': 'sub', 'category': self.M_KATRGORIE_FILMOW, 'title': 'Następna strona', 'page': match.group(1)}
        else:
            nextPageParams = None
        
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="wyszukiwanie">', '<div id="top100">')
        if not sts: return
        
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="item"', '<script', True)
        if False == sts: return

        data = data.split('<div id="item"')
        for item in data:
            retDict = self.getPropertiesValues(['href', 'title', 'src', 'alt'], item) 
            if 'href' in retDict:
                # title
                title = retDict.get('title', '')
                if title == '': title = self.cm.ph.getSearchGroups(item, '<h6>([^<]+?)</h6>')[0]
                if title == '': title = retDict.get('alt', '')

                params = {'name': 'sub', 'category': self.M_KATRGORIE_FILMOW, 'title': title, 'page': retDict['href'], 'icon': retDict.get('src', '')}
                self.addVideo( params )
        
        if nextPageParams:
            self.addDir( nextPageParams )
    # end listsVideosForCategory

    def getHostingTable(self, url):
        printDBG("getHostingTable url[%s]" % url)
        retTab = []
        sts, data = self.cm.getPage( url )
        if False == sts:
            printDBG("getHostingTable get page problem")
            return retTab
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<span id="mirrors">', '<span id="ocenHosting"')
        if False == sts:
            printDBG("getHostingTable separete uselfull HTML problem")
            return retTab
        data = data.split('<a')
        del data[0]
        for item in data:
            match = re.search("playMovie\('([^']+?)'\,'([^']+?)'\)", item)
            if match: 
                host = match.group(2)
                url = ''
                if host == 'yt':
                    hostName = 'YouTube'
                    url  = 'http://www.youtube.com/watch?v=' + match.group(1)
                elif host == 'cda':
                    hostName = 'CDA'
                    url  = 'http://ebd.cda.pl/630x430/' + match.group(1)
                else:
                    printDBG("HOST iPTAK UNKNOWN HOST [%s]" % host)
                    continue
                printDBG('getHostingTable add %s[%s]'  % (hostName, url))
                # resolve url to get direct url to video file
                retTab.extend(self.up.getVideoLinkExt( url ))
        return retTab

    def listsHistory(self):
            list = self.history.getHistoryList()
            for item in list:
                params = { 'name': 'history', 'category': self.M_WYSZUKAJ, 'title': item, 'plot': 'Szukaj: "%s"' % item}
                self.addDir(params)

    def getVideoUrl(self, url):
        retTab = []
        return retTab
        
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
        
        # reset cache due to refresh
        if name == 'main-menu' and 1 == refresh:
            self.menuData = None
 
    #MAIN MENU
        if name == None:
            self.listsMainMenu(self.SERVICE_MENU_TABLE)
    #NOWOSCI
        elif category == self.M_NOWOSCI:
            self.listsMenuNowosci()
    #POLECAMY
        elif category == self.M_POLECAMY:
            self.listsMenuPolecamy()
    #DISIAJ NAJLEPSZE
        elif category == self.M_DISIAJ_NAJLEPSZE:
            self.listsMenuDzisiajNajlepsze()
    #KATRGORIE FILMOW
        elif category == self.M_KATRGORIE_FILMOW:
            if name == 'main-menu':
                self.listsMenuKategorieFilmow()
            else:
                self.listsVideosForCategory(page)
    #WYSZUKAJ
        elif category == self.M_WYSZUKAJ:
            text = searchPattern
            self.listsVideosForCategory(self.MAINURL + "?s=" + urllib.quote_plus(text))
    #HISTORIA WYSZUKIWANIA
        elif category == self.M_HISTORIA:
            self.listsHistory()
    #WRONG WAY
        else:
            printDBG('handleService WRONG WAY')

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, iPtak(), True)

    def getLogoPath(self):  
        return RetHost(RetHost.OK, value = [ GetLogoDir('iptaklogo.png') ])

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] != 'video':
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])

        retlist = []
        urlList = self.host.getHostingTable(self.host.currList[Index]["page"])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], 0))

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

