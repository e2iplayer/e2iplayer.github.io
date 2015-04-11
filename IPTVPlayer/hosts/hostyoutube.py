# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, CSearchHistoryHelper, remove_html_markup, CSelOneLink, GetLogoDir
from Plugins.Extensions.IPTVPlayer.tools.iptvfilehost import IPTVFileHost
from Plugins.Extensions.IPTVPlayer.libs.youtubeparser import YouTubeParser
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
###################################################

###################################################
# FOREIGN import
###################################################
import os, re, urllib
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigDirectory, getConfigListEntry
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.Sciezkaurllist = ConfigDirectory(default = "/hdd/")

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Sort by:"), config.plugins.iptvplayer.ytSortBy))
    optionList.append(getConfigListEntry(_("Path to ytlist.txt, urllist.txt"), config.plugins.iptvplayer.Sciezkaurllist))
    optionList.append(getConfigListEntry(_("Video format:"), config.plugins.iptvplayer.ytformat))
    optionList.append(getConfigListEntry(_("Default video quality:"), config.plugins.iptvplayer.ytDefaultformat))
    optionList.append(getConfigListEntry(_("Use default video quality:"), config.plugins.iptvplayer.ytUseDF))
    return optionList
###################################################
###################################################

def gettytul():
    return 'Youtubes player'

