# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.libs.crypto.hash.sha1Hash import SHA1
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigInteger, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
from datetime import timedelta
from binascii import hexlify
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
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.tvgrypl                 = ConfigSelection(default = "small", choices = [ ("large", _("large")), ("medium", _("medium")), ("small", _("small")) ])
config.plugins.iptvplayer.tvgrypl_default_quality = ConfigSelection(default = "SD", choices = [("MOB", "MOB: niska"),("SD", "SD: standardowa"),("HD", "HD: wysoka")])
config.plugins.iptvplayer.tvgrypl_use_dq          = ConfigYesNo(default = True)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Wielkość ikon"), config.plugins.iptvplayer.tvgrypl))
    optionList.append(getConfigListEntry(_("Domyślna jakość wideo:"), config.plugins.iptvplayer.tvgrypl_default_quality))
    optionList.append(getConfigListEntry(_("Używaj domyślnej jakości wideo:"), config.plugins.iptvplayer.tvgrypl_use_dq))
    return optionList
###################################################

def gettytul():
    return 'tvgry.pl'

class TvGryPL(CBaseHostClass):
    MAIN_URL = 'http://tvgry.pl/'
    SEARCH_URL = MAIN_URL + 'wyszukiwanie.asp'
    MAIN_CAT_TAB = [{'category':'newest',         'title':_('Najnowsze filmy'), 'url': MAIN_URL+'ajax/waypoint.asp', 'list_type':'0'},
                    {'category':'newest',         'title':_('Popularne filmy'), 'url': MAIN_URL+'ajax/waypoint.asp', 'list_type':'1'},
                    {'category':'films',          'title':_('Tematy filmów'),   'url': MAIN_URL+'tematy.asp'},
                    {'category':'films',          'title':_('Redakcyjne'),      'url': MAIN_URL+'temat.asp?ID=83'},
                    {'category':'films',          'title':_('RPG akcji'),       'url': MAIN_URL+'temat.asp?ID=37'},
                    {'category':'films',          'title':_('Wiedźmin'),        'url': MAIN_URL+'temat.asp?ID=78'},
                    {'category':'search',         'title':_('Search'), 'search_item':True},
                    {'category':'search_history', 'title':_('Search history')} ]
     
    
    def __init__(self):
        printDBG("TvGryPL.__init__")
        CBaseHostClass.__init__(self, {'history':'TvGryPL.tv'})     
        
    def _getFullUrl(self, url):
        if 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        return url
        
    def _decodeData(self, data):
        try: return data.decode('cp1250').encode('utf-8')
        except: return data
        
    def _getIcon(self, url):
        map  = {'small':'N300', 'medium':'N460', 'large':'N960'}
        url  = self._getFullUrl(url)
        size = self.cm.ph.getSearchGroups(url, '/(N[0-9]+?)/', 1)[0]
        if '' != size: return url.replace(size, map[config.plugins.iptvplayer.tvgrypl.value])
        return url

    def getPage(self, url, params={}, post_data=None):
        sts,data = self.cm.getPage(url, params, post_data)
        if sts: data = self._decodeData(data)
        return sts,data
        

    def listsTab(self, tab, cItem):
        printDBG("TvGryPL.listsMainMenu")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            self.addDir(params)
            
    def listFilms(self, cItem):
        printDBG("TvGryPL.listGames")
        page = cItem.get('page', 1)
        url  = cItem['url']
        post_data = cItem.get('post_data', None)
        if 1 < page:
            if '?' in url: url += '&STRONA=%d' % page
            else: url += '?STRONA=%d' % page
        
        sts, data = self.getPage(url, {}, post_data)
        if not sts: return
        
        if 'tematy.asp' in url:
            if 1 == page:
                tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div class="lista-w-kat">', '</div>', False)[1]
                tmp = tmp.split('</a>')
                if len(tmp): del tmp[-1]
                for item in tmp:
                    icon = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"', 1)[0]
                    url = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"', 1)[0]
                    params = dict(cItem)
                    params.update( {'title':self.cleanHtmlStr(item), 'url':self._getFullUrl(url), 'desc':'', 'icon':self._getIcon(icon)} )
                    self.addDir(params)

        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="moviebox">', '</footer>', False)[1]
        if 'class="pagi-next"' in data: haveNextPage = True
        else: haveNextPage = False
        
        data = data.split('<div class="half-box promo')
        if len(data): del data[0]
        for item in data:
            tmp = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)" alt="([^"]+?)"', 2)
            url = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"', 1)[0]
            params = dict(cItem)
            params.update( {'title':self.cleanHtmlStr(tmp[1]), 'url':self._getFullUrl(url), 'desc':self.cleanHtmlStr('<"'+item), 'icon':self._getIcon(tmp[0])} )
            if 'temat.asp' in url: self.addDir(params)
            else: self.addVideo(params)
                
        if haveNextPage:
            params = dict(cItem)
            params.update({'title':_("Następna strona"), 'page':page+1})
            self.addDir(params)
            
    def listNewest(self, cItem):
        printDBG("TvGryPL.listNewest")
        listType = cItem.get('list_type', '0')
        page = cItem.get('page', 1)
        url  = cItem['url']
        if '?' in url: url += '&PART=%d' % page
        else: url += '?PART=%d' % page
        HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0', 'Cookie': 'typlisty=%s' % listType} 
        sts, data = self.getPage(url, {'header':HEADER})
        if not sts: return
        pattern = '<div class="container">'
        descPattern = '<div class="description">'
        data = data
        data = data.split(pattern)
        if len(data): del data[0]
        for item in data:
            tmp = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)" alt="([^"]+?)"', 2)
            url = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"', 1)[0]
            if descPattern in item: desc = self.cleanHtmlStr( item.split(descPattern)[-1] )
            else: desc = ''
            #printDBG("[%s]\n[%s]\n" % (tmp[0], tmp[1]) )
            params = {'title':self.cleanHtmlStr(tmp[1]), 'url':self._getFullUrl(url), 'desc':desc, 'icon':self._getIcon(tmp[0])}
            self.addVideo(params)
            
        # next page check
        page += 1
        url  = cItem['url']
        if '?' in url: url += '&PART=%d' % page
        else: url += '?PART=%d' % page
        sts, data = self.getPage(url, {'header':HEADER})
        if not sts: return
        if pattern in data:
            params = dict(cItem)
            params.update({'title':_("Następna strona"), 'page':page+1})
            self.addDir(params)


    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("TvGryPL.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        searchPattern = urllib.quote_plus(searchPattern)
        post_data = {'search':searchPattern}
        params = {'name':'category', 'category':'films', 'url': TvGryPL.SEARCH_URL, 'post_data':post_data}
        self.listFilms(params)
    
    def getLinksForVideo(self, cItem):
        printDBG("TvGryPL.getLinksForVideo [%s]" % cItem)
        id = self.cm.ph.getSearchGroups(cItem['url'] + '_', 'ID=([0-9]+?)[^0-9]', 1)[0]

        urlTab = []
        for item in ['MOB', 'SD', 'HD']:
            url = 'http://tvgry.pl/video/source.asp?SC=TV&ID=%s&QL=%s' % (id, item[:2])
            sts,data = self.getPage(url)
            if not sts: continue
            url = self.cm.ph.getSearchGroups(data, 'file>(http[^<]+?)<', 1)[0]
            if '' != url: urlTab.append({'name':item, 'url':url, 'q':item})
            
        if 1 < len(urlTab):
            map = {'MOB':0, 'SD':1, 'HD':2}
            oneLink = CSelOneLink(urlTab, lambda x: map[x['q']], map[config.plugins.iptvplayer.tvgrypl_default_quality.value])
            if config.plugins.iptvplayer.tvgrypl_use_dq.value: urlTab = oneLink.getOneLink()
            else: urlTab = oneLink.getSortedLinks()
        return urlTab
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('TvGryPL.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "TvGryPL.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = [] 

        if None == name:
            self.listsTab(TvGryPL.MAIN_CAT_TAB, {'name':'category'})
    #FILMS
        elif 'films' == category:
            self.listFilms(self.currItem)
        elif 'newest' == category:
            self.listNewest(self.currItem)
    #WYSZUKAJ
        elif category in ["search", "search_next_page"]:
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category'}) 
            self.listSearchResult(cItem, searchPattern, searchType)
    #HISTORIA WYSZUKIWANIA
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, TvGryPL(), True)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('tvgrypllogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] not in ['audio', 'video']:
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])

        retlist = []
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            need_resolve = 0
            name = self.host.cleanHtmlStr( item["name"] )
            url  = item["url"]
            retlist.append(CUrlItem(name, url, need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo

    def convertList(self, cList):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        
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
                
            title       =  self.host.cleanHtmlStr( cItem.get('title', '') )
            description =  self.host.cleanHtmlStr( cItem.get('desc', '') )
            icon        =  self.host.cleanHtmlStr( cItem.get('icon', '') )
            
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
