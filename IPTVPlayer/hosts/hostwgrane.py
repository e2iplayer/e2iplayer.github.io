# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, CSearchHistoryHelper, remove_html_markup, GetLogoDir
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
###################################################

###################################################
# FOREIGN import
###################################################
import re

###################################################

###################################################
# Config options for HOST
###################################################

def GetConfigList():
    return []
###################################################


def gettytul():
    return 'Wgrane.pl'

class Wgrane:
    MAINURL = 'http://www.wgrane.pl'
    CAT_URL = MAINURL + '/categories.html'
    VID_URL = MAINURL + '/watch.html?category=%s&sort=%s&page=%s'
    SEARCH_URL = MAINURL + '/szukaj/'

    SERVICE_MENU_TABLE = {
        1: "Kategorie",
        2: "Wyszukaj",
        3: "Historia wyszukiwania"
    }
    
    SORT_FILTERS_TABLE = [{'title':'Ostatnio dodane',         'sort':''        },
                          {'title':'Najczęściej oglądane',    'sort':'views'   },
                          {'title':'Najwyżej oceniane',       'sort':'points'  },
                          {'title':'Najczęściej komentowane', 'sort':'comments'},
                          {'title':'Ostatnio oglądane',       'sort':'recent'  }]
 
    def __init__(self):
        self.up = urlparser.urlparser()
        self.cm = common()
        self.history = CSearchHistoryHelper('Wgrane')
        # temporary data
        self.currList = []
        self.currItem = {}

    def getCurrList(self):
        return self.currList

    def setCurrList(self, list):
        self.currList = list
        
    def getCurrItem(self):
        return self.currItem

    def setCurrItem(self, item):
        self.currItem = item

    def addDir(self, params):
        params['type'] = 'category'
        self.currList.append(params)
        return
        
    def playVideo(self, params):
        params['type'] = 'video'
        self.currList.append(params)
        return
        
    def setTable(self):
        return self.SERVICE_MENU_TABLE

    def listsMainMenu(self, table):
        for num, val in table.items():
            params = {'name': 'main-menu', 'title': val, 'category': val}
            self.addDir(params)
            
    def listCategories(self, url, cat):
        printDBG("listCategories for url[%s] cat[%s]" % (url, cat))
        # add all item
        params = {'category': cat, 'title': '--Wszystkie--' , 'cat_id': ''}
        self.addDir(params)

        sts, data = self.cm.getPage(url)
        if not sts: return
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, "<div class='window_title'>", "<div class='footer'>")
        if not sts: return False
        data = data.split("<div class='list_title'>")
        if len(data) > 1:
            del data[0]
            for item in data:
                # cat_id: match.group(2) & title: match.group(1) & img: self.MAINURL + match.group(3)
                match = re.search("<b>([^<]+?)</b></a></div><a href='[^']*?category=([0-9]+?)'><img[^>]*?src='([^']+?)'", item)
                if not match: continue
                # plot
                printDBG('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA: [%s]' % match.group(2))
                plot = CParsingHelper.removeDoubles(remove_html_markup(item, ' ').replace(match.group(1), ''), ' ')
                params = {'category': cat, 'title': match.group(1) , 'cat_id': match.group(2) , 'icon': self.MAINURL + "/" + match.group(3), 'plot':plot}
                self.addDir(params)
                
    def listFilters(self, table, cat, cat_id, icon):
        printDBG("listFilters for cat[%s] cat_id[%s]" % (cat, cat_id))
        for item in table:
            item['category'] = cat
            item['cat_id'] = cat_id
            item['icon'] = icon
            self.addDir(item)
            
                    
    def listVideos(self, baseUrl, cat, cat_id, sort, page, search_pattern = ''):
        url = baseUrl % (cat_id, sort, page)
        printDBG("listVideos for url[%s]" % url)

        sts, data = self.cm.getPage(url)
        if not sts: return
        
        nextPage = False
        if -1 < data.find("class='black'>&raquo;</a>"):
            nextPage = True

        sts, data = CParsingHelper.getDataBeetwenMarkers(data, "<div class='window_title'>", "<div class='footer'>")
        if not sts: return False
        data = data.split("<div class='list' style='width: 173px;'>")
        if len(data) > 1:
            del data[0]
            for item in data:
                # vid_hash & img
                match = re.search("href='([0-9a-fA-F]{32})'[^>]*?><img[^>]*?src='([^']+?)'", item)
                if not match: continue
                vid_hash = match.group(1)
                img = self.MAINURL + "/" + match.group(2)
                if not match: continue
                # title
                match = re.search("<div class='list_title'><a href='%s'>([^<]+?)</a></div>" % vid_hash, item)
                if not match: continue
                title = match.group(1)
                # plot
                plot = CParsingHelper.removeDoubles(remove_html_markup(item, ' ').replace(title, ''), ' ')
            
                params = { 'title': title, 'url': self.MAINURL + "/" +vid_hash, 'icon': img, 'plot': plot}
                self.playVideo(params)
            
        if nextPage:
            params = {'title': "Następna strona", 'category': cat, 'cat_id':cat_id, 'sort':sort, 'page':str(int(page)+1), 'search_pattern':search_pattern}
            self.addDir(params)
        
    def getSearchResult(self, baseUrl, cat, page):
        printDBG("getSearchResult for url[%s] page[%s]" % (baseUrl, page))
        
        if 1 < int(page) != '1': url = baseUrl + page
        else: url = baseUrl
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        nextPage = False
        if -1 < data.find("class='pagination_next'"):
            nextPage = True

        sts, data = self.getDataBeetwenMarkers(data, '<td valign="top">', '<div class="menu_dol">', withMarkers = False)
        if not sts: return
      
        data = data.split('<td valign="top">')
        for item in data:
            # url & title
            match = re.search('<div class="video_title">[^<]*?<a href="([^"]+?)">([^<]+?)</a>', item)
            if match: 
                url = match.group(1)
                title = match.group(2)
            else: continue
            # img
            match = re.search('src="([^"]+?)"', item)
            if match: img = match.group(1)
            else: img = ''
            # plot
            match = re.search('<div class="video_details">(.+?)</td>', item, re.DOTALL)
            if match: plot = remove_html_markup(match.group(1)) #.replace("</div>", " ")
            else: plot = ''
            
            params = { 'title': title, 'url': url, 'icon': img, 'plot': plot}
            self.playVideo(params)
            
        if nextPage:
            params = {'title': "Następna strona", 'url': baseUrl, 'category': cat, 'page':str(int(page)+1)}
            self.addDir(params)
                
    def listsHistory(self):
        list = self.history.getHistoryList()
        for item in list:
            params = { 'name': 'history', 'category': 'Wyszukaj', 'title': item, 'plot': 'Szukaj: "%s"' % item}
            self.addDir(params)

    def getHostingTable(self, url):
        printDBG("getHostingTable for url[%s]" % url)
        
        directUrl = self.up.getVideoLink(url)
        if directUrl:
            return [{'name': self.up.getHostName(url), 'url': directUrl}]
        else:
            return []

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        if 0 == refresh:
            if len(self.currList) <= index:
                printDBG( "handleService wrong index: %s, len(self.currList): %d" % (index, len(self.currList)) )
                return
            if -1 == index:
                # use default value
                self.currItem = { "name": None }
                printDBG( "handleService for first self.category" )
            else:
                self.currItem = self.currList[index]

        name     = self.currItem.get("name", '')
        title    = self.currItem.get("title", '')
        category = self.currItem.get("category", '')
        page     = self.currItem.get("page", '1')
        icon     = self.currItem.get("icon", '')
        url      = self.currItem.get("url", '')
        cat_id   = self.currItem.get("cat_id", '')
        sort     = self.currItem.get("sort", '')
        search_pattern = self.currItem.get("search_pattern", '') 
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsMainMenu(self.SERVICE_MENU_TABLE)
    #KATEGORIE
        elif category == "Kategorie":
            self.listCategories(self.CAT_URL, 'add_filter')
        elif category == "add_filter":
            self.listFilters(self.SORT_FILTERS_TABLE, "video_category", cat_id, icon)
        elif category == "video_category":
            self.listVideos(self.VID_URL, category, cat_id, sort, page)
    #WYSZUKAJ
        elif category == "Wyszukaj":
            pattern = searchPattern.replace(" ", "+")
            self.listVideos(self.VID_URL + "&search=" + pattern, "search_next", '', '', page, pattern)
        elif category == "search_next":
            pattern = search_pattern
            self.listVideos(self.VID_URL + "&search=" + pattern, "search_next", '', '', page, pattern)
    #HISTORIA WYSZUKIWANIA
        elif category == "Historia wyszukiwania":
            self.listsHistory()


