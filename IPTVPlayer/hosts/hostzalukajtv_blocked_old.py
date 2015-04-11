# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser

from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, CSearchHistoryHelper, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html

###################################################
# FOREIGN import
###################################################
import re, urllib, urllib2, base64, math 
try:
    import simplejson
except:
    import json as simplejson   
from Components.config import config, ConfigYesNo, ConfigText, getConfigListEntry

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.zalukajtvPREMIUM = ConfigYesNo(default = False)
config.plugins.iptvplayer.zalukajtv_login = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.zalukajtv_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("Użytkownik PREMIUM Zalukaj.TV?", config.plugins.iptvplayer.zalukajtvPREMIUM))
    if config.plugins.iptvplayer.zalukajtvPREMIUM.value:
        optionList.append(getConfigListEntry("    Zalukaj.TV login:", config.plugins.iptvplayer.zalukajtv_login))
        optionList.append(getConfigListEntry("    Zalukaj.TV hasło:", config.plugins.iptvplayer.zalukajtv_password))    
    return optionList

###################################################
# Title of HOST
###################################################
def gettytul():
    return 'Zalukaj.tv'

###################################################
# class IPTVHost
###################################################
class IPTVHost(IHost):
    LOGO_NAME = 'zalukajtvlogo.png'

    def __init__(self):
        printDBG( "init begin" )
        self.host = Host()
        self.prevIndex = []
        self.currList = []
        self.prevList = []
        printDBG( "init end" )
        
    def isProtectedByPinCode(self):
        return False
    
    def getLogoPath(self):  
        return RetHost(RetHost.OK, value = [ GetLogoDir( self.LOGO_NAME ) ])

    def getInitList(self):
        printDBG( "getInitList begin" )
        self.prevIndex = []
        self.currList = self.host.getInitList()
        self.host.setCurrList(self.currList)
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
        printDBG( "getResolvedURL begin" )
        if url != None and url != '':        
            ret = self.host.getResolvedURL(url)
            if ret != None and ret != '':        
               printDBG( "getResolvedURL ret: "+ret)
               list = []
               list.append(ret)
               printDBG( "getResolvedURL end OK" )
               return RetHost(RetHost.OK, value = list)
            else:
               printDBG( "getResolvedURL end" )
               return RetHost(RetHost.NOT_IMPLEMENTED, value = [])                
        else:
            printDBG( "getResolvedURL end" )
            return RetHost(RetHost.NOT_IMPLEMENTED, value = [])

    def getSearchResults(self, pattern, searchType = None):
        printDBG( "getSearchResults begin" )
        printDBG( "getSearchResults pattern: " +pattern)
        self.prevIndex.append(0)
        self.prevList.append(self.currList)
        self.currList = self.host.getSearchResults(pattern, searchType)
        printDBG( "getSearchResults end" )
        return RetHost(RetHost.OK, value = self.currList)

