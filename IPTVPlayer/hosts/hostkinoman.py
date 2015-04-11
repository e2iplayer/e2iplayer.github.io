# -*- coding: utf-8 -*-
# based on: http://svn.sd-xbmc.org/filedetails.php?repname=sd-xbmc&path=%2Ftrunk%2Fxbmc-addons%2Fsrc%2Fplugin.video.polishtv.live%2Fhosts%2Fkinoman.py&rev=834&peg=834
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, CSearchHistoryHelper, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
import time
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
config.plugins.iptvplayer.kinoman_premium  = ConfigYesNo(default = False)
config.plugins.iptvplayer.kinoman_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.kinoman_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []

    optionList.append(getConfigListEntry("Użytkownik PREMIUM KinomanTV?", config.plugins.iptvplayer.kinoman_premium))
    if config.plugins.iptvplayer.kinoman_premium.value:
        optionList.append(getConfigListEntry("  KinomanTV login:", config.plugins.iptvplayer.kinoman_login))
        optionList.append(getConfigListEntry("  KinomanTV hasło:", config.plugins.iptvplayer.kinoman_password))

    return optionList
###################################################

def gettytul():
    return 'Kinoman'

class Kinoman(CBaseHostClass):
    HOST = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.18) Gecko/20110621 Mandriva Linux/1.9.2.18-0.1mdv2010.2 (2010.2) Firefox/3.6.18'
    HEADER = {'User-Agent': HOST, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
    SERVICE = 'kinoman'
    MAINURL = 'http://www.kinoman.tv'
    SEARCH_URL = MAINURL + '/szukaj?query='
    LIST_URL = MAINURL + '/filmy?'
    SERIAL_URL = MAINURL + '/seriale'
    SERVICE_MENU_TABLE = {
        1: "Kategorie filmowe",
        2: "Ostatnio dodane",
        3: "Najwyżej ocenione",
        4: "Najczęściej oceniane",
        5: "Najczęściej oglądane",
        6: "Ulubione",
        7: "Najnowsze",
        9: "Seriale",
        10: "Wyszukaj",
        11: "Historia wyszukiwania"
    }

    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'Kinoman', 'cookie':'kinoman.cookie'})  
        
        #Login data
        self.PREMIUM = config.plugins.iptvplayer.kinoman_premium.value
        self.LOGIN = config.plugins.iptvplayer.kinoman_login.value
        self.PASSWORD = config.plugins.iptvplayer.kinoman_password.value
        self.loggedIn = None

    def setTable(self):
        return self.SERVICE_MENU_TABLE

    def listsMainMenu(self, table):
        for num, val in table.items():
            params = {'name': 'main-menu', 'title': val, 'category': val}
            self.addDir(params)

    def listsCategoriesMenu(self, url):
        sts, data = self.cm.getPage( url, {'header': self.HEADER } )
        if not sts: return 
        data = CParsingHelper.getDataBeetwenMarkers(data, 'movie-kat-selection">', '</ul>', False)[1]
        data = data.split('</li>')
        for item in data:
            title = self.cleanHtmlStr(item)
            catID = CParsingHelper.getSearchGroups(item, 'data-value="([^"]+?)"', 1)[0]
            params = {'name': 'category', 'title': title, 'category': catID}
            self.addDir(params)


    def getFilmTab(self, url, category, pager):
        sts, data = self.cm.getPage( url, {'header': self.HEADER } )
        if not sts: return 
        nextPage = re.search('<li><a href="/filmy?.+?" rel="next">&raquo;</a></li>', data)        
        data = CParsingHelper.getDataBeetwenMarkers(data, '<div class="row-fluid  movie-item">', '<div class="container">', False)[1]
        data = data.split('<div class="row-fluid  movie-item">')
        titleA = re.compile('<a class="title"[^>]+?>')
        titleB = re.compile('</small>')
        plotA  = re.compile('<p class="desc">')
        plotB  = re.compile('</div>')
        for item in data:
            title = CParsingHelper.getDataBeetwenReMarkers(item, titleA, titleB, False)[1]
            page  = self.MAINURL + CParsingHelper.getSearchGroups(item, 'class="title" href="([^"]+?)"', 1)[0]
            plot  = CParsingHelper.getDataBeetwenReMarkers(item, plotA, plotB, False)[1]
            img   = CParsingHelper.getSearchGroups(item, 'src="([^"]+?)"', 1)[0]
            if '' != title and '' != page:
                params = {'title': title, 'page': page, 'icon': img, 'plot': plot}
                self.addVideo(params)
        if nextPage:
            params = {'name': 'nextpage', 'category': category, 'title': 'Następna strona', 'page': str(int(pager) + 1)}
            self.addDir(params)

    def getSerialCategories(self, url, category):
        sts, data = self.cm.getPage( url, {'header': self.HEADER } )
        if not sts: return 

        if category == '0 - 9':
            matchAll = re.compile('id="letter_0-9"(.+?)<div class="offset1', re.S).findall(data);
        else:
            matchAll = re.compile('id="letter_' + category + '"(.+?)<div class="offset1', re.S).findall(data);
        if len(matchAll) > 0:
            match = re.compile('<a href="(.+?)" class="pl-corners">(.+?)<span class="subtitle".+?</span></a>').findall(matchAll[0]);
            if len(matchAll) > 0:
                for i in range(len(match)):
                    title = match[i][1].replace('<span class="label label-important">NOWE</span> ', '')
                    params = {'name': 'getSeason', 'tvshowtitle': title, 'title': title, 'page': self.MAINURL+match[i][0]}
                    self.addDir(params)

    def listsABCMenu(self, table):
        for i in range(len(table)):
            params = {'name': 'abc-menu','category': table[i], 'title': table[i], 'icon':'' }
            self.addDir(params)

    def searchTab(self, url, serch):
        printDBG("getSearchResult for url[%s] searchType[%s]" % (url, serch) )

        sts, data = self.cm.getPage( url, {'header': self.HEADER } )
        if not sts: return
        
        if 'Filmy' == serch:
            marer1 = '<div class="results_title">[^<]*?Filmy:[^<]*?</div>'
            marer2 = '<div class="results_title">'
        else:
            marer1 = '<div class="results_title">[^<]*?Seriale:[^<]*?</div>'
            marer2 = '<div class="results_title">'
        
        sts, data = CParsingHelper.getDataBeetwenReMarkers(data, re.compile(marer1), re.compile(marer2), False)
        if False == sts:
            printDBG("getSearchResult problem no data beetween markers")
            return
            
        data = data.split('<div class="result box pl-round"')
        if len(data) > 1:
            del data[0]
            for item in data:
                item = item.replace('<br/>', '')
                # url & title
                match = re.search('<a href="([^"]+?)" class="en pl-white">([^<]+?)</a>', item)
                if match: 
                    url = self.MAINURL + match.group(1)
                    title = match.group(2).replace('\n', '').replace('\r', '').strip()
                else: continue
                # img
                match = re.search('<img src="([^"]+?)"', item)
                if match: img = match.group(1)
                else: img = ''
                # plot
                match = re.search('<p>([^<]+?)</p>', item)
                if match: plot = match.group(1)
                else: plot = ''
                
                params = { 'title': title, 'page': url, 'icon': img, 'plot': plot}
                if 'Filmy' == serch:
                    self.addVideo(params)
                else:
                    params['name']='getSeason'
                    params['tvshowtitle']=title
                    self.addDir(params)

    def getSeasonTab(self, url, serial):
        sts, data = self.cm.getPage( url, {'header': self.HEADER } )
        if not sts: return
        
        icon = re.compile('<img src="(.+?)" alt=""/>').findall(data)
        img = icon[0].replace('m.jpg', 'o.jpg')
        match = re.compile('<button data-action="scrollTo" data-scroll="(.+?)"').findall(data)
        if len(match) > 0:
            for i in range(len(match)):
                title = match[i].replace('_', ' ').capitalize()
                params = {'name': 'getEpisodes', 'season': match[i], 'tvshowtitle': serial, 'title': title, 'page': url, 'icon': img}
                self.addDir(params)

    def getEpisodesTab(self, url, serial, sezon, icon):
        printDBG("getSerialEpisodItems start url=[%s] episode[%s]" % (url, sezon) )
        sts, data = self.cm.getPage( url )
        if False == sts:
            printDBG("getSerialEpisodItems problem")
            return
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, 'id="%s"' % sezon, '</div>', False)
        if False == sts:
            printDBG("getSerialEpisodItems problem no data beetween markers")
            return
            
        data = re.compile('<a class="o" href="([^"]+?)/([^"]+?)/([^"]+?)">([^<]+?)</a>').findall(data)
        if len(data) > 0:
            for i in range(len(data)):
                page = self.MAINURL + data[i][0]+'/'+data[i][1]+'/'+data[i][2]
                title = self.cm.html_entity_decode( data[i][3] )
                plot = '%s - %s' % (serial, data[i][1])
                params = {'season': sezon, 'tvshowtitle': serial, 'episode':data[i][1], 'title': title, 'page': page, 'icon': icon}
                self.addVideo(params)

    def getHostTable(self, url, vip=False):
        videoTab = []
        http_params = {'header': self.HEADER, }
        if vip: 
            http_params.update({'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE })
            
        sts, data = self.cm.getPage( url, http_params )
        if not sts: return videoTab
            
        playersData = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="single-player">', '</a>')
        for playerData in playersData:
            playerTitle = self.cleanHtmlStr(playerData)
            playerId = self.cm.ph.getSearchGroups(playerData, 'class="player-wrapper" id="player_([0-9]+?)"')[0]
            if '' != playerId:
                sts, data = self.cm.getPage( self.MAINURL+'/players/init/' + playerId, http_params )
                if not sts: 
                    continue
                data = data.replace('\\', '')
                hash = self.cm.ph.getSearchGroups(data, '"data":"([^"]+?)"')[0]

                if '' != hash:
                    post_data = { 'hash': hash }
                    if vip: 
                        post_data['type'] = 'vip'
                        
                    sts, data = self.cm.getPage(self.MAINURL+'/players/get', http_params, post_data)
                    if not sts:
                        continue
                    
                    url = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
                    printDBG("Kinoman getHostTable[%s]" % url)
                    if '' != url:
                        tmpTab = self.up.getVideoLinkExt( url )
                        for item in tmpTab:
                            item['name'] = playerTitle + ' ' + item['name']
                        videoTab.extend(tmpTab)
                    else:
                        url = self.cm.ph.getSearchGroups(data, "ShowNormalPlayer.+?'(.+?)',")[0]
                        if url:
                            videoTab.append({'name': playerTitle + ' vip', 'url': self.up.decorateUrl(url, {'Referer':'http://www.kinoman.tv/assets/kinoman.tv/swf/flowplayer-3.2.7.swf'})})
        return videoTab
        
    def tryTologinTmp(self, protocol='http'):
        printDBG('tryTologinTmp start [%s]' % protocol)
        if '' == self.LOGIN.strip() or '' == self.PASSWORD.strip():
            printDBG('tryTologin wrong login data')
            return False
        
        post_data = {'username':self.LOGIN, 'password':self.PASSWORD, 'submit_login':'login', 'submit':''} #'auto_login':'1'
        params = {'header':self.HEADER, 'cookiefile':self.COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        sts, data = self.cm.getPage( protocol + "://www.kinoman.tv/auth/login", params, post_data)
        if not sts:
            printDBG('tryTologin problem with login')
            return False
            
        if -1 != data.find('<a href="/auth/logout">wyloguj'):
            printDBG('tryTologin user[%s] logged with VIP accounts' % self.LOGIN)
            return True
     
        printDBG('tryTologin user[%s] does not have status VIP' % self.LOGIN)
        return False
        
    def tryTologin(self):
        printDBG('tryTologin start')
        ret = self.tryTologinTmp('http')
        if False == ret:
            ret = self.tryTologinTmp('https')
        return ret

    def getPageStr(self, prefix, page):
        if 1 < int(page):
            return prefix + page
        return ''
        
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        if None == self.loggedIn and self.PREMIUM:
            self.loggedIn = self.tryTologin()
            if not self.loggedIn:
                self.sessionEx.open(MessageBox, 'Problem z zalogowaniem użytkownika "%s".' % self.LOGIN, type = MessageBox.TYPE_INFO, timeout = 10 )
            else:
                self.sessionEx.open(MessageBox, 'Zostałeś poprawnie \nzalogowany.', type = MessageBox.TYPE_INFO, timeout = 10 )
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", '')
        title    = self.currItem.get("title", '')
        category = self.currItem.get("category", '')
        page     = self.currItem.get("page", '1')
        icon     = self.currItem.get("icon", '')
        link     = self.currItem.get("url", '')
        sezon    = self.currItem.get("season", '')
        epizod   = self.currItem.get("episode", '')
        serial   = self.currItem.get("tvshowtitle", '')
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
        if str(page) == 'None' or page == '': page = '1'
        #MAIN MENU
        if name == None:
            self.listsMainMenu(self.SERVICE_MENU_TABLE)
        #KATEGORIE FILMOWE
        elif category == self.setTable()[1]:
            self.listsCategoriesMenu(self.MAINURL + '/filmy')
        #OSTATNIO DODANE
        elif category == self.setTable()[2]:
            url = self.LIST_URL + self.getPageStr('p=', page)
            self.getFilmTab(url, category, page)
        #NAJWYŻEJ OCENIONE
        elif category == self.setTable()[3]:
            url = self.LIST_URL + 'sorting=movie.rate' + self.getPageStr('&p=', page)
            self.getFilmTab(url, category, page)
        #NAJCZĘŚCIEJ OCENIANE
        elif category == self.setTable()[4]:
            url = self.LIST_URL + 'sorting=total_rates' + self.getPageStr('&p=', page)
            self.getFilmTab(url, category, page)
        #NAJCZĘŚCIEJ OGLĄDANE
        elif category == self.setTable()[5]:
            url = self.LIST_URL + 'sorting=movie.views' + self.getPageStr('&p=', page)
            self.getFilmTab(url, category, page)
        #ULUBIONE
        elif category == self.setTable()[6]:
            url = self.LIST_URL + 'sorting=total_favs' + self.getPageStr('&p=', page)
            self.getFilmTab(url, category, page)
        #NAJNOWSZE
        elif category == self.setTable()[7]:
            url = self.LIST_URL + 'sorting=movie.created' + self.getPageStr('&p=', page)
            self.getFilmTab(url, category, page)
        #SERIALE
        elif category == self.setTable()[9]:
            self.listsABCMenu(self.cm.makeABCList())
        #WYSZUKAJ
        elif category == 'Wyszukaj':
            printDBG("Wyszukaj: " + searchType)
            pattern = urllib.quote_plus(searchPattern)
            if 'filmy' == searchType:
                self.searchTab(self.SEARCH_URL + pattern, 'Filmy')
            elif 'seriale' == searchType:
                self.searchTab(self.SEARCH_URL + pattern, 'Seriale')
        #HISTORIA WYSZUKIWANIA
        elif category == "Historia wyszukiwania":
            self.listsHistory()

        #LISTA SERIALI
        if name == 'abc-menu':
            self.getSerialCategories(self.SERIAL_URL, category)
        if name == 'getSeason':
            self.getSeasonTab(page, title)
        if name == 'getEpisodes':
            self.getEpisodesTab(page, serial, sezon, icon)
        #LISTA FILMÓW
        if name == 'category' or name == 'nextpage':
            if category.isdigit() == True:
                    self.getFilmTab(self.LIST_URL + 'genres%5B65%5D=' + category + 'genres%5b65%5d=' + category + self.getPageStr('&p=', page), category, page)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Kinoman(), True)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('kinomanlogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] != 'video':
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])

        linkTab = []
        if True == self.host.loggedIn:
            linkTab.extend( self.host.getHostTable(self.host.currList[Index]["page"], True) )
        linkTab.extend( self.host.getHostTable(self.host.currList[Index]["page"]) )
        retlist = []
        for item in linkTab:
            retlist.append(CUrlItem(item['name'], item['url'], 0))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
    def getResolvedURL(self, url):
        # resolve url to get direct url to video file
        url = self.host.up.getVideoLink( url )
        urlTab = []

        if isinstance(url, basestring):
            urlTab.append(url)

        return RetHost(RetHost.OK, value = urlTab)

    def convertList(self, cList):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        searchTypesOptions.append(("Seriale", "seriale"))
        searchTypesOptions.append(("Filmy", "filmy"))
    
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
                
            title       = self.host.cleanHtmlStr(cItem.get('title', ''))
            description = self.host.cleanHtmlStr(cItem.get('plot', ''))
            description = self.host.cleanHtmlStr(description)
            icon        = self.host.cleanHtmlStr(cItem.get('icon', ''))
            
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