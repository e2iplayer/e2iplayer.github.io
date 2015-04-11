# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CDisplayListItem, RetHost, CUrlItem, CBaseHostClass
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, CSearchHistoryHelper, GetLogoDir, printExc
import Plugins.Extensions.IPTVPlayer.libs.pCommon as pCommon
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
from base64 import b64decode
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, fileExists
###################################################

###################################################
# Config options for HOST
###################################################
# None

def GetConfigList():
    return []
###################################################

def gettytul():
    return 'SuperFilm'

class SuperFilm(CBaseHostClass):
    MAINURL = 'http://superfilm.pl'
    # movies, series
    SEARCH_URL = MAINURL + '/szukaj?filters=%2Btype%3A'
    MAIN_CAT_TAB = [{'category':'films',          'title':_('Filmy'),              'url': MAINURL + '/filmy'},
                    {'category':'films',          'title':_('Filmy dokumentalne'), 'url': MAINURL + '/Dokumentalny'},
                    {'category':'series',         'title':_('Seriale'),            'url': MAINURL + '/seriale'},
                    {'category':'mixed',          'title':_('Dla dzieci'),         'url': MAINURL + '/Dla-dzieci'},
                    {'category':'top100',         'title':_('Top 100'),            'url': MAINURL + '/filmy/top'},
                    {'category':'search',         'title':_('Search'),             'search_item':True},
                    {'category':'search_history', 'title':_('Search history')} ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'SuperFilm', 'cookie':'superfilm.cookie'})
    
    def getPropertiesValues(self, properties, data):
        retDict = dict()
        for prop in properties:
            match = re.search(prop + '="([^"]+?)"', data)
            if match: 
                retDict[prop] = match.group(1)
        return retDict

    def listsTab(self, tab, cItem):
        printDBG("SuperFilm.listsMainMenu")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            self.addDir(params)

    def listsCategoriesMenu(self, cItem, category):
        printDBG("SuperFilm.listsCategoriesMenu")
        sts, data = self.cm.getPage( cItem['url'] )
        if False == sts: return
            
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<fieldset><legend class="uc">Kategorie:</legend>', '</ul>')
        if not sts: return
        match = re.compile('<li data-filter="[^"]+?" data-change="active invert"><a class="blur" href="([^"]+?)">([^<]+?)</a> \(([0-9]+?)\)<').findall(data)
        if len(match) > 0:
            for i in range(len(match)):
                params = {'name': 'category', 'title': match[i][1]+' ('+match[i][2]+')', 'category': category, 'url': match[i][0]}
                self.addDir(params)

    def getCatTable(self, cItem, category='', mixed=False):
        printDBG("SuperFilm.getCatTable category[%s]" % category)
        page = cItem.get('page', '1')
        url = cItem['url']
        if '?' not in url: url += '?'
        else: url += '&'
        if page != '1': url += 'page=' + page
        sts, data = self.cm.getPage( url )
        if False == sts: return
        
        if -1 != data.find('Następna &gt;'): nextPage = True
        else: nextPage = False
            
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="media">', '<footer id="footer">')
        if not sts: return
        data = data.split('<div class="media">')
        if len(data): del data[0]
        for item in data:
            # url & title
            match = self.cm.ph.getSearchGroups(item, '<a class="none-decoration" href="([^"]+?)">([^<]+?)</a>', 2)
            url = match[0]
            title = match[1]
            if '' == url: continue
            # img
            icon = self.cm.ph.getSearchGroups(item, '<img class="cover" src="([^"]+?)"')[0]
            if '' != icon: icon = self.MAINURL + icon.replace("57x0", "157x0")
            params = { 'title': title, 'url': url, 'icon': icon, 'desc': self.cleanHtmlStr(item)}
            cat = category
            if mixed and '/serial-' not in url: cat = ''
            if '' == cat: self.addVideo(params)
            else:
                params['name'] = 'seasons'
                params['category'] = cat
                self.addDir(params)
        #pagination
        if nextPage:
            params = {'name': 'category', 'category': cItem['category'], 'title': 'Następna strona', 'url': cItem['url'], 'page': str(int(page) + 1)}
            self.addDir(params)
            
    def getSerialEpisods(self, cItem):
        printDBG("SuperFilm.getSerialEpisods")
        sts, data = self.cm.getPage( cItem['url'] )
        if False == sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="accordion_seasons"', '<i class="icon-comments">')[1]
        
        data = data.split('<ul class="nav nav-list">')
        if len(data): del data[0]
        for item in data:
            data2 = item.split('</li>')
            if len(data2): del data2[-1]
            for item2 in data2:
                title = self.cleanHtmlStr(item2) + ('(%s)' % self.cm.ph.getSearchGroups(item2, 'itemprop="episodeNumber" content="([^"]+?)"')[0])
                url = self.cm.ph.getSearchGroups(item2, 'href="(http[^"]+?)"')[0]
                params = { 'title': title, 'url': url, 'icon': cItem['icon']}
                self.addVideo(params)

    def getHostingTable(self,url):
        printDBG("SuperFilm.getHostingTable")
        sts, data = self.cm.getPage( url )
        if False == sts: return []
        data = re.compile('type="video/mp4" src="(http[^"]+?mp4)"').findall(data)
        urlTab = []
        idx = 1
        for url in data:
            if url.startswith('http') and 'blank.mp4' not in url:
                urlTab.append({'name' : 'superfilm.pl [%d]' % idx, 'url' : url } )
                idx += 1
        return urlTab

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG("SuperFilm.handleService")
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "SuperFilm.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = [] 

        if None == name:
            self.listsTab(SuperFilm.MAIN_CAT_TAB, {'name':'category'})
    #FILMY
        elif category == "films":
            self.getCatTable(self.currItem)
    #SERIALE
        elif category == "series":
            self.listsCategoriesMenu(self.currItem, 'list_serials')
        elif category == "list_serials":
            self.getCatTable(self.currItem, 'list_episodes')
        elif category == "list_episodes":
            self.getSerialEpisods(self.currItem)
    #DLA DZIECI
        elif category == "mixed":
            self.getCatTable(self.currItem, 'list_episodes', True)
    #TOP 100
        elif category == "top100":
            self.getCatTable(self.currItem)

    #WYSZUKAJ
        elif category in ["search", "search_next_page"]:
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category'}) 
            pattern = urllib.quote_plus(searchPattern)
            if 'filmy' == searchType:
                cItem['url'] = self.SEARCH_URL + 'movies' + '&q=' + pattern
                self.getCatTable(cItem)
            elif 'seriale' == searchType:
                cItem['url'] = self.SEARCH_URL + 'series' + '&q=' + pattern
                self.getCatTable(cItem, 'list_episodes')
    #HISTORIA WYSZUKIWANIA
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        else: printExc()
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, SuperFilm(), True)

    def getLogoPath(self):  
        return RetHost(RetHost.OK, value = [ GetLogoDir('/superfilm.png') ])

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] != 'video':
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])

        retlist = []
        urlList = self.host.getHostingTable(self.host.currList[Index]["url"])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], 0))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo

    def convertList(self, cList):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        searchTypesOptions.append(("Seriale", "seriale"))
        searchTypesOptions.append(("Filmy", "filmy"))
    
        for cItem in cList:
            hostLinks = []
            type = CDisplayListItem.TYPE_UNKNOWN
            possibleTypesOfSearch = None

            if 'category' == cItem['type']:
                if cItem.get('search_item', False):
                    type = CDisplayListItem.TYPE_SEARCH
                    possibleTypesOfSearch = searchTypesOptions
                else:
                    type = CDisplayListItem.TYPE_CATEGORY
            elif cItem['type'] == 'video':
                type = CDisplayListItem.TYPE_VIDEO
            elif 'more' == cItem['type']:
                type = CDisplayListItem.TYPE_MORE
            elif 'audio' == cItem['type']:
                type = CDisplayListItem.TYPE_AUDIO
                
            if type in [CDisplayListItem.TYPE_AUDIO, CDisplayListItem.TYPE_VIDEO]:
                url = cItem.get('url', '')
                if '' != url:
                    hostLinks.append(CUrlItem("Link", url, 1))
                
            title       =  cItem.get('title', '')
            description =  cItem.get('desc', '')
            icon        =  cItem.get('icon', '')
            
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

    def getSearchItemInx(self):
        try:
            list = self.host.getCurrList()
            for i in range( len(list) ):
                if list[i]['category'] == 'search':
                    return i
        except:
            printDBG('getSearchItemInx EXCEPTION')
            return -1

    def setSearchPattern(self):
        try:
            list = self.host.getCurrList()
            if 'history' == list[self.currIndex]['name']:
                pattern = list[self.currIndex]['title']
                search_type = list[self.currIndex]['search_type']
                self.host.history.addHistoryItem( pattern, search_type)
                self.searchPattern = pattern
                self.searchType = search_type
        except:
            printDBG('setSearchPattern EXCEPTION')
            self.searchPattern = ''
            self.searchType = ''
        return
