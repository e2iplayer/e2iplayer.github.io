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
config.plugins.iptvplayer.cda_searchsort = ConfigSelection(default = "best", choices = [("best", _("Najtrafniejsze")), ("date", _("Najnowsze")), ("rate", _("Najlepiej oceniane")), ("alf", _("Alfabetycznie"))])

def GetConfigList():
    optionList = []
    optionList.append( getConfigListEntry( _("Sortuj wyniki wyszukiwania po:"), config.plugins.iptvplayer.cda_searchsort ) )
    return optionList
###################################################

def gettytul():
    return 'cda.pl'

class cda(CBaseHostClass):
    MAINURL  = 'http://www.cda.pl/'
    SEARCH_URL = MAINURL + 'video/show/%s/p%d?s=%s'
    CATEGORIES_TAB = [{'url' : '',       'title' : '--Wszystkie--'}, 
                      {'url' : '/kat26', 'title' : 'Krótkie filmy i animacje'}, 
                      {'url' : '/kat24', 'title' : 'Filmy Extremalne'}, 
                      {'url' : '/kat27', 'title' : 'Motoryzacja, wypadki'}, 
                      {'url' : '/kat28', 'title' : 'Muzyka'}, 
                      {'url' : '/kat29', 'title' : 'Prosto z Polski'}, 
                      {'url' : '/kat30', 'title' : 'Rozrywka'}, 
                      {'url' : '/kat31', 'title' : 'Sport'}, 
                      {'url' : '/kat32', 'title' : 'Śmieszne filmy'}, 
                      {'url' : '/kat33', 'title' : 'Różności'}, 
                      {'url' : '/kat34', 'title' : 'Życie studenckie'} ] 
    
    def __init__(self):
        printDBG("cda.__init__")
        CBaseHostClass.__init__(self, {'history':'cda.pl'})
    
    def listsMainMenu(self):
        printDBG("cda.listsMainMenu")
        self.addDir({'name':'category', 'title':'Główna',                'category':'categories', 'url' : 'video'})
        self.addDir({'name':'category', 'title':'Poczekalnia',           'category':'categories', 'url' : 'video/poczekalnia'})
        self.addDir({'name':'category', 'title':'Wyszukaj',              'category':'Wyszukaj'})
        self.addDir({'name':'category', 'title':'Historia wyszukiwania', 'category':'Historia wyszukiwania'})
        
    def listCategories(self, cItem):
        printDBG("cda.listCategories cItem[%s]" % cItem)
        for item in cda.CATEGORIES_TAB:
            item = dict(item)
            item['name']     = cItem['name']
            item['category'] = 'category'
            item['url']      = cItem['url'] + item['url']
            self.addDir(item)
            
    def listCategory(self, cItem):
        printDBG("cda.listCategory cItem[%s]" % cItem)
        page = cItem.get('page', 1)
        url = cda.MAINURL + cItem['url'] + ('/p%d' % page)
        self.listItems(cItem, url, page)
        
    def listSearchResult(self, cItem, searchPattern):
        printDBG("cda.listSearchResult cItem[%s], searchPattern[%s]" % (cItem, searchPattern))
        searchsort = config.plugins.iptvplayer.cda_searchsort.value
        page = cItem.get('page', 1)
        url  = cda.SEARCH_URL % (searchPattern.replace(' ', '_'), page, searchsort)
        tmpItem = dict(cItem)
        tmpItem.update({'category' : 'search_next_page', 'search_pattern':searchPattern})
        self.listItems(tmpItem, url, page, True)
        
    def listItems(self, cItem, url, page, search=False):
        sts, data = self.cm.getPage(url)
        if sts:
            if 'Następna strona' in data:
                nextPage = True
            else:
                nextPage = False
            if search:
                data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="thumbElem video', '<div class="clear"></div>', False)[1]
                data = data.split('<div class="thumbElem video')
            elif 'poczekalnia' in url:
                data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="videoInfo">', '<div class="bottom" id="dolny_pasek">', False)[1]
                data = data.split('<div class="videoInfo">')                
            else:
                data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="rowElem">', '<div class="clear"></div>', False)[1]
                data = data.split('</label>')
                
            for item in data:
                desc1   = self.cleanHtmlStr( self.cm.ph.getDataBeetwenReMarkers(item, re.compile('''<span class=["']timeElem[^>]*?>'''), re.compile('</span>'), False)[1] )
                desc2  = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<label  title="', '"', False)[1] )
                if '' == desc2: desc2   = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<img  title="', '"', False)[1] )
                desc = desc1 + ' | ' + desc2
                
                title  = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<div class="text">', '</div>', False)[1] )
                if '' == title: title  = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<span style="color: #B82D2D; font-size: 14px">', '</a>', False)[1] )
                if '' == title: title  = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, 'alt="', '"', False)[1] )
                url    = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, 'href="', '"', False)[1] )
                icon   = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, 'src="', '"', False)[1] )
                if url.startswith('/video'):
                    url = self.MAINURL + url
                    self.addVideo({'title':title, 'url':url, 'icon':icon, 'desc':desc})
                
            if nextPage:
                nextPage = dict(cItem)
                nextPage.update({'title':'Następna strona', 'page':page+1})
                self.addDir(nextPage)
        
    def getLinksForVideo(self, cItem):
        printDBG("cda.getLinksForVideo [%s]" % cItem['url'])
        return self.up.getVideoLinkExt(cItem['url'])
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.up.getVideoLinkExt(fav_data)
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('cda.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "cda.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = []
        
        if None == name:
            self.listsMainMenu()
    #KATEGORIE
        if 'categories' == category:
            self.listCategories(self.currItem)
    #KATEGORIA
        if 'category' == category:
            self.listCategory(self.currItem)
    #WYSZUKAJ
        elif category in ["Wyszukaj", "search_next_page"]:
            self.listSearchResult(self.currItem, searchPattern)
    #HISTORIA WYSZUKIWANIA
        elif category == "Historia wyszukiwania":
            self.listsHistory()
        
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, cda(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('cdapllogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): RetHost(retCode, value=retlist)

        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo

    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
    
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
        description =  clean_html(cItem.get('desc', ''))
        icon        =  cItem.get('icon', '')
        
        return CDisplayListItem(name = title,
                                    description = description,
                                    type = type,
                                    urlItems = hostLinks,
                                    urlSeparateRequest = 1,
                                    iconimage = icon,
                                    possibleTypesOfSearch = possibleTypesOfSearch)
    # end converItem

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
