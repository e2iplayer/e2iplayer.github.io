# -*- coding: utf-8 -*-
# based on plugin.video.polishtv.live.r670

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem
import Plugins.Extensions.IPTVPlayer.libs.pCommon as pCommon
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, CSearchHistoryHelper, CSelOneLink, GetLogoDir

###################################################
# FOREIGN import
###################################################
import re, urllib
from Components.config import config, ConfigSelection, ConfigYesNo, getConfigListEntry
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.wrzutaDefaultformat = ConfigSelection(default = "360", choices = [("0", "format: najgorszy"), ("240", "format: 240p"), ("360", "format: 360p"),  ("480", "format: 480p"), ("720", "format: 720"), ("9999", "format: najlepszy")])
config.plugins.iptvplayer.wrzutaUseDF = ConfigYesNo(default = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("Domyślny format video:", config.plugins.iptvplayer.wrzutaDefaultformat))
    optionList.append(getConfigListEntry("Używaj domyślnego format video:", config.plugins.iptvplayer.wrzutaUseDF))
    return optionList
###################################################


def gettytul():
    return 'Wrzuta Player'
    
class Wrzuta(CBaseHostClass):
    SERVICE = 'wrzuta'
    MAINURL = 'http://www.wrzuta.pl'
    TOPURL = MAINURL + '/filmy/popularne/'
    NEWURL = MAINURL + '/filmy/najnowsze/'
    CHANURL= MAINURL + '/kanaly'
    CHANLIST = '/wrzucone/katalogi/nazwa_rosnaca/'

    SERVICE_MENU_TABLE =  {
        1: "Najpopularniejsze",
        2: "Najnowsze",
        3: "Kanały",
        6: "Historia Wyszukiwania",
        5: "Wyszukaj",
    }

    CATEGORIES = {
        '': 'Wszystkie',
        'muzyka': 'Muzyka',
        'filmy_trailery': 'Filmy & Trailery',
        'seriale_animacje': 'Seriale & Animacje',
        'sport': 'Sport',
        'motoryzacja': 'Motoryzacja',
        'humor_rozrywka': 'Humor & Rozrywka',
        'zwierzaki': 'Zwierzaki',
        'gry_tech': 'Gry & Tech',
        'erotyka': 'Erotyka'
    }
    def __init__(self):
        printDBG('WRZUTA.__init__')
        CBaseHostClass.__init__(self, {'history':'wrzuta.pl'})
    
    def setTable(self):
        printDBG('WRZUTA.setTable') 
        return self.SERVICE_MENU_TABLE

    def listsMainMenu(self, table):
        printDBG('WRZUTA.listsMainMenu') 
        for num, val in table.items():
            params = {'name': 'main-menu','category': val, 'title': val, 'icon': ''}
            self.addDir(params)

    def listsCategories(self, url, category):
        printDBG('WRZUTA.listsCategories') 
        for num, val in self.CATEGORIES.items():
            params = {'name': category, 'page': url+num, 'title': val, 'icon': ''}
            self.addDir(params)

    def listsChannels(self, url, page, category):
        printDBG('WRZUTA.listsChannels') 
        
        sts, data = self.cm.getPage(url+'/'+page)
        if not sts: return
        
        r = re.compile('class="big-avatar">.+?<img src="(.+?)".+?<a href="(.+?)" class="channel-name">(.+?)</a>', re.DOTALL).findall(data)
        if len(r)>0:
            for i in range(len(r)):
                params = {'name': 'chanvideo', 'title': r[i][2], 'page': r[i][1], 'icon': r[i][0]}
                self.addDir(params)
        r2 = re.compile('<a class="paging-next" rel="(.+?)"').findall(data)
        if len(r2)>0:
            params = {'name': 'nextpage', 'category': category, 'title': 'Następna strona', 'page': r2[0], 'icon': ''}
            self.addDir(params)

    def listsChanDirs(self, url, page): #img maybe?
        printDBG('WRZUTA.listsChanDirs')
        sts, data = self.cm.getPage(url+self.CHANLIST+page)
        if not sts: return 
        r = re.compile('<a href="(.+?)" class="file-name">(.+?)</a>').findall(data)
        printDBG("tst2 "+str(r))
        if len(r)>0:
            params = {'name': 'chandirvideo', 'title': 'Ostatnio dodane', 'page': url+'/materialy/filmy', 'icon': ''}
            self.addDir(params)
            for i in range(len(r)):
                params = {'name': 'chandirvideo', 'title': r[i][1], 'page': r[i][0], 'icon': ''}
                self.addDir(params)
        r2 = re.compile('<a class="paging-next" rel="(.+?)"').findall(data)
        if len(r2)>0:
            params = {'name': 'chanvideo', 'category': r2[0], 'title': 'Następna strona', 'page': url, 'icon': ''}
            self.addDir(params)

    def listsVideo(self,url, name, category): #Duration #mod & join next
        printDBG('WRZUTA.listsVideo')
        if category != '': nUrl = url+'/'+category
        else: nUrl = url

        sts, data = self.cm.getPage(nUrl)
        if not sts: return
        
        r2 = re.search('<a class="paging-next" rel="([^"]+?)"', data)
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="content"', '<div id="right"', withMarkers = False)
        if not sts:
            printDBG("listsVideo no data beetween markers")
            data = ''
        
        r = re.compile('<img src="([^"]+?)".+? (?:height="81" width="144"|width="144" height="81").+?class="(?:box-entry-duration|mini-time|file-time)">(.+?)<.+?<div class="(?:file-info|info-inside|file-detail)">.+?<a href="(.+?)".+?>(.+?)</a>', re.DOTALL).findall(data)
        if len(r)>0:
            for i in range(len(r)):
                params = {'title': self.cm.html_entity_decode(r[i][3].strip()), 'page': r[i][2], 'icon': r[i][0]}
                self.addVideo(params)
        if r2:
            params = {'name': name, 'category': r2.group(1), 'title': 'Następna strona', 'page': url, 'icon': ''}
            self.addDir(params)

    def listsChanVideo(self, url, name, category): #Duration
        printDBG('WRZUTA.listsChanVideo')
        sts, data = self.cm.getPage(url+'/'+category)
        if not sts: return 
        r = re.compile('<img (?:width="184" height="104"|width="144" height="81") src="(.+?)".+?<div class="file-time">(.+?)</div>.+?<a class="file-name" href="(.+?)">(.+?)</a>', re.DOTALL).findall(data)
        if len(r)>0:
            for i in range(len(r)):
                params = {'title': self.cm.html_entity_decode(r[i][3].strip()), 'page': r[i][2], 'icon': r[i][0]}
                self.addVideo(params)
        r2 = re.compile('<a class="paging-next" rel="(.+?)"').findall(data)
        if len(r2)>0:
            params = {'name': name, 'category': r2[0], 'title': 'Następna strona', 'page': url, 'icon': ''}
            self.addDir(params)

    def getVideoLinks(self,url):
        printDBG('WRZUTA.getVideoLinks')
        nurl = url.split("/")
        url = 'http://'+ nurl[2] + '/u/' + nurl[4]
        retList = []
        sts, data = self.cm.getPage(url)
        if not sts: return retList
        match = re.compile('var _src = {(.+?)};', re.DOTALL).findall(data)
        if len(match) > 0:
            match2 = re.compile("\t'(.+?)': (.+?),?\n").findall(match[0])
            for num, item in match2[::-1]:
                if item != '""':
                    parts = re.compile('"(.*?)"').findall(item)
                    linkVideo = ''.join(parts)
                    if linkVideo.find("http://c.wrzuta.pl/wht") == -1:
                        retList.append({'name': num, 'url': linkVideo})
                        
        maxRes = int(config.plugins.iptvplayer.wrzutaDefaultformat.value) * 1.1
        def __getLinkQuality( itemLink ):
            return int(itemLink['name'])
        obj = CSelOneLink(retList, __getLinkQuality, maxRes)
        if config.plugins.iptvplayer.wrzutaUseDF.value:
            retList = obj.getOneLink()
        else: retList = obj.getSortedLinks()
        return retList

    def getFavouriteData(self, cItem):
        return cItem['page']
        
    def getLinksForFavourite(self, fav_data):
        return self.getVideoLinks(fav_data)
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG( "WRZUTA.handleService %d" % refresh)
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        
        name = self.currItem.get( "name", None )
        title = self.currItem.get( "title", '')
        category = self.currItem.get( "category", '')
        page = self.currItem.get( "page", '')
        icon = self.currItem.get( "icon", '')
        link = self.currItem.get( "url", '')
        action = self.currItem.get( "action", '')
        path = self.currItem.get( "path", '')

        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| [%s] " % name )
        self.currList = []

        if category == None: category = ''
        if page == None: page = ''

    #MAIN MENU
        if name == None:
            self.listsMainMenu(self.SERVICE_MENU_TABLE)
    #NAJPOPULARNIEJSZE
        elif category == self.setTable()[1]:
            self.listsCategories(self.TOPURL, 'topvideo')
    #NAJNOWSZE
        elif category == self.setTable()[2]:
            self.listsCategories(self.NEWURL, 'newvideo')
    #KANAŁY
        elif category == self.setTable()[3]:
            self.listsChannels(self.CHANURL, page, category)
    #WYSZUKAJ
        elif category == self.setTable()[5]:
            url = self.MAINURL + '/szukaj/filmow/' + urllib.quote_plus(searchPattern)
            self.listsVideo(url, 'servideo', '')
    #HISTORIA WYSZUKIWANIA
        elif category == self.setTable()[6]:
            self.listsHistory()
    #LISTA FILMÓW
        elif name == 'topvideo' or name == 'newvideo' or name == 'servideo':
            self.listsVideo(page, name, category)

        elif name == 'chanvideo':
            self.listsChanDirs(page, category)

        elif name == 'chandirvideo':
            self.listsChanVideo(page, name, category)
    
