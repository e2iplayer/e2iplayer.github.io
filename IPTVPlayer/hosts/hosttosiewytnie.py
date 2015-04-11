# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CDisplayListItem, RetHost, CUrlItem
import Plugins.Extensions.IPTVPlayer.libs.pCommon as pCommon
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, GetLogoDir
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser

###################################################
# FOREIGN import
###################################################
import re
try:
    import simplejson as json
except:
    import json
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigInteger, getConfigListEntry
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.tosiewytnieAge = ConfigInteger(default = 6, limits = (0,99))
config.plugins.iptvplayer.tosiewytnieUkryjAge = ConfigYesNo(default = False)

def GetConfigList():
    optionList = []
    optionList.append( getConfigListEntry( "Wiek widza:", config.plugins.iptvplayer.tosiewytnieAge ) )
    optionList.append( getConfigListEntry( "Ukryj Video na liście powyżej wieku widza:", config.plugins.iptvplayer.tosiewytnieUkryjAge ) )
    return optionList
###################################################

###################################################
# Title of HOST
###################################################
def gettytul():
    return 'ToSieWytnie.pl'


class IPTVHost(IHost):
    LOGO_NAME = 'tosiewytnielogo.png'

    def __init__(self):
        printDBG( "init begin" )
        self.host = Host()
        self.prevIndex = []
        self.currList = []
        self.prevList = []
        self.host.setAge(config.plugins.iptvplayer.tosiewytnieAge.value)
        self.host.setUkryjAge(config.plugins.iptvplayer.tosiewytnieUkryjAge.value)
        printDBG( "init end" )
    
    def getLogoPath(self):  
        return RetHost(RetHost.OK, value = [ GetLogoDir(self.LOGO_NAME) ])

    def getInitList(self):
        printDBG( "getInitList begin" )
        self.prevIndex = []
        self.currList = self.host.getInitList()
        self.prevList = []
        printDBG( "getInitList end" )
        return RetHost(RetHost.OK, value = self.currList)

    def getListForItem(self, Index = 0, refresh = 0, selItem = None):
        printDBG( "getListForItem begin" )
        self.prevIndex.append(Index)
        self.prevList.append(self.currList)
        self.currList = self.host.getListForItem(Index, refresh, selItem)
        #self.currList = [ self.prevList[-1][Index] ]
        printDBG( "getListForItem end" )
        return RetHost(RetHost.OK, value = self.currList)

    def getPrevList(self, refresh = 0):
        printDBG( "getPrevList begin" )
        if(len(self.prevList) > 0):
            self.prevIndex.pop()
            self.currList = self.prevList.pop()
            self.host.setCurrList(self.currList)
            printDBG( "getPrevList end OK" )
            return RetHost(RetHost.OK, value = self.currList)
        else:
            printDBG( "getPrevList end ERROR" )
            return RetHost(RetHost.ERROR, value = [])

    def getCurrentList(self, refresh = 0):
        printDBG( "getCurrentList begin" )
        #if refresh == 1
        #self.prevIndex[-1] #ostatni element prevIndex
        #self.prevList[-1]  #ostatni element prevList
        #tu pobranie listy dla dla elementu self.prevIndex[-1] z listy self.prevList[-1]  
        printDBG( "getCurrentList end" )
        return RetHost(RetHost.OK, value = self.currList)

    def getLinksForVideo(self, Index = 0, item = None):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    def getResolvedURL(self, url):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])

    def getSearchResults(self, pattern, searchType = None):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])

    ###################################################
    # Additional functions on class IPTVHost
    ###################################################