###################################################
# class HOST
###################################################
class Host:
    currList = []
    MAIN_URL = ''
    PREMIUM = False
    konto = ''
    HOST = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.18) Gecko/20110621 Mandriva Linux/1.9.2.18-0.1mdv2010.2 (2010.2) Firefox/3.6.18'

    def __init__(self):
        printDBG( 'Host __init__ begin' )
        self.exSession = MainSessionWrapper()
        self.COOKIEFILE = GetCookieDir('zalukajtv.cookie')
        self.cm = common()
        self.up = urlparser()
        self.history = CSearchHistoryHelper('wspolne')
        self.currList = []
        printDBG( 'Host __init__ end' )
        
    def setCurrList(self, list):
        printDBG( 'Host setCurrList begin' )
        self.currList = list
        printDBG( 'Host setCurrList end' )
        return 
        
    def fullUrl(self, phUrl):
        if not phUrl.startswith('http'):
            if '/' == phUrl[0]:
                phUrl = '/' + phUrl
            phUrl = self.MAIN_URL + phUrl
        return phUrl

    def getInitList(self):
        printDBG( 'Host getInitList begin' )
        ####################################
        # logowanie
        ####################################
        if config.plugins.iptvplayer.zalukajtvPREMIUM.value:
           url = 'http://zalukaj.tv/account.php'
           try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': True, 'host': self.HOST, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': self.COOKIEFILE, 'use_post': True, 'return_data': True },{'login': config.plugins.iptvplayer.zalukajtv_login.value, 'password': config.plugins.iptvplayer.zalukajtv_password.value})
           except:
              printDBG( 'Host getInitList query error' )
              printDBG( 'Host getInitList query error url:'+url )
              printDBG( 'Host getInitList query error: Uzywam Player z limitami')
              data = None
           if data:
              self.PREMIUM = True
              printDBG( 'Host getInitList: chyba zalogowano do premium...' )
              url = 'http://zalukaj.tv/libs/ajax/login.php?login=1'
              try: 
                 data = self.cm.getURLRequestData({ 'url': url, 'use_host': True, 'host': self.HOST, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': self.COOKIEFILE, 'use_post': False, 'return_data': True })
                 printDBG( 'Host listsItems data: '+data )
                 parse = re.search('Typ Konta:.*?>(.*?)<.*?>(.*?)<', data, re.S)
                 if parse:
                    self.konto = '- Typ Konta: '+parse.group(1)+parse.group(2)
                 else: 
                    self.konto = ''
              except:
                 printDBG( 'Host getInitList: blad pobrania danych o koncie premium' )
                 
           if '' == self.konto:
              self.exSession.open(MessageBox, 'Problem z zalogowaniem użytkownika \n"%s" jako VIP.' % config.plugins.iptvplayer.zalukajtv_login.value, type = MessageBox.TYPE_INFO, timeout = 10)

              #if 'Wyloguj' in data:
              #   self.PREMIUM = True 
              #   printDBG('Host getInitList:' + config.plugins.iptvplayer.zalukajtv_login.value + ', Zostales poprawnie zalogowany')
              #else:
              #   printDBG('Host getInitList: Blad logowania, uzywam Player z limitami')
        ####################################
        self.currList = self.listsItems(-1, '', 'main-menu')
        printDBG( 'Host getInitList end' )
        return self.currList

    def getListForItem(self, Index = 0, refresh = 0, selItem = None):
        printDBG( 'Host getListForItem begin' )
        valTab = []
        if len(self.currList[Index].urlItems) == 0:
           return valTab
        valTab = self.listsItems(Index, self.currList[Index].urlItems[0], self.currList[Index].urlSeparateRequest)
        self.currList = valTab
        printDBG( 'Host getListForItem end' )
        return self.currList

    def getSearchResults(self, pattern, searchType = None):
        printDBG( "Host getSearchResults begin" )
        printDBG( "Host getSearchResults pattern: " +pattern)
        valTab = []
        valTab = self.listsItems(-1, pattern, 'search')
        #valTab = [] #test       
        self.currList = valTab
        printDBG( "Host getSearchResults end" )
        return self.currList

    def listsItems(self, Index, url, name = ''):
        printDBG( 'Host listsItems begin' )
        printDBG( 'Host listsItems url: '+url )
        valTab = []
        if name == 'main-menu':
           printDBG( 'Host listsItems begin name='+name )
           self.MAIN_URL = 'http://zalukaj.tv'
           valTab.append(CDisplayListItem('Filmy '+self.konto,   'http://zalukaj.tv',         CDisplayListItem.TYPE_CATEGORY, ['http://zalukaj.tv/'],          'filmy', '', None)) 
           valTab.append(CDisplayListItem('Seriale', 'http://zalukaj.tv/seriale', CDisplayListItem.TYPE_CATEGORY, ['http://zalukaj.tv/seriale'],   'seriale', '', None)) 
           valTab.append(CDisplayListItem('Szukaj',  'Szukaj filmów',             CDisplayListItem.TYPE_SEARCH,   ['http://szukaj.zalukaj.tv/szukaj'],   'seriale', '', None)) 
           valTab.append(CDisplayListItem('Historia wyszukiwania', 'Historia wyszukiwania', CDisplayListItem.TYPE_CATEGORY, ['http://zalukaj.tv/seriale'],   'history', '', None)) 
           printDBG( 'Host listsItems end' )
           return valTab

        # ########## #
        if 'history' == name:
           printDBG( 'Host listsItems begin name='+name )
           for histItem in self.history.getHistoryList():
               valTab.append(CDisplayListItem(histItem['pattern'], 'Szukaj ', CDisplayListItem.TYPE_CATEGORY, [histItem['pattern'],histItem['type']], 'search', '', None))          
           printDBG( 'Host listsItems end' )
           return valTab
           
        # ########## #
        if 'search' == name:
           printDBG( 'Host listsItems begin name='+name )
           pattern = url 
           if Index==-1: 
              self.history.addHistoryItem( pattern, 'video')
           url = 'http://k.zalukaj.tv/szukaj'
           try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': True, 'return_data': True },{'searchinput': pattern})
           except:
              printDBG( 'Host listsItems query error' )
              printDBG( 'Host listsItems query error url:'+url )
              return valTab
           #printDBG( 'Host listsItems data: '+data )
           phMovies = re.findall('class="tivief4".*?src="(.*?)".*?<a href="(.*?)".*?title="(.*?)".*?div style.*?">(.*?)<.*?class="few_more">(.*?)<', data, re.S)
           if phMovies:
              for (phImage, phUrl, phTitle, phDescr, phMore) in phMovies:
                  printDBG( 'Host listsItems phImage: '  +phImage )
                  printDBG( 'Host listsItems phUrl: '    +phUrl )
                  printDBG( 'Host listsItems phTitle: '  +phTitle )
                  printDBG( 'Host listsItems phDescr: '  +phDescr )
                  printDBG( 'Host listsItems phMore: '   +phMore )
                  valTab.append(CDisplayListItem(phTitle, phMore+' | '+decodeHtml(phDescr), CDisplayListItem.TYPE_VIDEO, [CUrlItem('', phUrl, 1)], 0, phImage, None)) 
           printDBG( 'Host listsItems end' )
           return valTab
           
        # ########## #
        if 'seriale' == name:
           printDBG( 'Host listsItems begin name='+name )
           self.MAIN_URL = 'http://zalukaj.tv' 
           try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
           except:
              printDBG( 'Host listsItems query error' )
              printDBG( 'Host listsItems query error url:'+url )
              return valTab
           #printDBG( 'Host listsItems data: '+data )
           parse = re.search('<div id="two"(.*?)</table>', data, re.S)
           if not parse: return ''
           phMovies = re.findall('<td class="wef32f"><a href="(.*?)" title="(.*?)"', parse.group(1), re.S)
           if phMovies:
              for (phUrl, phTitle) in phMovies:
                  printDBG( 'Host listsItems phUrl: '  +phUrl )
                  printDBG( 'Host listsItems phTitle: '+phTitle )
                  valTab.append(CDisplayListItem(phTitle, phTitle, CDisplayListItem.TYPE_CATEGORY, [self.fullUrl(phUrl)], 'seriale-sezony', '', None))          
           valTab.insert(0,CDisplayListItem('--Ostatnio zaktualizowane seriale--',   'Ostatnio zaktualizowane seriale', CDisplayListItem.TYPE_CATEGORY, ['http://zalukaj.tv/seriale'], 'seriale-last', '', None))
           printDBG( 'Host listsItems end' )
           return valTab
        if 'seriale-last' == name:
           printDBG( 'Host listsItems begin name='+name )
           self.MAIN_URL = 'http://zalukaj.tv' 
           try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
           except:
              printDBG( 'Host listsItems query error' )
              printDBG( 'Host listsItems query error url:'+url )
              return valTab
           #printDBG( 'Host listsItems data: '+data )
           phMovies = re.findall('<div class="latest tooltip".*?href="(.*?)" title="(.*?)".*?src="(.*?)"', data, re.S)
           if phMovies:
              for (phUrl, phTitle, phImage) in phMovies:
                  printDBG( 'Host listsItems phUrl: '  +phUrl )
                  printDBG( 'Host listsItems phTitle: '+phTitle )
                  printDBG( 'Host listsItems phImage: '+phImage )
                  valTab.append(CDisplayListItem(phTitle, phTitle, CDisplayListItem.TYPE_CATEGORY, [self.fullUrl(phUrl)], 'seriale-sezon', phImage, None))          
           printDBG( 'Host listsItems end' )
           return valTab
        if 'seriale-sezony' == name:
           printDBG( 'Host listsItems begin name='+name )
           self.MAIN_URL = 'http://zalukaj.tv' 
           try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
           except:
              printDBG( 'Host listsItems query error' )
              printDBG( 'Host listsItems query error url:'+url )
              return valTab
           #printDBG( 'Host listsItems data: '+data )
           phImage = ''
           parse = re.search('<div id="sezony".*?img src="(.*?)"', data, re.S)
           if parse: phImage = parse.group(1)
           printDBG( 'Host listsItems phImage: '  +phImage )
           phMovies = re.findall('<a class="sezon" href="(.*?)".*?>(.*?)<', data, re.S)
           if phMovies:
              for (phUrl, phTitle) in phMovies:
                  printDBG( 'Host listsItems phUrl: '  +phUrl )
                  printDBG( 'Host listsItems phTitle: '+phTitle )
                  valTab.append(CDisplayListItem(phTitle, phTitle, CDisplayListItem.TYPE_CATEGORY, [self.fullUrl(phUrl)], 'seriale-sezon', phImage, None))          
           printDBG( 'Host listsItems end' )
           return valTab
        if 'seriale-sezon' == name:
           printDBG( 'Host listsItems begin name='+name )
           self.MAIN_URL = 'http://zalukaj.tv' 
           try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
           except:
              printDBG( 'Host listsItems query error' )
              printDBG( 'Host listsItems query error url:'+url )
              return valTab
           #printDBG( 'Host listsItems data: '+data )
           phImage = ''
           parse = re.search('<img src="(.*?)"', data, re.S)
           if parse: phImage = parse.group(1)
           printDBG( 'Host listsItems phImage: '  +phImage )
           phMovies = re.findall('id="sezony".*?>(.*?)<.*?href="(.*?)" title="(.*?)"', data, re.S)
           if phMovies:
              for (phEpisode, phUrl, phTitle) in phMovies:
                  printDBG( 'Host listsItems phEpizod: '  +phEpisode )
                  printDBG( 'Host listsItems phUrl: '  +phUrl )
                  printDBG( 'Host listsItems phTitle: '+phTitle )
                  valTab.append(CDisplayListItem(phEpisode+' - '+phTitle, phTitle, CDisplayListItem.TYPE_VIDEO, [CUrlItem('', self.fullUrl(phUrl), 1)], 0, phImage, None))          
                  printDBG( 'Host listsItems end' )
           return valTab
        if 'filmy' == name:
           printDBG( 'Host listsItems begin name='+name )
           self.MAIN_URL = 'http://zalukaj.tv' 
           try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
           except:
              printDBG( 'Host listsItems query error' )
              printDBG( 'Host listsItems query error url:'+url )
              return valTab
           #printDBG( 'Host listsItems data: '+data )
           sts,parse = CParsingHelper.getDataBeetwenMarkers(data, '<table id="one"', '</table>', False)
           phMovies = re.findall('<td class="wef32f"><a href="([^"]+?)">([^<]+?)</a>', parse, re.S)
           if phMovies:
              for (phUrl, phTitle) in phMovies:
                  printDBG( 'Host listsItems phUrl: '   + phUrl )
                  printDBG( 'Host listsItems phTitle: ' + phTitle )
                  valTab.append(CDisplayListItem(phTitle, phTitle, CDisplayListItem.TYPE_CATEGORY, [ self.fullUrl(phUrl) ], 'filmy-clip', '', None))          
           #valTab.insert(0,CDisplayListItem('--Najpopularniejsze--', 'Najpopularniejsze wyswietlenia-miesiac', CDisplayListItem.TYPE_CATEGORY, ['http://zalukaj.tv/#wyswietlenia-miesiac'], 'filmy-last', '', None))          
           #valTab.insert(0,CDisplayListItem('--Ostatnio oglądane--', 'Ostatnio oglądane',                      CDisplayListItem.TYPE_CATEGORY, ['http://zalukaj.tv/#lastseen'],             'filmy-last', '', None))          
           valTab.insert(0,CDisplayListItem('--Ostatnio dodane--',   'Ostatnio dodane',                        CDisplayListItem.TYPE_CATEGORY, ['http://zalukaj.tv'],            'filmy-last', '', None))          
           printDBG( 'Host listsItems end' )
           return valTab
        if 'filmy-clip' == name:
           printDBG( 'Host listsItems begin name='+name )
           self.MAIN_URL = 'http://zalukaj.tv' 
           try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
           except:
              printDBG( 'Host listsItems query error' )
              printDBG( 'Host listsItems query error url:'+url )
              return valTab
           #printDBG( 'Host listsItems data: '+data )
           phMovies = re.findall('background-image:url(.*?);"><p><span>(.*?)</span>.*?<h3><a href="(.*?)".*?">(.*?)<.*?">(.*?)<.*?class="few_more">(.*?)<', data, re.S)
           if phMovies:
              for (phImage, phRok, phUrl, phTitle, phDescr, phMore) in phMovies:
                  printDBG( 'Host listsItems phImage: '  +phImage )
                  printDBG( 'Host listsItems phRok: '    +phRok )
                  printDBG( 'Host listsItems phUrl: '    +phUrl )
                  printDBG( 'Host listsItems phTitle: '  +phTitle )
                  printDBG( 'Host listsItems phDescr: '  +phDescr )
                  printDBG( 'Host listsItems phMore: '   +phMore )
                  valTab.append(CDisplayListItem(phTitle, phRok+' | '+phMore+' | '+decodeHtml(phDescr), CDisplayListItem.TYPE_VIDEO, [CUrlItem('', phUrl, 1)], 0, phImage[1:-1], None)) 
           match = re.findall('class="pc_current">.*?href="(.*?)">(.*?)<', data, re.S)
           if match:               
                  phUrl = match[-1][0]
                  phTitle = match[-1][1]
                  valTab.append(CDisplayListItem('Strona '+phTitle, 'Strona: '+phUrl, CDisplayListItem.TYPE_CATEGORY, [self.fullUrl(phUrl)], name, '', None)) 
           printDBG( 'Host listsItems end' )
           return valTab
        if 'filmy-last' == name:
           printDBG( 'Host listsItems begin name='+name )
           self.MAIN_URL = 'http://zalukaj.tv' 
           try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
           except:
              printDBG( 'Host listsItems query error' )
              printDBG( 'Host listsItems query error url:'+url )
              return valTab
           #printDBG( 'Host listsItems data: '+data )
           phMovies = re.findall('class="tivief4".*?src="(.*?)".*?<h3><a href="(.*?)".*?">(.*?)<.*?">(.*?)<.*?class="few_more">(.*?)<', data, re.S)
           if phMovies:
              for (phImage, phUrl, phTitle, phDescr, phMore) in phMovies:
                  printDBG( 'Host listsItems phImage: '  +phImage )
                  printDBG( 'Host listsItems phUrl: '    +phUrl )
                  printDBG( 'Host listsItems phTitle: '  +phTitle )
                  printDBG( 'Host listsItems phDescr: '  +phDescr )
                  printDBG( 'Host listsItems phMore: '   +phMore )
                  valTab.append(CDisplayListItem(phTitle, phMore+' | '+decodeHtml(phDescr), CDisplayListItem.TYPE_VIDEO, [CUrlItem('', self.fullUrl(phUrl), 1)], 0, phImage, None)) 
           printDBG( 'Host listsItems end' )
           return valTab

        return valTab

    def getResolvedURL(self, url):
        printDBG( 'Host getResolvedURL begin' )
        printDBG( 'Host getResolvedURL url: '+url )
        videoUrl = ''
        valTab = []
        
        if self.PREMIUM:
            sts, data = self.cm.getPage(url, {'use_host': True, 'host': self.HOST, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': self.COOKIEFILE})
            if sts:
                parse = re.search('/player.php.*?"', data, re.S)
                if parse: 
                    printDBG( 'parse1p: '+parse.group(0) )
                    url2 = self.fullUrl(parse.group(0))
                    sts, data = self.cm.getPage(url2, {'use_host': True, 'host': self.HOST, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': self.COOKIEFILE, 'use_post': False, 'return_data': True })
                    if sts:
                        parse = re.search('<a href="(.*?)"', data, re.S)
                        if parse:
                            printDBG( 'parse2p: '+parse.group(1) )
                            url2 = parse.group(1)
                            sts,data = self.cm.getPage(url2, { 'use_host': True, 'host': self.HOST, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': self.COOKIEFILE, 'use_post': False, 'return_data': True })
                            if sts: 
                                printDBG( 'parse3pdata ')
                                match = re.compile("url:'(.+?)'").findall(data)
                                if len(match) > 0:                       
                                    printDBG( 'parse3p: PREMIUM: '+match[0] )
                                    linkvideo = match[0]
                                    return linkvideo
                    else:
                        printDBG( 'Host getResolvedURL query error premium' )
                        printDBG( 'Host getResolvedURL query error premium url: '+url2 )
                else:
                    printDBG( 'Host getResolvedURL query error premium' )
                    printDBG( 'Host getResolvedURL query error premium url: '+url2 )
            else:
                printDBG( 'Host getResolvedURL query error premium' )
                printDBG( 'Host getResolvedURL query error premium url: '+url )
              
        if url[0:30] == 'http://zalukaj.tv/zalukaj-film' or url[0:31] == 'http://zalukaj.tv/serial-online':      
            sts, data = self.cm.getPage(url)
            if not sts:
               printDBG( 'Host getResolvedURL query error' )
               printDBG( 'Host getResolvedURL query error url: '+url )
               return ''
               
            parse = re.search('/player.php.*?"', data, re.S)
            if not parse: return '' 
            printDBG( 'parse1: '+parse.group(0) )
            url2 = self.fullUrl(parse.group(0))
            sts, data = self.cm.getPage(url2)
            if not sts:
               printDBG( 'Host getResolvedURL query error' )
               printDBG( 'Host getResolvedURL query error url: '+ url2 )
               return ''
            parse = re.search('<a href="([^"]+?)"', data, re.S)
            if not parse: 
               return ''
            printDBG( 'parse2: '+parse.group(1) )
            url2 = parse.group(1)
            sts, data = self.cm.getPage(url2)
            if not sts:
               return ''
            parse = re.search('iframe src="([^"]+?)" width=', data)
            if not parse:
               return ''
            ret = self.up.getVideoLink( parse.group(1) )
            if ret:
               return ret
        return ''
        
def decodeHtml(text):
	return  clean_html(text.decode("utf-8", 'ignore')).encode("utf-8")