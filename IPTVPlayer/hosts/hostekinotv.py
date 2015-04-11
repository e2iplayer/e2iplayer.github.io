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
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################
# FOREIGN import
###################################################
import re
from Components.config import config, ConfigYesNo, ConfigText, ConfigSelection, getConfigListEntry
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.ekinotvPREMIUM = ConfigYesNo(default = False)
config.plugins.iptvplayer.ekinotv_login = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.ekinotv_password = ConfigText(default = "", fixed_size = False)

config.plugins.iptvplayer.ekinotv_sortby = ConfigSelection(default = "data-dodania", choices = [("alfabetycznie", "nazwy"), ("ocena", "oceny"),("odslony", "ilości odsłon"),("data-dodania", "daty dodania"),("data-premiery", "daty premiery"), ('data-aktualizacji', 'daty aktualizacji')])            
config.plugins.iptvplayer.ekinotv_sortorder = ConfigSelection(default = "desc", choices = [("desc", "malejąco"),("asc", "rosnąco")]) 

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("Użytkownik PREMIUM Ekino TV?", config.plugins.iptvplayer.ekinotvPREMIUM))
    if config.plugins.iptvplayer.ekinotvPREMIUM.value:
        optionList.append(getConfigListEntry("    Ekino TV login:", config.plugins.iptvplayer.ekinotv_login))
        optionList.append(getConfigListEntry("    Ekino TV hasło:", config.plugins.iptvplayer.ekinotv_password))
    optionList.append(getConfigListEntry("Sortuj według:", config.plugins.iptvplayer.ekinotv_sortby))
    optionList.append(getConfigListEntry("Kolejność wyświetlania:", config.plugins.iptvplayer.ekinotv_sortorder))
    return optionList
###################################################

def gettytul():
    return 'ekino.tv'

