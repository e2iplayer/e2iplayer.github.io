## @file  ihost.py
#

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import CSearchHistoryHelper, GetCookieDir, printDBG, printExc
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html

class CUrlItem:
    def __init__(self, name = "", url = "", urlNeedsResolve = 0):
        self.name = name
        self.url = url # used only for TYPE_VIDEO item 
        self.urlNeedsResolve = urlNeedsResolve #  additional request to host is needed to resolv this url (url is not direct link)
## class CDisplayListItem
# define attribiutes for item of diplay list
# communicate display layer with host
#
class CDisplayListItem:
    TYPE_CATEGORY = "CATEGORY"
    TYPE_VIDEO    = "VIDEO"
    TYPE_AUDIO    = "AUDIO"
    TYPE_SEARCH   = "SEARCH"
    TYPE_ARTICLE  = "ARTICLE"
    TYPE_PICTURE  = "PICTURE"
    TYPE_MORE     = "MORE"
    TYPE_UNKNOWN  = "UNKNOWN"
    
    def __init__(self, name = "", \
                description = "", \
                type = TYPE_UNKNOWN, \
                urlItems = [], \
                urlSeparateRequest = 0, \
                iconimage = '', \
                possibleTypesOfSearch = None):
        self.name = name
        self.description = description
        self.type = type
        self.iconimage = iconimage 
        
        # used only for TYPE_VIDEO item
        self.urlItems = urlItems # url to VIDEO
        # links are not available the separate request is needed to get links
        self.urlSeparateRequest = urlSeparateRequest
        # used only for TYPE_SEARCH item
        self.possibleTypesOfSearch = possibleTypesOfSearch
        self.privateData = None
        
class ArticleContent:
    def __init__(self, title = '', text = '', images = []):
        self.title  = title
        self.text   = text
        self.images = images
        
class CFavItem:
    RESOLVER_SELF       = 'SELF'
    RESOLVER_URLLPARSER = 'URLLPARSER'
    TYPE_UNKNOWN = CDisplayListItem.TYPE_UNKNOWN
    def __init__( self, name         = '', \
                  description        = '', \
                  type               = TYPE_UNKNOWN, \
                  iconimage          = '', \
                  data               = '', \
                  resolver           = RESOLVER_SELF ):
        self.name        = name
        self.description = description
        self.type        = type
        self.iconimage   = iconimage 
        self.data        = data
        self.resolver    = resolver
        
    def fromDisplayListItem(self, dispItem):
        self.name        = dispItem.name
        self.description = dispItem.description
        self.type        = dispItem.type
        self.iconimage   = dispItem.iconimage
        return self
    
    def setFromDict(self, data):
        for key in data:
            setattr(self, key, data[key])
        return self
        
    def getAsDict(self):
        return vars(self)
       
class RetHost:
    OK = "OK"
    ERROR = "ERROR"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    def __init__(self, status , value, message = ''):
        self.status = status
        self.value = value  
        self.message = message

## class IHost
# interface base class with method used to
# communicate display layer with host
#
class IHost:

    def isProtectedByPinCode(self):
        return False
    
    # return list of types which can be added as favourite
    def getSupportedFavoritesTypes(self):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
    
    # get favourite item CFavItem for item with given index
    def getFavouriteItem(self, Index=0):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    # similar as getLinksForItem, returns links 
    # for given CFavItem
    def getLinksForFavourite(self, favItem):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])

    # return firs available list of item category or video or link
    def getInitList(self):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
    
    # return List of item from current List
    # for given Index
    # 1 == refresh - force to read data from 
    #                server if possible 
    # server instead of cache 
    # item - object of CDisplayListItem for selected item
    def getListForItem(self, Index = 0, refresh = 0, item = None):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    # return prev requested List of item 
    # for given Index
    # 1 == refresh - force to read data from 
    #                server if possible
    def getPrevList(self, refresh = 0):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    # return current List
    # for given Index
    # 1 == refresh - force to read data from 
    #                server if possible
    def getCurrentList(self, refresh = 0):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    # return current List
    # for given Index
    def getMoreForItem(self, Index=0):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    def getLinksForVideo(self, Index = 0, item = None):
        return self.getLinksForItem(Index, item)
        
    # return list of links for AUDIO, VIDEO, PICTURE
    # for given Index, 
    # item - object of CDisplayListItem for selected item
    def getLinksForItem(self, Index = 0, item = None):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    def getArticleContent(self, Index = 0):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    # return resolved url
    # for given url
    def getResolvedURL(self, url):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    # return full path to player logo
    def getLogoPath(self):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    def getSearchResults(self, pattern, searchType = None):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