class Host:
    currList = []
    Age = 6
    UkryjAge = False
    #                             name               description         type                            urlItems                                            urlSeparateRequest iconimage possibleTypesOfSearch      
    MAIN_MENU = [CDisplayListItem('Kanały',          'Kanały',           CDisplayListItem.TYPE_CATEGORY, ['http://tosiewytnie.pl/app/channellist?'],         0,                 '',       None), \
                 #CDisplayListItem('Gatunki',         'Gatunki',          CDisplayListItem.TYPE_CATEGORY, ['http://tosiewytnie.pl/app/genreslist?'],          0,                 '',       None), \
                 CDisplayListItem('Polecane',        'Polecane',         CDisplayListItem.TYPE_CATEGORY, ['http://tosiewytnie.pl/app/recommended?'],         1,                 '',       None), \
                 CDisplayListItem('TOP100 Zawsze',   'TOP100 Zawsze',    CDisplayListItem.TYPE_CATEGORY, ['http://tosiewytnie.pl/app/rankings?'],            1,                 '',       None), \
                 CDisplayListItem('TOP100 Tygodnia', 'TOP100 Tygodnia',  CDisplayListItem.TYPE_CATEGORY, ['http://tosiewytnie.pl/app/rankings?type=week'],   1,                 '',       None), \
                 CDisplayListItem('TOP100 Miesiąca', 'TOP100 Miesiąca',  CDisplayListItem.TYPE_CATEGORY, ['http://tosiewytnie.pl/app/rankings?type=month'],  1,                 '',       None), \
                ] 

    def __init__(self):
        printDBG( 'Host __init__ begin' )
        self.cm = pCommon.common()
        self.currList = []
        self.Age = 6
        self.UkryjAge = False
        printDBG( 'Host __init__ begin' )
        
    def setCurrList(self, list):
        printDBG( 'Host setCurrList begin' )
        self.currList = list
        printDBG( 'Host setCurrList begin' )
        return 

    def setAge(self, age):
        printDBG( 'Host setAge begin' )
        self.Age = age
        printDBG( 'Host setAge end' )
        return 

    def setUkryjAge(self, UkryjAge):
        printDBG( 'Host setUkryjAge begin' )
        self.UkryjAge = UkryjAge
        printDBG( 'Host setUkryjAge end' )
        return 

    def getInitList(self):
        printDBG( 'Host getInitList begin' )
        self.currList = self.MAIN_MENU 
        printDBG( 'Host getInitList end' )
        return self.currList

    def getListForItem(self, Index = 0, refresh = 0, selItem = None):
        printDBG( 'Host getListForItem begin' )
        valTab = []
        if len(self.currList[Index].urlItems) == 0:
           return valTab
        valTab = self.listsItems(self.currList[Index].urlItems[0], self.currList[Index].urlSeparateRequest)
        self.currList = valTab
        printDBG( 'Host getListForItem end' )
        return self.currList


    def listsItems(self, url, clip = True):
        printDBG( 'Host listsItems begin' )
        valTab = []
        query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
        try:
            printDBG( 'Host listsItems begin query' )
            data = self.cm.getURLRequestData(query_data)
            printDBG( 'Host listsItems begin json' )
            result = json.loads(data)
        except:
            printDBG( 'Host listsItems ERROR' )
            return valTab
        if clip:
            printDBG('Host listsItems clip')
            for item in result['clips']:
                minimalAge = 0
                minimalAge = item['minimalAge']
                printDBG('Host listsItems clip Age')
                printDBG('Host listsItems clip Age minimal')
                printDBG(str(minimalAge))
                printDBG('Host listsItems clip Age host')
                printDBG(str(self.Age))
                printDBG('Host listsItems clip Age ==')
                if self.Age >= minimalAge:
                   printDBG('Host listsItems clip Age ok')
                   valTab.append(CDisplayListItem(item['title'].encode('UTF-8'),  '[minimalAge: '+str(minimalAge)+' ] '+item['description'].encode('UTF-8'),  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', item['clipUrl'].encode('UTF-8'), 0)], 0, item['thumbnail'].encode('UTF-8'), None))
                else:
                   printDBG('Host listsItems clip Age nok')
                   if self.UkryjAge:
                      printDBG('Host listsItems clip Age nok ukryj')
                   else:
                      printDBG('Host listsItems clip Age nok noukryj')
                      valTab.append(CDisplayListItem(item['title'].encode('UTF-8'),  '[minimalAge: '+str(minimalAge)+' ] '+item['description'].encode('UTF-8'),  CDisplayListItem.TYPE_VIDEO, [], 0, item['thumbnail'].encode('UTF-8'), None))
            if result['page'] != result['pageCount']:
                valTab.append(CDisplayListItem('nextpage',  'Następna strona',  CDisplayListItem.TYPE_CATEGORY, [url + "&page=" + str(result['page']+1)], 1, '', None))
            printDBG( 'Host listsItems clip end' )
            return valTab
        else:
            printDBG('Host listsItems clip else')
            for item in result:
                if item['name'] != 'Najnowsze' and item['name'] != 'Wszystkie':
                   valTab.append(CDisplayListItem(item['name'].encode('UTF-8'),  item['description'].encode('UTF-8'),  CDisplayListItem.TYPE_CATEGORY, ['http://tosiewytnie.pl/app/cliplist?nid='+str(item['nid'])], 1, item['logo'], None))
            return valTab