class EkinoTv(CBaseHostClass):
    SERVICE = 'ekinotv'
    MAINURL = 'http://www.ekino.tv/'
    LOGIN_URL        = MAINURL + 'logowanie.html'
    SEARCH_URL       = MAINURL + 'szukaj-wszystko,%s,%s,%s.html'
    FILMS_LIST_URL   = MAINURL + 'filmy,%s,%s,%s,%s,1900-2014,,%s.html?sort_field=%s&sort_method=%s'
    FILMS_CAT_URL    = MAINURL + 'kategorie.html'  
    
    SERIALS_LIST_URL = MAINURL + 'seriale-online,%s,%s,%s,%s.html'
    SERIALS_CAT_URL  = MAINURL + '/seriale-online.html'
    
    
    POPULAR = ',wszystkie,wszystkie,1900-2013,.html?sort_field=odslony&sort_method=desc'
    MOVIE3DURL = 'http://www.ekino.tv/gorace-filmy.html?mode=3d'
    
    VERSION_TABLE = [ {'title':'--Wszystkie--', 'ver':'wszystkie',  'mode':'wszystkie'},
                      {'title':'Z lektorem',    'ver':'lektor',     'mode':'wszystkie'},
                      {'title':'Z napisami PL', 'ver':'napisy',     'mode':'wszystkie'},
                      {'title':'Dubbingowane',  'ver':'dubbing',    'mode':'wszystkie'},
                      {'title':'Orginane',      'ver':'oryginalny', 'mode':'wszystkie'},
                      {'title':'Polskie',       'ver':'polskie',    'mode':'wszystkie'},
                      {'title':'2D',            'ver':'wszystkie',  'mode':'2d'},
                      {'title':'HD',            'ver':'wszystkie',  'mode':'hd'},
                      {'title':'3D',            'ver':'wszystkie',  'mode':'3d'} ]
    VER_TRANSLATE  = {'polskie' : 'pl', 'napisy':'subtitles', 'lektor' : 'lector', 'dubbing' : 'dubbing', 'oryginalny' : 'original'}
    MOD_TRANSLATE  = {'2d' : 'normal', 'hd':'hd', '3d' : '3d'}
    MAIN_CAT_TAB = [{ 'category':'films',          'title':'Filmy' },
                    { 'category':'serials',        'title':'Seriale' },
                    { 'category':'Wyszukaj',       'title':'Wyszukaj' },
                    { 'category':'Historia wyszukiwania', 'title':'Historia wyszukiwania'} ]
                    
    
    def __init__(self):
        printDBG("EkinoTv.__init__")
        CBaseHostClass.__init__(self, {'history':'EkinoTv.tv', 'cookie':'ekinotv.cookie'})
        self.loggedIn = False
            
    def _checkNexPage(self, data, page):
        if -1 != data.find('>%s</a></li>' % page):
            return True
        else: return False
            
    def _resolveUrl(self, url, currPath=''):
        if not url.startswith('http') and '' != url:
            if '' == currPath: return EkinoTv.MAINURL + url
            else: return currPath + url
        else: return url
            
    def _getTitle(self, data):  
        title = ''
        t1 = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<h2>', '</h2>', False)[1])
        t2 = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<h3>', '</h3>', False)[1])

        title = t1
        if '' != t2 and t1.upper() != t2.upper():
            title += " (%s)" % t2
        return title
        if '' != title:
            # Get available versions
            tab = re.findall('class="s-icon_([^_^"]+?)[_"]', data)
            ver = ''
            for v in tab:
               ver += '%s, ' % v
            if '' != ver: 
                ver = ver[:-2]
                title += ", (%s)" % ver
        return title
            
    def listsTab(self, tab, cItem):
        printDBG("EkinoTv.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            self.addDir(params)
            
    def listsFilmsCategories(self, cItem):
        printDBG("EkinoTv.listsFilmsCategories")
        sts, data = self.cm.getPage(EkinoTv.FILMS_CAT_URL)
        if sts:
            data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="videosCategories">', '<span>Wersja</span>', False)[1]
            data = re.compile('<a href="([^"]+?).html">([^<]+?)</a>([^<]+?)<').findall(data)
            for item in data:
                params = dict(cItem)
                params.update({'title' : self.cleanHtmlStr(item[1] + ' ' + item[2]), 'cat' : item[0].split(',')[-1]})
                self.addDir(params)
                    
    def listsFilms(self, cItem):
        printDBG("EkinoTv.listsFilms")
        page = cItem.get('page', 0)
        url  = cItem.get('url', '')
        if '' == url:
            sortby    = config.plugins.iptvplayer.ekinotv_sortby.value          
            sortorder = config.plugins.iptvplayer.ekinotv_sortorder.value
            url       = self._resolveUrl(EkinoTv.FILMS_LIST_URL % (cItem['cat'], page, cItem['ver'], cItem.get('quality', 'wszystkie'), cItem['mode'], sortby, sortorder) )
        else:
            url = url % page
            
        sts, data = self.cm.getPage(url)
        if sts:
            nextPage = self._checkNexPage(self.cm.ph.getDataBeetwenMarkers(data, '<ul class="pagination">', '</ul>', False)[1], page+2)
            data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="movies">', '</ul>', False)[1]
            data = data.split('</li>')
            del data[-1]
            for item in data:
                url    = self._resolveUrl(self.cm.ph.getSearchGroups(item, 'data-movie_url="([^"]+?)"')[0])
                icon   = self._resolveUrl(self.cm.ph.getSearchGroups(item, 'src="([^"]+?jpg)"')[0])
                params = dict(cItem)
                params.update({'link_type':'film', 'title' : self._getTitle(item), 'url':url, 'icon':icon, 'desc' : self.cleanHtmlStr(item)})
                self.addVideo(params)
            if nextPage:
                params = dict(cItem)
                params.update({'title':'Następna strona', 'page':page+1})
                self.addDir(params)
                
    def listsLetters(self, cItem):
        printDBG('EkinoTv.listsLetters start')
        sts, data = self.cm.getPage(EkinoTv.SERIALS_CAT_URL)
        if sts:
            data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="serialsmenu">', '</ul>', False)[1]
            data = re.findall(',([^"^,]+?)\.html"><span class="name">([^<]+?)</span><span class="count">([^<]+?)<', data)
            for item in data:
                params = dict(cItem)
                params.update({'title':'%s (%s)' % (item[1], item[2]), 'cat':item[0]})
                self.addDir(params)
                
    def listsSerials(self, cItem, category):
        printDBG('EkinoTv.listsSerials start')
        page = cItem.get('page', 0)
        url  = cItem.get('url', '')
        if '' == url:
            sortby    = config.plugins.iptvplayer.ekinotv_sortby.value          
            sortorder = config.plugins.iptvplayer.ekinotv_sortorder.value
            url       = self._resolveUrl(EkinoTv.SERIALS_LIST_URL % (cItem['cat'], page, sortby, sortorder) )
        else:
            url = url % page
        sts, data = self.cm.getPage(url)
        if sts:
            nextPage = self._checkNexPage(self.cm.ph.getDataBeetwenMarkers(data, '<ul class="pagination">', '</ul>', False)[1], page+2)
            data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="list">', '</ul>', False)[1]
            data = data.split('</li>')
            del data[-1]
            for item in data:
                url    = self._resolveUrl(self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0])
                icon   = self._resolveUrl(self.cm.ph.getSearchGroups(item, """['"]([^"^']+?jpg)['"]""")[0])
                params = dict(cItem)
                params.update({'title' : self._getTitle(item), 'url':url, 'category':category, 'icon':icon, 'desc':self.cleanHtmlStr(item)})
                self.addDir(params)
            if nextPage:
                params = dict(cItem)
                params.update({'title':'Następna strona', 'page':page+1})
                self.addDir(params)
                
    def listEpisodes(self, cItem):
        printDBG('EkinoTv.listEpisodes start')
        url = self._resolveUrl(cItem['url'])
        sts, data = self.cm.getPage(url)
        if sts:
            data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="seasons">', '<div class="sidebar">', False)[1]
            data = data.split('<div class="h">')
            del data[0]
            for item in data:
                sTitle = self.cm.ph.getDataBeetwenMarkers('>' + item, '>', '</div>', False)[1]
                eData = self.cm.ph.getDataBeetwenMarkers(item, '<ul class="episodes">', '</ul>', False)[1].split('</li>')
                del eData[-1]
                for eItem in eData:
                    if 'noFiles' not in eItem:
                        eTitle = self.cleanHtmlStr(eItem)
                        url    = self.cm.ph.getSearchGroups(eItem, """href=['"]([^"^']+?)['"]""")[0]
                        params = dict(cItem)
                        params.update({'link_type':'serial', 'title' : '%s: %s' % (sTitle, eTitle), 'url':url})
                        self.addVideo(params)
    
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("EkinoTv.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        searchPattern = searchPattern.replace(' ', '+')
        url = EkinoTv.SEARCH_URL % (searchPattern, searchType, '<page>')
        url = url.replace('<page>', '%s')
        tmpItem = dict(cItem)
        if 'filmy' == searchType:
            tmpItem.update({'name':'category', 'category':'films2', 'url':url})
            self.listsFilms(tmpItem)
        elif 'seriale' == searchType:
            tmpItem.update({'name':'category', 'category':'serials1', 'url':url})
            self.listsSerials(tmpItem, 'episodes_list')
        else:
            assert False
                    
    def _getPremiumPlayers(self, url):
        printDBG("EkinoTv._getPremiumPlayers [%s]" % url)
        players = []
        url = self._resolveUrl(url)
        sts, data = self.cm.getPage(url, {'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE})
        if sts:
            link = self.cm.ph.getSearchGroups(data, """url: ['"]([^"^']+?)['"]""")[0]
            if '' != link:
                players.append({'name':'premium', 'url':link, 'need_resolve':0})
        return players
        
    def _getPlayers(self, url):
        printDBG("EkinoTv._getPremiumPlayers [%s]" % url)
        players = []
        url = self._resolveUrl(url)
        sts, data = self.cm.getPage(url)
        if sts:
            data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="players">', '</ul>', False)[1]
            data = re.findall('<a href="([^"]+?)">([^<]+?)<', data)
            for item in data:
                players.append({'name':item[1], 'url':item[0], 'need_resolve':1})
        return players

    def getLinksForVideo(self, cItem):
        printDBG("EkinoTv.getLinksForVideo [%s]" % cItem['url'])
        if len(cItem.get('url_cache', [])):
            return cItem['url_cache']
        # GET ALL VERSION LINKS
        urlTab = []
        tmpLinks = []
        url = self._resolveUrl(cItem['url'])
        sts, data = self.cm.getPage(url)
        if sts:
            # get modes
            tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div class="langs hd_3d">', '</div>')[1]
            tmp = re.findall('href="([^"]+?)\?mode=([^"]+?)"', tmp)
            modes = {}
            for item in tmp: 
                modes[item[1]] = item[0]
                
            mode = EkinoTv.MOD_TRANSLATE.get(cItem.get('mode', ''), '')
            if mode in modes.keys(): 
               modes = {mode:modes[mode]}
            if 0 == len(modes):
               modes = {'normal':'fake'}
            for mode in modes.keys():
                if 'fake' != modes[mode]:
                    url = self._resolveUrl(modes[mode] + ('?mode=%s' % mode))
                    sts, data = self.cm.getPage(url)
                if sts:
                    # get langs
                    tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div class="langs">', '</div>')[1]
                    tmp = re.findall('href="([^"]+?)"', tmp)
                    filter_ver = EkinoTv.VER_TRANSLATE.get(cItem.get('ver', ''), '')
                    for url in tmp:
                        ver = self.cm.ph.getSearchGroups(url, ",([^,^.]+?)\.html")[0]
                        if '' == filter_ver or ver == filter_ver:
                            tmpLinks.append({'url': url, 'ver':ver, 'mode':mode})
            if 0 == len(tmpLinks):
                tmpLinks.append({'url': cItem['url'], 'ver':'unknown', 'mode':'unknown'})
        # GET PLAYER FOR GIVEN LINK
        for item in tmpLinks:
            players = []
            if self.loggedIn:
                players = self._getPremiumPlayers(item['url'])
            if 0 == len(players):
                players = self._getPlayers(item['url'])
            for player in players:
                params = dict(player)
                params.update({'name':'%s | %s | %s' % (params['name'], item['ver'], item['mode'])})
                urlTab.append(params)
        if len(urlTab):
            cItem['url_cache'] = urlTab
        return urlTab
        
    def getResolvedURL(self, url):
        printDBG("EkinoTv.getLinksForVideo [%s]" % url)
        videoLinks = []
        url = self._resolveUrl(url)
        sts, data = self.cm.getPage(url)
        if sts:
            sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="free_player"', '</div>')
            if sts: 
                match = re.search('<iframe[^>]+?src="([^"]+?)"', data, re.IGNORECASE)
                if not match: match = re.search('<embed[^>]+?src="([^"]+?)"', data, re.IGNORECASE)
                if match:
                    videoLinks = self.up.getVideoLinkExt(match.group(1))
        return videoLinks
        
    def tryTologin(self):
        printDBG('EkinoTv.tryTologin start')
        if '' == self.LOGIN.strip() or '' == self.PASSWORD.strip():
            printDBG('tryTologin wrong login data')
            return False 
        post_data = {'form_login_username':self.LOGIN, 'form_login_password':self.PASSWORD, "form_login_rememberme": "1"}
        params = {'cookiefile':self.COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        sts, data = self.cm.getPage(EkinoTv.LOGIN_URL, params, post_data)         
        if sts and 'Wyloguj' in data:
            return True
        return False
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('EkinoTv.handleService start') 
        self.PREMIUM         = config.plugins.iptvplayer.ekinotvPREMIUM.value
        if False == self.loggedIn and self.PREMIUM:
            self.LOGIN           = config.plugins.iptvplayer.ekinotv_login.value
            self.PASSWORD        = config.plugins.iptvplayer.ekinotv_password.value
            self.loggedIn = self.tryTologin()
            if not self.loggedIn:
                self.sessionEx.open(MessageBox, 'Problem z zalogowaniem użytkownika "%s".' % self.LOGIN, type = MessageBox.TYPE_INFO, timeout = 10 )
            else:
                self.sessionEx.open(MessageBox, 'Zostałeś poprawnie \nzalogowany.', type = MessageBox.TYPE_INFO, timeout = 10 )
                
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "EkinoTv.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = []
        
        if None == name:
            self.listsTab(EkinoTv.MAIN_CAT_TAB, {'name':'category'})
    #FILMS CATEGORIES
        elif 'films' == category:
            tmpItem = dict(self.currItem)
            tmpItem.update({'category':'films1'})
            self.listsFilmsCategories(tmpItem)
    #FILMS FILTERS
        elif 'films1' == category:
            tmpItem = dict(self.currItem)
            tmpItem.update({'category':'films2'})
            self.listsTab(EkinoTv.VERSION_TABLE, tmpItem)
    #LIST FILMS
        elif 'films2' == category:
            self.listsFilms(self.currItem)
    #FILMS LETTERS
        elif 'serials' == category:
            tmpItem = dict(self.currItem)
            tmpItem.update({'category':'serials1'})
            self.listsLetters(tmpItem)
    #LIST SERIALS
        elif 'serials1' == category:
            self.listsSerials(self.currItem, 'episodes_list')
    #LIST EPISODES
        elif 'episodes_list' == category:
            self.listEpisodes(self.currItem)
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
        CHostBase.__init__(self, EkinoTv(), True)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('ekinotvlogo.png')])
        
    # return resolved url
    # for given url
    def getResolvedURL(self, url):
        if url != None and url != '':
            tmpTab = self.host.getResolvedURL(url)
            list = []
            for item in tmpTab:
                list.append(item['url'])
            return RetHost(RetHost.OK, value = list)
        else:
            return RetHost(RetHost.ERROR, value = [])

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
            need_resolve = item['need_resolve']
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo

    def convertList(self, cList):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        searchTypesOptions.append(("Filmy", "filmy"))
        searchTypesOptions.append(("Seriale", "seriale"))
    
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
