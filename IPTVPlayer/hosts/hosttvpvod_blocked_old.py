# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSelOneLink, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html

from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
try:    import simplejson as json
except: import json
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
config.plugins.iptvplayer.tvpVodProxyEnable = ConfigYesNo(default = False)
config.plugins.iptvplayer.tvpVodDefaultformat = ConfigSelection(default = "590000", choices = [("360000",  "320x180"),
                                                                                               ("590000",  "398x224"),
                                                                                               ("820000",  "480x270"),
                                                                                               ("1250000", "640x360"),
                                                                                               ("1750000", "800x450"),
                                                                                               ("2850000", "960x540"),
                                                                                               ("5420000", "1280x720"),
                                                                                               ("6500000", "1600x900"),
                                                                                               ("9100000", "1920x1080") ])
config.plugins.iptvplayer.tvpVodUseDF = ConfigYesNo(default = True)


def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("Domyślny format video",           config.plugins.iptvplayer.tvpVodDefaultformat))
    optionList.append(getConfigListEntry("Używaj domyślnego format video:", config.plugins.iptvplayer.tvpVodUseDF))
    optionList.append(getConfigListEntry("Korzystaj z proxy?",              config.plugins.iptvplayer.tvpVodProxyEnable))
    return optionList
###################################################


def gettytul():
    return 'TVP VOD player'

