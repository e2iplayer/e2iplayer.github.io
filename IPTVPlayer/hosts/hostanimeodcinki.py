# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
import re
import urllib
import time
import random
try:    import simplejson as json
except: import json


###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################

###################################################

###################################################
# Config options for HOST
###################################################
def GetConfigList():
    optionList = []
    return optionList
###################################################

def gettytul():
    return 'Anime-Odcinki.pl'

class AnimeOdcinki(CBaseHostClass):
    MAINURL  = 'http://www.anime-odcinki.pl/'
    SEARCH_URL = MAINURL + '/search/node/'
    MAIN_CAT_TAB = [{ 'category':'list_letters',          'title':'Lista anime',           'url':MAINURL+'lista-anime'  },
                    { 'category':'list_letters',          'title':'Lista filmów',          'url':MAINURL+'lista-filmow' },
                    { 'category':'list_emiotwane',        'title':'Anime Emitowane',       'url':MAINURL                },
                    { 'category':'list_new_episodes',     'title':'Nowe odcinki emitowane','url':MAINURL                },
                    { 'category':'list_new_added',        'title':'Ostatnio dodane odcinki z poprzednich sezonów',  'url':MAINURL },
                    { 'category':'Wyszukaj',              'title':'Wyszukaj'             },
                    { 'category':'Historia wyszukiwania', 'title':'Historia wyszukiwania'} ]
                    
    
    def __init__(self):
        printDBG("AnimeOdcinki.__init__")
        CBaseHostClass.__init__(self, {'history':'AnimeOdcinki.com'})
            
    def _checkNexPage(self, data):
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="pagenav">', '</ul>', False)[1]
        if 'Go to next page' in data and '<a href=' in data:
            return True
        else:
            return False
            
    def _resolveUrl(self, url, currPath=''):
        if not url.startswith('http') and '' != url:
            if '' == currPath:
                return AnimeOdcinki.MAINURL + url
            else:
                return currPath + url
        else:
            return url
            
    def listsTab(self, tab, cItem):
        printDBG("AnimeOdcinki.listsMainMenu")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            self.addDir(params)
            
    def _listBase(self, cItem, category, m1, m2, sp):
        url = self._resolveUrl(cItem['url'])
        sts, data = self.cm.getPage(url)
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, m2, False)[1]
        data = data.split(sp)
        if len(data): del data[-1]
        for item in data:
            params = dict(cItem)
            url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"', 1)[0]
            title = self.cleanHtmlStr(item)
            icon  = self._resolveUrl( self.cm.ph.getSearchGroups(item, """<img src=['"]([^"^']+?\.jpg[^"^']*?)['"]""")[0] )
            if len(title) and '|' == title[0]: title = title[1:]
            params.update({'title':title, 'url':url, 'category':category, 'icon':icon})
            if '/film/' in url or category == 'video': self.addVideo(params)
            else: self.addDir(params)
                
    def listsLetters(self, cItem, category):
        printDBG('AnimeOdcinki.listsLetters start')
        self._listBase(cItem, category, '<div class="view-content">', '</div>', '</span>')
            
    def listsAnimes(self, cItem, category):
        printDBG('AnimeOdcinki.listsAnimes start')
        self._listBase(cItem, category, '<tbody>', '</tbody>', '</tr>')
        
    def listEmitowane(self, cItem, category):
        printDBG('AnimeOdcinki.listEmitowane start')
        self._listBase(cItem, category, 'Anime Emitowane', '</ul>', '</li>')
        
    def listNewEpisodes(self, cItem):
        printDBG('AnimeOdcinki.listNewEpisodes start')
        self._listBase(cItem, 'video', '<ul class="jcarousel jcarousel-view--new-emitowane--block jcarousel-dom-1 jcarousel-skin-default">', '</ul>', '</div>')

    def listNewAdded(self, cItem):
        printDBG('AnimeOdcinki.listNewAdded start')
        self._listBase(cItem, 'video', '<ul class="jcarousel jcarousel-view--nowe-odcinki--block jcarousel-dom-2 jcarousel-skin-default">', '</ul>', '</div>')            
                
    def listEpisodes(self, cItem):
        printDBG('AnimeOdcinki.listEpisodes start')
        page = cItem.get('page', 0)
        url  = self._resolveUrl(cItem['url']) + ('?page=%d' % page)
        sts, data = self.cm.getPage(url)
        if not sts: return
        desc = self.cm.ph.getDataBeetwenMarkers(data, '<div class="content">', "</section>", False)[1]
        icon = self._resolveUrl( self.cm.ph.getSearchGroups(desc, """<img src=['"]([^"^']+?\.jpg[^"^']*?)['"]""")[0] )
        desc = self.cleanHtmlStr(desc)
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="view-content">', '</section>', False)[1]
        nextPage = False
        if '<ul class="pagination">' in data:
            if '"Przejdź do następnej strony"' in data: nextPage = True
            data = data[:data.find('<ul class="pagination">')] 
        '''
        trailer = self.cm.ph.getSearchGroups(data, """href=['"](http[^"^']+?youtu[^"^']+?)['"]""")[0]
        if '' != trailer:
            params = dict(cItem)
            params.update({'title':_('Zwiastun'), 'url':trailer, 'desc':desc, 'icon':icon})
            self.addVideo(params)
        '''
        data = data.split('<div class="views-row views-row')
        for item in data:
            idx = item.find('>')
            if 0 > idx: continue
            item = item[idx+1:]
            title = self.cleanHtmlStr(item)
            url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"', 1)[0]
            params= {'title':title, 'url':url, 'desc':desc, 'icon':icon}
            self.addVideo(params)
        
        if nextPage:
            params = dict(cItem)
            params.update({'title':'Następna strona', 'page':page+1})
            self.addDir(params)
                    
    def listItems(self, cItem):
        printDBG('AnimeOdcinki.listItems start')     
        page     = cItem.get('page', 0)
        url = self._resolveUrl(cItem['url']) + '?rowstart=%d' % (page * 20) 
        currPath = url[:url.rfind('/')] + '/'
        sts, data = self.cm.getPage(url)
        if sts:
            try: pagesNum = int(self.cm.ph.getSearchGroups(data, "Strona[^;]+?;([0-9]+?):")[0])-1
            except: pagesNum = 0 
            data = self.cm.ph.getDataBeetwenMarkers(data, '</tr></table><table cellpadding', "class='main-footer-top", True)[1]
            data = data.split('</tr></table>')
            if len(data): del data[0]
            if len(data): del data[-1]
            for item in data:
                params = dict(cItem)
                tmp = self.cm.ph.getSearchGroups(item, """<a href=["']([^'^"]+?)["']>([^<]+?)</a>""", 2)
                if '' != tmp[0] and '' != tmp[1]:                
                    icon =  self._resolveUrl(self.cm.ph.getSearchGroups(item, """src=['"]([^"^']+?)['"]""")[0], currPath)
                    desc = self.cleanHtmlStr(item)
                    params.update({'title':tmp[1], 'url':self._resolveUrl(tmp[0], currPath), 'icon':icon, 'desc':desc})
                    self.addVideo(params)
            if pagesNum > page:
                params = dict(cItem)
                params.update({'title':'Następna strona', 'page':page+1})
                self.addDir(params)
    
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("AnimeOdcinki.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        url = AnimeOdcinki.SEARCH_URL + urllib.quote_plus(searchPattern)
        sts, data = self.cm.getPage(url)
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ol class="search-results node-results">', '</ol>')[1]
        data = data.split("</li>")
        if len(data): del data[-1]
        for item in data:
            tmp   = self.cm.ph.getSearchGroups(item, '<a href="([^"]+?)"[^>]*?>([^<]+?)<', 2)
            url   = tmp[0]
            title = self.cleanHtmlStr(tmp[1])
            if '' != url and '' != title:
                desc = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<div class="search-snippet-info">', '</div>')[1] )
                icon = ''
                params = {'name':'category', 'title':title, 'url':self._resolveUrl(url), 'icon':icon, 'desc':desc}
                if re.search('/anime/[^/]+?$', url):
                    params['category'] = 'episodes_list'
                    self.addDir(params)
                else: self.addVideo(params)
    
    def getLinksForVideo(self, cItem):
        printDBG("AnimeOdcinki.getLinksForVideo [%s]" % cItem['url'])
        if len(cItem.get('url_cache', [])):
            return cItem['url_cache']
        urlTab = []
        url = self._resolveUrl(cItem['url'])
        if 'anime-odcinki.pl' in url:       
            sts, data = self.cm.getPage(url)
            if sts:
                data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="content">', "<ul")[1]
                printDBG(data)
                players = re.compile(""">(http[^<]+?)<""").findall(data)
                for player in players:
                    playerUrl = self.cleanHtmlStr( player )
                    if '' != playerUrl:
                        tmpTab = self.up.getVideoLinkExt(playerUrl)
                        urlTab.extend(tmpTab)
        else: urlTab = self.up.getVideoLinkExt(url)
        if len(urlTab): cItem['url_cache'] = urlTab
        return urlTab
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('AnimeOdcinki.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "AnimeOdcinki.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = []
        
        if None == name:
            self.listsTab(AnimeOdcinki.MAIN_CAT_TAB, {'name':'category'})
    #LIST LETTERS
        elif 'list_letters' == category:
            self.listsLetters(self.currItem, 'anime_list')
    #FILMS LETTERS
        elif 'anime_list' == category:
            self.listsAnimes(self.currItem, 'episodes_list')
    #LIST EPISODES
        elif 'episodes_list' == category:
            self.listEpisodes(self.currItem)
    #LIST ITEMS
        elif 'list_items' == category:
            self.listItems(self.currItem)
    #LIST EMITOWANE
        elif 'list_emiotwane' == category:
            self.listEmitowane(self.currItem, 'episodes_list')
    #LIST NEW EPISODES
        elif 'list_new_episodes' == category:
            self.listNewEpisodes(self.currItem)
    #LIST NEW ADDED 
        elif 'list_new_added' == category:
            self.listNewAdded(self.currItem)
    #WYSZUKAJ
        elif category in ["Wyszukaj", "search_next_page"]:
            self.listSearchResult(self.currItem, searchPattern, searchType)
    #HISTORIA WYSZUKIWANIA
        elif category == "Historia wyszukiwania":
            self.listsHistory()
        else:
            printExc()

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, AnimeOdcinki(), True)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('animeodcinkilogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] != 'video':
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])

        retlist = []
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo

    def convertList(self, cList):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        #searchTypesOptions.append(("Items", "items"))
        #searchTypesOptions.append(("Channel", "channel"))
    
        for cItem in cList:
            hostLinks = []
            type = CDisplayListItem.TYPE_UNKNOWN
            possibleTypesOfSearch = None

            if cItem['type'] == 'category':
                if cItem['title'] == 'Wyszukaj':
                    type = CDisplayListItem.TYPE_SEARCH
                    possibleTypesOfSearch = searchTypesOptions
                else:
                    type = CDisplayListItem.TYPE_CATEGORY
            elif cItem['type'] == 'video':
                type = CDisplayListItem.TYPE_VIDEO
                url = cItem.get('url', '')
                if '' != url:
                    hostLinks.append(CUrlItem("Link", url, 1))
                
            title       =  cItem.get('title', '')
            description =  clean_html(cItem.get('desc', '')) + clean_html(cItem.get('plot', ''))
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
                search_type = list[self.currIndex]['search_type']
                self.host.history.addHistoryItem( pattern, search_type)
                self.searchPattern = pattern
                self.searchType = search_type
        except:
            printDBG('setSearchPattern EXCEPTION')
            self.searchPattern = ''
            self.searchType = ''
        return
