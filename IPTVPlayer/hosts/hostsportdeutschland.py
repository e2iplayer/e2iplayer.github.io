# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
from datetime import datetime
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
config.plugins.iptvplayer.sportdeutschland_streamprotocol = ConfigSelection(default = "rtmp", choices = [("rtmp", "rtmp"),("hls", "HLS - m3u8")]) 


def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry( "SportDeutschland " + _("preferowany protokół strumieniowania" + ": "), config.plugins.iptvplayer.sportdeutschland_streamprotocol))
    return optionList
###################################################

def gettytul():
    return 'SportDeutschland.TV'

class SportDeutschland(CBaseHostClass):
    MAINURL      = 'http://sportdeutschland.tv/'
    MAIN_API_URL = 'http://splink.tv/api/'
    SEARCH_URL   = ''
    HTTP_JSON_HEADER  = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:12.0) Gecko/20100101 Firefox/12.0', 
                         'Accept'    : 'application/vnd.vidibus.v2.html+json',
                         'Referer'   : MAINURL, 
                         'Origin'    : MAINURL
                        }
    MAIN_MENU = [{'title':'Kategorie', 'category':'categories'},
                 #{'title':'Program',   'category':'program'},
                 {'title':'Wyszukaj',  'category':'Wyszukaj'},
                 {'title':'Historia wyszukiwania', 'category':'Historia wyszukiwania'}]
                 
    def __init__(self):
        printDBG("SportDeutschland.__init__")
        CBaseHostClass.__init__(self, {'history':'SportDeutschland'})       
        self.cm.HEADER = dict(SportDeutschland.HTTP_JSON_HEADER)

    def _cleanHtmlStr(self, str):
            str = self.cm.ph.replaceHtmlTags(str, ' ').replace('\n', ' ')
            return clean_html(self.cm.ph.removeDoubles(str, ' ').replace(' )', ')').strip())
            
    def _getJItemStr(self, item, key, default=''):
        v = item.get(key, None)
        if None == v:
            return default
        return clean_html(u'%s' % v).encode('utf-8')
        
    def _getJItemNum(self, item, key, default=0):
        v = item.get(key, None)
        if None != v:
            try:
                NumberTypes = (int, long, float, complex)
            except NameError:
                NumberTypes = (int, long, float)
                
            if isinstance(v, NumberTypes):
                return v
        return default
        
    def _getItemsListFromJson(self, url):
        sts,data = self.cm.getPage(url)    
        if sts:
            try:
                data = json.loads(data)
                data = data['items']
                return data
                
            except:
                printExc()
        return []
        
    def _utc2local(self, utc_datetime):
        now_timestamp = time.time()
        offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
        return utc_datetime + offset
        
    def listsMainMenu(self):
        printDBG("SportDeutschland.listsMainMenu")
        for item in SportDeutschland.MAIN_MENU:
            params = {'name':'category', 'title':item['title'], 'category':item['category']}
            self.addDir(params)
            
    def listCategories(self, cItem):
        printDBG("SportDeutschland.listCategories")
        data = self._getItemsListFromJson(SportDeutschland.MAIN_API_URL + 'sections?per_page=9999')
        
        params = {'name':'category', 'title':_('--Wszystkie--'), 'category':'category', 'permalink':'', 'uuid':'', 'page':1}
        self.addDir(params)
        
        for item in data:
            params = {'name':'category', 'title':self._getJItemStr(item, 'title'), 'category':'category', 'permalink':self._getJItemStr(item, 'permalink'), 'uuid':self._getJItemStr(item, 'uuid'), 'page':1}
            self.addDir(params)
        
    def listCategory(self, cItem):
        printDBG("SportDeutschland.listCategory cItem[%s]" % cItem)
        baseUrl     = SportDeutschland.MAIN_API_URL
        page        = self._getJItemNum(cItem, 'page', 1)
        baseUuid    = self._getJItemStr(cItem, 'uuid')
        pattern     = cItem.get('pattern', '')
        if '' == pattern:
            if '' != baseUuid:
                baseUrl += 'sections/%s' % (baseUuid)
            baseUrl += '/assets?'
        else:
            baseUrl += 'search?q=%s&' % pattern
        data = self._getItemsListFromJson(baseUrl + 'page=%d&per_page=100' % page)
        for item in data:
            params = {'name':'category', 'title':self._getJItemStr(item, 'title'), 'category':'category', 'icon':self._getJItemStr(item, 'image'), 'desc':self._getJItemStr(item, 'teaser'), 'video':self._getJItemStr(item, 'video')}
            printDBG(":::::::::::::::::::::::::::::::::::::\n%s\n:::::::::::::::::::::::::::::::" % item)
            planowany = False
            #if 'LIVE' == self._getJItemStr(item, 'duration', ''):
            try:
                dateUTC = self._getJItemStr(item, 'date').replace('T', ' ').replace('Z', ' UTC')
                dateUTC = datetime.strptime(dateUTC, "%Y-%m-%d %H:%M:%S %Z")
                if dateUTC > datetime.utcnow():
                    params['title'] += _(" (planowany %s)") % self._utc2local(dateUTC).strftime('%Y/%m/%d %H:%M:%S')
                    planowany = True
            except:
                printExc()
            
            sectionPermalink = self._getJItemStr(item.get('section', {}), 'permalink')
            permalink   = self._getJItemStr(item, 'permalink')
            if '' != sectionPermalink and '' != permalink:
                params['url'] = SportDeutschland.MAIN_API_URL + 'permalinks/%s/%s' % (sectionPermalink, permalink)
            else:
                params['url'] = ''
                
            if '' != params['url'] or '' != params['video']:
                if not planowany or params['video'].startswith('http'):
                    self.addVideo(params)
                else:
                    self.addArticle(params)
            else:
                printDBG('SportDeutschland.listCategory wrong item[%s]' % item)
                
        data = self._getItemsListFromJson(baseUrl + 'page=%d&per_page=100' % (page+1))
        if 0 < len(data):
            params = dict(cItem)
            params.update({'title':'Następna strona', 'page':page+1})
            self.addDir(params)
            
    def getLinksForVideo(self, cItem):
        printDBG("SportDeutschland.getLinksForVideo [%s]" % cItem)
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0',
                       'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' }
        videoUrls =[]
        videoUrl = ''
        if '' != cItem['video']:
            videoUrl = cItem['video']
        else:        
            if '' != cItem['url']:
                sts,data = self.cm.getPage(cItem['url'])
                if sts:
                    try:
                        data = json.loads(data)
                        #printDBG("[%s]" % data)
                        videoUrl = self._getJItemStr(data['asset'], 'video')
                        if '' == videoUrl:
                            assets_info = self._getJItemStr(data['asset'], 'url')
                            if len(assets_info):
                                sts,assets_info = self.cm.getPage(assets_info, {'header' : HTTP_HEADER})
                                if sts:
                                    try:
                                        assets_info = json.loads(assets_info)
                                        videoUrl = self._getJItemStr(assets_info, 'video')
                                        printDBG('SportDeutschland.getLinksForVideo "video" from "assets_info" |%s|' % videoUrl)
                                    except: printExc()
                        if '' == videoUrl:  
                            player = self._getJItemStr(data['asset'], 'player')
                            if '' != player:
                                sts,data = self.cm.getPage(player, {'header' : HTTP_HEADER})
                                if sts: videoUrl = self.cm.ph.getSearchGroups(data, '<a class="asset"[^>]+?href="([^"]+?)"')[0]
                    except:
                        printExc()
        
        if '.smil?' in videoUrl:
            if 'rtmp' == config.plugins.iptvplayer.sportdeutschland_streamprotocol.value:
                sts,data = self.cm.getPage(videoUrl)
                if sts:
                    #printDBG("+++++++++++++++++++++++++++++++++\n%s\n+++++++++++++++++++++++++++++++++" % data)
                    videoUrl = self.cm.ph.getSearchGroups(data, 'meta base="(rtmp[^"]+?)"')[0]
                    videoUrl += '/' + self.cm.ph.getSearchGroups(data, 'video src="([^"]+?)"')[0]
                    if videoUrl.startswith('rtmp'):
                        videoUrls.append({'name':'SportDeutschland rtmp', 'url':videoUrl.replace('&amp;', '&')})
            else:
                videoUrl = videoUrl.replace('.smil?', '.m3u8?')
                videoUrls = getDirectM3U8Playlist(videoUrl, checkExt=False)
        elif videoUrl.split('?')[0].endswith('mp4'):
            videoUrl = self.up.decorateUrl(videoUrl, {"iptv_buffering":"forbidden"})
            videoUrls.append({'name':'SportDeutschland mp4', 'url':videoUrl})
        return videoUrls
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('SportDeutschland.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "SportDeutschland.handleService: ---------> name[%s], category[%s] " % (name, category) )
        self.currList = []
        
        if None == name:
            self.listsMainMenu()
        elif 'categories' == category:
            self.listCategories(self.currItem)
        elif 'category' == category:
            self.listCategory(self.currItem)
    #WYSZUKAJ
        elif category == "Wyszukaj":
            self.listCategory({'pattern':searchPattern, 'category':'category'})
    #HISTORIA WYSZUKIWANIA
        elif category == "Historia wyszukiwania":
            self.listsHistory()
        else:
            printExc()

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, SportDeutschland(), True)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('SportDeutschlandlogo.png')])

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
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo

    def convertList(self, cList):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        #searchTypesOptions.append(("Filmy", "filmy"))
        #searchTypesOptions.append(("Seriale", "seriale"))
    
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
            elif cItem['type'] == 'article':
                type = CDisplayListItem.TYPE_ARTICLE
                url = cItem.get('url', '')
                if '' != url:
                    hostLinks.append(CUrlItem("Link", url, 1))
                
            title       =  cItem.get('title', '')
            description =  clean_html(cItem.get('desc', ''))
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
