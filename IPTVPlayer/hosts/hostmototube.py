# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, CSearchHistoryHelper, remove_html_markup, GetLogoDir
import Plugins.Extensions.IPTVPlayer.libs.pCommon as pCommon
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
    return 'MotoTube'

class AleKinoTV:
    MAINURL = 'http://www.mototube.pl'
    SEARCH_URL = MAINURL + '/szukaj/'

    SERVICE_MENU_TABLE = {
        1: "Kategorie",
        2: "Wyszukaj",
        3: "Historia wyszukiwania"
    }
 
    def __init__(self):
        self.up = urlparser.urlparser()
        self.cm = pCommon.common()
        self.history = CSearchHistoryHelper('MotoTube')
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
    
    def fWrite(self, file, data):
        #helper to see html returned by ajax
        file_path = '/mnt/hdd/' + file
        text_file = open(file_path, "w")
        text_file.write(data)
        text_file.close()    

    def getDataBeetwenMarkers(self, data, marker1, marker2, withMarkers = True):
        idx1 = data.find(marker1)
        if -1 == idx1: return False, None
        idx2 = data.find(marker2, idx1 + len(marker1))
        if -1 == idx2: return False, None
        
        if withMarkers:
            idx2 = idx2 + len(marker2)
        else:
            idx1 = idx1 + len(marker1)

        return True, data[idx1:idx2]

    def setTable(self):
        return self.SERVICE_MENU_TABLE

    def listsMainMenu(self, table):
        for num, val in table.items():
            params = {'name': 'main-menu', 'title': val, 'category': val}
            self.addDir(params)
            
    def listCategories(self, url, cat):
        printDBG("listCategories for url[%s] cat[%s]" % (url, cat))
        sts, data = self.cm.getPage(url)
        if not sts: return
        sts, data = self.getDataBeetwenMarkers(data, '<div class="submenu">', '</div>', withMarkers = False)
        if not sts: return
        match = re.compile('<a class="submenu" href="([^"]+?)">([^<]+?)</a>').findall(data)
        if match:
            for i in range(len(match)):
                params = {'title': match[i][1], 'url': match[i][0], 'category': cat, 'plot':match[i][0]}
                self.addDir(params)
                
    def listVideos(self, baseUrl, cat, page):
        printDBG("listVideos for url[%s] page[%s]" % (baseUrl, page))
        
        if 1 < int(page) != '1': url = baseUrl + page
        else: url = baseUrl
        sts, data = self.cm.getPage(url)
        if not sts: return
        
        nextPage = False
        if -1 < data.find("class='pagination_next'"):
            nextPage = True

        sts, data = self.getDataBeetwenMarkers(data, '<td class="video">', '</table>', withMarkers = False)
        if not sts: return
        
        data = data.split('<td class="video">')
        for item in data:
            # url & title
            match = re.search('class="video_title"><a href="([^"]+?)">([^<]+?)</a>', item)
            if match: 
                url = match.group(1)
                title = match.group(2)
            else: continue
            # img
            match = re.search('src="([^"]+?)"', item)
            if match: img = match.group(1)
            else: img = ''
            # plot
            match = re.search('<p style="margin:5px;" class="video_details">(.+?)</p>', item, re.DOTALL)
            if match: plot = remove_html_markup(match.group(1))
            else: plot = ''
            
            params = { 'title': title, 'url': url, 'icon': img, 'plot': plot}
            self.playVideo(params)
            
        if nextPage:
            params = {'title': "Następna strona", 'url': baseUrl, 'category': cat, 'page':str(int(page)+1)}
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
        
        sts, data = self.cm.getPage(url)
        if not sts:
            return []
        #check for internal link
        match = re.search('addVariable\("file","\.\.([^"]+?)"', data)
        if match:
            directUrl = self.MAINURL + match.group(1)
            return [{'name':'Internal_Link', 'url': directUrl}]
        #check for external link
        match = re.search('<embed src="([^"]+?)"', data)
        if match:
            return self.getLink(match.group(1))
        return []
            
    def getLink(self, url):
        printDBG('getLink for url[%s]' % (url))
        
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
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsMainMenu(self.SERVICE_MENU_TABLE)
    #KATEGORIE
        elif category == "Kategorie":
            self.listCategories(self.MAINURL + "/najnowsze/", 'video_category')
        elif category == "video_category":
            self.listVideos(url, category, page)
    #WYSZUKAJ
        elif category == "Wyszukaj":
            pattern = searchPattern.replace(" ", "-")
            self.getSearchResult(self.SEARCH_URL + pattern + "/", "search_next", page)
        elif category == "search_next":
            self.getSearchResult(url, "search_next", page)
    #HISTORIA WYSZUKIWANIA
        elif category == "Historia wyszukiwania":
            self.listsHistory()


class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, AleKinoTV(), True)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('mototubelogo.png')])

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
        url = self.host.up.getVideoLink( url )
        urlTab = []

        if isinstance(url, basestring) and url.startswith('http'):
            urlTab.append(url)

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
                self.host.history.addHistoryItem( pattern)
                self.searchPattern = pattern
        except:
            printDBG('setSearchPattern EXCEPTION')
            self.searchPattern = ''
        return
