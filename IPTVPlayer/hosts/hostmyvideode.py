# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
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
config.plugins.iptvplayer.myvideode_proxyenabled = ConfigYesNo(default = False)
config.plugins.iptvplayer.myvideode_sortby = ConfigSelection(default = "", choices = [("", _("Relevance")), ("creationDate", _("Upload date")),("movieTotalViewCount", _("View count")),("movieRating", _("Rating")),("alphaSort", _("Alphabetically"))])            
###################################################
# Config options for HOST
###################################################
def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Use German proxy for link request"), config.plugins.iptvplayer.myvideode_proxyenabled))
    optionList.append(getConfigListEntry(_("Sort search result by"), config.plugins.iptvplayer.myvideode_sortby))
    return optionList
###################################################

def gettytul():
    return 'MyVideo.de'

class MyVideo(CBaseHostClass):
    MAINURL  = 'http://www.myvideo.de/'
    SEARCH_URL = MAINURL + 'search?q=%s&category=%s&sortField=%s&spellCheckRejected=true&_format=ajax'
    SEARCH_NAV_URL = '&rows=10&start=%d&nextButtonCounter=%d'
    
    MAIN_ADD_TAB = [{'category': 'community_sort',        'title': 'Community', 'url':'/Videos_A-Z'}, \
                    {'category': 'Historia wyszukiwania', 'title': _("Search history")}, \
                    {'category': 'Wyszukaj',              'title': _("Search"), 'search_item':True}]
    def __init__(self):
        printDBG("MyVideo.__init__")
        CBaseHostClass.__init__(self, {'history':'MyVideo.de'})  
        self.menuTree = []
            
    def _checkNexPage(self, data):
        data = self.cm.ph.getDataBeetwenMarkers(data, '<nav class="paginator">', '</nav>', False)[1]
        if re.search('<a href="([^"]+?)" class="button as-next">', data):
            return True
        else:
            return False
  
    def _getJsonUrl(self, data):
        url = self.cm.ph.getSearchGroups(data, ' <a class="videolist--next button[^>]+?data-service-url="([^"]+?)"')[0]
        if url:
            url += "?page=%s&pagesize=20&_format=json"
        return url
            
    def _resolveUrl(self, url, currPath=''):
        if not url.startswith('http') and '' != url:
            if '/' == url[0]: url = url[1:]
            if '' == currPath: return MyVideo.MAINURL + url
            else: return currPath + url
        else: return url
            
    def _listVideosFromJson(self, data):
        try:
            data = json.loads( self.getStr(data) )
            for item in data['items']:
                title = self.getStr(item.get('title', ''))
                icon  = self._resolveUrl(self.getStr(item.get('thumbnail', '')))
                desc  = self.cleanHtmlStr( self.getStr(item.get('description', '')) )
                url   = self.getStr(item.get('href', ''))
                params = {'title':title, 'url':url, 'icon':icon, 'desc':desc}
                self.addVideo(params)
        except:
            printExc()
                
    def prepareMenuTree(self, cItem):
        printDBG("MyVideo.listsMainMenu")
        def _getCategoriesLinks(data):
            retTab = []
            data = re.findall('href="([^"]+?)"[^>]*?>([^<]+?)</a>', data)
            for item in data:
                title = self.cleanHtmlStr(item[1])
                url   = self.cleanHtmlStr(item[0])
                if '' != title and '' != url:
                    retTab.append({'title':title, 'url':url})
            return retTab
        sts, data = self.cm.getPage(MyVideo.MAINURL)
        if sts:
            data = self.cm.ph.getDataBeetwenMarkers(data, 'nav class="navigation">', '<script>', False)[1]
            data = data.split('<li class="navigation--item has-children">')
            if len(data): del data[0]
            for mainItem in data:
                subMenuTab = mainItem.split('<ul class="navigation--column">')
                title = self.cleanHtmlStr(subMenuTab[0])
                if title in ['TV & Serien', 'Themen', 'Community']: continue
                self.menuTree.append({'title':title})
                del subMenuTab[0]
                self.menuTree[-1]['menu_list'] = []
                if 1 == len(subMenuTab):
                    self.menuTree[-1]['menu_list'] = [{'title':'', 'menu_list': _getCategoriesLinks(subMenuTab[0])}]
                else:
                    for subItem in subMenuTab:
                        title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(subItem, '<p class="navigation--column-title">', '</p>', False)[1].replace('&nbsp;', ''))
                        if '' != title:
                            self.menuTree[-1]['menu_list'].append({'title':title, 'menu_list': _getCategoriesLinks(subItem)})
                        elif 0 < len(self.menuTree[-1]['menu_list'][-1]):
                            self.menuTree[-1]['menu_list'][-1]['menu_list'].extend(_getCategoriesLinks(subItem))
        printDBG(self.menuTree)
                
    def listsTab(self, tab, cItem, key='', value=''):
        printDBG("MyVideo.listsMainMenu")
        i = 0
        for item in tab:
            params = dict(cItem)
            params.update(item)
            if '' != key: params[key] = (value % i)
            self.addDir(params)
            i += 1

    def listsSubMenu(self, cItem, category):
        printDBG("MyVideo.listsSubMenu")
        if 1 == len(cItem['menu_list']):
            tab = cItem['menu_list'][0]['menu_list']
        else:
            tab = cItem['menu_list']
        for item in tab:
            params = dict(cItem)
            params.update(item)
            if 'url' in params:
                    params['category'] = category
            if params.get('url', '') not in ['/Musik/Musik_K%C3%Bcnstler', '/musik-tv', '/filme/kino-dvd-trailer', '/aktion/halloween']:
                self.addDir(params)
            
    def listCategoryItems(self, cItem):
        printDBG("MyVideo.listCategoryItems url[%s]" % cItem['url'])     
        type = cItem['url'].lower()
        if type.startswith('/top_100'):
            self._listTop100Type(cItem)
        elif type.startswith('/filme'):
            self.listFilmeItems(cItem)
        elif type.startswith('/musik'):
            self.listSublContent(cItem)
        
    def listSublContent(self, cItem):
        printDBG("MyVideo.listSublContent url[%s]" % cItem['url']) 
        url = self._resolveUrl(cItem['url'])
        sts, data = self.cm.getPage(url)
        if sts:
            if "<div class='lContent'>" in data:
                data = self.cm.ph.getDataBeetwenMarkers(data, "<div class='lHeadTab'>", "</table>", False)[1]
                if '' != data:
                    data = re.findall("""src='(/iframe\.php\?function=[^']+?)'[^?]*?>([^<]+?)</a>""", data)
                    for item in data:
                        url   = urllib.unquote(item[0]).replace('&amp;', '&')
                        title = self.cleanHtmlStr(item[1])
                        params = dict(cItem)
                        params.update({'category':'l_content', 'title':title, 'url':url})
                        self.addDir(params) 
                else:
                    self.listlContentItems(cItem)
            return True
        return False
        
    def _getlContentItems(self, data):
        printDBG("MyVideo._getlContentItems")
        retTab = []
        for item in data:
            for marker in ["""<a href=["'](/watch/[^'^"]+?)["'][^>]*?title=["']([^'^"]+?)["'][^>]*?>""", """<a href=["'](/watch/[^'^"]+?)["'][^>]*?>([^<]+?)</a>""", \
                           """<a href=["'](/[^'^"]+?\-m\-[0-9]+?)["'][^>]*?title=["']([^'^"]+?)["'][^>]*?>""", """<a href=["'](/[^'^"]+?\-m\-[0-9]+?)["'][^>]*?>([^<]+?)</a>""", \
                           """<a href=["'](/[^'^"]+?)["'][^>]*?title=["']([^'^"]+?)["'][^>]*?>""", """<a href=["'](/[^'^"]+?)["'][^>]*?>([^<]+?)</a>"""]:
                tmp =  self.cm.ph.getSearchGroups(item, marker, 2)
                if '' != tmp[0].strip() and '' != tmp[1].strip(): break
            icon  = self.cm.ph.getSearchGroups(item, """["'](http[^'^"]+?\.jpg)["']""")[0]
            desc  = self.cleanHtmlStr( '<fake ' + item )
            params = {'title':self.cleanHtmlStr( tmp[1] ), 'url':tmp[0].strip(), 'icon':icon, 'desc':desc}
            retTab.append(params)
        return retTab
    
    def listlContentItems(self, cItem):
        printDBG("MyVideo.listlContentItems url[%s]" % cItem['url']) 
        url = self._resolveUrl(cItem['url'])
        page = cItem.get('page', 1)
        if '?' in url:
            url += ('&lpage=%s' % page)
        sts, data = self.cm.getPage(url)
        if sts:
            # check if next page is available
            nextPage = self.cm.ph.getSearchGroups(data, """'(/[^']+?\?lpage=%s&[^']+?)'""" % (page+1))[0]
            if '' != nextPage: 
                if '?' not in url:
                    cItem['url'] = re.sub("lpage=[0-9]+?&amp;", "", nextPage)
                nextPage = True
            else: 
                nextPage = False
             
            data = data[data.find("<div class='lContent'>"):]
            if "<td class='body'>" in data:  data = data[data.find("<td class='body'>"):]
            data = data[:data.find("</td>")]
            marker = "<div class='floatLeft fRand'"
            if marker not in data: marker = "<div class='body floatLeft "
            data = data.split(marker)
            if len(data): del data[0]
            
            data = self._getlContentItems(data)
            for params in data:
                self.addVideo(params)
            if nextPage:
                params = dict(cItem)
                params.update({'title':_("Next page"), 'page':(page+1)})
                self.addDir(params)
            
    def listFilmeItems(self, cItem):
        printDBG("MyVideo.listTop100Items")
        cItem.update({'category':'filme'})
        page = cItem.get('page', 1)
        url = self._resolveUrl(cItem['url'] + ('/page/%s' % page))
        sts, data = self.cm.getPage(url)
        if sts: 
            nextPage = self._checkNexPage(data)
            if 'window.MV.contentListTooltipData' in data:
                data = self.cm.ph.getDataBeetwenMarkers(data, 'window.MV.contentListTooltipData = {', '};', False)[1]
            else: data = self.cm.ph.getDataBeetwenMarkers(data, 'window.MV.videoListTooltipData = {', '};', False)[1]
            self._listVideosFromJson('{%s}' % data)
            if nextPage:
                params = dict(cItem)
                params.update({'title':_("Next page"), 'page':(page+1)})
                self.addDir(params)
    
    def _listTop100Type(self, cItem):
        printDBG("MyVideo.listCategoryItems url[%s]" % cItem['url']) 
        url = self._resolveUrl(cItem['url'])
        sts, data = self.cm.getPage(url)
        if sts: 
            data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="dropdown dropdown--filters', '<div class="dropdown--anchor">', False)[1]
            data = re.findall('href="([^"]+?)"[^>]*?>([^<]+?)</a>', data)
            if 2 > len(data):
                cItem.update({'category':'top_100'})
                self.listTop100Items(cItem)
                return
            for item in data:
                params = dict(cItem)
                params.update({'category':'top_100', 'title':self.cleanHtmlStr(item[1]), 'url':item[0]})
                self.addDir(params)
            
    def listTop100Items(self, cItem):
        printDBG("MyVideo.listTop100Items")
        page = cItem.get('page', 1)
        url = self._resolveUrl(cItem['url'])
        if 1 < page: 
            url = url % page
        sts, data = self.cm.getPage(url)
        if sts: 
            if 1 == page:
                jsonUrl = self._getJsonUrl(data)
                sts, data = self.cm.getPage(self._resolveUrl(jsonUrl % page))
            else:
                jsonUrl = cItem['url']
            self._listVideosFromJson(data)
            page += 1
            try:
                sts, data = self.cm.getPage(self._resolveUrl(jsonUrl % page))
                data = json.loads( self.getStr(data) )
                if 0 < len(data['items']):
                    params = dict(cItem)
                    params.update({'title':_("Next page"), 'url':jsonUrl, 'page':page})
                    self.addDir(params)
            except:
                printExc()
    
    def listCommunitySortOrder(self, cItem, category):
        printDBG("MyVideo.listCommunitySortOrder")
        url = self._resolveUrl(cItem['url'])
        sts, data = self.cm.getPage(url)
        if sts:
            data = self.cm.ph.getDataBeetwenMarkers(data, "<select id='searchOrder'", "</select>", False)[1]
            data = re.findall("<option value='([^']+?)'[^>]*?>([^<]+?)</option>", data)
            for item in data:
                params = dict(cItem)
                params.update({'title':item[1], 'sort_order':item[0], 'category':category})
                self.addDir(params)
                
    def listCommunityCategories(self, cItem, category):
        printDBG("MyVideo.listCommunityCategories")
        url = self._resolveUrl('/Videos_A-Z/Videos_in_Kategorien')
        sts, data = self.cm.getPage(url)
        if sts:
            data = self.cm.ph.getDataBeetwenMarkers(data, "<div class='lContent'>", "<div class='clear'>", False)[1]
            marker = "<div class='body floatLeft "
            data = data.split(marker)
            if len(data): del data[0]
            data = self._getlContentItems(data)
            if len(data):   
                params = dict(cItem)
                params.update({'title':_("--All--"), 'url':'/Videos_A-Z?searchWord=&searchOrder=' +  cItem['sort_order'], 'category':category})
                self.addDir(params)
            for item in data:
                params = dict(cItem)
                params.update(item)
                params['category'] = category
                tmp = params['url'].split('&searchOrder=')
                params['url'] = tmp[0] + ('&searchOrder=%s' % cItem['sort_order'])
                self.addDir(params)
                
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("MyVideo.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        url = MyVideo.SEARCH_URL % (searchPattern.replace(' ', '+'), searchType, config.plugins.iptvplayer.myvideode_sortby.value)
        self.listSearchItems({'name':'category', 'category':'list_search_items', 'url':url+MyVideo.SEARCH_NAV_URL})
        return
        
    def listSearchItems(self, cItem):
        printDBG("MyVideo.listSearchItems")
        page = cItem.get('page', 0)
        def _getUrl(url, page):
            return self._resolveUrl(url % (page*10, page))
        url = _getUrl(cItem['url'], page)
        sts, data = self.cm.getPage(url)
        if sts:
            data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="results--video ">', "Results -->")[1]
            data = data.split('<div class="results--video ">')
            del data[0]
            data = self._getlContentItems(data)
            for params in data:
                self.addVideo(params)                
            sts, data = self.cm.getPage(_getUrl(cItem['url'], page+1))
            if sts and '<div class="results--video ">' in data:
                params = dict(cItem)
                params.update({'title':_("Next page"), 'page':(page+1)})
                self.addDir(params)

    def getLinksForVideo(self, cItem):
        printDBG("MyVideo.getLinksForVideo [%s]" % cItem['url'])
        if len(cItem.get('url_cache', [])):
            return cItem['url_cache']
        urlTab = []
        url = self._resolveUrl(cItem['url'])
        if config.plugins.iptvplayer.myvideode_proxyenabled.value and '' != config.plugins.iptvplayer.german_proxyurl.value:
            url = strwithmeta(url, {'http_proxy':config.plugins.iptvplayer.german_proxyurl.value})
        urlTab = self.up.getVideoLinkExt(url)
        if len(urlTab):
            cItem['url_cache'] = urlTab
        return urlTab
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('MyVideo.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "MyVideo.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = []
        
        if None == name:
            self.prepareMenuTree(self.currItem)
            self.listsTab(self.menuTree, {'name':'category', 'category':'sub_menu'})
            self.listsTab(MyVideo.MAIN_ADD_TAB, {'name':'category'})
        elif 'sub_menu' == category:
            self.listsSubMenu(self.currItem, 'cat_list')
    #LIST CATEGORY ITEMS
        elif 'cat_list' == category:
            self.listCategoryItems(self.currItem)
    #LIST TOP 100 ITEMS   
        elif 'top_100' == category:
            self.listTop100Items(self.currItem)
    #LIST FILME ITEMS
        elif 'filme' == category:
            self.listFilmeItems(self.currItem)
    #LIST L_CONTENT ITEMS
        elif 'l_content' == category:
            self.listlContentItems(self.currItem) 
    #LIST COMMUNITY SORT ORDER
        elif 'community_sort' == category:
            self.listCommunitySortOrder(self.currItem, 'list_community_cat')
    #LIST COMMUNITY CATEGORIES
        elif 'list_community_cat' == category:
            self.listCommunityCategories(self.currItem, 'l_content')
    #LIST SEARCH ITEMS
        elif 'list_search_items' == category:
            self.listSearchItems(self.currItem)
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
        CHostBase.__init__(self, MyVideo(), True)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('myvideodelogo.png')])

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
        searchTypesOptions.append(("MUSIC", "MUSIC"))
        #searchTypesOptions.append(("TV", "TV"))
        searchTypesOptions.append(("FILM", "FILM"))
        #searchTypesOptions.append(("CHANNEL", "CHANNEL"))
        searchTypesOptions.append(("COMMUNITY", "COMMUNITY"))
    
        for cItem in cList:
            hostLinks = []
            type = CDisplayListItem.TYPE_UNKNOWN
            possibleTypesOfSearch = None

            if cItem['type'] == 'category':
                if cItem.get('search_item', False):
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