class Youtube(CBaseHostClass):
    UTLIST_FILE      = 'ytlist.txt'
    MAIN_GROUPED_TAB = [{'category': 'from_file',             'title': _("User links"),     'desc': _("User links stored in the ytlist.txt file.")}, \
                        {'category': 'Historia wyszukiwania', 'title': _("Search history"), 'desc': _("History of searched phrases.")}, \
                        {'category': 'Wyszukaj',              'title': _("Search"),         'desc': _("Search youtube materials "), 'search_item':True}]
    SEARCH_TYPES = [  (_("Video"),    "video"   ), 
                      (_("Channel"),  "channel" ),
                      (_("Playlist"), "playlist"),
                      (_("Movie"),    "movie"   ),
                      (_("Live"),     "live"    ) ]
                      #("Program",            "show"    ),
                      #("traylist",           "traylist"),
        
    def __init__(self):
        printDBG("Youtube.__init__")
        CBaseHostClass.__init__(self, {'history':'ytlist', 'cookie':'youtube.cookie'})            
        self.ytp = YouTubeParser()
        self.currFileHost = None
    
    def _cleanHtmlStr(self, str):
            str = self.cm.ph.replaceHtmlTags(str, ' ').replace('\n', ' ')
            return clean_html(self.cm.ph.removeDoubles(str, ' ').replace(' )', ')').strip())
            
    def _getCategory(self, url):
        printDBG("Youtube._getCategory")
        if '/playlist?list=' in url:
            category = 'playlist'
        elif None != re.search('/watch\?v=[^\&]+?\&list=',  url):
            category = 'traylist'
        elif 'user/' in url or 'channel/' in url:
            category = 'channel'
        else:
            category = 'video'
        return category
        
    def listsMainMenu(self):
        printDBG("Youtube.listsMainMenu")
        for item in Youtube.MAIN_GROUPED_TAB:
            params = {'name': 'category'}
            params.update(item)
            self.addDir(params)
        
    def listCategory(self, cItem, searchMode=False):
        printDBG("Youtube.listCategory cItem[%s]" % cItem)
        
        sortList = True
        filespath = config.plugins.iptvplayer.Sciezkaurllist.value
        groupList = True
        if 'sub_file_category'  not in cItem:
            self.currFileHost = IPTVFileHost()
            self.currFileHost.addFile(filespath + Youtube.UTLIST_FILE, encoding='utf-8')
            tmpList = self.currFileHost.getGroups(sortList)
            if 0 < len(tmpList):
                params = dict(cItem)
                params.update({'sub_file_category':'all', 'group': 'all', 'title':_("--All--")})
                self.addDir(params)
            for item in tmpList:
                if '' == item: title = _("--Other--")
                else:          title = item
                params = dict(cItem)
                params.update({'sub_file_category':'group', 'title':title, 'group':item})
                self.addDir(params)
        else:
            if 'all' == cItem['sub_file_category']:
                tmpList = self.currFileHost.getAllItems(sortList)
                for item in tmpList:
                    params = dict(cItem)
                    category = self._getCategory(item['url'])
                    params.update({'title':item['full_title'], 'url':item['url'], 'desc': item['url'], 'category': category})
                    if 'video' == category:
                        self.addVideo(params)
                    else:
                        self.addDir(params)
            elif 'group' == cItem['sub_file_category']:
                tmpList = self.currFileHost.getItemsInGroup(cItem['group'], sortList)
                for item in tmpList:
                    if '' == item['title_in_group']:
                        title = item['full_title']
                    else:
                        title = item['title_in_group']
                    params = dict(cItem)
                    category = self._getCategory(item['url'])
                    params.update({'title':title, 'url':item['url'], 'desc': item['url'], 'category': category})
                    if 'video' == category:
                        self.addVideo(params)
                    else:
                        self.addDir(params)
                        
    def getVideos(self, cItem):
        printDBG('Youtube.getVideos cItem[%s]' % (cItem))
        
        category = cItem.get("category", '')
        url      = cItem.get("url", '')
        page     = cItem.get("page", '1')
                
        if "channel" == category:
            if -1 == url.find('browse_ajax'):
                if url.endswith('/videos'): 
                    url = url + '?flow=list&view=0&sort=dd'
                else:
                    url = url + '/videos?flow=list&view=0&sort=dd'
            self.currList = self.ytp.getVideosFromChannelList(url, category, page, cItem)
        elif "playlist" == category:
            self.currList = self.ytp.getVideosFromPlaylist(url, category, page, cItem)   
        elif "traylist" == category:
            self.currList = self.ytp.getVideosFromTraylist(url, category, page, cItem)
        else:
            printDBG('YTlist.getVideos Error unknown category[%s]' % category)
            
    def getSearchResult(self, cItem, pattern, searchType):
        page = self.currItem.get("page", '1')
        tmpList =  self.ytp.getSearchResult(pattern, searchType, page, 'Wyszukaj', config.plugins.iptvplayer.ytSortBy.value)
        for item in tmpList:
            item.update({'name':'category'})
            if 'video' == item['type']:
                self.addVideo(item)
            else:
                self.addDir(item)
                
    def getLinksForVideo(self, url):
        printDBG("Youtube.getLinksForVideo url[%s]" % url)
        ytformats = config.plugins.iptvplayer.ytformat.value
        maxRes = int(config.plugins.iptvplayer.ytDefaultformat.value) * 1.1

        if not url.startswith("http://") and not url.startswith("https://") :
            url = 'http://www.youtube.com/' + url
        tmpTab = self.ytp.getDirectLinks(url, ytformats)
        
        def __getLinkQuality( itemLink ):
            tab = itemLink['format'].split('x')
            return int(tab[0])
        tmpTab = CSelOneLink(tmpTab, __getLinkQuality, maxRes).getSortedLinks()
        if config.plugins.iptvplayer.ytUseDF.value and 0 < len(tmpTab):
            tmpTab = [tmpTab[0]]
        
        videoUrls = []
        for item in tmpTab:
            videoUrls.append({'name': item['format'] + ' | ' + item['ext'] , 'url':item['url']})
        return videoUrls
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo(fav_data)
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('Youtube.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "Youtube.handleService: ---------> name[%s], category[%s] " % (name, category) )
        self.currList = []
        
        if None == name:
            self.listsMainMenu()
        elif 'from_file' == category :
            self.listCategory(self.currItem)
        elif category in ["channel","playlist","movie","traylist"]:
            self.getVideos(self.currItem)
    #WYSZUKAJ
        elif category == 'Wyszukaj':
            pattern = urllib.quote_plus(searchPattern)
            printDBG("Wyszukaj pattern[%s], type[%s]" % (pattern, searchType))
            self.getSearchResult(self.currItem, pattern, searchType)
    #HISTORIA WYSZUKIWANIAmain_item
        elif category == 'Historia wyszukiwania':
            self.listsHistory()

class IPTVHost(CHostBase):
    def __init__(self):
        CHostBase.__init__(self, Youtube(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('youtubelogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index].get('url', ''))
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo

    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = self.host.SEARCH_TYPES
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
        description =  cItem.get('plot', '')
        if '' == description:
            description =  cItem.get('time', '') + ' | ' + cItem.get('desc', '')
        icon        =  cItem.get('icon', '')
        
        return CDisplayListItem(name = title,
                                description = description,
                                type = type,
                                urlItems = hostLinks,
                                urlSeparateRequest = 1,
                                iconimage = icon,
                                possibleTypesOfSearch = possibleTypesOfSearch)
    # end converItem

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