class TvpVod(CBaseHostClass):
    USER_AGENT = 'Apache-HttpClient/UNAVAILABLE (java 1.4)'
    HEADER = {'User-Agent': USER_AGENT, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
    PAGE_NUM     = 20
    PAGE_PARAMS  = 'pageSize=' + str(PAGE_NUM) + '&thumbnailSize=240&deviceType=1&pageNo=%s'
    MAINURL      = 'http://vod.tvp.customers.multiscreen.tv/'
    NAVI_URL     = MAINURL + 'Navigation'
    NEWS_URL     = MAINURL + 'News/NewsListJSON?' + PAGE_PARAMS + '&parentId=%s'
    EPISODES_URL = MAINURL + 'Movies/EpisodesJSON?' + PAGE_PARAMS + '&parentId=%s'
    SERIES_URL   = MAINURL + 'Movies/SeriesJSON?' + PAGE_PARAMS + '&parentId=%s'
    SEARCH_URL   = MAINURL + 'Movies/SearchJSON?' + PAGE_PARAMS + '&searchString=%s'
    IMAGE_URL    = 'http://s.v3.tvp.pl/images/%s/%s/%s/uid_%s_width_200_gs_0.%s' 
    FORMATS = {"video/mp4":"mp4"}
    SEC_FORMATS = {"application/x-mpegurl":"m3u8"} #, "video/x-ms-wmv":"wmv", "application/x-mpegurl":"m3u8"}
    PARAMS_KEYS = { 'plot' : ['lead_root', 'description_root'] }
    
    def __init__(self):
        params = {'history':'TvpVod', 'cookie':'playtube.cookie', 'proxyURL': config.plugins.iptvplayer.proxyurl.value, 'useProxy': config.plugins.iptvplayer.tvpVodProxyEnable.value}
        CBaseHostClass.__init__(self, params)
        self.cache = None
            
    def getJItemStr(self, item, key, default=''):
        v = item.get(key, None)
        if None == v:
            return default
        return v.encode('utf-8')

    def listsMainMenu(self):
        printDBG("listsMainMenu")
        sts, data = self.cm.getPage( self.NAVI_URL )
        if not sts: return
        try:
            data = json.loads(data)
            for item in data:
                if 'VOD' == item['Title']:
                    data = item['SubCategories']
                    for item in data:
                        params = {'name': 'category', 'title': item['Title'].encode("utf-8"), 'category': item['ListType'].encode("utf-8"), 'id': str(item['Id']).encode("utf-8")}
                        self.addDir(params)
                    break
        except:
            printExc()
        if len(self.getCurrList()):
            staticTab = ["Wyszukaj", "Historia wyszukiwania"]
            for item in staticTab:
                params = {'name': 'category', 'title': item, 'category': item}
                self.addDir(params)

    def listItems(self, baseUrl, category, nextCategory, id, page):
        printDBG("listItems category[%s], nextCategory[%r], id[%s], page[%s]" % (category, nextCategory, id, page))
        url = baseUrl % (page, id)
        sts, data = self.cm.getPage( url )
        if not sts: return
        try:
            num = 0
            data = json.loads(data)
            for item in data:
                params = {'title': self.getTitle(item), 'id': str(item['asset_id']), 'icon': self.getImageUrl(item), 'plot': self.getStrParam('plot', item)}
                if 'video' == self.getJItemStr(item, 'type'):
                    self.addVideo(params)
                else:
                    params.update({'name': 'category', 'category': nextCategory})
                    self.addDir(params)
                num += 1
            if num > 0:
                page = str(int(page) + 1)
                url = baseUrl % (page, id)
                sts, data = self.cm.getPage( url )
                if not sts: return
                if 'asset_id' in data:
                    params = {'name': 'category', 'title': 'Następna strona', 'category': category, 'id': id, 'page':page}
                    self.addDir(params)
        except:
            printExc()
            
    def getTitle(self, item):
        printDBG("getTitle")
        title = self.getJItemStr( item, 'Title' ) 
        if 2 < len(title): return title
        title = self.getJItemStr( item, 'website_title' )  + ' ' + self.getJItemStr( item, 'title' )
        if 2 < len(title): return title
        return self.getJItemStr( item, 'title_root' )
        
            
    def getImageUrl(self, item):
        printDBG("getImageUrl")
        keys = ['logo_4x3', 'image_16x9', 'image_4x3', 'image_ns954', 'image_ns644', 'image']
        iconFile = ""
        try:
            for key in keys:
                if None != item.get(key, None):
                    iconFile = self.getJItemStr( item[key][0], 'file_name')
                if len(iconFile):
                    printDBG("-----------------iconFile[%s]" % iconFile)
                    tmp = iconFile.split('.')
                    return self.IMAGE_URL % (iconFile[0], iconFile[1], iconFile[2], tmp[0], tmp[1])
        except:
            printExc()
        return ''
       
    def getStrParam(self, param, item):
        printDBG("getStrParam param[%s]" % param)
        value = ''
        for key in self.PARAMS_KEYS[param]:
            tmp = self.getJItemStr( item, key ) 
            if len(tmp) > len(value):
                value = tmp
        return value
        
    def getFormatFromBitrate(self, bitrate):
        tab = [ ("360000",  "320x180"),
                ("590000",  "398x224"),
                ("820000",  "480x270"),
                ("1250000", "640x360"),
                ("1750000", "800x450"),
                ("2850000", "960x540"),
                ("5420000", "1280x720"),
                ("6500000", "1600x900"),
                ("9100000", "1920x1080") ]
        ret = ''
        for item in tab:
            if int(bitrate) == int(item[0]):
                ret = item[1]
        if '' == ret:
            ret = 'Bitrate[%s]' % bitrate
        return ret
        
    def getVideoLink(self, asset_id):
        printDBG("getVideoLink asset_id [%s]" % asset_id)
        sts, data = self.cm.getPage( 'http://www.tvp.pl/shared/cdn/tokenizer_v2.php?mime_type=video%2Fmp4&object_id=' + asset_id, {'host': self.USER_AGENT} )
        if False == sts:
            printDBG("getVideoLink problem")
        
        videoTab = []
        try:
            data = json.loads( data )
            
            def _getVideoLink(data, FORMATS):
                videoTab = []
                for item in data['formats']:
                    if item['mimeType'] in FORMATS.keys():
                        formatType = FORMATS[item['mimeType']].encode('utf-8')
                        name = self.getFormatFromBitrate( str(item['totalBitrate']) ) + '\t ' + formatType
                        url = item['url'].encode('utf-8')
                        if 'm3u8' == formatType:
                            videoTab.extend( getDirectM3U8Playlist(url) )
                        else:
                            videoTab.append( {'name' : name, 'bitrate': str(item['totalBitrate']), 'url' : url })
                if 1 < len(videoTab):
                    max_bitrate = int(config.plugins.iptvplayer.tvpVodDefaultformat.value)
                    def __getLinkQuality( itemLink ):
                        return int(itemLink['bitrate'])
                    oneLink = CSelOneLink(videoTab, __getLinkQuality, max_bitrate)
                    if config.plugins.iptvplayer.tvpVodUseDF.value:
                        videoTab = oneLink.getOneLink()
                    else:
                        videoTab = oneLink.getSortedLinks()
                return videoTab
            
            videoTab = _getVideoLink(data, TvpVod.FORMATS )
            if 0 == len(videoTab): videoTab = _getVideoLink(data, TvpVod.SEC_FORMATS )
        except:
            printExc("getVideoLink exception") 
        return videoTab

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        title    = self.currItem.get("title", '')
        category = self.currItem.get("category", '')
        page     = self.currItem.get("page", '0')
        icon     = self.currItem.get("icon", '')
        url      = self.currItem.get("url", '')
        plot     = self.currItem.get("plot", '')
        id       = self.currItem.get("id", '')
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsMainMenu()           
    #FILMY
        elif category == "episodes": 
            self.listItems(self.EPISODES_URL, category, 'episodes', id, page)
        elif category == "series":
            self.listItems(self.SERIES_URL, category, 'episodes', id, page)
    #WYSZUKAJ
        elif category == "Wyszukaj":
            pattern = urllib.quote_plus(searchPattern)
            printDBG("Wyszukaj: pattern[%s]" % pattern)
            self.listItems(self.SEARCH_URL, category, 'episodes', pattern, page)
            
    #HISTORIA WYSZUKIWANIA
        elif category == "Historia wyszukiwania":
            self.listsHistory()

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, TvpVod(), True)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('tvpvodlogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] != 'video':
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])

        retlist = []
        urlList = self.host.getVideoLink(self.host.currList[Index].get('id', ''))
        for item in urlList:
            need_resolve = 0
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

    def convertList(self, cList):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        #searchTypesOptions.append(("Wideo", "video"))
        #searchTypesOptions.append(("Serie", "series"))
    
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
            description =  cItem.get('plot', '')
            description = clean_html(description.decode("utf-8")).encode("utf-8")
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