class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Wgrane(), True)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('wgranelogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] != 'video':
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])

        retlist = []
        urlList = self.host.getHostingTable(self.host.currList[Index]["url"])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], 0))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
    def getResolvedURL(self, url):
        # resolve url to get direct url to video file
        urlTab = []
        #url = self.host.up.getVideoLink( url )
        #if isinstance(url, basestring) and url.startswith('http'):
        #    urlTab.append(url)

        return RetHost(RetHost.OK, value = urlTab)

    def convertList(self, cList):
        hostList = []
    
        for cItem in cList:
            hostLinks = []
            type = CDisplayListItem.TYPE_UNKNOWN
            possibleTypesOfSearch = None

            if cItem['type'] == 'category':
                if cItem['title'] == 'Wyszukaj':
                    type = CDisplayListItem.TYPE_SEARCH
                else:
                    type = CDisplayListItem.TYPE_CATEGORY
            elif cItem['type'] == 'video':
                type = CDisplayListItem.TYPE_VIDEO
                url = cItem.get('url', '')
                if '' != url:
                    hostLinks.append(CUrlItem("Link", url, 1))
                
            title       =  cItem.get('title', '')
            title       =  clean_html(title.decode("utf-8")).encode("utf-8")
            description =  cItem.get('plot', '')
            description =  clean_html(description.decode("utf-8")).encode("utf-8")
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
                self.host.history.addHistoryItem( pattern)
                self.searchPattern = pattern
        except:
            printDBG('setSearchPattern EXCEPTION')
            self.searchPattern = ''
        return
