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
config.plugins.iptvplayer.playpuls_defaultformat = ConfigSelection(default = "999999", choices = [("0", "najgorsza"), ("999999", "najlepsza")])
config.plugins.iptvplayer.playpuls_usedf = ConfigYesNo(default = False)
config.plugins.iptvplayer.playpuls_proxy = ConfigYesNo(default = False)

def GetConfigList():
    optionList = []
    optionList.append( getConfigListEntry( "Domyślny jakość video:", config.plugins.iptvplayer.playpuls_defaultformat ) )
    optionList.append( getConfigListEntry( "Używaj domyślnej jakości video:", config.plugins.iptvplayer.playpuls_usedf ) )
    optionList.append( getConfigListEntry( "PlayPuls korzystaj z proxy?", config.plugins.iptvplayer.playpuls_proxy) )
    return optionList
###################################################

def gettytul():
    return 'PlayPuls'

class Playpuls(CBaseHostClass):
    MAINURL = 'http://playpuls.pl/'
    SEARCH_URL = MAINURL + 'search/node/'
    
    def __init__(self):
        printDBG("Playpuls.__init__")
        CBaseHostClass.__init__(self, {'history':'Playpuls', 'proxyURL': config.plugins.iptvplayer.proxyurl.value, 'useProxy': config.plugins.iptvplayer.playpuls_proxy.value})        
        self.cacheMenuTree = []
    
    def _cleanHtmlStr(self, str):
        str = str.replace('<', ' <').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        return self.cm.ph.removeDoubles(clean_html(str), ' ').strip()
    
    def listsMainMenu(self):
        printDBG("Playpuls.listsMainMenu")
        sts, data = self.cm.getPage(Playpuls.MAINURL)
        if sts:
            menuData = self.cm.ph.getDataBeetwenMarkers(data, '<div id="navigation">', '</div>', False)[1]
            menuData = re.compile('<li class="menu__item menu-[0-9]+? menuparent[^"]*?"><a href="[/]*?([^"]+?)" title="([^"]+?)" class="menu__link">([^<]+?)</a>').findall(menuData)
            for item in menuData:
                if item[1] in 'Filmy': continue
                params = {'name':'category', 'title':item[1], 'category':'menu', 'url':Playpuls.MAINURL + item[0]}
                self.addDir(params)
            #
            self.addDir({'name':'category', 'title':'Wyszukaj',              'category':'Wyszukaj'})
            self.addDir({'name':'category', 'title':'Historia wyszukiwania', 'category':'Historia wyszukiwania'})
        
    def listCategory(self, cItem, searchMode=False):
        printDBG("Playpuls.listCategory cItem[%s]" % cItem)
        data = None
        if 'data' not in cItem:
            sts, data = self.cm.getPage(cItem['url'])
            if not sts: return
            if searchMode:
              data = self.cm.ph.getDataBeetwenMarkers(data, '<ol class="search-results', '</ol>', False)[1]
            elif '<div class="region region-vod-list">' in data:
                data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="region region-vod-list">', '</section>', False)[1]
                data = data.split('<div class="line-break">')
                del data[0]
                tmpList = []
                for item in data:
                    title = self.cm.ph.getDataBeetwenReMarkers(item, re.compile('<h2[^>]*?>'), re.compile('</h2>'), False)[1].strip()
                    if '' == title or 'Zobacz również' in title:
                        continue
                    tmpList.append({'title':title, 'data':item})
                if 1 == len(tmpList):
                    data = tmpList[0]['data']
                elif 1 < len(tmpList):
                    for item in tmpList:
                        params = dict(cItem)
                        params.update(item)
                        self.addDir(params)
                    data = None
                else:
                    printExc()
                    data = None
            else:
                data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="view-content">', '</section>', False)[1]
        else:
            data = cItem['data']
        if None != data:
            self._listItems(data)
        
    def _listItems(self, data):
        printDBG("Playpuls._listItems")
        data = data.split(' row">')
        del data[0]
        descMarker = '<div class="video-description">'
        for idx in range(len(data)):
            if idx < len(data)-1: item = data[idx] + '>'
            else: item = data[idx]
            #printDBG("============================================")
            #printDBG(item)
            #printDBG("============================================")
            url  = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            icon = self.cm.ph.getSearchGroups(item, 'class="cover" src="([^"]+?)"')[0]
            if '' == icon: icon = self.cm.ph.getSearchGroups(item, 'class="screenshot" src="([^"]+?)"')[0]
            
            # parse title
            title = self._cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(item, '<div class="video-caption">', '</div>', False)[1])
            if '' == title: title = self.cm.ph.getDataBeetwenMarkers(item, '<h3>', '</h3>', False)[1]
            if '' == title: title = self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0]
            
            # parse description
            if descMarker in item: desc = self._cleanHtmlStr(item.split(descMarker)[-1])
            else: desc  = self._cleanHtmlStr(item)#self.cm.ph.getDataBeetwenMarkers(item, '<p>', '</p>', False)[1]
            
            if '/vod' in url:
                category = 'vod'
            else:
                category = 'menu'
            if '' != url:
                params = {'name':'category', 'category':category, 'title':title, 'url':Playpuls.MAINURL+url, 'icon':icon, 'desc':desc}
                if 'vod' == category: self.addVideo(params)
                else: self.addDir(params)
                
    def getLinksForVideo(self, cItem):
        printDBG("Playpuls.getLinksForVideo [%s]" % cItem['url'])
        videoUrls =[]
        sts, data = self.cm.getPage(cItem['url'])
        if sts:
            data = self.cm.ph.getSearchGroups(data, "var source = '([^']+?)'")[0]
            data = 'http://redir.atmcdn.pl/hls/o2/pulstv/vod/' + data + '/hls/playlist.hls/playlist.m3u8'
            videoUrls = getDirectM3U8Playlist(data, checkExt=False)
            if 0 < len(videoUrls):
                max_bitrate = int(config.plugins.iptvplayer.playpuls_defaultformat.value)
                def __getLinkQuality( itemLink ):
                    return int(itemLink['bitrate'])
                videoUrls = CSelOneLink(videoUrls, __getLinkQuality, max_bitrate).getSortedLinks()
                if config.plugins.iptvplayer.playpuls_usedf.value:
                    videoUrls = [videoUrls[0]]            
        return videoUrls
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('Playpuls.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "Playpuls.handleService: ---------> name[%s], category[%s] " % (name, category) )
        self.currList = []
        
        if None == name:
            self.listsMainMenu()
        elif 'menu' == category:
            self.listCategory(self.currItem)
    #WYSZUKAJ
        elif category == "Wyszukaj":
            self.listCategory({'url':Playpuls.SEARCH_URL + searchPattern}, True)
    #HISTORIA WYSZUKIWANIA
        elif category == "Historia wyszukiwania":
            self.listsHistory()
        else:
            printExc()

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Playpuls(), True)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('playpulslogo.png')])

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
