# -*- coding: utf-8 -*-
# Based on (root)/trunk/xbmc-addons/src/plugin.video.polishtv.live/self.HOSTs/ @ 419 - Wersja 636

#ToDo
#    Błąd przy wyszukiwaniu filmów z polskimi znakami

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.libs.anyfilesapi import AnyFilesVideoUrlExtractor
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
###################################################
# FOREIGN import
###################################################
import re, string
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
config.plugins.iptvplayer.anyfilespl_login = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.anyfilespl_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("Anyfiles.pl " + _('login:'), config.plugins.iptvplayer.anyfilespl_login))
    optionList.append(getConfigListEntry("Anyfiles.pl " + _('password:'), config.plugins.iptvplayer.anyfilespl_password))
    return optionList
###################################################

def gettytul():
    return 'AnyFiles'

class AnyFiles(CBaseHostClass):
    MAINURL = 'http://video.anyfiles.pl'
    SEARCHURL = MAINURL + '/Search.jsp'
    NEW_LINK = MAINURL + '/najnowsze/0'
    HOT_LINK = MAINURL + '/najpopularniejsze/0'
    SERVICE_MENU_TABLE = {
        1: "Kategorie",
        2: "Najnowsze",
        3: "Popularne",
        4: "Wyszukaj",
        5: "Historia wyszukiwania"
    }

    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'AnyFiles', 'cookie':'anyfiles.cookie'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.anyfiles = AnyFilesVideoUrlExtractor()

    def setTable(self):
            return self.SERVICE_MENU_TABLE

    def listsMainMenu(self, table):
        for num, val in table.items():
            params = {'type': 'category', 'name': 'main-menu','category': val, 'title': val, 'icon': ''}
            self.currList.append(params)
        
    def searchTab(self, text):
        printDBG(gettytul() + ': ' +'searchTab start')
        params = dict(self.defaultParams)
        params['header'] = {'Referer' : self.MAINURL}
        if self.SEARCHURL in text:
            url = text
            post_data = {}
        else:
            url = self.SEARCHURL 
            post_data = {'q': text, 'oe': 'polish'}
            
        sts,data = self.cm.getPage(url, params, post_data)
        if not sts:
            return
        printDBG(data)
        match = re.compile('src="(.+?)" class="icon-img "></a>.+?<a[^>]+?class="box-title" href="(.+?)">(.+?)</a></td></tr>').findall(data)
        if len(match) > 0:
            for i in range(len(match)):
                params = {'type': 'video', 'title': match[i][2], 'page': self.MAINURL + match[i][1], 'icon': match[i][0]}
                self.currList.append(params)
            match = re.search('Paginator.+?,(.+?), 8, (.+?),',data)
            if match:
                if int(match.group(2)) < int(match.group(1)):
                    nextpage = (int(match.group(2))+1) * 18
                    newpage = self.SEARCHURL + "?st=" + str(nextpage)
                    params = {'type': 'category', 'name': 'nextpage', 'title': 'Następna strona', 'page': newpage, 'icon': ''}
                    self.currList.append(params)
        
    def getCategories(self):
        printDBG(gettytul() + ': ' +'getCategories start')
        sts, data = self.cm.getPage(self.MAINURL, self.defaultParams)
        if sts:
            data = re.compile('<tr><td><a href="([^"]+?)" class="kat-box-title">([^<]+?)</a>').findall(data)
            for item in data:
                c = item[0].split('/')
                title = string.capwords(c[1].replace('+',' '))
                params = {'type': 'category', 'name': 'category', 'title': title, 'page': self.MAINURL + item[0], 'icon': ''}
                self.currList.append(params)

    def getMovieTab(self, url):
        printDBG(gettytul() + ': ' +'getMovieTab start')
        
        sts, data = self.cm.getPage(url, self.defaultParams)
        if sts:
            # check if next Page available
            nextPageparams = None
            match = re.search('Paginator[^,]+?,([^,]+?), 8, ([^,]+?),', data)
            if match:
                if int(match.group(2)) < int(match.group(1)):
                    nextpage = (int(match.group(2))+1) * 20
                    p = url.split('/')
                    if len(p) == 7:
                        newpage = self.MAINURL + "/" + p[3] + "/" + p[4] + "/" + p[5] + "/" + str(nextpage)
                    else:
                        newpage = self.MAINURL + "/" + p[3] + "/" + str(nextpage)
                    nextPageparams = {'type': 'category', 'name': 'nextpage', 'title': 'Następna strona', 'page': newpage, 'icon': ''}
            # get videos
            data = self.cm.ph.getDataBeetwenMarkers(data, 'class="kat-box-div">', '<script', False)[1].split('class="kat-box-div">')
            for item in data:
                icon = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
                plot = clean_html(self.cm.ph.getDataBeetwenMarkers(item, 'class="div_opis">Opis:', '</div>', False)[1])
                match = self.cm.ph.getSearchGroups(item, '<a href="([^"]+?)" class="kat-box-name">([^<]+?)<', 2)
                params = {'type': 'video', 'title': match[1], 'page': self.MAINURL + match[0], 'plot': plot, 'icon': icon}
                self.currList.append(params)
                    
            if nextPageparams is not None:
                self.currList.append(nextPageparams)
                
    def getFavouriteData(self, cItem):
        return cItem['page']
        
    def getLinksForFavourite(self, fav_data):
        return self.anyfiles.getVideoUrl(fav_data)
        
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG(gettytul() + ': ' +'handleService start')
        login    = config.plugins.iptvplayer.anyfilespl_login.value
        password = config.plugins.iptvplayer.anyfilespl_password.value
        if not self.anyfiles.isLogged() and '' != login and '' != password:
            if not self.anyfiles.tryTologin():
                self.sessionEx.open(MessageBox, _('User [%s] login failed.') % login, type = MessageBox.TYPE_INFO, timeout = 10 )
            else:
                self.sessionEx.open(MessageBox, _('User [%s] logged correctly.') % login, type = MessageBox.TYPE_INFO, timeout = 10 )
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        title    = self.currItem.get("title", '')
        category = self.currItem.get("category", '')
        page     = self.currItem.get("page", '')
        icon     = self.currItem.get("icon", '')
        link     = self.currItem.get("url", '')

 
        printDBG(gettytul() + ': ' + "handleService: |||||||||||||||||||||||||||||||||||| [%s] " % name )
        self.currList = []


    #MAIN MENU
        if name == None:
            self.listsMainMenu(self.SERVICE_MENU_TABLE)   
    #KATEGORIE
        if category == self.setTable()[1]:
           self.getCategories()
    #NAJNOWSZE
        if category == self.setTable()[2]:
            self.getMovieTab(self.NEW_LINK)
    #POPULARNE
        if category == self.setTable()[3]:
            self.getMovieTab(self.HOT_LINK)
    #LISTA TYTULOW W KATEGORII
        if name == 'category':
            self.getMovieTab(page)
    #WYSZUKAJ
        if category == self.setTable()[4]:
            if searchPattern != None:
                self.searchTab(searchPattern)

        if name == 'nextpage':
            if self.SEARCHURL in page:
                self.searchTab(page)
            else:
                self.getMovieTab(page)
    #HISTORIA WYSZUKIWANIA
        elif category == "Historia wyszukiwania":
            self.listsHistory()
            
