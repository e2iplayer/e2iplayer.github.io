# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigInteger, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
from datetime import datetime, timedelta
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
config.plugins.iptvplayer.zdfmediathek_iconssize = ConfigSelection(default = "medium", choices = [ ("large", _("large")), ("medium", _("medium")), ("small", _("small")) ])
config.plugins.iptvplayer.zdfmediathek_prefformat = ConfigSelection(default = "mp4,rtmp,m3u8", choices = [\
("mp4,rtmp,m3u8", "mp4,rtmp,m3u8"),("mp4,m3u8,rtmp", "mp4,m3u8,rtmp"), \
("rtmp,mp4,m3u8", "rtmp,mp4,m3u8"),("rtmp,m3u8,mp4", "rtmp,m3u8,mp4"), \
("m3u8,rtmp,mp4", "m3u8,rtmp,mp4"),("m3u8,mp4,rtmp", "m3u8,mp4,rtmp")])
config.plugins.iptvplayer.zdfmediathek_prefquality = ConfigSelection(default = "3", choices = [("0", _("low")), ("1", _("medium")), ("2", _("high")), ("3", _("very high")), ("4", _("hd"))])
config.plugins.iptvplayer.zdfmediathek_prefmoreimportant = ConfigSelection(default = "quality", choices = [("quality", _("quality")), ("format", _("format"))])
config.plugins.iptvplayer.zdfmediathek_onelinkmode = ConfigYesNo(default=True)


def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Icons size"), config.plugins.iptvplayer.zdfmediathek_iconssize))
    optionList.append(getConfigListEntry(_("Prefered format"), config.plugins.iptvplayer.zdfmediathek_prefformat))
    optionList.append(getConfigListEntry(_("Prefered quality"), config.plugins.iptvplayer.zdfmediathek_prefquality))
    optionList.append(getConfigListEntry(_("More important"), config.plugins.iptvplayer.zdfmediathek_prefmoreimportant))
    optionList.append(getConfigListEntry(_("One link mode"), config.plugins.iptvplayer.zdfmediathek_onelinkmode))
    return optionList
###################################################

def gettytul():
    return 'ZDFmediathek'

