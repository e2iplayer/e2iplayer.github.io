# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
import time
import base64
try:
    import json
except:
    import simplejson as json
###################################################


###################################################
# Config options for HOST
###################################################

def GetConfigList():
    optionList = []
    return optionList
###################################################

def gettytul():
    return 'SeansikTV'

class SeansikTV(CBaseHostClass):
    MAINURL = 'http://seansik.tv'
    DEFAULT_ICON = MAINURL + '/st/img/cover/average.png'
    
    SORT_TAB = [
        {'title': "Nowo dodane",       'url':"/act/list?type=%s&sort=new&order=desc"},
        {'title': "Alfabetycznie"  ,   'url':"/act/list?type=%s&sort=title&order=asc"},
        {'title': "Najpopularniejsze", 'url':"/act/list?type=%s&sort=popular&order=desc"},
        {'title': "Najwyżej ocenione", 'url':"/act/list?type=%s&sort=vote&order=desc"},
    ]

    MAIN_TAB = [
        {'category':"films",           'title': "Filmy",  'url':'film'},
        {'category':"series",          'title': "Seriale",'url':'series'},
        {'category':"animes",          'title': "Anime",  'url':'anime'},
        {'category':'search',          'title':_('Search'), 'search_item':True},
        {'category':'search_history',  'title':_('Search history')}
    ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'SeansikTV'})
        self.linksCacheCache = {}
    
    def _getStr(self, v, default=''):
        return clean_html(self._encodeStr(v, default))
        
    def _encodeStr(self, v, default=''):
        if type(v) == type(u''): return v.encode('utf-8')
        elif type(v) == type(''): return v
        else: return default
    
    def _getFullUrl(self, url):
        if 0 < len(url) and not url.startswith('http'):
            url =  self.MAINURL + url
        return url
        
    def _listsTab(self, tab, cItem):
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            self.addDir(params)
            
    def _addPage(self, url, page):
        if len(url) and url[-1] not in ['&', '?']: 
            if '?' in url: url = url + "&"
            else:          url = url + "?"        
        return self._getFullUrl( url + ("page=%d" % page) )
        
    def addSortParam(self, cItem, category):
        for item in SeansikTV.SORT_TAB:
            params = dict(cItem)
            params['title']    = item['title'] 
            params['url']      = item['url'] % params['url']
            params['category'] = category
            params['name']     = 'category'
            self.addDir(params)
            
    def listCategories(self, cItem, category, filter='categories'):
        printDBG("SeansikTV.listCategories")
        baseUrl = self._getFullUrl( cItem['url'] )
        sts, data = self.cm.getPage( baseUrl )
        if False == sts: return
        
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, '<li onclick="selectBox(this)" name="%s">' % filter, '</ul>', True)
        data = re.compile('<input[^>]+?value="([0-9]+?)"[^>]+?/>([^<]+?)<').findall(data)
        if len(data):
            params = {'name':'category', 'category':category, 'title':'--Wszystkie--', 'url':baseUrl}
            self.addDir(params) 
        for item in data:
            url = baseUrl + ('&%s=%s' % (filter, item[0]) )
            params = {'name':'category', 'category':category, 'title':item[1].strip(), 'url':url}
            self.addDir(params) 
            
            
    def listItems(self, cItem, category):
        printDBG("SeansikTV.listItems")

        page = cItem.get('page', 1)
        url = self._addPage( cItem.get('url'), page)
        sts, data = self.cm.getPage( url )
        if False == sts: return
        
        # check next page
        netxtPage = CParsingHelper.getDataBeetwenMarkers(data, '<b class="active">%d</b>' % page, '</div>', False)[1]
        if 'page' in netxtPage: 
            netxtPage = True
            page += 1
        else: netxtPage = False

        sts, data = CParsingHelper.getDataBeetwenMarkers(data, '<div class="content table-sofi', '<div class="content">', False)
        data = data.split('<div class="content table-sofi')
        for item in data:
            icon = self._getFullUrl( CParsingHelper.getSearchGroups(item, 'src="([^"]+?jpg)"')[0] )
            
            sts, tmp = CParsingHelper.getDataBeetwenReMarkers(item, re.compile('<td colspan="2"[^>]+?>'), re.compile('</td>'), False)
            url = self._getFullUrl( CParsingHelper.getSearchGroups(tmp, 'href="([^"]+?)"')[0] )
            tmp = tmp.split('</a>')
            title = self.cleanHtmlStr(tmp[0])
            if 0 < len(tmp): desc  = self.cleanHtmlStr(tmp[-1])
            # validate data
            if '' == url or '' == title: continue
            params = {'name':'category', 'category':category, 'title':title, 'url':url, 'icon':icon, 'desc':desc}
            if 'video' != category: self.addDir(params)
            else: self.addVideo(params)
        if netxtPage:
            params = dict(cItem)
            params.update({'title':'Następna strona', 'page':page})
            self.addDir(params)
            
    def listItems2(self, cItem, category):
        printDBG("SeansikTV.listItems2")
        self.listItems(cItem, category)
        return
        
        page = cItem.get('page', 1)
        url = self._addPage( cItem.get('url'), page)
        sts, data = self.cm.getPage( url )
        if False == sts: return
        
        netxtPage = False
        if ">&raquo;</a>" in data:
            page = page+1
            netxtPage = True
        
        marker = '<tr class="tdb_'
        data = CParsingHelper.getDataBeetwenMarkers(data, marker, '<div class="content">', False)[1]
        data = data.split(marker)
        for item in data:
            url   = self._getFullUrl( CParsingHelper.getSearchGroups(item, 'href="([^"]+?)"')[0] )
            title = self.cleanHtmlStr( CParsingHelper.getDataBeetwenMarkers(item, 'title">', '</td>', False)[1] )
            desc  = self.cleanHtmlStr( marker + item )
            # validate data
            if '' == url or '' == title: continue
            params = {'name':'category', 'category':category, 'title':title, 'url':url, 'desc':desc}
            self.addDir(params)
        if netxtPage:
            params = dict(cItem)
            params.update({'title':'Następna strona', 'page':page})
            self.addDir(params)
                
    def listSeasons(self, cItem, category):
        printDBG("SeansikTV.listSeasons")
        url = self._getFullUrl(cItem['url'])
        sts, data = self.cm.getPage( url )
        if False == sts: return
        icon = self._getFullUrl( CParsingHelper.getSearchGroups(data, 'href="([^"]+?\.jpg)" rel="image_src"')[0] )
        data = CParsingHelper.getDataBeetwenMarkers(data, '<div class="jump">', '</div>', False)[1]
        data = re.findall('<a href="#([^"]+?)">([^<]+?)</a>', data)
        for item in data:
            params = dict(cItem)
            params.update({'category':category, 'season':item[0], 'title':item[1], 'icon':icon})
            self.addDir(params)
        if 0 == len(self.currList):
            cItem.update({'season':'season1', 'category':category, 'icon':icon})
            self.listEpisodes(cItem)
    
    def listEpisodes(self, cItem):
        printDBG("SeansikTV.listEpisodes")
        url = self._getFullUrl(cItem['url'])
        sts, data = self.cm.getPage( url )
        if False == sts: return
        data = CParsingHelper.getDataBeetwenMarkers(data, 'id="%s"' % cItem['season'], '</table>', False)[1]
        marker = '<tr itemprop="episode"'
        data = data.split(marker)
        if len(data): del data[0]
        for item in data:
            if 'cross_add gray' in item:
                url   = self._getFullUrl( CParsingHelper.getSearchGroups(item, 'href="([^"]+?)"')[0] )
                title = self.cleanHtmlStr( CParsingHelper.getDataBeetwenMarkers(item, '</td>', '</td>', False)[1] )
                desc  = self.cleanHtmlStr( item.split('</b>')[1] )
                # validate data
                if '' == url or '' == title: continue
                params = dict(cItem)
                params.update({'title':title, 'url':url, 'desc':desc})
                self.addVideo(params)
                
    def getHostingTable(self, urlItem):
        printDBG("SeansikTV.getHostingTable")
        # use cache if possible
        if 0 < len( self.linksCacheCache.get('tab', []) ) and (urlItem['url'] + urlItem.get('ver', '')) == self.linksCacheCache.get('marker', None):
            return self.linksCacheCache['tab']
        hostingTab = []

        sts, data = self.cm.getPage( self._getFullUrl( urlItem['url'] ) )
        if not sts: return hostingTab
        
        long_hashes  = CParsingHelper.getSearchGroups(data, '_sasa[ ]*?=[ ]*?{([^}]+?)}')[0]
        short_hashes = CParsingHelper.getDataBeetwenMarkers(data, '<div id="translation_', '<div class="content"', False)[1]
        #printDBG("long_hashes[%s]" % long_hashes)
        #printDBG("short_hashes[%s]" % short_hashes)
        
        marker = '<h3 class="brb"'
        data = CParsingHelper.getDataBeetwenMarkers(data, marker, '<div id="boxShow">', False)[1]
        data = data.split(marker)
        for item in data:
            embed_id    = CParsingHelper.getSearchGroups(item, 'id="embedTitle_([0-9]+?)">')[0]
            if '' == embed_id: continue
            quality     = CParsingHelper.getDataBeetwenMarkers(item, '<span class="f-left">', '</span>', False)[1]
            hosting     = CParsingHelper.getDataBeetwenMarkers(item, '<b>', '</b>', False)[1].strip()
            translation = CParsingHelper.getDataBeetwenMarkers(item, 'align="rigth">', '</span>', False)[1].strip()
            
            title  = CParsingHelper.removeDoubles(translation + ': ' + hosting + ' ' + quality, ' ')
            if len(embed_id):
                # get embed hash
                short_hash = CParsingHelper.getSearchGroups(short_hashes, '''<div onclick="frame\('([^']+?)', this, event\);" data-id="%s"''' % embed_id)[0]
                if '' == short_hash: short_hash = CParsingHelper.getSearchGroups(short_hashes, '<div data-vid_key="([^"]+?)".+?data-id="%s"' % embed_id)[0]
                #printDBG("embed_id[%s] short_hash[%s]" % (embed_id, short_hash))
                if '' == short_hash: continue
                long_hash = CParsingHelper.getSearchGroups(long_hashes, '"%s":"([^"]+?)"' % short_hash)[0]
                if '' == long_hash: continue
                try:
                    url = base64.b64decode(long_hash)
                    if 'src=' in url:
                        url = CParsingHelper.getSearchGroups(url, 'src="([^"]+?)"')[0]
                    printDBG("======================================= [%s]" % url)
                    #if 1 != self.up.checkHostSupport('http://' + hosting + '/'):
                    #    continue
                except:
                    continue
                #if url.startswith('http'):
                hostingTab.append({'name':title, 'url':strwithmeta(self.cleanHtmlStr(url), {'hosting':hosting}), 'need_resolve':1})
        self.linksCacheCache = {'marker': urlItem['url'], 'tab': hostingTab}
        return hostingTab
                
    def getVideoLinks(self, url):
        printDBG("SeansikTV.getVideoLinks url[%r]" % url)
        if not isinstance(url, strwithmeta): return []
        hosting = url.meta.get('hosting', '')
        if 'flowplayer' == hosting: return [{'name':'flowplayer', 'url':url}]
        return self.up.getVideoLinkExt( url )
       
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):

        return self.getHostingTable({'url':fav_data})

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        
        # clear hosting tab cache
        self.linksCacheCache = {}

        name     = self.currItem.get("name", '')

        category = self.currItem.get("category", '')
        action   = self.currItem.get("action", '')
        sub_cat  = self.currItem.get("sub_cat", '')
        page     = self.currItem.get("page", '1')
        icon     = self.currItem.get("icon", '')
        url      = self.currItem.get("url", '')
        plot     = self.currItem.get("plot", '')
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self._listsTab(SeansikTV.MAIN_TAB, {'name':'category'})
    #FILMY
        elif category == "films":
            self.addSortParam(self.currItem, 'list_films_categories')
    #FILMS ITEMS
        elif category == 'list_films_items':
            self.listItems(self.currItem, 'video')
    #FILMS CATEGORIES
        elif category == 'list_films_categories':
            self.listCategories(self.currItem, 'list_films_items')
    #SERIES
        elif category == "series":
            self.addSortParam(self.currItem, 'list_series_categories')
    #LIST SERIES ITEMS
        elif category == "list_series_items_1":
            self.listItems2(self.currItem, 'series_seasons')
        elif category == "list_series_items":
            self.listItems(self.currItem, 'series_seasons')
    #SERIES CATEGORIES
        elif category == "list_series_categories":
            self.listCategories(self.currItem, 'list_series_items_1')
    #LIST SERIES SEASONS
        elif category == "series_seasons":
            self.listSeasons(self.currItem, 'series_episodes')
    #LIST SERIES EPISODES
        elif category == "series_episodes":
            self.listEpisodes(self.currItem)
    #ANIMES
        elif category == "animes":
            self.addSortParam(self.currItem, 'list_anime_categories')
        elif category == "list_anime_categories":
            self.listCategories(self.currItem, 'list_anime_categories_1')
        elif category == "list_anime_categories_1":
            self.listCategories(self.currItem, 'list_series_items_1', 'audience_type')
    #WYSZUKAJ
        elif category == "search":
            printDBG("Wyszukaj: " + searchType)
            pattern = urllib.quote_plus(searchPattern)
            params = {'name':'category'}
            if 'filmy' == searchType:
                params.update({'url':'/act/list?type=film&title=' + pattern, 'category':'list_films_items'})
                self.listItems(params, 'video')
            elif 'seriale' == searchType:
                params.update({'url':'/act/list?type=series&title=' + pattern, 'category':'list_series_items'})
                self.listItems2(params, 'series_seasons')
            elif 'anime' == searchType:
                params.update({'url':'/act/list?type=anime&title=' + pattern, 'category':'list_series_items'})
                self.listItems2(params, 'series_seasons')
            
    #HISTORIA WYSZUKIWANIA
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))


class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, SeansikTV(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('seansiktvlogo.png')])

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
        retlist = []
        urlList = self.host.getVideoLinks(url)
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)

    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        searchTypesOptions.append(("Filmy",  "filmy"))
        searchTypesOptions.append(("Seriale","seriale"))
        searchTypesOptions.append(("Anime",  "anime"))
    
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
            
        title       =  self.host._getStr( cItem.get('title', '') )
        description =  self.host._getStr( cItem.get('desc', '') ).strip()
        icon        =  self.host._getStr( cItem.get('icon', '') )
        if '' == icon: icon = SeansikTV.DEFAULT_ICON
        
        return CDisplayListItem(name = title,
                                description = description,
                                type = type,
                                urlItems = hostLinks,
                                urlSeparateRequest = 1,
                                iconimage = icon,
                                possibleTypesOfSearch = possibleTypesOfSearch)
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