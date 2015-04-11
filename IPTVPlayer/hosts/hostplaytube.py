# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import CParsingHelper
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
import base64
try:    import json
except: import simplejson as json
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
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
config.plugins.iptvplayer.playtube_premium  = ConfigYesNo(default = False)
config.plugins.iptvplayer.playtube_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.playtube_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []

    optionList.append(getConfigListEntry("Użytkownik PREMIUM PlayTube?", config.plugins.iptvplayer.playtube_premium))
    if config.plugins.iptvplayer.playtube_premium.value:
        optionList.append(getConfigListEntry("  PlayTube login:", config.plugins.iptvplayer.playtube_login))
        optionList.append(getConfigListEntry("  PlayTube hasło:", config.plugins.iptvplayer.playtube_password))

    return optionList
###################################################


def gettytul():
    return 'PlayTube'

class PlayTube(CBaseHostClass):
    HOST = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.18) Gecko/20110621 Mandriva Linux/1.9.2.18-0.1mdv2010.2 (2010.2) Firefox/3.6.18'
    HEADER = {'User-Agent': HOST, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
    AJAX_HEADER = dict(HEADER)
    AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Cache-Control': 'no-cache'} )
    
    MAINURL = 'http://www.playtube.pl/'
    SERIALS_URL = MAINURL + 'seriale.html'
    

    #"Seriale",
    SERVICE_MENU_TABLE = [
        "Filmy",
        "Seriale",
        "Wyszukaj",
        "Historia wyszukiwania"
    ]
    
    SERIALS_MENU_TAB = [{'title': 'Alfabetycznie',           'category': 'Serials_alphabetically'},
                        {'title': 'Ostatnio zaktualizowane', 'category': 'Serials_last_updated'},
                        {'title': 'Ostatnio dodane',         'category': 'Serials_last_added'},
                        {'title': 'Najwyżej oceniane',       'category': 'Serials_top_rated'}]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'PlayTube', 'cookie':'playtube.cookie'})

        #Login data
        self.PREMIUM = config.plugins.iptvplayer.playtube_premium.value
        self.LOGIN = config.plugins.iptvplayer.playtube_login.value
        self.PASSWORD = config.plugins.iptvplayer.playtube_password.value
        self.loggedIn = None
        
        # to speed up navigation beetween filters they will be parsed only once
        self.filters = {}
        self.filters['sort'] = []
        self.filters['ver'] = []
        self.filters['cat'] = []
        self.filtersFilled = False
        
        self.linksCacheCache = {}
        
    def fillFilters(self, refresh=False):
        printDBG('getFilters')
        def SetFilters(raw, tab):
            printDBG("---------------------")
            for it in raw:
                tab.append({'tab': it[1], 'val': it[0]})
                printDBG("filter: %r" % tab[-1])
                
        if self.filtersFilled and not refresh: 
            return False
        
        sts, data = self.cm.getPage(self.MAINURL)
        if False == sts:
            return

        rawSortFilters = CParsingHelper.getDataBeetwenMarkers(data, 'Sortuj:', '</div>', False)[1]
        rawVerFilters  = CParsingHelper.getDataBeetwenMarkers(data, 'Wyświetl:', '</div>', False)[1]
        rawCatFilters  = CParsingHelper.getDataBeetwenMarkers(data, 'Kategorie Filmowe', '<script>', False)[1]
        data = '' # free data ;)
        rawSortFilters = re.compile('href="[^,]+?\,([^,]+?)\,wszystkie,0\.html">([^<]+?)<').findall(rawSortFilters)
        rawVerFilters  = re.compile('href="[^,]+?\,[^,]+?\,([^,]+?),0\.html">([^<]+?)<').findall(rawVerFilters)
        rawCatFilters  = re.compile('href="([^,]+?\,[^.]+?)\.html">([^<]+?)<').findall(rawCatFilters)
        
        if 0 < len(rawSortFilters) and 0 < len(rawVerFilters) and 0 < len(rawCatFilters):
            self.filters['sort'] = []
            self.filters['ver'] = []
            self.filters['cat'] = [{'tab': 'Wszystkie', 'val': 'glowna'}]
            SetFilters(rawSortFilters, self.filters['sort'])
            SetFilters(rawVerFilters, self.filters['ver'])
            SetFilters(rawCatFilters, self.filters['cat'])
            self.filtersFilled = True
        
    def addFilter(self, refresh, item, filterID, category):
        self.fillFilters(refresh)
        for it in self.filters[filterID]:
            params = dict(item)
            params['category'] = category
            params['title'] = it['tab']
            params[filterID] = it['val']  
            self.addDir(params)
            
    def listsMainMenu(self, tab):
        for item in tab:
            params = {'name': 'category', 'title': item, 'category': item}
            self.addDir(params)
            
    def listSerialsMenu(self, tab):
        for item in tab:
            params = {'name': 'category', 'title': item['title'], 'category': item['category']}
            self.addDir(params)
            
    def listSerialsAlphabeticallyMenu(self, category):
        printDBG("listSerialsAlphabeticallyMenu")
        sts, data = self.cm.getPage( self.SERIALS_URL )
        if not sts: 
            return
        data = CParsingHelper.getDataBeetwenMarkers(data, '<div class="content alphabet">', '</ul>', False)[1]
        data = re.compile('<a href="([^"]+?)">([^<]+?)</a>').findall(data)
        for item in data:
            if not item[0].startswith('http'):
                url =  self.MAINURL + item[0]
            params = {'name': 'category', 'title': item[1], 'category': category, 'url': url}
            self.addDir(params)
        
    def listSerialsByLetter(self, category, url):
        printDBG("listSerialsByLetter")
        sts, data = self.cm.getPage( url )
        if False == sts: return

        sts, data = CParsingHelper.getDataBeetwenMarkers(data, 'Seriale na liter', '<div class="right">', False)
        data = data.split('</li>')
        self.listItems(data, category)
        
    def listSerialsLastUpdated(self, category):
        printDBG("listSerialsLastUpdated")
        sts, data = self.cm.getPage( self.SERIALS_URL )
        if False == sts: return
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, 'Ostatnio zaktualizowane seriale', '<div class="right">', False)
        data = data.split('</li>')
        def getPlot(item):
            return item
        self.listItems(data, category, None, getPlot, False)
  
    def listSerialsBack(self, category, marker1, marker2):
        sts, data = self.cm.getPage( self.SERIALS_URL )
        if not sts: 
            return
        data = CParsingHelper.getDataBeetwenMarkers(data, marker1, marker2, False)[1].replace("\\'", '"').replace('\\', '')
        marker = '<a onmouseover="toolTip('
        data = data.split(marker)
        def getPlot(item):
            return CParsingHelper.getDataBeetwenMarkers(item, 'width="100"></td><td>', '<div', False)[1]
        self.listItems(data, category, None, getPlot)
        
    def listSerialsLastAdded(self, category):
        printDBG("listSerialsLastAdded")
        self.listSerialsBack(category, 'Ostatnio dodane seriale', '<div class="footer">')
        
    def listSerialsTopRated(self, category):
        printDBG("listSerialsTopRated")
        self.listSerialsBack(category, 'Najwyżej oceniane Seriale', '<div class="section promotedSerials"')
        
    def listSerialSeasons(self, category, url, icon):
        printDBG("listSerialSeasons")
        sts, data = self.cm.getPage( url )
        if False == sts: return
        
        plot = CParsingHelper.getDataBeetwenMarkers(data, '<p class="serialDescription">', '</p>', False)[1]
        data = CParsingHelper.getDataBeetwenMarkers(data, '<div class="seasonExpand">', '<script>', False)[1]
        data = re.compile('<a href="[/]?(serial,[^,]+?,sezon,[1-9][0-9]*?.html)">([^<]+?)</a>').findall(data)
        for item in data:
            if not item[0].startswith('http'):
                url =  self.MAINURL + item[0]
            params = {'name': 'category', 'title': item[1], 'category': category, 'url': url, 'icon':icon, 'plot':plot}
            self.addDir(params)
            
    def listSerialEpisodes(self, url, icon, plot):
        printDBG("listSerialEpisodes")
        sts, data = self.cm.getPage( url )
        if False == sts: return

        sts, data = CParsingHelper.getDataBeetwenMarkers(data, '<div class="section serial episodes">', '<script>', False)
        data = re.compile('<li><a href="[/]?(serial,[^,]+?,sezon,[1-9][0-9]*?,epizod,[0-9]+?.html)">([^<]+?)</a></li>').findall(data)
        for item in data:
            if not item[0].startswith('http'):
                url =  self.MAINURL + item[0]
            params = {'title':item[1], 'url':url, 'icon':icon, 'plot':plot}
            self.addVideo(params)
            
    def listFilms(self, cItem, page):
        printDBG("listFilms cItem[%r], page[%s]" % (cItem, page))
        
        url = self.MAINURL + '%s,%s,%s,%s.html' % (cItem['cat'], cItem['sort'], cItem['ver'], page)
        sts, data = self.cm.getPage( url )
        if False == sts: return
        
        nextPageItem = None
        if '.html">&gt;</a>' in data:
            page = str(int(page)+1)
            nextPageItem = dict(cItem)
            nextPageItem['page'] = page
            nextPageItem['title'] = 'Następna strona'
        
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, '<ul class="moviesList">', '</ul>', False)
        data = data.split('<li data-url=')
        self.listItems(data, 'video', nextPageItem, None, True, cItem.get('ver', ''))
        
    def listSearchResults(self, pattern, searchType):
        printDBG("listFilms pattern[%s], searchType[%s]" % (pattern, searchType))
        url = self.MAINURL + 'szukaj.html?query=%s&mID=' % pattern
        sts, data = self.cm.getPage( url )
        if False == sts: return
        
        if 'filmy' == searchType:
            sts, data = CParsingHelper.getDataBeetwenMarkers(data, '<h2 id="movies-res">Filmy:', '<a href="#top"', False)
            category = 'video'
        else:
            sts, data = CParsingHelper.getDataBeetwenMarkers(data, '<h2 id="serials-res">Seriale:', '<a href="#top"', False)
            category = 'Serial_seasons_list'
        data = data.split('<li data-url=')
        self.listItems(data, category)  
    
    def listItems(self, data, itemType, nextPageItem=None, getPlot=None, setRating=True, ver=''):
        for item in data:
            icon  = CParsingHelper.getSearchGroups(item, 'src="([^"]+?jpg)"')[0]
            url   = CParsingHelper.getSearchGroups(item, 'href="([^"]+?)"')[0]
            title = CParsingHelper.getSearchGroups(item, 'title="([^"]+?)"')[0]
            if '' == title: title = CParsingHelper.getSearchGroups(item, '<div class="title">([^<]+?)</div>')[0]
            
            strRating = ''
            if setRating:
                strRating = CParsingHelper.getSearchGroups(item, '<div class="rating" style="width:([0-9]+?)\%">')[0]
                if '' == strRating: strRating = '0'
                strRating = 'Ocena: %s | ' % (str(int(strRating)/10) + '/10')
            
            if None == getPlot: plot = CParsingHelper.getDataBeetwenMarkers(item, '<div class="description">', '<a', False)[1]
            else:               plot = getPlot(item)
            plot  = self.cleanHtmlStr(plot)
            # validate data
            if '' == url or '' == title: continue
            if not url.startswith('http'): url = self.MAINURL + url
            if len(icon) and not icon.startswith('http'): icon = self.MAINURL + icon
            
            if 'video' == itemType:
                params = {'title':title, 'url':url, 'icon':icon, 'plot': strRating + plot, 'ver': ver}
                self.addVideo(params)
            else:
                params = {'name': 'category', 'title':title, 'category': itemType, 'url':url, 'icon':icon, 'plot': strRating + plot}
                self.addDir(params)

        if None != nextPageItem:
            self.addDir(nextPageItem)

    def getLink(self, url):
        printDBG("getLink url[%s]" % url)
        urlItem = url.split('|')
        if 3 == len(urlItem):
            url        = urlItem[0]
            post_data  = { 'action': 'getPlayer', 'id': urlItem[1], 'playerType': urlItem[2] }
            HEADER = dict(self.AJAX_HEADER)
            HEADER['Referer'] = url
            if 'free' == urlItem[2]:
                http_params = {'header': HEADER}
            else:
                http_params = {'header': HEADER, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE}
                
            sts, data = self.cm.getPage( url, http_params, post_data)
            if not sts: return ''
            data = CParsingHelper.getDataBeetwenMarkers(data, '<div class="player">', '<div class="playerTypes">', False)[1]
            if 'free' == urlItem[2]:
                data = CParsingHelper.getSearchGroups(data, '<iframe [^>]*?src="([^"]+?)"')[0]
                sts, data = self.cm.getPage( data )
                if not sts: return ''
                data = CParsingHelper.getSearchGroups(data, '<iframe [^>]*?src="([^"]+?)"')[0]
                return self.up.getVideoLink( data )
            else:
                return CParsingHelper.getSearchGroups(data, 'url: [\'"](http[^\'"]+?)[\'"]')[0]
            return ''
        else:
            return url
            
    def getLinks(self, url, lang, playerType):
        printDBG("getLinks lang[%r], playerType[%r]" % (lang, playerType) )
        hostingTab = []
        HEADER = dict(self.AJAX_HEADER)
        HEADER['Referer'] = url
        if 'free' == playerType['val']:
            http_params = {'header': HEADER}
        else:
            http_params = {'header': HEADER, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE}
        #post_data = { 'action': 'getPlayer', 'lang': lang['val'], 'playerType': playerType['val'] }
        post_data = { 'action': 'getPlayer', 'id': lang['val'], 'setHosting': '1' }
        
        sts, data = self.cm.getPage( url, http_params, post_data)
        if not sts or 'Player premium jest dostępny tylko dla' in data: 
            return hostingTab
        
        # get players ID
        playersData = CParsingHelper.getDataBeetwenMarkers(data, '<div class="services">', '</div>', False)[1]
        playersData = re.compile('data-id="([0-9]+?)" data-playertype="([^"]+?)"[^>]*?>([^<]+?)</a>').findall(data)
        for item in playersData:
            tmp = {'need_resolve':1, 'name': '%s|%s|%s' % (lang['title'].ljust(16), playerType['title'].center(12), item[2].strip().rjust(14)), 'url': '%s|%s|%s' % (url, item[0], playerType['val']) }
            hostingTab.append(tmp)
         
        # new method to get premium links
        if 0 == len(hostingTab):
            sts, tmp = CParsingHelper.getDataBeetwenMarkers(data, 'newPlayer.init("', '")', False)
            try:
                tmp = CParsingHelper.getSearchGroups(data, 'id="%s" data-key="([^"]+?)"' % tmp)[0]
                tmp = base64.b64decode(tmp[2:])
                tmp = byteify( json.loads(tmp)['url'] )
                title = '%s | premium' % lang['title'].ljust(16)
                tmp = {'need_resolve':1, 'name': title, 'url': tmp}
                hostingTab.append(tmp)
                printDBG("||||||||||||||||||||||||||||||||||||%s|||||||||||||||||||||||||||||||" % tmp)
            except:
                printExc()
        return hostingTab
        
            
    def getHostingTable(self, urlItem):
        printDBG("getHostingTable url[%s]" % urlItem['url'])
        # use cache if possible
        if 0 < len( self.linksCacheCache.get('tab', []) ) and (urlItem['url'] + urlItem.get('ver', '')) == self.linksCacheCache.get('marker', None):
            return self.linksCacheCache['tab']
            
        hostingTab = []
        # get lang tab
        langTab = []
        sts, data = self.cm.getPage( urlItem['url'] )
        if False == sts: return hostingTab
        data = CParsingHelper.getDataBeetwenMarkers(data, '<div class="langs">', '</div>', False)[1]
        data = re.compile('data-id="([^"]+?)"[^>]*?>(.+?)</a>', re.DOTALL).findall(data)
        for item in data:
            tmp = {'val': item[0], 'title': self.cleanHtmlStr(item[1])}
            if tmp['val'] == urlItem.get('ver', ''):
                langTab = [tmp]
                break
            else: langTab.append( tmp )
            
        for lang in langTab: 
            tmpTab = []
            if self.loggedIn:
                tmpTab = self.getLinks(urlItem['url'], lang, {'val': 'premium', 'title':'Premium'})
            if 0 == len(tmpTab):
                tmpTab = self.getLinks(urlItem['url'], lang, {'val': 'free', 'title':'Free'})
            hostingTab.extend(tmpTab)
        self.linksCacheCache = {'marker': urlItem['url'] + urlItem.get('ver', ''), 'tab': hostingTab}
        return hostingTab
        
    def tryTologin(self):
        printDBG('tryTologin start')
        if '' == self.LOGIN.strip() or '' == self.PASSWORD.strip():
            printDBG('tryTologin wrong login data')
            return False
        
        post_data = {'email':self.LOGIN, 'password':self.PASSWORD}
        params = {'header':self.HEADER, 'cookiefile':self.COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        sts, data = self.cm.getPage( self.MAINURL + "logowanie.html", params, post_data)
        if not sts:
            printDBG('tryTologin problem with login')
            return False
            
        if 'wyloguj.html' in data:
            printDBG('tryTologin user[%s] logged with VIP accounts' % self.LOGIN)
            return True
     
        printDBG('tryTologin user[%s] does not have status VIP' % self.LOGIN)
        return False
        
    def getFavouriteData(self, cItem):
        try:
            favItem = {'url':cItem['url']}
            if 'ver' in cItem: favItem['ver'] = cItem['ver']
            return json.dumps(favItem).encode('utf-8')
        except: printExc()
        return None
        
    def getLinksForFavourite(self, fav_data):
        if None == self.loggedIn and self.PREMIUM:
            self.loggedIn = self.tryTologin()
            
        try: 
            favItem = byteify( json.loads(fav_data) )
            return self.getHostingTable(favItem)
        except: printExc()
        return []

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        if None == self.loggedIn and self.PREMIUM:
            self.loggedIn = self.tryTologin()
            if not self.loggedIn:
                self.sessionEx.open(MessageBox, 'Problem z zalogowaniem użytkownika "%s".' % self.LOGIN, type = MessageBox.TYPE_INFO, timeout = 10 )
            else:
                self.sessionEx.open(MessageBox, 'Zostałeś poprawnie \nzalogowany.', type = MessageBox.TYPE_INFO, timeout = 10 )
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        
        # clear hosting tab cache
        self.linksCacheCache = {}

        name     = self.currItem.get("name", '')
        title    = self.currItem.get("title", '')
        category = self.currItem.get("category", '')
        page     = self.currItem.get("page", '0')
        icon     = self.currItem.get("icon", '')
        url      = self.currItem.get("url", '')
        plot     = self.currItem.get("plot", '')
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsMainMenu(self.SERVICE_MENU_TABLE)           
    #FILMY
        elif category == "Filmy": # add sort filter
            self.addFilter(refresh, self.currItem, 'sort', 'Filmy_ver')
        elif category == 'Filmy_ver':
            self.addFilter(refresh, self.currItem, 'ver', 'Filmy_cat')
        elif category == 'Filmy_cat':
            self.addFilter(refresh, self.currItem, 'cat', 'Filmy_lists')
        elif category == "Filmy_lists":
            self.listFilms(self.currItem, page)
    #SERIALE
        elif category == "Seriale":
            self.listSerialsMenu(self.SERIALS_MENU_TAB)
        elif category == "Serials_alphabetically":
            self.listSerialsAlphabeticallyMenu('Serials_letter_list')
        elif category == "Serials_letter_list":
            self.listSerialsByLetter('Serial_seasons_list', url)
        elif category == "Serials_last_updated":
            self.listSerialsLastUpdated('Serial_seasons_list')
        elif category == "Serials_last_added":
            self.listSerialsLastAdded('Serial_seasons_list')
        elif category == "Serials_top_rated":
            self.listSerialsTopRated('Serial_seasons_list')
        elif category == "Serial_seasons_list":
            self.listSerialSeasons('Serial_episodes_list', url, icon)
        elif category == "Serial_episodes_list":
            self.listSerialEpisodes(url, icon, plot)
    #WYSZUKAJ
        elif category == "Wyszukaj":
            printDBG("Wyszukaj: " + searchType)
            pattern = urllib.quote_plus(searchPattern)
            self.listSearchResults(pattern, searchType)
            
    #HISTORIA WYSZUKIWANIA
        elif category == "Historia wyszukiwania":
            self.listsHistory()


class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, PlayTube(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('playtubelogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): RetHost(retCode, value=retlist)
        
        urlList = self.host.getHostingTable(self.host.currList[Index])
        for item in urlList:
            need_resolve = 1
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
    def getResolvedURL(self, url):
        # resolve url to get direct url to video file
        url = self.host.getLink(url)
        urlTab = []
        if isinstance(url, basestring) and url.startswith('http'):
            urlTab.append(url)
        return RetHost(RetHost.OK, value = urlTab)

    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        #searchTypesOptions.append(("Seriale", "seriale"))
        searchTypesOptions.append(("Filmy", "filmy"))
        searchTypesOptions.append(("Seriale", "seriale"))
    
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
            
        title       =  self.host.cleanHtmlStr(cItem.get('title', ''))
        description =  cItem.get('plot', '')
        description =  self.host.cleanHtmlStr(description)
        icon        =  cItem.get('icon', '')
        
        return CDisplayListItem(name = title,
                                description = description,
                                type = type,
                                urlItems = hostLinks,
                                urlSeparateRequest = 1,
                                iconimage = icon,
                                possibleTypesOfSearch = possibleTypesOfSearch)
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