class IPTVHost(CHostBase):
    def __init__(self):
        CHostBase.__init__(self, Wrzuta(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])
        
    def getLogoPath(self):  
        return RetHost(RetHost.OK, value = [ GetLogoDir('wrzutalogo.png') ])
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): RetHost(retCode, value=retlist)
        urlList = self.host.getVideoLinks(self.host.currList[Index]["page"])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], 0))
        return RetHost(RetHost.OK, value = retlist)

    def converItem(self, cItem):
        hostList = []
        hostLinks = []
        type = CDisplayListItem.TYPE_UNKNOWN
        
        url = ''
        desc = ''
        if cItem['type'] in ['category']:
            if cItem.get('title', '')  == 'Wyszukaj':
                type = CDisplayListItem.TYPE_SEARCH
            else:
                type = CDisplayListItem.TYPE_CATEGORY
        elif cItem['type']  == 'video':
            type = CDisplayListItem.TYPE_VIDEO
            url = cItem.get('page', '')
            hostLinks.append(CUrlItem('', url, 0))
            
        name = cItem.get('title', '')
        icon = cItem.get('icon', '')
        desc = ' ' + cItem.get('page', '')

        return CDisplayListItem(name = name,
                                description = desc,
                                type = type,
                                urlItems = hostLinks,
                                urlSeparateRequest = 1,
                                iconimage = icon,
                                possibleTypesOfSearch = [])
        
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
        
