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
import unicodedata
import string
import base64
import binascii
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

def GetConfigList():
    optionList = []
    return optionList
###################################################

def gettytul():
    return 'SerialNet.pl'


class SerialeNet(CBaseHostClass):
    DEFAULT_ICON = ''
    MAIN_URL = "http://serialnet.pl/"
    CAT_TAB  = [{'category':'abc_menu',        'title':_('Alfabetycznie'),             'url':MAIN_URL},
                {'category':'last_update',     'title':_('Ostatnio uzupełnione'),      'url':MAIN_URL},
                {'category':'search',          'title':_('Search'), 'search_item':True},
                {'category':'search_history',  'title':_('Search history')} ]
    
    def __init__(self):
        printDBG("SerialeNet.__init__")
        CBaseHostClass.__init__(self, {'history':'SerialeNet', 'cookie':'serialenet.cookie'})
        self.seasonsCache = []
    
    def _cleanHtmlStr(self, str):
        str = str.replace('<', ' <').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        return self.cm.ph.removeDoubles(clean_html(str), ' ').strip()
        
    def _getStr(self, v, default=''):
        return clean_html(self._encodeStr(v, default))
        
    def _encodeStr(self, v, default=''):
        if type(v) == type(u''): return v.encode('utf-8')
        elif type(v) == type(''): return v
        else: return default
            
    def _getFullUrl(self, url, baseUrl=None):
        if None == baseUrl: baseUrl = SerialeNet.MAIN_URL
        if 0 < len(url) and not url.startswith('http'):
            url =  baseUrl + url
        return url
        
    def _getNormalizeStr(self, txt, idx=None):
        POLISH_CHARACTERS = {u'ą':u'a', u'ć':u'c', u'ę':u'ę', u'ł':u'l', u'ń':u'n', u'ó':u'o', u'ś':u's', u'ż':u'z', u'ź':u'z',
                             u'Ą':u'A', u'Ć':u'C', u'Ę':u'E', u'Ł':u'L', u'Ń':u'N', u'Ó':u'O', u'Ś':u'S', u'Ż':u'Z', u'Ź':u'Z',
                             u'á':u'a', u'é':u'e', u'í':u'i', u'ñ':u'n', u'ó':u'o', u'ú':u'u', u'ü':u'u',
                             u'Á':u'A', u'É':u'E', u'Í':u'I', u'Ñ':u'N', u'Ó':u'O', u'Ú':u'U', u'Ü':u'U',
                            }
        txt = txt.decode('utf-8')
        if None != idx: txt = txt[idx]
        nrmtxt = unicodedata.normalize('NFC', txt)
        ret_str = []
        for item in nrmtxt:
            if ord(item) > 128:
                item = POLISH_CHARACTERS.get(item)
                if item: ret_str.append(item)
            else: # pure ASCII character
                ret_str.append(item)
        return ''.join(ret_str).encode('utf-8')
            
    def _isalpha(self, txt, idx=None):
        return self._getNormalizeStr(txt, idx).isalpha()
        
    def decodeJS(self, s):
        ret = ''
        try:
            if len(s) > 0:
               js = 'unpack' + s[s.find('}(')+1:-1]
               js = js.replace("unpack('",'''unpack("''').replace(");'",''');"''').replace("\\","/")
               js = js.replace("//","/").replace("/'","'")
               js = "self." + js
               match = re.compile("\('(.+?)'").findall(eval(js))
               if len(match) > 0:
                  ret = base64.b64decode(binascii.unhexlify(match[0].replace("/x","")))
        except: printExc()
        return ret

    def unpack(self, p, a, c, k, e=None, d=None):
        for i in xrange(c-1,-1,-1):
            if k[i]:
               p = re.sub('\\b'+self.int2base(i,a)+'\\b', k[i], p)
        return p
        
    def int2base(self, x, base):
        digs = string.digits + string.lowercase + string.uppercase
        if x < 0: sign = -1
        elif x==0: return '0'
        else: sign = 1
        x *= sign
        digits = []
        while x:
            digits.append(digs[x % base])
            x /= base
        if sign < 0:
            digits.append('-')
        digits.reverse()
        return ''.join(digits)
        
    def _listsSeries(self, url):
        printDBG("SerialeNet.listsSeriesByLetter")
        url = self._getFullUrl(url)
        sts, data = self.cm.getPage(url)
        if sts:
            data = self.cm.ph.getDataBeetwenMarkers(data, '<ul id="list" class="bottom">', '<script>', False)[1]
            retTab = []
            match = re.compile('<a href="([^"]+?)"[^>]*?>(.+?)</a>').findall(data)
            for item in match:
                tmp = item[1].split('<p>')
                t1 = self._cleanHtmlStr(tmp[0])
                if len(t1):
                    if 1 < len(tmp): t2 = self._cleanHtmlStr(tmp[1])
                    else: t2 = ''
                    retTab.append({'t1':t1, 't2':t2, 'url':self._getFullUrl(item[0])})
            return retTab
        return []
        
    def listsTab(self, tab, cItem):
        printDBG("SerialeNet.listsMainMenu")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            self.addDir(params)

    def listABC(self, cItem, category):
       abcTab = self.cm.makeABCList()
       for item in abcTab:
            params = dict(cItem)
            params.update({'title':item, 'letter':item, 'category':category})
            self.addDir(params)
    
    def listsSeriesByLetter(self, cItem, category):
        printDBG("SerialeNet.listsSeriesByLetter")
        letter = cItem.get('letter', '')
        match = self._listsSeries(cItem['url'])
        for item in match:
            t1 = item['t1']
            t2 = item['t2']
            match = False
            if letter.isalpha():
                if letter == self._getNormalizeStr(t1, 0).upper():
                    match = True
                elif len(t2) and letter == self._getNormalizeStr(t2, 0).upper():
                    match = True
                    t1,t2 = t2,t1
            else:
                if not self._isalpha(t1, 0):
                    match = True
                elif len(t2) and not self._isalpha(t2, 0):
                    match = True
                    t1,t2 = t2,t1
            if match:
                params = dict(cItem)
                if len(t2): t1 += ' (%s)' % t2
                params.update({'title':t1, 'url':item['url'], 'category':category})
                self.addDir(params)
        self.currList.sort(key=lambda item: item['title'])

    def listSeasons(self, cItem, category):
        printDBG("SerialeNet.listSeasons")
        url = self._getFullUrl(cItem['url'])
        self.seasonsCache = []
        sts, data = self.cm.getPage(url)
        if sts:
            desc  = self.cm.ph.getDataBeetwenMarkers(data, '<div id="desc">', '</div>', False)[1]
            icon = self._getFullUrl(self.cm.ph.getSearchGroups(desc, 'src="([^"]+?)"')[0])
            desc = self._cleanHtmlStr(desc)
            data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="wrp1"><br/>', '<script>', False)[1]
            data = data.split('<div')
            if len(data): del data[0]
            for item in data:
                sts, seasonName = self.cm.ph.getDataBeetwenMarkers(item, '<h3>', '</h3>', False)
                if sts: 
                    self.seasonsCache.append({'title':seasonName, 'episodes':[]})
                    episodes = re.findall('<a title="([^"]*?)"[^>]+?href="([^"]+?)"[^>]*?>(.+?)</a>', item)
                    for e in episodes:
                        self.seasonsCache[-1]['episodes'].append({'title':self._cleanHtmlStr(e[2]), 'url':e[1]})
            
            if 1 < len(self.seasonsCache):
                seasonsId = 0
                for item in self.seasonsCache:
                    params = dict(cItem)
                    params.update({'seasons_id':seasonsId, 'title':item['title'], 'category':category, 'icon':icon, 'desc':desc})
                    self.addDir(params)
                    seasonsId += 1
            elif 1 == len(self.seasonsCache):
                cItem.update({'seasons_id':0})
                self.listEpisodes(cItem)
    
    def listEpisodes(self, cItem):
        seasonsID = cItem.get('seasons_id', -1)
        if -1 < seasonsID and seasonsID < len(self.seasonsCache):
            season = self.seasonsCache[seasonsID]
            printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>> listEpisodes[%s]" % season)
            for item in season['episodes']:
                params = dict(cItem)
                params.update(item)
                self.addVideo(params)
               
    def listLastUpdated(self, cItem, category):
        printDBG("SerialeNet.listLastUpdated")
        url = self._getFullUrl(cItem['url'])
        sts, data = self.cm.getPage(url)
        if sts:
            data = self.cm.ph.getDataBeetwenMarkers(data, '<h2>Ostatnio dodane</h2> <div class="item">', '<script>', False)[1]
            data = data.split('<div class="item">')
            for item in data:
                desc  = self._cleanHtmlStr(item)
                icon  = self._getFullUrl(self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0])
                title = self._cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<p id="s_title">', '</p>', False)[1])
                url   = self._getFullUrl(self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0])
                params = dict(cItem)
                params.update({'title':title, 'category':category, 'icon':icon, 'desc':desc, 'url':url})
                self.addDir(params)
                    
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("SerialeNet.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        keywordList = self._getNormalizeStr(searchPattern).upper().split(' ')
        keywordList = set(keywordList)
        if len(keywordList):
            series  = self._listsSeries(SerialeNet.MAIN_URL)
            for item in series:
                txt = self._getNormalizeStr( (item['t1'] + ' ' +  item['t2']) ).upper()
                txtTab = txt.split(' ')
                matches = 0
                for word in keywordList:
                    if word in txt: matches += 1
                    if word in txtTab: matches += 10
                if 0 < matches:
                    title = item['t1']
                    if len(item['t2']): title += ' (%s)' % item['t2']
                    params = dict(cItem)
                    params.update({'title':title, 'url':item['url'], 'matches':matches})
                    self.addDir(params)
            self.currList.sort(key=lambda item: item['matches'], reverse=True)
    
    def getLinksForVideo(self, cItem):
        videoUrlTab = []
        baseUrl   = self._getFullUrl( cItem['url'] )
        try:
            sts, data = self.cm.getPage( baseUrl )
            verUrl = self._getFullUrl(self.cm.ph.getSearchGroups(data, '<iframe id="framep" class="radi" src="([^"]+?)"')[0])
            sts, data = self.cm.getPage( verUrl )
            versions = []
            sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<b>Wersja:</b>', '<script>', False)
            if sts:
                data = data.split('<input')
                if len(data): del data[0]
                for item in data:
                    name  = self.cm.ph.getSearchGroups(item, 'name="([^"]+?)"')[0]
                    value = self.cm.ph.getSearchGroups(item, 'value="([^"]+?)"')[0]
                    versions.append({'title':value, 'url': verUrl + ('&wi=va&%s=%s' % (name, value) )})
            else:
                versions.append({'title':'', 'url': verUrl + '&wi=va'})
            for item in versions:
                try:
                    url = item['url']
                    sts, data = self.cm.getPage( url )
                    videoUrl = ''
                    if "url: escape('http" in data:
                        match = re.search("url: escape\('([^']+?)'", data)
                        if match: videoUrl = match.group(1)
                    elif "eval(function(p,a,c,k,e,d)" in data:
                        printDBG( 'Host resolveUrl packed' )
                        match = re.search('eval\((.+?),0,{}\)\)', data, re.DOTALL)
                        if match: videoUrl = self.decodeJS('eval(' + match.group(1) + ',0,{}))')
                    elif "var flm = '" in data:
                        printDBG( 'Host resolveUrl var flm' )
                        match = re.search("var flm = '([^']+?)';", data)
                        if match: videoUrl = match.group(1)
                    elif 'primary: "html5"' in data:
                        printDBG( 'Host resolveUrl html5' )
                        match = re.search('file: "([^"]+?)"', data)
                        if match: videoUrl = match.group(1)
                    if videoUrl.startswith('http'):
                        videoUrlTab.append({'name':item['title'], 'url':videoUrl})
                    printDBG("SerialeNet.getLinksForVideo >>>>>>>>>>>>>>>> videoUrl[%s]" % videoUrl)
                except: printExc()
        except: printExc()
        return videoUrlTab 
        
    def getVideoLink(self, url):
        printDBG("getVideoLink url [%s]" % url)
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('SerialeNet.handleService start')

        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "SerialeNet.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = [] 

        if None == name:
            self.listsTab(SerialeNet.CAT_TAB, {'name':'category'})
    #ABC
        elif category == 'abc_menu':
            self.listABC(self.currItem, 'series_by_letter')
    #BY LETTER
        elif category == 'series_by_letter':
            self.listsSeriesByLetter(self.currItem, 'seasons')
    #SEASONS
        elif category == 'seasons':
            self.listSeasons(self.currItem, 'episodes')
    #EPISODES
        elif category == 'episodes':
            self.listEpisodes(self.currItem)
    #LAST UPDATED
        elif category == 'last_update':
            self.listLastUpdated(self.currItem, 'seasons')
    #WYSZUKAJ
        elif category == "search":
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category', 'category':'seasons'}) 
            self.listSearchResult(cItem, searchPattern, searchType)
    #HISTORIA WYSZUKIWANIA
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, SerialeNet(), True)
    
    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('tvpvodlogo.png')])

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
            if '' == icon: icon = SerialeNet.DEFAULT_ICON
            
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
