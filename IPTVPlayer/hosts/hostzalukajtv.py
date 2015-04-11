# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
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
config.plugins.iptvplayer.zalukajtv_filmssort = ConfigSelection(default = "ostatnio-dodane", choices = [("ostatnio-dodane", "ostatnio dodane"), ("ostatnio-ogladane", "ostatnio oglądane"), ("odslon", "odsłon"), ("ulubione", "ulubione"), ("oceny", "oceny"), ("mobilne", "mobilne")]) 
config.plugins.iptvplayer.zalukajtvPREMIUM   = ConfigYesNo(default = False)
config.plugins.iptvplayer.zalukajtv_login     = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.zalukajtv_password  = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("Sortuj filmy: ", config.plugins.iptvplayer.zalukajtv_filmssort))
    optionList.append(getConfigListEntry("Zaloguj:", config.plugins.iptvplayer.zalukajtvPREMIUM))
    if config.plugins.iptvplayer.zalukajtvPREMIUM.value:
        optionList.append(getConfigListEntry("  " + _("login") + ":", config.plugins.iptvplayer.zalukajtv_login))
        optionList.append(getConfigListEntry("  " + _("hasło") + ":", config.plugins.iptvplayer.zalukajtv_password))
    return optionList
###################################################

def gettytul():
    return 'ZalukajTv'