class ZDFmediathek(CBaseHostClass):
    DEFAULT_ICON = 'http://www.zdf.de/ZDFmediathek/img/fallback/236x133.jpg'
    MAIN_API_URL = 'http://heute-api.live.cellular.de/'
    RUBRIKEN_API_URL = MAIN_API_URL + 'mediathek/rubriken'
    SENDUNG_API_URL  = MAIN_API_URL + 'mediathek/sendung'
    SEARCH_API_URL   = MAIN_API_URL + 'mediathek/suche?search='
    NEWS_API_URL     = MAIN_API_URL + 'mediathek/nachrichten'
    NEWS_SHOW_API_URL = MAIN_API_URL + 'mediathek/nachrichtensendungen'
    THEMEN_API_URL    = MAIN_API_URL + 'mediathek/themen'
    MISSED_SHOW_API_URL = MAIN_API_URL + 'mediathek/sendungverpasst'
    A_Z_API_URL      = MAIN_API_URL + 'mediathek/a-z'
    HOME_API_URL     = MAIN_API_URL + 'mediathek/start'
    VIDEO_API_URL    = MAIN_API_URL + 'mediathek/video'
    VIDEO_WEB_URL    = "http://www.zdf.de/ZDFmediathek/xmlservice/web/beitragsDetails?ak=web&id="
    
    MAIN_CAT_TAB = [{'category':'startseite',     'title':_('Home page'), 'url': HOME_API_URL},
                    {'category':'nachrichten',    'title':_('News'), 'url': NEWS_API_URL},
                    {'category':'sendungverpasst','title':_('Missed the show?')},
                    {'category':'a_z',            'title':_('Program A-Z')},
                    {'category':'rubriken',       'title':_('Categories'), 'url': RUBRIKEN_API_URL},
                    {'category':'themen',         'title':_('Topics'), 'url': NEWS_API_URL},
                    {'category':'search',         'title':_('Search'), 'search_item':True},
                    {'category':'search_history', 'title':_('Search history')} ]

    START_CAT_TAB =   [{'key':'live',         'title':_('All programs in the Live Stream')}, 
                       {'key':'themen',       'title':_("Topics")}, 
                       {'key':'tipps',        'title':_('Featured')}, 
                       {'key':'aktuell',      'title':_('Recent')},
                       {'key':'meistGesehen', 'title':_('Most Popular')}]
        
    SENDUNG_CAT_TAB = [{'key':'tipps',        'title':_('Featured')}, 
                       {'key':'aktuell',      'title':_('Recent')},
                       {'key':'meistGesehen', 'title':_('Most Popular')}]
                       
    A_Z_CAT_TAB     = [{'id':'A/C',        'title':_('ABC')},
                       {'id':'D/E',        'title':_('DFE')},
                       {'id':'G/I',        'title':_('GHI')},
                       {'id':'J/K',        'title':_('JKL')},
                       {'id':'M/O',        'title':_('MNO')},
                       {'id':'P/S',        'title':_('PQRS')},
                       {'id':'T/V',        'title':_('TUV')},
                       {'id':'W/Z',        'title':_('WXYZ')},
                       {'id':'0-9/0-9',    'title':_('0-9')}, ]
                       
    QUALITY_MAP = {'veryhigh':3, 'high':2, 'med':1, 'low':0 }
    
    def __init__(self):
        printDBG("ZDFmediathek.__init__")
        CBaseHostClass.__init__(self, {'history':'ZDFmediathek.tv'})     
    
    def _cleanHtmlStr(self, str):
        str = str.replace('<', ' <').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        return self.cm.ph.removeDoubles(clean_html(str), ' ').strip()
        
    def _getStr(self, v, default=''):
        return clean_html(self._encodeStr(v, default))
        
    def _encodeStr(self, v, default=''):
        if type(v) == type(u''): return v.encode('utf-8')
        elif type(v) == type(''): return v
        else: return default
        
    def _getNum(self, v, default=0):
        try: return int(v)
        except:
            try: return float(v)
            except: return default
            
    def _getIcon(self, iconsItem):
        iconssize = config.plugins.iptvplayer.zdfmediathek_iconssize.value
        iconsTab = []
        for item in iconsItem.keys():
            item = iconsItem[item]
            if "contentblob" in item["url"]:
                iconsTab.append({'size':item["width"], 'url':item["url"]})
        idx = len(iconsTab)
        if idx:
            iconsTab.sort(key=lambda k: k['size'])
            if 'large' == iconssize:    idx -= 1
            elif 'medium' == iconssize: idx /=  2
            elif 'small' == iconssize:  idx = 0
            return iconsTab[idx]['url']
        return ''
       
    def listsTab(self, tab, cItem):
        printDBG("ZDFmediathek.listsMainMenu")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            self.addDir(params)
            
    def _listBase(self, cItem, categories, baseUrl, key, addPage=False):
        if addPage:
            page = cItem.get('page', 0)
            url =  baseUrl + '?page=%s' % page
        else: url = baseUrl
        sts, data = self.cm.getPage(url)
        try:
            data = json.loads(data)
            for item in data[key]["teaser"]:
                if  item["type"] in categories:
                    category = item["type"]
                    params = dict(cItem)
                    if category in ["video", "livevideo"]:
                        desc = str(timedelta(seconds=int(item["length"]))) + ", " + item.get("beschreibung", "")
                    else:
                        desc = (_("%s items in category") % self._getStr(item["length"])) + ", " + self._getStr(item.get("beschreibung", ""))
                    icon = self._getIcon(item["teaserBild"])
                    params.update({'category':category, 'title':item["titel"],'id':item["id"], 'desc':desc, 'icon':icon, 'url':'', 'beschreibung':self._getStr(item.get("beschreibung", ""))})
                    params.pop("key", None)
                    if category in ["video", "livevideo"]:
                        self.addVideo(params)
                    else:
                        self.addDir(params)
        except: printExc()
        # add next page when needed
        if addPage:
            url = baseUrl + '?page=%s' % (page+1)
            sts, newData = self.cm.getPage(url)
            try:
                newData = json.loads(newData)
                if  len(newData[key]["teaser"]) and newData[key]["teaser"] != data[key]["teaser"]:
                    params = dict(cItem)
                    desc = item.get("beschreibung", "")
                    params.update({'page':page+1, 'title':_('Next page'), 'desc':desc})
                    self.addDir(params)
            except: printExc()
            
    def listRubriken(self, cItem, category):
        printDBG("ZDFmediathek.listRubriken")
        self._listBase(cItem, [category], cItem['url'], "rubriken")

    def listRubrik(self, cItem, category):
        printDBG("ZDFmediathek.listRubrik")
        url = ZDFmediathek.RUBRIKEN_API_URL + ('/%s' % cItem["id"])
        self._listBase(cItem, [category], url, "aktuell")
        
    def listA_Z(self, cItem, category):
        printDBG("ZDFmediathek.listA_Z")
        url = ZDFmediathek.A_Z_API_URL + ('/%s' % cItem["id"])
        self._listBase(cItem, [category], url, "ergebnis")
        
    def listNachrichten(self, cItem, category):
        printDBG("ZDFmediathek.listNachrichten")
        url = ZDFmediathek.NEWS_API_URL
        self._listBase(cItem, [category, "sendung"], url, "ganzeSendungen", False)
        
    def listThemen(self, cItem, category):
        printDBG("ZDFmediathek.listThemen")
        url = ZDFmediathek.THEMEN_API_URL
        self._listBase(cItem, [category], url, "themen", False)
        
    def listSendungverpasst(self, cItem):
        printDBG("ZDFmediathek.listSendungverpasst")
        if "date" in cItem:
            url = ZDFmediathek.MISSED_SHOW_API_URL + '/' + cItem['date']
            self._listBase(cItem, ["video", "livevideo"], url, "ergebnis", False)
        else:
            # convert to timestamp
            now = int(time.time())
            for item in range(7):
                date =  datetime.fromtimestamp(now - item * 24 * 3600).strftime('%Y-%m-%d')
                params = dict(cItem)
                params.update({'date':date, 'title':date})
                self.addDir(params)
        
    def listSendung(self, cItem, url, cat_tab=None):
        printDBG("ZDFmediathek.listSendung")
        if None == cat_tab: cat_tab = ZDFmediathek.SENDUNG_CAT_TAB
        if '' != cItem.get("id", ''):
            url += ('/%s' % cItem["id"])
        if "key" in cItem:
            self._listBase(cItem, ["video", "livevideo", "sendung", "thema"], url, cItem['key'], True)
        else:
            tmpTab = []
            page = cItem.get('page', 0)
            sts, data = self.cm.getPage(url + '?page=%s' % page)
            try:
                data = json.loads(data)
                for item in cat_tab:
                    if item['key'] in data and len(data[item['key']].get("teaser", [])):
                        params = dict(cItem)
                        params.update(item)
                        params["desc"] = cItem.get("beschreibung", "")
                        tmpTab.append(params)
            except: printExc()
            if 1 == len(tmpTab):
                cItem['key'] = tmpTab[0]['key']
                self._listBase(cItem, ["video", "livevideo"], url, cItem['key'], True)
            else:
                for item in tmpTab: self.addDir(item)

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("ZDFmediathek.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        searchPattern = urllib.quote_plus(searchPattern)
        url = ZDFmediathek.SEARCH_API_URL + searchPattern
        self._listBase(cItem, ["video", "livevideo"], url, "ergebnis", False)
    
    def getLinksForVideo(self, cItem):
        printDBG("ZDFmediathek.getLinksForVideo id[%s]" % cItem['id'])
        urlTab = []        
        tmpVideoFormats = {'f4m':[], 'm3u8':[], 'rtmp':[], 'mp4':[]}

        # GET VIDEO URL FROM MOBILE API
        '''
        url = ZDFmediathek.VIDEO_API_URL + '/' + cItem['id'] + '?page=0'
        sts, data = self.cm.getPage(url)
        try:
            live = False
            data = json.loads(data)
            data = data["video"]
            if "livevideo" in data['type']: 
                live = True
            data = data["formitaeten"]
            for item in data:
                if 'm3u8_' in item["type"]:
                    urlTab.append({'name':item["type"], 'url':item["url"]})
        except: printExc()
        '''
        
        # GET VIDEO URL FROM WEB API
        preferedQuality = int(config.plugins.iptvplayer.zdfmediathek_prefquality.value)
        preferedFormat  = config.plugins.iptvplayer.zdfmediathek_prefformat.value
        tmp = preferedFormat.split(',')
        formatMap = {}
        for i in range(len(tmp)):
            formatMap[tmp[i]] = i
        
        def _rtmpGetUrl(url):
            retUrl = ''
            sts, data = self.cm.getPage(url)
            if sts:
                retUrl = self.cm.ph.getDataBeetwenMarkers(data, "<default-stream-url>", "</default-stream-url>", False)[1].strip()
            return retUrl.strip()
        def _httpGetUrl(url):
            # simple check if url is valid
            sts, data = self.cm.getPage(url, {'return_data':False})
            if sts:
                data.close()
                return url
            else: return ''
            
        tmpUrlTab = []
        url = ZDFmediathek.VIDEO_WEB_URL + cItem['id']
        sts, data = self.cm.getPage(url)
        live = False
        if "<type>livevideo</type>" in data: 
            live = True
        try:
            data = self.cm.ph.getDataBeetwenMarkers(data, "<formitaeten>", "</formitaeten>", False)[1]
            data = data.split("</formitaet>")
            del data[-1]
            for item in data:
                quality = self.cm.ph.getDataBeetwenMarkers(item, "<quality>", "</quality>", False)[1].strip()
                url = self.cm.ph.getDataBeetwenMarkers(item, "<url>", "</url>", False)[1].strip()
                for type in [{'pattern':'http_m3u8_http', 'name':'m3u8'}, {'pattern':'mp4_http', 'name':'mp4'}, {'pattern':'rtmp_zdfmeta_http', 'name':'rtmp', 'get_url':_rtmpGetUrl}]:
                    if type['pattern'] in item:
                        qualityVal = ZDFmediathek.QUALITY_MAP.get(quality,10)
                        qualityPref = abs(qualityVal - preferedQuality)
                        formatPref  = formatMap.get(type['name'], 10)
                        tmpUrlTab.append({'url':url, 'quality_name':quality, 'quality':qualityVal, 'quality_pref':qualityPref, 'format_name':type['name'], 'format_pref':formatPref, 'get_url':type.get('get_url', _httpGetUrl)})
        except: printExc()
        def _cmpLinks(it1, it2):
            prefmoreimportantly = config.plugins.iptvplayer.zdfmediathek_prefmoreimportant.value
            if 'quality' == prefmoreimportantly:
                if it1['quality_pref'] < it2['quality_pref'] :   return -1
                elif it1['quality_pref']  > it2['quality_pref'] : return 1
                else:
                    if it1['quality'] < it2['quality'] :   return -1
                    elif it1['quality']  > it2['quality'] : return 1
                    else:
                        if it1['format_pref'] < it2['format_pref'] :   return -1
                        elif it1['format_pref']  > it2['format_pref'] : return 1
                        else: return 0
            else:
                if it1['format_pref'] < it2['format_pref'] :   return -1
                elif it1['format_pref']  > it2['format_pref'] : return 1
                else:
                    if it1['quality_pref'] < it2['quality_pref'] :   return -1
                    elif it1['quality_pref']  > it2['quality_pref'] : return 1
                    else:
                        if it1['quality'] < it2['quality'] :   return -1
                        elif it1['quality']  > it2['quality'] : return 1
                        else: return 0
        tmpUrlTab.sort(_cmpLinks)
        onelinkmode = config.plugins.iptvplayer.zdfmediathek_onelinkmode.value
        for item in tmpUrlTab:
            url = item['url']
            name = item['quality_name'] + ' ' + item['format_name']
            if onelinkmode or 'rtmp' == item['format_name']: url = item['get_url'](url)
            if '' != url:
                urlTab.append({'name':name, 'url':self.up.decorateUrl(url, {'iptv_livestream':live})})
                if onelinkmode: break
        printDBG(tmpUrlTab)
        return urlTab
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('ZDFmediathek.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "ZDFmediathek.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = [] 

        if None == name:
            self.listsTab(ZDFmediathek.MAIN_CAT_TAB, {'name':'category'})
    #STARTSEITE
        elif 'startseite' == category:
            self.listSendung(self.currItem, ZDFmediathek.HOME_API_URL, ZDFmediathek.START_CAT_TAB)
    #RUBRIKEN
        elif 'rubriken' == category:
            self.listRubriken(self.currItem, 'rubrik')
    #RUBRIK
        elif 'rubrik' == category:
            self.listRubrik(self.currItem, 'sendung')
    #SENDUNG
        elif 'sendung' == category:
            self.listSendung(self.currItem, ZDFmediathek.SENDUNG_API_URL)
    #NACHRICHTEN
        elif 'nachrichten' == category:
            self.listNachrichten(self.currItem, 'nachrichten_sendung')
    #NARCHRICHTEN SENDUNG
        elif 'nachrichten_sendung' == category:
            self.listSendung(self.currItem, ZDFmediathek.NEWS_SHOW_API_URL)
    #THEMEN
        elif 'themen' == category:
            self.listThemen(self.currItem, 'thema')
    #THEMA
        elif 'thema' == category:
            self.listSendung(self.currItem, ZDFmediathek.THEMEN_API_URL)
    #SENDUNGVERPASS
        elif 'sendungverpasst' == category:
            self.listSendungverpasst(self.currItem)
    #A-Z
        elif 'a_z' == category:
            self.listsTab(ZDFmediathek.A_Z_CAT_TAB, {'name':'category', 'category':'list_a_z'})
    #LIST A-Z
        elif 'list_a_z' == category:
            self.listA_Z(self.currItem, 'sendung')
    #WYSZUKAJ
        elif category in ["search", "search_next_page"]:
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category', 'category':'search_next_page'}) 
            self.listSearchResult(cItem, searchPattern, searchType)
    #HISTORIA WYSZUKIWANIA
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, ZDFmediathek(), True)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('zdfmediatheklogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] not in ['audio', 'video']:
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])

        retlist = []
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
        #searchTypesOptions.append((_("Games"), "games"))
        #searchTypesOptions.append((_("Channles"), "streams"))
    
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
            if '' == icon: icon = ZDFmediathek.DEFAULT_ICON
            
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
