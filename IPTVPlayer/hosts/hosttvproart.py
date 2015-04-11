# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, GetLogoDir
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
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
    optionList = []
    return optionList
###################################################

def gettytul():
    return 'TvProArt.pl online'
 
class TvProArt:
    MAI_URL = 'http://tvproart.pl/tvonline/'
 
    def __init__(self):
        self.cm = common()
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

    def listsMainMenu(self):
        printDBG("listsMainMenu")
        url = self.MAI_URL
        sts, data = self.cm.getPage( url )       
        if not sts: return
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, '<div class="menulist"', '<a href="tvonline">', True)
        data = re.compile('<a class="menuitemtv" href="([^"]+?)">([^<]+?)</a></div>').findall(data)
        for item in data:
            params = {'name': 'category', 'title': item[1], 'url': self.MAI_URL + item[0]}
            self.addDir(params)
    
    def listVideos(self, catUrl, page):
        printDBG("listVideos")
        sts, data = self.cm.getPage( catUrl + '/offset/%d' % page)
        if not sts: return
        nextPage = None
        if ('offset/%d' % (page + 1)) in data: nextPage = page + 1
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, '<p class="material">', '</table>', True)
        data = re.compile('<a class="matlink" href="([^"]+?)">([^<]+?)</a').findall(data)
        for item in data:
            params = {'name': 'category', 'title': item[1], 'url': self.MAI_URL + item[0]}
            self.playVideo(params)
            
        if None != nextPage:
            params = {'name': 'category', 'page': nextPage, 'title': 'Następna strona', 'url': catUrl}
            self.addDir(params)
            
    def getVideoLinks(self, url):
        printDBG('getVideoLink url[%s]' % url)
        urlItems = []
        sts, data = self.cm.getPage( url )
        if not sts: return
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, 'playlist: [', ']', True)
        data = re.compile("'http://tvproart.pl/tvonline/([^/]+?)/([^']+?\.mp4)'").findall(data)
        for item in data:
            urlItems.append({'name':item[0], 'url': self.MAI_URL + item[0] + '/' + item[1]})
        return urlItems

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
        icon     = self.currItem.get("icon", '')
        url      = self.currItem.get("url", '')
        page     = self.currItem.get("page", 0)
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s]" % (name) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsMainMenu()
    #Videos list
        elif name == "category":
            self.listVideos(url, page)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, TvProArt(), withSearchHistrory = False)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('tvproartpl.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] != 'video':
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])

        retlist = []
        url = self.host.currList[Index].get("url", '')
        urlItems = self.host.getVideoLinks(url)
        for item in urlItems:
            retlist.append(CUrlItem(item['name'], item['url']))
        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo

    def convertList(self, cList):
        hostList = []

        for cItem in cList:
            hostLinks = []
            type = CDisplayListItem.TYPE_UNKNOWN

            if cItem['type'] == 'category':
                type = CDisplayListItem.TYPE_CATEGORY
            elif cItem['type'] == 'video':
                type = CDisplayListItem.TYPE_VIDEO
                url = cItem.get('url', '')
                if '' != url:
                    hostLinks.append(CUrlItem("Link", url, 1))
                
            title       =  cItem.get('title', '')
            description =  cItem.get('desc', '')
            icon        =  cItem.get('icon', '')
            
            hostItem = CDisplayListItem(name = title,
                                        description = description,
                                        type = type,
                                        urlItems = hostLinks,
                                        urlSeparateRequest = 1,
                                        iconimage = icon,
                                        possibleTypesOfSearch = [])
            hostList.append(hostItem)

        return hostList
    # end convertList