class ZalukajTv(CBaseHostClass):
    HOST = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.18) Gecko/20110621 Mandriva Linux/1.9.2.18-0.1mdv2010.2 (2010.2) Firefox/3.6.18'
    HEADER = {'User-Agent': HOST, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
    AJAX_HEADER = dict(HEADER)
    AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Cache-Control': 'no-cache'} )
    
    MAINURL   = 'http://zalukaj.tv'
    FILMS_URL = MAINURL + '/gatunek,%d/%s,%s,strona-%d'
    SEARCH_URL= MAINURL + '/szukaj'
    LOGIN_URL = MAINURL + '/account.php'
    MAIN_CAT_TAB = [{'category':'films_sub_menu', 'title':"Filmy",   'url': ''},
                    {'category':'series_sub_menu','title':"Seriale", 'url': MAINURL},
                    {'category':'search',         'title':"Szukaj filmu", 'search_item':True},
                    {'category':'search_history', 'title':_('Search history')} ]
                    
    FILMS_SUB_MENU = [{ 'category':'films_category', 'title':'Kategorie',        'url':MAINURL },
                      { 'category':'films_list',     'title':'Ostatnio oglądane', 'url':MAINURL + '/cache/lastseen.html' },
                      { 'category':'films_list',     'title':'Ostation dodane',   'url':MAINURL + '/cache/lastadded.html'},
                      { 'category':'films_popular',  'title':'Najpopularniejsze', 'url':'' } ]
                    
    FILMS_POPULAR = [{ 'category':'films_list', 'title':'Wczoraj',        'url':MAINURL + '/cache/wyswietlenia-wczoraj.html' },
                     { 'category':'films_list', 'title':'Ostatnie 7 dni', 'url':MAINURL + '/cache/wyswietlenia-tydzien.html' },
                     { 'category':'films_list', 'title':'W tym miesiącu', 'url':MAINURL + '/cache/wyswietlenia-miesiac.html'} ]
                     
    SERIES_SUB_MENU = [{ 'category':'series_list',   'title':'Lista',     'url':MAINURL },
                       { 'category':'series_updated','title':'Ostatnio zaktualizowane', 'url':MAINURL + '/seriale' } ]
                    
    LANGS_TAB = [{ 'title':'Wszystkie',     'lang':'wszystkie'      },
                 { 'title':'Z lektorem',    'lang':'tlumaczone'     },
                 { 'title':'Napisy pl',     'lang':'napisy-pl'      },
                 { 'title':'Nietłumaczone', 'lang':'nie-tlumaczone' } ]
     
    
    def __init__(self):
        printDBG("ZalukajTv.__init__")
        CBaseHostClass.__init__(self, {'history':'ZalukajTv', 'cookie':'zalukajtv.cookie'})
        self.loggedIn = None  
    
    def _getPage(self, url, http_params_base={}, params=None, loggedIn=None):
        if None == loggedIn: loggedIn=self.loggedIn
        HEADER = ZalukajTv.HEADER
        if loggedIn: http_params = {'header': HEADER, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE}
        else: http_params = {'header': HEADER}
        http_params.update(http_params_base)
        return self.cm.getPage(url, http_params, params)
        
    def _getFullUrl(self, url):
        if 0 < len(url) and not url.startswith('http'): url =  self.MAINURL + url
        return url
            
    def _listLeftTable(self, cItem, category, m1, m2, sp):
        printDBG("ZalukajTv.listLeftGrid")
        sts, data = self._getPage(cItem['url'])
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, m1, m2, False)[1]
        data = data.split(sp)
        if len(data): del data[-1]
        for item in data:
            params = dict(cItem)
            url    = self._getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"', 1)[0] )
            if ZalukajTv.MAINURL not in url: continue
            params.update({'category':category, 'title':self.cleanHtmlStr( item ), 'url':url})
            self.addDir(params)
        
    def listFilmsCategories(self, cItem, category):
        printDBG("ZalukajTv.listFilmsCategories")
        self._listLeftTable(cItem, category, '<table id="one" cellpadding="0" cellspacing="3">', '</table>', '</td>')
        
    def listSeries(self, cItem, category):
        printDBG("ZalukajTv.listFilmsCategories")
        self._listLeftTable(cItem, category, '<table id="main_menu" cellpadding="0" cellspacing="3">', '</table>', '</td>')
        
    def listFilms(self, cItem):
        printDBG("ZalukajTv.listFilms")
        url      = cItem['url']
        page = cItem.get('page', 1)
        nextPage = False
        extract  = False
        try:
            cat  = int(url.split('/')[-1])
            sort = config.plugins.iptvplayer.zalukajtv_filmssort.value
            url  = ZalukajTv.FILMS_URL % (cat, sort, cItem['lang'], page)
            extract = True
        except: pass
        sts, data = self._getPage(url, {}, cItem.get('post_data', None))
        if not sts: return
        sp = '<div class="tivief4">'
        if extract:
            if (',strona-%d' % (page+1)) in data: nextPage = True
            m2 = '<div class="categories_page">' 
            if m2 not in data: m2 = '<div class="doln">'
            data = self.cm.ph.getDataBeetwenMarkers(data, sp, m2, True)[1]
        data = data.split(sp)
        if len(data): del data[0]
        for item in data:
            year = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<p>', '</p>', False)[1] )
            desc = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '</h3>', '</div>', False)[1] )
            more = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<p class="few_more">', '</p>', False)[1] )
            desc = '%s | %s | %s |' % (year, more, desc)
            icon = self._getFullUrl( self.cm.ph.getDataBeetwenMarkers(item, 'background-image:url(', ')', False)[1] )
            if '' == icon: icon = self._getFullUrl( self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"', 1)[0] )
            url  = self._getFullUrl( self.cm.ph.getSearchGroups(item, '<a href="([^"]+?)"', 1)[0] )
            title = self.cleanHtmlStr( self.cm.ph.getSearchGroups(item, 'title="([^"]+?)"', 1)[0] ) 
            title2 = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<h3>', '</h3>', False)[1] ) 
            if len(title) < len(title2): title = title2
            if '' != url: self.addVideo({'title':title, 'url':url, 'desc':desc, 'icon':icon})
        if nextPage: 
            params = dict(cItem)
            params.update({'title':_('Następna strona'), 'page':page+1})
            self.addDir(params)
            
    def listUpdatedSeries(self, cItem, category):
        printDBG("ZalukajTv.listUpdatedSeries")
        sts, data = self._getPage(cItem['url'])
        if not sts: return
        sp = '<div class="latest tooltip">'
        m2 = '<div class="doln">'
        data = self.cm.ph.getDataBeetwenMarkers(data, sp, m2, True)[1]
        data = data.split(sp)
        if len(data): del data[0]
        for item in data:
            icon  = self._getFullUrl( self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"', 1)[0] )
            url   = self._getFullUrl( self.cm.ph.getSearchGroups(item, '<a href="([^"]+?)"', 1)[0] )
            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<div class="latest_title">', '</div>', False)[1] ) 
            desc  = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<div class="latest_info">', '</div>', False)[1] )
            if '' == url: continue
            params = dict(cItem)
            params.update({'category':category, 'title':title, 'url':url, 'desc':desc, 'icon':icon})
            self.addDir(params)
            
    def _listSeriesBase(self, cItem, category, m1, m2, sp):
        printDBG("ZalukajTv._listSeriesBase")
        sts, data = self._getPage(cItem['url'])
        if not sts: return

        data = self.cm.ph.getDataBeetwenMarkers(data, m1, m2, True)[1]
        icon  = self._getFullUrl( self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"', 1)[0] )
        if '' == icon: icon = cItem.get('icon', '')
        data = data.split(sp)
        if len(data): del data[-1]
        for item in data:
            url   = self._getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"', 1)[0] )
            title = self.cleanHtmlStr( item ) 
            if '' == url: continue
            params = dict(cItem)
            params.update({'category':category, 'title':title, 'url':url, 'icon':icon})
            if 'video' == category: self.addVideo(params)
            else: self.addDir(params)
                
    def listSeriesSeasons(self, cItem, category):
        printDBG("ZalukajTv.listSeriesSeasons")
        self._listSeriesBase(cItem, category, '<div id="sezony" align="center">', '<div class="doln2">', '</div>')
        if 1 == len(self.currList):
            newItem = self.currList[0]
            self.currList = []
            self.listSeriesEpisodes(newItem)
        
    def listSeriesEpisodes(self, cItem):
        printDBG("ZalukajTv.listSeriesEpisodes")
        self._listSeriesBase(cItem, 'video', '<div id="odcinkicat">', '<div class="doln2">', '</div>')
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("ZalukajTv.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        searchPattern = urllib.quote_plus(searchPattern)
        post_data = {'searchinput':searchPattern}
        params = {'name':'category', 'category':'films_list', 'url': ZalukajTv.SEARCH_URL, 'post_data':post_data}
        self.listFilms(params)
    
    def getLinksForVideo(self, cItem):
        printDBG("ZalukajTv.getLinksForVideo url[%s]" % cItem['url'])
        if self.loggedIn: tries= [True, False]
        else: tries= [False]
        urlTab = []
        for loggedIn in tries:
            url = cItem['url']
            sts, data = self._getPage(url=url)
            if not sts: continue
            url = self._getFullUrl( self.cm.ph.getSearchGroups(data, '"(/player.php[^"]+?)"', 1)[0] )
            if '' == url:
                printDBG( 'No player.php in data[%s]' % '')
                continue 
            sts, data = self._getPage(url)
            if not sts: continue
            url = self._getFullUrl(self.cm.ph.getSearchGroups(data, '<a href="([^"]+?)"', 1)[0])
            if '' == url:
                printDBG( 'No href in data[%s]' % '')
                continue
            sts, data = self._getPage(url, loggedIn=loggedIn)
            if not sts: continue
            # First check for premium link
            url = self.cm.ph.getSearchGroups(data, "url:'([^']+?)'", 1)[0]
            if url.startswith('http'):
                printDBG("Premium url: [%s]" % url)
                urlTab.append({'name':'zalukaj.tv premium', 'url':url})
            else:
                printDBG( 'No premium link data[%s]' % data)
                url = self.cm.ph.getSearchGroups(data, 'iframe src="([^"]+?)" width=', 1)[0]
                urlTab.extend(self.up.getVideoLinkExt(url))
                # premium link should be checked at first, so if we have free link here break
                break
        return urlTab
        
    def tryTologin(self):
        printDBG('ZalukajTv.tryTologin start')
        sts,msg = False, 'Problem z zalogowaniem użytkownika \n"%s".' % config.plugins.iptvplayer.zalukajtv_login.value
        post_data = {'login': config.plugins.iptvplayer.zalukajtv_login.value, 'password': config.plugins.iptvplayer.zalukajtv_password.value}
        params    = { 'host': ZalukajTv.HOST, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': self.COOKIE_FILE }
        sts,data  = self.cm.getPage(ZalukajTv.LOGIN_URL, params, post_data)
        if sts:
            printDBG( 'Host getInitList: chyba zalogowano do premium...' )
            sts,data = self._getPage(url='http://zalukaj.tv/libs/ajax/login.php?login=1', loggedIn=True)
            if sts:
                sts,tmp = self.cm.ph.getDataBeetwenMarkers(data, '<p>Typ Konta:', '</p>', False)
                if sts: 
                    tmp = tmp.replace('(kliknij by oglądać bez limitów)', '')
                    msg = 'Zostałeś poprawnie zalogowany.' + '\nTyp Konta: '+self.cleanHtmlStr(tmp)
                    tmp = self.cm.ph.getDataBeetwenMarkers(data, '<p>Zebrane Punkty:', '</p>', False)[1].replace('&raquo; Wymień na VIP &laquo;', '')
                    if '' != tmp: msg += '\nZebrane Punkty: '+self.cleanHtmlStr(tmp)
        return sts,msg
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('ZalukajTv.handleService start')
        if None == self.loggedIn and config.plugins.iptvplayer.zalukajtvPREMIUM.value:
            self.loggedIn,msg = self.tryTologin()
            if not self.loggedIn: self.sessionEx.open(MessageBox, msg, type = MessageBox.TYPE_INFO, timeout = 10 )
            else: self.sessionEx.open(MessageBox, msg, type = MessageBox.TYPE_INFO, timeout = 10 )
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "ZalukajTv.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = [] 

        if None == name:
            self.listsTab(ZalukajTv.MAIN_CAT_TAB, {'name':'category'})
    #FILMS
        elif 'films_sub_menu' == category:
            self.listsTab(ZalukajTv.FILMS_SUB_MENU, self.currItem)
        elif 'films_popular' == category:
            self.listsTab(ZalukajTv.FILMS_POPULAR, self.currItem) 
        elif 'films_category' == category:
            self.listFilmsCategories(self.currItem, 'add_lang')
    #LANGS
        elif 'add_lang' == category:
            newItem = dict(self.currItem)
            newItem.update({'category':'films_list'})
            self.listsTab(ZalukajTv.LANGS_TAB, newItem)
    #LIST FILMS 
        elif 'films_list' == category:
            self.listFilms(self.currItem)
    #SERIES
        elif 'series_sub_menu' == category:
            self.listsTab(ZalukajTv.SERIES_SUB_MENU, self.currItem)
        elif 'series_list' == category:
            self.listSeries(self.currItem, 'series_seasons')
        elif 'series_updated' == category:
            self.listUpdatedSeries(self.currItem, 'series_episodes')
        elif 'series_seasons' == category:
            self.listSeriesSeasons(self.currItem, 'series_episodes')
        elif 'series_episodes' == category:
            self.listSeriesEpisodes(self.currItem)
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
        CHostBase.__init__(self, ZalukajTv(), True)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('zalukajtvlogo.png')])

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
        searchTypesOptions = []
        
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
