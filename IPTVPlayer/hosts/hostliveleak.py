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
try:    import json
except: import simplejson as json


###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################

###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.liveleak_searchsort = ConfigSelection(default = "relevance", choices = [("relevance", _("Najtrafniejsze")), ("date", _("Najnowsze")), ("views", _("Popularność")), ("votes", _("Najlepiej oceniane"))])

def GetConfigList():
    optionList = []
    optionList.append( getConfigListEntry( _("Sortuj wyniki wyszukiwania po:"), config.plugins.iptvplayer.liveleak_searchsort ) )
    return optionList
###################################################

def gettytul():
    return 'LiveLeak.com'

class LiveLeak(CBaseHostClass):
    MAINURL  = 'http://www.liveleak.com/'
    ITEMS_BROWSE_URL = MAINURL + 'browse?'
    CHANNEL_BROWSE_URL = MAINURL + 'channel?a=browse&'
    CHANNEL_URL = MAINURL + 'c/'
    
    MAIN_CAT_TAB = [{ 'category':'tab_items',             'title':'Items'                },
                    { 'category':'tab_channels',          'title':'Channels'             },
                    { 'category':'Wyszukaj',              'title':'Wyszukaj'             },
                    { 'category':'Historia wyszukiwania', 'title':'Historia wyszukiwania'} ]
    
    ITEMS_CAT_TAB = [{ 'category':'recent_items', 'title':'Recent Items (Popular)',  'url':'selection=popular'},
                     { 'category':'recent_items', 'title':'Recent Items (All)',      'url':'selection=all'    },
                     { 'category':'recent_items', 'title':'Feature Potential Items', 'url':'upcoming=1'       },
                     { 'category':'recent_items', 'title':'Top Items (Today)',       'url':'rank_by=day'      },
                     { 'category':'recent_items', 'title':'Top Items (This Week)',   'url':'rank_by=week'     },
                     { 'category':'recent_items', 'title':'Top Items (This Month)',  'url':'rank_by=month'    },
                     { 'category':'recent_items', 'title':'Top Items (All time)',    'url':'rank_by=all_time' } ]
    
    CHANNEL_CAT_TAB = [ { 'category':'channel',  'title':'News & Politics',  'url':'news'          },
                        { 'category':'channel',  'title':'Yoursay',          'url':'yoursay'       },
                        { 'category':'channel',  'title':'Liveleakers',      'url':'liveleakers'   },
                        { 'category':'channel',  'title':'Must See',         'url':'must_see'      },
                        { 'category':'channel',  'title':'Ukraine',          'url':'ukraine'       },
                        { 'category':'channel',  'title':'Syria',            'url':'syria'         },
                        { 'category':'channel',  'title':'Entertainment',    'url':'entertainment' },
                        { 'category':'channels', 'title':'Browse Channels',  'url':''              } ] 
    
    def __init__(self):
        printDBG("LiveLeak.__init__")
        CBaseHostClass.__init__(self, {'history':'LiveLeak.com'})        
    
    def _checkNexPage(self, data):
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="pagenav">', '</ul>', False)[1]
        if 'Go to next page' in data and '<a href=' in data:
            return True
        else:
            return False
            
    def listsTab(self, tab, cItem):
        printDBG("LiveLeak.listsMainMenu")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            self.addDir(params)
    
    def _listItems(self, cItem, data, nextPage):
        printDBG('_listItems start')

        sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="item_list">', '</ul>', False)
        if sts:
            data = data[data.find('<li'):]
            data = data.split('</li>')
            del data[-1]
            for item in data:
                params = dict(cItem)
                params['name']  = 'category'
                params['title'] = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, 'alt="([^"]+?)"')[0])
                params['icon']  = self.cm.ph.getSearchGroups(item, 'src="([^"]+?\.jpg[^"]*?)"')[0]
                params['url']   = self.cm.ph.getSearchGroups(item, '<a href="([^"]+?)"')[0]
                params['desc']  = self.cleanHtmlStr(item)
                if '' != params['url'] and '' != params['title']:
                    params['name']  = 'video'
                    self.addVideo(params)
        if nextPage:
            params = dict(cItem)
            params.update({'name':'category', 'title':_('Następna strona'), 'page':str(int(cItem.get('page', '1'))+1)})
            self.addDir(params)
                
    def listRecentItems(self, cItem):
        printDBG('listRecentItems start')
        page = cItem.get('page', '1')
        url = LiveLeak.ITEMS_BROWSE_URL + cItem['url'] + '&page=' + page
        sts, data = self.cm.getPage(url)
        if sts:
            nextPage = self._checkNexPage(data)
            self._listItems(cItem, data, nextPage)
        
    def listChannels(self, cItem):
        printDBG('listChannels start')
        page = cItem.get('page', '1')
        url = LiveLeak.CHANNEL_BROWSE_URL + cItem['url'] + '&page=' + page
        sts, data = self.cm.getPage(url)
        if sts:
            nextPage = self._checkNexPage(data)
            
            marker = '<ul class="item_grid">'
            if marker not in data:
                marker = '<ul class="item_list">'
            sts, data = self.cm.ph.getDataBeetwenMarkers(data, marker, '</ul>', False)
            if sts:
                data = data[data.find('<li'):]
                data = data.split('</li>')
                del data[-1]
                for item in data:
                    params = dict(cItem)
                    params['name']  = 'category'
                    params['title'] = self.cleanHtmlStr(self.cm.ph.getSearchGroups(item, 'title="([^"]+?)"')[0])
                    params['icon']  = self.cm.ph.getSearchGroups(item, 'src="([^"]+?\.jpg[^"]*?)"')[0]
                    params['url']   = self.cm.ph.getSearchGroups(item, '/c/([^"]+?)"')[0]
                    params['desc']  = self.cleanHtmlStr(item)
                    params['category'] = 'channel'
                    if '' != params['url'] and '' != params['title']:
                        self.addDir(params)
            if nextPage:
                params = dict(cItem)
                params.update({'name':'category', 'title':_('Następna strona'), 'page':str(int(cItem.get('page', '1'))+1)})
                self.addDir(params)
    
    def listChannelItems(self, cItem):
        printDBG('listChannelItems start')
        page          = cItem.get('page', '1')
        if 'channel_token' not in  cItem:
            url = LiveLeak.CHANNEL_URL + cItem['url']
            sts, data = self.cm.getPage(url)
            if not sts: return
            cItem['channel_token'] = self.cm.ph.getSearchGroups(data, 'channel_token=([^&]+?)&')[0]
        channel_token = cItem.get('channel_token', '')
        url = LiveLeak.ITEMS_BROWSE_URL + ('container_id=channel_items_%s&channel_token=%s&ajax=1&page=%s' % (channel_token, channel_token, page)) 
        sts, data = self.cm.getPage(url)
        if sts:
            nextPage = self._checkNexPage(data)
            self._listItems(cItem, data, nextPage)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("LiveLeak.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        if 'items' == searchType:
            sort = config.plugins.iptvplayer.liveleak_searchsort.value
            params = dict(cItem)
            params.update({ 'category':'recent_items',  'url':'q=%s&sort_by=%s' % (searchPattern.replace(' ', '+'), sort)})
            self.listRecentItems(params)
        else:
            sort = config.plugins.iptvplayer.liveleak_searchsort.value
            params = dict(cItem)
            params.update({ 'category':'channels',  'url':'q=%s&sort_by=%s' % (searchPattern.replace(' ', '+'), sort)})
            self.listChannels(params)
        
    def getLinksForVideo(self, cItem):
        printDBG("LiveLeak.getLinksForVideo [%s]" % cItem['url'])
        return self.up.getVideoLinkExt(cItem['url'])
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('LiveLeak.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "LiveLeak.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = []
        
        if None == name:
            self.listsTab(LiveLeak.MAIN_CAT_TAB, {'name':'category'})
    #ITEMS TAB
        elif 'tab_items' == category:
            self.listsTab(LiveLeak.ITEMS_CAT_TAB, self.currItem)
    #CHANNELS TAB
        elif 'tab_channels' == category:
            self.listsTab(LiveLeak.CHANNEL_CAT_TAB, self.currItem)
    #LIST ITEMS
        elif 'recent_items' == category:
            self.listRecentItems(self.currItem)
    #BROWSE CHANNELS
        elif 'channels' == category:
            self.listChannels(self.currItem)
    #LIST CHANNEL ITEMS
        elif 'channel' == category:
            self.listChannelItems(self.currItem)
    #WYSZUKAJ
        elif category in ["Wyszukaj", "search_next_page"]:
            self.listSearchResult(self.currItem, searchPattern, searchType)
    #HISTORIA WYSZUKIWANIA
        elif category == "Historia wyszukiwania":
            self.listsHistory()
        else:
            printExc()

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, LiveLeak(), True)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('liveleaklogo.png')])

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
        searchTypesOptions.append(("Items", "items"))
        searchTypesOptions.append(("Channel", "channel"))
    
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
            description =  clean_html(cItem.get('desc', '')) + clean_html(cItem.get('plot', ''))
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