class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, AnyFiles(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])
    
    # return full path to player logo
    def getLogoPath(self):  
        return RetHost(RetHost.OK, value = [GetLogoDir('anyfileslogo.png')])

    # return list of links for VIDEO with given Index
    # for given Index
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): RetHost(retCode, value=retlist)
        
        urlsTab = self.host.anyfiles.getVideoUrl(self.host.currList[Index]["page"])
        for urlItem in urlsTab:
            retlist.append(CUrlItem(urlItem['name'], urlItem['url'], 0))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo

    def converItem(self, cItem):
        hostList = []
        hostLinks = []
            
        type = CDisplayListItem.TYPE_UNKNOWN
        possibleTypesOfSearch = None
        if cItem['type'] == 'category':
            if cItem['title'] == 'Wyszukaj':
                type = CDisplayListItem.TYPE_SEARCH
            else:
                type = CDisplayListItem.TYPE_CATEGORY
        elif cItem['type'] == 'video':
            type = CDisplayListItem.TYPE_VIDEO
            
        title       =  cItem.get('title', '')
        description =  cItem.get('plot', '')
        icon        =  cItem.get('icon', '')
        
        return CDisplayListItem(name = title,
                                description = description,
                                type = type,
                                urlItems = hostLinks,
                                urlSeparateRequest = 1,
                                iconimage = icon )
    
    def getSearchItemInx(self):
        # Find 'Wyszukaj' item
        try:
            list = self.host.getCurrList()
            for i in range( len(list) ):
                if list[i]['category'] == 'Wyszukaj':
                    return i
        except:
            printExc('getSearchItemInx EXCEPTION')
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
            printExc('setSearchPattern EXCEPTION')
            self.searchPattern = ''
            self.searchType = ''
        return



    