'''
CHostBase implements some typical methods
          from IHost interface
'''
class CHostBase(IHost):
    def __init__( self, host, withSearchHistrory, favouriteTypes=[] ):
        self.host = host
        self.withSearchHistrory = withSearchHistrory
        self.favouriteTypes     = favouriteTypes

        self.currIndex = -1
        self.listOfprevList = [] 
        self.listOfprevItems = [] 
        
        self.searchPattern = ''
        self.searchType = ''
        
    def getSupportedFavoritesTypes(self):
        return RetHost(RetHost.OK, value = self.favouriteTypes)
        
    def isValidIndex(self, Index, validTypes=None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return False
        if None != validTypes and self.converItem(self.host.currList[Index]).type not in validTypes:
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return False
        return True
        
    def getFavouriteItem(self, Index=0):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index, self.favouriteTypes): RetHost(retCode, value=retlist)
        
        cItem = self.host.currList[Index]
        data = self.host.getFavouriteData(cItem)
        if None != data:
            favItem = CFavItem(data=data)
            favItem.fromDisplayListItem(self.converItem(cItem))
            
            retlist = [favItem]
            retCode = RetHost.OK

        return RetHost(retCode, value=retlist)
    # end getFavouriteItem
    
    def getLinksForFavourite(self, favItem):
        retlist = []
        urlList = self.host.getLinksForFavourite(favItem.data)
        for item in urlList:
            need_resolve = item.get("need_resolve", 0)
            name = self.host.cleanHtmlStr( item["name"] )
            url  = item["url"]
            retlist.append(CUrlItem(name, url, need_resolve))
        return RetHost(RetHost.OK, value = retlist)
    
    # return firs available list of item category or video or link
    def getInitList(self):
        self.currIndex = -1
        self.listOfprevList = [] 
        self.listOfprevItems = []
        
        self.host.handleService(self.currIndex)
        convList = self.convertList(self.host.getCurrList())
        
        return RetHost(RetHost.OK, value = convList)
    
    def getListForItem(self, Index = 0, refresh = 0, selItem = None):
        self.listOfprevList.append(self.host.getCurrList())
        self.listOfprevItems.append(self.host.getCurrItem())
        
        self.currIndex = Index
        if self.withSearchHistrory:
            self.setSearchPattern()
            try:
                if len(self.searchPattern):
                    sts, prevPattern = CSearchHistoryHelper.loadLastPattern()
                    if sts and prevPattern != self.searchPattern:
                        CSearchHistoryHelper.saveLastPattern(self.searchPattern)
            except:
                printExc()
        
        self.host.handleService(Index, refresh, self.searchPattern, self.searchType)
        convList = self.convertList(self.host.getCurrList())
        
        return RetHost(RetHost.OK, value = convList)

    def getPrevList(self, refresh = 0):
        if(len(self.listOfprevList) > 0):
            hostList = self.listOfprevList.pop()
            hostCurrItem = self.listOfprevItems.pop()
            self.host.setCurrList(hostList)
            self.host.setCurrItem(hostCurrItem)
            
            convList = self.convertList(hostList)
            return RetHost(RetHost.OK, value = convList)
        else:
            return RetHost(RetHost.ERROR, value = [])

    def getCurrentList(self, refresh = 0):
        if refresh == 1:
            self.host.handleService(self.currIndex, refresh, self.searchPattern, self.searchType)
        convList = self.convertList(self.host.getCurrList())
        return RetHost(RetHost.OK, value = convList)
        
    def getMoreForItem(self, Index=0):
        self.host.handleService(Index, 2, self.searchPattern, self.searchType)
        convList = self.convertList(self.host.getCurrList())
        return RetHost(RetHost.OK, value = convList)

    # this method must be overwritten 
    # by the child class
    '''
    def getSearchItemInx(self):
        return -1
    '''
    
    # this method must be overwritten 
    # by the child class
    '''
    def setSearchPattern(self):
        return
    '''
    
    def convertList(self, cList):
        hostList = []
        for cItem in cList:
            hostItem = self.converItem(cItem)
            if None != hostItem: hostList.append(hostItem)
        return hostList
    # end convertList
    
    # this method must be overwritten 
    # by the child class
    '''
    def converItem(self, cItem):
        return None
    '''

    def getSearchResults(self, searchpattern, searchType = None):
        retList = []

        if self.withSearchHistrory:
            self.host.history.addHistoryItem( searchpattern, searchType )

        self.searchPattern = searchpattern
        self.searchType = searchType
        
        # Find 'Wyszukaj' item
        list = self.host.getCurrList()
        
        searchItemIdx = self.getSearchItemInx()
        if searchItemIdx > -1:
            return self.getListForItem( searchItemIdx )
        else:
            return RetHost(RetHost.ERROR, value = [])
            
    # end getSearchResults
    

