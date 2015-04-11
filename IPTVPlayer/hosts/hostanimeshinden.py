# -*- coding: utf-8 -*-
# Based on (root)/trunk/xbmc-addons/src/plugin.video.polishtv.live/self.HOSTs/ @ 419 - Wersja 636

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, CSelOneLink, GetLogoDir
import Plugins.Extensions.IPTVPlayer.libs.pCommon as pCommon
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
###################################################

###################################################
# FOREIGN import
###################################################
from time import sleep
import re
from urllib import quote_plus
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################

###################################################
# Config options for HOST
###################################################
# None

def GetConfigList():
    optionList = []
    # None
    return optionList
###################################################

def gettytul():
    return 'Anime-Shinden'

class AnimeShinden(CBaseHostClass):
    MAINURL = 'http://shinden.pl/'
    ANIME_LIST_URL = MAINURL+'anime?'
    TOP_LIST_URL = MAINURL+'anime/top?'
    MAIN_CAT_TAB = [{ 'category':'list_filters',          'title':'Filtruj'              },
                    { 'category':'top',                   'title':'Top'                  },
                    { 'category':'Wyszukaj',              'title':'Wyszukaj'             },
                    { 'category':'Historia wyszukiwania', 'title':'Historia wyszukiwania'} ]
    
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'shinden.pl', 'cookie':'shinden.cookie'})
        self.genresData = {}
        self.genres = []
        
    def _getFullUrl(self, url):
        if 0 < len(url) and not url.startswith('http'):
            url =  self.MAINURL + url
        return url
        
    def _fillGenres(self):
        printDBG('AnimeShinden._fillGenres start')
        sts, data = self.cm.getPage(AnimeShinden.ANIME_LIST_URL)
        if not sts: return 
        data = self.cm.ph.getDataBeetwenMarkers(data, '<section class="search-section">', '</section>', False)[1]
        
        markers = self.cm.ph.getDataBeetwenMarkers(data, '<ul ', '</ul>', False)[1]
        markers = re.compile('id="go([^"]+?)">([^<]+?)<').findall(markers)
        for item in markers:
            if 'Tabtag' == item[0]: break
            filters = []
            genData = self.cm.ph.getDataBeetwenMarkers(data, 'id="%s">' % item[0], '</ul>', False)[1]
            if 'genre-item' in genData:
                genData = genData.split('<li>')
                if len(genData): del genData[0]
                for gen in genData:
                    title  = self.cleanHtmlStr(gen)
                    filter = self.cm.ph.getSearchGroups(gen, 'data-id[ ]*?=[ ]*?"([0-9]+?)"')[0]
                    filters.append({'title':title, 'url':'genres=e%%3Bi%s&genres-type=one' % filter})
            else:
                genData = re.compile('href="\?([^"]+?)"[^>]*?>([^<]+?)<').findall(genData)
                for gen in genData: filters.append({'title':gen[1], 'url':gen[0]})
            if len(filters): 
                self.genres.append(item[1])
                self.genresData[item[1]] = filters
            else: printExc("_fillGenres error for [%s]" % item[1])
    
    def listFilters(self, category):
        if 0 == len(self.genres): self._fillGenres()
        for item in self.genres:
            self.addDir( {'name':'category', 'category':category, 'title':item} )
            
    def listsFiltersValues(self, cItem, category):
        printDBG('AnimeShinden.listsFiltersValues')
        for item in self.genresData.get(cItem['title'], []):
            params = dict(cItem)
            params.update( item )
            params['category'] = category
            self.addDir( params )
            
    def listAnimes(self, cItem, category, baseUrl):
        printDBG('AnimeShinden.listAnimes')
        page = cItem.get('page', 1)
        sts, data = self.cm.getPage(baseUrl + ( 'page=%d&%s' % (page, cItem.get('url', '')) ))
        if not sts: return
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<li class="pagination-next">', '</li>', False)[1]
        if '<a href="' in tmp: nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<table ', '</table>', False)[1]
        data = data.split('<tr>')
        if len(data): del data[0]
        for item in data:
            item = item.split('</h3>')
            if 2 > len(item): continue
            tmp = self.cm.ph.getSearchGroups(item[0], 'href="([^"]+?)"[^>]*?>(.+?)</a>', 2)
            icon = self._getFullUrl( self.cm.ph.getSearchGroups(item[0], 'src="([^"]+?)"')[0] )
            params = {'name':'category', 'category':category, 'title':self.cleanHtmlStr(tmp[1]), 'url':tmp[0], 'icon':icon, 'desc':self.cleanHtmlStr(item[1])}
            self.addDir(params)
            
        if nextPage:
            params = dict(cItem)
            params.update({'title':_('Następna strona'), 'page':page+1})
            self.addDir(params)
            
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("AnimeShinden.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        url = 'type=contains&search=' + quote_plus(searchPattern)
        params = dict(cItem)
        params.update({'category':'list_animes', 'url':url})
        self.listAnimes(params, 'list_episodes', AnimeShinden.ANIME_LIST_URL)
            
    def listItems(self, cItem):
        printDBG('AnimeShinden.listItems')
        url = self._getFullUrl( cItem['url'] ) + '/episodes'
        sts, data = self.cm.getPage(url)
        if not sts: return 
        data = self.cm.ph.getDataBeetwenMarkers(data, '<tbody class="list-episode-checkboxes">', '</tbody>', False)[1]
        data = data.split('</tr>')
        if len(data): del data[-1]
        for item in data:
            params = dict(cItem)
            url = self._getFullUrl( self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0] )
            title = self.cleanHtmlStr(item)
            if 'class="fa fa-fw fa-check"' not in item: title = title.replace('Zobacz', 'niedostępny')
            else: title = title.replace('Zobacz', 'zbobacz')
            params.update({'title':title, 'url':url})
            self.addVideo(params)
        
    def getLinksForVideo(self, cItem):
        printDBG('AnimeShinden.listItems url[%s]' % cItem['url'])
        urlsTab = []
        
        url = self._getFullUrl( cItem['url'] )
        sts, data = self.cm.getPage(url)
        if not sts: return urlsTab
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<table class=" data-view-table-big">', ' </table>', False)[1]
        data = data.split('</thead>')
        if 2 > len(data): return urlsTab
        headers =  re.compile('<th>(.+?)</th>').findall(data[0])
        data = data[1].split('</tr>')
        if len(data): del data[-1]
        for item in data:
            titles = re.compile('<td[^>]*?>(.+?)</td>').findall(item)
            title = ''
            if len(headers) > len(titles): num = len(titles)
            else: num = len(headers)
            for idx in range(num):
                title += '%s %s, ' % (headers[idx], titles[idx])
            if '' != title: title = title[:-2]
            onlineId = self.cm.ph.getSearchGroups(item, '"online_id":"([0-9]+?)"')[0]
            urlsTab.append({'name': title, 'url':onlineId, 'need_resolve':1})
        return urlsTab
        
    def getVideoLinks(self, onlineId):
        printDBG('AnimeShinden.listItems onlineId[%s]' % onlineId)
        urlsTab = []
        url = AnimeShinden.MAINURL+'xhr/%s/player_load' % onlineId
        sts, data = self.cm.getPage(url, {'cookiefile':self.COOKIE_FILE, 'use_cookie': True, 'save_cookie':True})
        if not sts: return urlsTab
        try: sleep(int(data)+1)
        except: printExc()
        url = AnimeShinden.MAINURL+'xhr/%s/player_show' % onlineId
        sts, data = self.cm.getPage(url, {'cookiefile':self.COOKIE_FILE, 'use_cookie': True, 'load_cookie':True})
        if not sts: return linksTab
        printDBG(data)
        if '<embed src="http://player.shinden.pl' in data:
            data = re.compile('<embed [^>]+?>').findall(data)
            for idx in range(len(data)):
                urls = re.compile('file=(http[^>]+?&amp;)').findall(data[idx])
                for url in urls: 
                    if '/hd.' in url: title = 'hd'
                    else: title = 'sd'
                    urlsTab.append({'name': 'Część %d, kopia %s' % (idx+1, title), 'url':url})
        else:
            url = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
            urlsTab = self.up.getVideoLinkExt(url) 
        return urlsTab
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('AnimeShinden.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "AnimeShinden.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = []
        
        if None == name:
            self.listsTab(AnimeShinden.MAIN_CAT_TAB, {'name':'category'})
        elif  'list_filters' == category: 
            self.listFilters('list_filter_values')
        elif 'list_filter_values' == category:
            self.listsFiltersValues(self.currItem, 'list_animes')
        elif 'list_animes' == category:
            self.listAnimes(self.currItem, 'list_episodes', AnimeShinden.ANIME_LIST_URL)
        elif 'top' == category:
            self.listAnimes(self.currItem, 'list_episodes', AnimeShinden.TOP_LIST_URL)
        elif 'list_episodes' == category:
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
        elif category in ["Wyszukaj"]:
            self.listSearchResult(self.currItem, searchPattern, searchType)
    #HISTORIA WYSZUKIWANIA
        elif category == "Historia wyszukiwania":
            self.listsHistory()
        else:
            printExc()

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, AnimeShinden(), True)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('animeodcinkilogo.png')])

    def getLinksForVideo(self, Index=0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            need_resolve = 1
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
    def getResolvedURL(self, url):
        # resolve url to get direct url to video file
        retlist = []
        urlList = self.host.getVideoLinks(url)
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)

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
            else: type = CDisplayListItem.TYPE_CATEGORY
        elif cItem['type'] == 'video':
            type = CDisplayListItem.TYPE_VIDEO
            url = cItem.get('url', '')
            if '' != url: hostLinks.append(CUrlItem("Link", url, 1))
            
        title       =  cItem.get('title', '')
        description =  clean_html(cItem.get('desc', '')) + clean_html(cItem.get('plot', ''))
        icon        =  cItem.get('icon', '')
        
        return CDisplayListItem(name = title,
                                    description = description,
                                    type = type,
                                    urlItems = hostLinks,
                                    urlSeparateRequest = 1,
                                    iconimage = icon,
                                    possibleTypesOfSearch = possibleTypesOfSearch)

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

