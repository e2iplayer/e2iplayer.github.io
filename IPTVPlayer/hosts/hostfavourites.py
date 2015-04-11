# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem, CFavItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import CSelOneLink, printDBG, printExc, GetLogoDir, GetFavouritesDir
from Plugins.Extensions.IPTVPlayer.tools.iptvfavourites import IPTVFavourites
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigInteger, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
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

def GetConfigList():
    optionList = []
    return optionList
###################################################

def gettytul():
    return _('Favourites')

class Favourites(CBaseHostClass):
     
    def __init__(self):
        printDBG("Favourites.__init__")
        CBaseHostClass.__init__(self)
        self.helper = IPTVFavourites(GetFavouritesDir())
        self.host = None
        self.hostName = ''
        
    def _setHost(self, hostName):
        if hostName == self.hostName: return True
        try:
            _temp = __import__('Plugins.Extensions.IPTVPlayer.hosts.host' + hostName, globals(), locals(), ['IPTVHost'], -1)
            host = _temp.IPTVHost()
            if isinstance(host, IHost):
                self.hostName = hostName
                self.host = host
                return True
        except: printExc()
        return False
                
    def listGroups(self, category):
        printDBG("Favourites.listGroups")
        sts = self.helper.load()
        if not sts: return
        data = self.helper.getGroups()
        self.listsTab(data, {'category':category})
        
    def listFavourites(self, cItem):
        printDBG("Favourites.listFavourites")
        sts, data = self.helper.getGroupItems(cItem['group_id'])
        if not sts: return
        
        typesMap = {CDisplayListItem.TYPE_VIDEO: self.addVideo, 
                    CDisplayListItem.TYPE_AUDIO: self.addAudio, 
                    CDisplayListItem.TYPE_PICTURE: self.addPicture, 
                    CDisplayListItem.TYPE_ARTICLE: self.addArticle }
        
        for idx in range(len(data)):
            item = data[idx]
            addFun = typesMap.get(item.type, None)
            params = {'title':item.name, 'icon':item.iconimage, 'desc':item.description, 'group_id':cItem['group_id'], 'item_idx':idx}
            if None != addFun: addFun(params)
        
    def getLinksForVideo(self, cItem):
        printDBG("Favourites.getLinksForVideo idx[%r]" % cItem)
        ret = RetHost(RetHost.ERROR, value = [])
        sts, data = self.helper.getGroupItems(cItem['group_id'])
        if not sts: return ret
        item = data[cItem['item_idx']]
        
        if CFavItem.RESOLVER_URLLPARSER != item.resolver:
            if self._setHost(item.resolver):
                ret = self.host.getLinksForFavourite(item)
        else:
            self.host = None
            self.hostName = None
            retlist = []
            urlList = self.up.getVideoLinkExt(item.data)
            for item in urlList:
                name = self.host.cleanHtmlStr( item["name"] )
                url  = item["url"]
                retlist.append(CUrlItem(name, url, 0))
            ret = RetHost(RetHost.OK, value = retlist)
        return ret
        
    def getResolvedURL(self, url):
        try: return self.host.getResolvedURL(url)
        except: return RetHost(RetHost.ERROR, value = [])

    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('Favourites.handleService start')

        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        self.currList = [] 

        if None == name:
            self.listGroups('list_favourites')
        elif 'list_favourites' == category:
            self.listFavourites(self.currItem)
        else:
            printExc()
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Favourites(), False, [])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('favouriteslogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] not in ['audio', 'video']:
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])
        return self.host.getLinksForVideo(self.host.currList[Index])
    # end getLinksForVideo
        
    def getResolvedURL(self, url):
        return self.host.getResolvedURL(url)
    
    def convertList(self, cList):
        hostList = []
        searchTypesOptions = []
        
        for cItem in cList:
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
                

                
            title       =  self.host.cleanHtmlStr( cItem.get('title', '') )
            description =  self.host.cleanHtmlStr( cItem.get('desc', '') )
            icon        =  self.host.cleanHtmlStr( cItem.get('icon', '') )
            
            hostItem = CDisplayListItem(name = title,
                                        description = description,
                                        type = type,
                                        urlItems = [],
                                        urlSeparateRequest = 1,
                                        iconimage = icon,
                                        possibleTypesOfSearch = possibleTypesOfSearch)
            hostList.append(hostItem)

        return hostList
    # end convertList