class CBaseHostClass:
    def __init__(self, params={}):
        self.sessionEx = MainSessionWrapper() 
        self.up = urlparser()
        
        proxyURL = params.get('proxyURL', '')
        useProxy = params.get('useProxy', False)
        self.cm = common(proxyURL, useProxy)

        self.currList = []
        self.currItem = {}
        if '' != params.get('history', ''):
            self.history = CSearchHistoryHelper(params['history'])
        if '' != params.get('cookie', ''):
            self.COOKIE_FILE = GetCookieDir(params['cookie'])
        self.moreMode = False
        
    def listsTab(self, tab, cItem):
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            self.addDir(params)
        
    @staticmethod 
    def cleanHtmlStr(str):
        str = str.replace('<', ' <').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        return CParsingHelper.removeDoubles(clean_html(str), ' ').strip()

    @staticmethod 
    def getStr(v, default=''):
        if type(v) == type(u''): return v.encode('utf-8')
        elif type(v) == type(''):  return v
        return default
            
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
        
    def addMore(self, params):
        params['type'] = 'more'
        self.currList.append(params)
        return
        
    def addVideo(self, params):
        params['type'] = 'video'
        self.currList.append(params)
        return
        
    def addAudio(self, params):
        params['type'] = 'audio'
        self.currList.append(params)
        return
    
    def addPicture(self, params):
        params['type'] = 'picture'
        self.currList.append(params)
        return
  
    def addArticle(self, params):
        params['type'] = 'article'
        self.currList.append(params)
        return
    
    def listsHistory(self, baseItem={'name': 'history', 'category': 'Wyszukaj'}, desc_key='plot', desc_base='Typ: '):
        list = self.history.getHistoryList()
        for histItem in list:
            plot = ''
            try:
                if type(histItem) == type({}):
                    pattern     = histItem.get('pattern', '')
                    search_type = histItem.get('type', '')
                    if '' != search_type: plot = desc_base + search_type
                else:
                    pattern     = histItem
                    search_type = None
                params = dict(baseItem)
                params.update({'title': pattern, 'search_type': search_type,  desc_key: plot})
                self.addDir(params)
            except: printExc()
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        self.moreMode = False
        if 0 == refresh:
            if len(self.currList) <= index:
                return
            if -1 == index:
                self.currItem = { "name": None }
            else:
                self.currItem = self.currList[index]
        if 2 == refresh: # refresh for more items
            printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> endHandleService index[%s]" % index)
            # remove item more and store items before and after item more
            self.beforeMoreItemList = self.currList[0:index]
            self.afterMoreItemList = self.currList[index+1:]
            self.moreMode = True
    
    def endHandleService(self, index, refresh):
        if 2 == refresh: # refresh for more items
            currList = self.currList
            self.currList = self.beforeMoreItemList
            for item in currList:
                if 'more' == item['type'] or (item not in self.beforeMoreItemList and item not in self.afterMoreItemList):
                    self.currList.append(item)
            self.currList.extend(self.afterMoreItemList)
            self.beforeMoreItemList = []
            self.afterMoreItemList  = []
        self.moreMode = False