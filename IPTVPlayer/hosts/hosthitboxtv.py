# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
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
config.plugins.iptvplayer.hitbox_iconssize = ConfigSelection(default = "medium", choices = [ ("large", _("large")), ("medium", _("medium")), ("small", _("small")) ])

def GetConfigList():
    optionList = []
    return optionList
###################################################

def gettytul():
    return 'hitbox.tv'

class Hitbox(CBaseHostClass):
    NUM_OF_ITEMS = 20
    STATIC_URL = 'http://edge.sf.hitbox.tv/'
    MAIN_URL   = 'http://api.hitbox.tv/'
    MAIN_URLS  = 'https://api.hitbox.tv/'

    MAIN_CAT_TAB = [{'category':'games_list',     'title':_('Games played Now'), 'url': MAIN_URL+'api/games?fast=true&limit=%s&media=true&offset=%s&size=list&liveonly=true'},
                    {'category':'media',          'title':_('Live'),   'url':MAIN_URL+'api/media/live/list?filter=popular&game=0&hiddenOnly=false&showHidden=true&fast=true&limit=%s&media=true&offset=%s&size=list&liveonly=true'},
                    {'category':'media',          'title':_('Videos'), 'url':MAIN_URL+'api/media/video/list?filter=weekly&follower_id=&game=0&fast=true&limit=%s&media=true&offset=%s&size=list'},
                    {'category':'search',         'title':_('Search'), 'search_item':True},
                    {'category':'search_history', 'title':_('Search history')} ]
                    
    GAME_CAT_TAB = [{'category':'media',  'title':_('Live Channels'), 'url':'live' },
                    {'category':'media',  'title':_('Videos'),        'url':'video'} ]
    
    def __init__(self):
        printDBG("Hitbox.__init__")
        CBaseHostClass.__init__(self, {'history':'Hitbox.tv'})
        
    def _getFullUrl(self, url, baseUrl=None):
        if None == baseUrl: baseUrl = Hitbox.MAIN_URL
        if 0 < len(url) and not url.startswith('http'):
            url =  baseUrl + url
        return url
        
    def _getStr(self, v, default=''):
        if isinstance(v, str): return v
        elif isinstance(v, list): return '%r' % v
        else: return default
            
    def _getCategoryBaseParams(self, item):
        params = {}
        params['title'] = self._getStr( item.get("category_name") )
        if '' == params['title']: params['title'] = self._getStr( item.get("category_name_short") )
        params['icon'] = self._getFullUrl( self._getStr( item.get("category_logo_small") ), Hitbox.STATIC_URL )
        if '' == params['icon']: params['icon'] = self._getFullUrl( self._getStr( item.get("category_logo_large") ), Hitbox.STATIC_URL )
        params['desc'] = ''
        for tmp in [('category_viewers', _('viewers: ')), ('category_media_count', _('media count: ')), ('category_updated', _('updated: '))]:
            desc = self._getStr( item.get(tmp[0]) )
            if '' != desc: params['desc'] += ('%s %s, ' % (tmp[1], desc))
        if '' != params['desc']: params['desc'] = params['desc'][:-2]
        return params
        
    def _getLiveStreamsBaseParams(self, item):
        params = {}
        params['title'] = '%s (%s)' % ( self._getStr( item.get("media_display_name") ), self._getStr( item.get("media_status") ))
        params['icon'] = self._getFullUrl( self._getStr( item.get("media_thumbnail") ), Hitbox.STATIC_URL )
        if '' == params['icon']: params['icon'] = self._getFullUrl( self._getStr( item.get("media_thumbnail_large") ), Hitbox.STATIC_URL )
        if '' == params['icon']: params['icon'] = self._getFullUrl( self._getStr( item.get("user_logo_small") ), Hitbox.STATIC_URL )
        if '' == params['icon']: params['icon'] = self._getFullUrl( self._getStr( item.get("user_logo") ), Hitbox.STATIC_URL )
        if '' == params['icon']: params['icon'] = self._getFullUrl( self._getStr( item.get('channel', {}).get("user_logo_small") ), Hitbox.STATIC_URL )
        if '' == params['icon']: params['icon'] = self._getFullUrl( self._getStr( item.get('channel', {}).get("user_logo") ), Hitbox.STATIC_URL )
        params['desc'] = ''
        for tmp in [('media_views', _('views: ')), ('media_countries', _('countries: ')), ('media_live_since', _('live since: '))]:
            desc = self._getStr( item.get(tmp[0]) )
            if '' != desc: params['desc'] += ('%s %s, ' % (tmp[1], desc))
        if '' != params['desc']: params['desc'] = params['desc'][:-2]
        return params
            
    def listGames(self, cItem, category):
        printDBG("Hitbox.listGames")
        page = cItem.get('page', 0)
        sts, data = self.cm.getPage(cItem['url'] % (Hitbox.NUM_OF_ITEMS, page*Hitbox.NUM_OF_ITEMS) )
        if not sts: return 
        try:
            data = byteify(json.loads(data))["categories"]
            for item in data:
                params = dict(cItem)
                params['url'] =  item['category_id']
                params['category'] = category
                params.update( self._getCategoryBaseParams(item) )
                #params['seo_key'] = item['category_seo_key']
                self.addDir(params)
            # check next page
            sts, data = self.cm.getPage(cItem['url'] % (1, (page+1)*Hitbox.NUM_OF_ITEMS) )
            if not sts: return 
            if len(json.loads(data)["categories"]):
                params = dict(cItem)
                params.update( {'title':_('Next page'), 'page':page+1} )
                self.addDir(params)
        except: printExc()
        
    def listGamesTab(self, cItem, category=''):
        printDBG("Hitbox.listGamesTab")
        for item in Hitbox.GAME_CAT_TAB:
            params = dict(cItem)
            params['title'] = item['title']
            params['category'] = item['category']
            params['url'] = Hitbox.MAIN_URL+'api/media/'+item['url']+'/list?fast=true&filter=&media=true&size=list&game='+cItem['url']+'&limit=%s&offset=%s'
            self.addDir(params)
        
    def listMedia(self, cItem):
        printDBG("Hitbox.listMedia")
        page = cItem.get('page', 0)
        sts, data = self.cm.getPage(cItem['url'] % (Hitbox.NUM_OF_ITEMS, page*Hitbox.NUM_OF_ITEMS) )
        if not sts: return 
        try:
            data = byteify(json.loads(data))
            if 'live' == data['media_type']: key = 'livestream'
            elif 'video' == data['media_type']: key = 'video'
            else:
                printExc("Uknown type [%s]" % data['media_type'])
                return
                
            data = data[key]
            for item in data:
                params = dict(cItem)
                params.update( self._getLiveStreamsBaseParams(item) )
                if key == 'video': params['media_id'] = item['media_id']
                else: params['channel_link'] = item['channel']['channel_link']
                self.addVideo(params)
            # check next page
            sts, data = self.cm.getPage(cItem['url'] % (1, (page+1)*Hitbox.NUM_OF_ITEMS) )
            if not sts: return 
            if len(json.loads(data)[key]):
                params = dict(cItem)
                params.update( {'title':_('Next page'), 'page':page+1} )
                self.addDir(params)
        except: printExc()

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("Hitbox.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        searchPattern = urllib.quote_plus(searchPattern)
        item = dict(cItem)
        item['category'] = 'media'
        item['url'] = Hitbox.MAIN_URLS+'api/media/'+searchType+'/list?filter=popular&media=true&search='+searchPattern+'&limit=%s&media=true&start=%s&size=list'
        if 'live' == searchType: item['url'] += '&liveonly=true'
        self.listMedia(item)
    
    def getLinksForVideo(self, cItem):
        printDBG("Hitbox.getLinksForVideo [%s]" % cItem)
        urlTab = []
        url = ''
        if 'channel_link' in cItem:
            url = Hitbox.MAIN_URL + 'player/hls/%s.m3u8' % cItem['channel_link'].split('/')[-1]
            '''
            url = Hitbox.MAIN_URL + 'api/media/live/%s?showHidden=true' % cItem['channel_link'].split('/')[-1]
            sts, data = self.cm.getPage(url)
            if not sts: return urlTab
            try:
                data = byteify( json.loads(data) )
                channelData = data['livestream'][0]
                url = Hitbox.MAIN_URL +  'api/player/config/live/%s?embed=false&showHidden=true' % 
                
                
                url = Hitbox.LIVE_URL % (cItem['channel'], urllib.quote(self._getStr(data['token'])), self._getStr(data['sig']))
                data = getDirectM3U8Playlist(url, checkExt=False)
                for item in data:
                    item['url'] = urlparser.decorateUrl(item['url'], {'iptv_block_exteplayer':True, 'iptv_proto':'m3u8', 'iptv_livestream':True})
                    urlTab.append(item)
            except: printExc()
            '''
        elif 'media_id' in cItem:
            sts, data = self.cm.getPage( Hitbox.MAIN_URL + 'api/player/config/video/%s?redis=true&embed=false&qos=false&redis=true&showHidden=true' % cItem['media_id'] )
            if sts:
                try:
                    data = byteify( json.loads(data) )
                    if data['clip']['url'].startswith('http'):
                        url = data['clip']['url']
                except: printExc()
        if '' != url:
            data = getDirectM3U8Playlist(url, checkExt=False)
            for item in data:
                item['url'] = urlparser.decorateUrl(item['url'], {'iptv_proto':'m3u8', 'iptv_livestream':True})
                urlTab.append(item)
    
        return urlTab
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('Hitbox.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "Hitbox.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = [] 

        if None == name:
            self.listsTab(Hitbox.MAIN_CAT_TAB, {'name':'category'})
    #GAMES
        elif 'games_list' == category:
            self.listGames(self.currItem, 'games_tab')
        elif 'games_tab' == category:
            self.listGamesTab(self.currItem)
    #MEDIA
        elif 'media' == category:
            self.listMedia(self.currItem)
    #WYSZUKAJ
        elif category in ["search"]:
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
        CHostBase.__init__(self, Hitbox(), True)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('hitboxtvlogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            need_resolve = 0
            name = self.host._getStr( item["name"] )
            url  = item["url"]
            retlist.append(CUrlItem(name, url, need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo

    def convertList(self, cList):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        searchTypesOptions.append((_("Live now"), "live"))
        searchTypesOptions.append((_("Recordings"), "video"))
    
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
                
            title       =  self.host._getStr( cItem.get('title', '') )
            description =  self.host._getStr( cItem.get('desc', '') ).strip()
            icon        =  self.host._getStr( cItem.get('icon', '') )
            
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
