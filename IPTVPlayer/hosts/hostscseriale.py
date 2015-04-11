# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, CSearchHistoryHelper, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html

###################################################
# FOREIGN import
###################################################
import re, urllib, urllib2, base64, math 
try:
    import simplejson
except:
    import json as simplejson   
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.scserialePREMIUM = ConfigYesNo(default = False)
config.plugins.iptvplayer.scseriale_login = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.scseriale_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("Użytkownik PREMIUM SCSeriale ?", config.plugins.iptvplayer.scserialePREMIUM))
    if config.plugins.iptvplayer.scserialePREMIUM.value:
        optionList.append(getConfigListEntry("    SCSeriale login:", config.plugins.iptvplayer.scseriale_login))
        optionList.append(getConfigListEntry("    SCSeriale hasło:", config.plugins.iptvplayer.scseriale_password))    
    return optionList

###################################################
# Title of HOST
###################################################
def gettytul():
    return 'SCSeriale'

###################################################
# class IPTVHost
###################################################
class IPTVHost(IHost):
    LOGO_NAME = 'scserialelogo.png'

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
        return RetHost(RetHost.OK, value = [GetLogoDir(self.LOGO_NAME)])
    
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
    COOKIEFILE = ''
    HOST = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.18) Gecko/20110621 Mandriva Linux/1.9.2.18-0.1mdv2010.2 (2010.2) Firefox/3.6.18'

    def __init__(self):
        printDBG( 'Host __init__ begin' )
        self.exSession = MainSessionWrapper()
        self.COOKIEFILE = GetCookieDir('scseriale.cookie')        
        self.cm = common()
        self.currList = []
        self.up = urlparser()
        self.history = CSearchHistoryHelper('wspolne')
        printDBG( 'Host __init__ end' )
        
    def setCurrList(self, list):
        printDBG( 'Host setCurrList begin' )
        self.currList = list
        printDBG( 'Host setCurrList end' )
        return 

    def getInitList(self):
        printDBG( 'Host getInitList begin' )
        ####################################
        # logowanie
        ####################################
        self.PREMIUM = self.listsItems(-1, 'zaloguj', 'zaloguj')
        ####################################
        self.currList = self.listsItems(-1, 'main-menu', 'main-menu')
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
        self.currList = valTab
        printDBG( "Host getSearchResults end" )
        return self.currList

    def listsItems(self, Index, url, name = ''):
        printDBG( 'Host listsItems begin' )
        printDBG( 'Host listsItems url: '+url )
        valTab = []
        # ########## #
        if name == 'main-menu':
           printDBG( 'Host listsItems begin name='+name )
           self.MAIN_URL = 'http://scs.pl'
           valTab.append(CDisplayListItem("Seriale wg. kategorii"+self.konto,'http://scs.pl/seriale.html', CDisplayListItem.TYPE_CATEGORY, ['http://scs.pl/seriale.html'],       'seriale-kategorie',  '', None)) 
           valTab.append(CDisplayListItem("Seriale alfabetycznie",           'http://scs.pl/seriale.html', CDisplayListItem.TYPE_CATEGORY, ['http://scs.pl/seriale.html'],       'seriale-abc',  '', None)) 
           valTab.append(CDisplayListItem("Ostatnio aktualizowane seriale",  'http://scs.pl/ostatnio_aktualizowane_seriale.html',   CDisplayListItem.TYPE_CATEGORY, ['http://scs.pl/ostatnio_aktualizowane_seriale.html'], 'seriale-last', '', None)) 
           valTab.append(CDisplayListItem('Szukaj',                          'Szukaj',                     CDisplayListItem.TYPE_SEARCH,   ['http://scs.pl/serial,szukaj.html'], 'search',       '', None)) 
           valTab.append(CDisplayListItem('Historia wyszukiwania', 'Historia wyszukiwania', CDisplayListItem.TYPE_CATEGORY, [''],   'history', '', None)) 
           printDBG( 'Host listsItems end' )
           return valTab

        # ########## #
        if 'zaloguj' == name:
           printDBG( 'Host listsItems begin name='+name )
           if config.plugins.iptvplayer.scserialePREMIUM.value:
              url = 'http://scs.pl/logowanie.html'
              try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': True, 'host': self.HOST, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': self.COOKIEFILE, 'use_post': True, 'return_data': True },{'email': config.plugins.iptvplayer.scseriale_login.value, 'password': config.plugins.iptvplayer.scseriale_password.value})
              except:
                 printDBG( 'Host listsItems query error' )
                 printDBG( 'Host listsItems query error url:'+url )
                 printDBG( 'Host listsItems query error: Uzywam Player z limitami')
                 data = None
              if data:
                 self.PREMIUM = True
                 printDBG( 'Host listsItems: chyba zalogowano do premium...' )
                 url = 'http://scs.pl/premium.html'
                 try: 
                    data = self.cm.getURLRequestData({ 'url': url, 'use_host': True, 'host': self.HOST, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': self.COOKIEFILE, 'use_post': False, 'return_data': True })
                    printDBG( 'Host listsItems data: '+data )
                    parse = re.search('Konto premium ważne do(.*?)".*?;(.*?)<', data, re.S)
                    if parse:
                       self.konto = ' - Twoje konto: '+parse.group(2)+parse.group(1)
                    else: 
                       self.konto = ''
                 except:
                    printDBG( 'Host listsItems: blad pobrania danych o koncie premium' )
                 
              if '' == self.konto:
                 self.exSession.open(MessageBox, 'Problem z zalogowaniem użytkownika \n"%s" jako VIP.' % config.plugins.iptvplayer.scseriale_login.value, type = MessageBox.TYPE_INFO, timeout = 10)
                 
           printDBG( 'Host listsItems end' )
           return self.PREMIUM

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
              self.history.addHistoryItem( pattern, 'seriale')
           url = 'http://scs.pl/serial,szukaj.html'
           postdata = { 'search': pattern }
           try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': True, 'return_data': True },postdata)
           except:
              printDBG( 'Host listsItems query error' )
              printDBG( 'Host listsItems query error url:'+url )
              return valTab
           #printDBG( 'Host listsItems data: '+data )
           match = re.findall('<div class="img_box"><a href="(.*?)">.*?<img src="(.*?)" alt="(.*?)"', data, re.S)
           if len(match) > 0:
              for i in range(len(match)):
                  phImage = match[i][1]
                  phUrl = self.MAIN_URL+'/'+ match[i][0]
                  phTitle = match[i][2]
                  printDBG( 'Host listsItems phImage: '  +phImage )
                  printDBG( 'Host listsItems phUrl: '    +phUrl )
                  printDBG( 'Host listsItems phTitle: '  +phTitle )
                  valTab.append(CDisplayListItem(phTitle, phTitle, CDisplayListItem.TYPE_CATEGORY, [phUrl], 'seriale-sezony', phImage, None))
           printDBG( 'Host listsItems end' )
           return valTab
           
        # ########## #
        if 'seriale-last' == name:
           printDBG( 'Host listsItems begin name='+name )
           try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
           except:
              printDBG( 'Host listsItems query error' )
              printDBG( 'Host listsItems query error url:'+url )
              return valTab
           #printDBG( 'Host listsItems data: '+data )
           match = re.compile('online">(.+?)</a></div></div><span class="newest_ep" id=".+?">Ostatnio dodany:<br/><a href="odcinek,(.+?),(.+?),(.+?),(.+?).html">').findall(data)
           if len(match) > 0:
              for i in range(len(match)):
                  phImage='http://static.scs.pl/static/serials/' + match[i][1].replace('.html', '.jpg')+'.jpg'
                  phTitleS = match[i][1]
                  phTitle = match[i][0] + ' - ' + match[i][4] + ' - ' + match[i][2].capitalize().replace('-', ' ')
                  phUrlS = self.MAIN_URL + '/serial,' + match[i][0]
                  phUrl = self.MAIN_URL + '/odcinek,' + match[i][1] + ',' + match[i][2] + ',' + match[i][3] + ',' + match[i][4] + '.html'
                  printDBG( 'Host listsItems phImage: '  +phImage )
                  printDBG( 'Host listsItems phUrl: '  +phUrl )
                  printDBG( 'Host listsItems phTitle: '+phTitle )
                  valTab.append(CDisplayListItem(phTitleS, phTitleS, CDisplayListItem.TYPE_CATEGORY, [phUrlS], 'seriale-sezony', phImage, None))
                  valTab.append(CDisplayListItem(phTitle,  phTitle,  CDisplayListItem.TYPE_VIDEO, [CUrlItem('', phUrl, 1)], 0, phImage, None))
           printDBG( 'Host listsItems end' )
           return valTab
        if 'seriale-kategorie' == name:
           printDBG( 'Host listsItems begin name='+name )
           try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
           except:
              printDBG( 'Host listsItems query error' )
              printDBG( 'Host listsItems query error url:'+url )
              return valTab
           #printDBG( 'Host listsItems data: '+data )
           phMovies = re.findall('<span class="title1">(.*?)</span>(.*?)<.*?href="(.*?)"', data, re.S)
           if phMovies:
              for (phTitle, phCount, phUrl) in phMovies:
                  printDBG( 'Host listsItems phTitle: '+phTitle )
                  printDBG( 'Host listsItems phCount: '+phCount )
                  printDBG( 'Host listsItems phUrl: '  +phUrl )
                  valTab.append(CDisplayListItem(phTitle+phCount, phTitle, CDisplayListItem.TYPE_CATEGORY, [self.MAIN_URL+'/'+phUrl], 'seriale-kategoria', '', None))          
           printDBG( 'Host listsItems end' )
           return valTab
        if 'seriale-kategoria' == name:
           printDBG( 'Host listsItems begin name='+name )
           try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
           except:
              printDBG( 'Host listsItems query error' )
              printDBG( 'Host listsItems query error url:'+url )
              return valTab
           #printDBG( 'Host listsItems data: '+data )
           match = re.compile('class="serial_green" href="serial,(.+?)">(.+?)</a><br/>').findall(data)
           if len(match) > 0:
              for i in range(len(match)):
                  phImage='http://static.scs.pl/static/serials/' + match[i][0].replace('.html', '.jpg')
                  phTitle = match[i][1]
                  phUrl = self.MAIN_URL + '/serial,' + match[i][0]
                  printDBG( 'Host listsItems phImage: '  +phImage )
                  printDBG( 'Host listsItems phUrl: '  +phUrl )
                  printDBG( 'Host listsItems phTitle: '+phTitle )
                  valTab.append(CDisplayListItem(phTitle, phTitle, CDisplayListItem.TYPE_CATEGORY, [phUrl], 'seriale-sezony', phImage, None))
           printDBG( 'Host listsItems end' )
           return valTab
        if 'seriale-abc' == name:
           printDBG( 'Host listsItems begin name='+name )
           abcTab = self.cm.makeABCList()
           for i in range(len(abcTab)):
               phTitle = abcTab[i]
               valTab.append(CDisplayListItem(phTitle, phTitle, CDisplayListItem.TYPE_CATEGORY, [url,phTitle], 'seriale-alfabet', '', None))          
           printDBG( 'Host listsItems end' )
           return valTab
        if 'seriale-alfabet' == name:
           printDBG( 'Host listsItems begin name='+name )
           try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
           except:
              printDBG( 'Host listsItems query error' )
              printDBG( 'Host listsItems query error url:'+url )
              return valTab
           #printDBG( 'Host listsItems data: '+data )
           letter = self.currList[Index].urlItems[1]
           match = re.compile(' <a class="serial_green" href="serial,(.+?)">(.+?)</a><br/>').findall(data)
           if len(match) > 0:
              for i in range(len(match)):
                addItem = False
                if letter == '0 - 9' and (ord(match[i][1][0]) < 65 or ord(match[i][1][0]) > 91): addItem = True
                if (letter == match[i][1][0].upper()): addItem = True
                if (addItem):
                    phImage='http://static.scs.pl/static/serials/' + match[i][0].replace('.html', '.jpg')
                    phTitle = match[i][1]
                    phUrl = self.MAIN_URL + '/serial,' + match[i][0]
                    printDBG( 'Host listsItems phImage: '  +phImage )
                    printDBG( 'Host listsItems phUrl: '  +phUrl )
                    printDBG( 'Host listsItems phTitle: '+phTitle )
                    valTab.append(CDisplayListItem(phTitle, phTitle, CDisplayListItem.TYPE_CATEGORY, [phUrl], 'seriale-sezony', phImage, None))          
           printDBG( 'Host listsItems end' )
           return valTab
        if 'seriale-sezony' == name:
           printDBG( 'Host listsItems begin name='+name )
           try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
           except:
              printDBG( 'Host listsItems query error' )
              printDBG( 'Host listsItems query error url:'+url )
              return valTab
           #printDBG( 'Host listsItems data: '+data )
           phMovies = re.compile('<meta itemprop="seasonNumber" content="(.+?)">').findall(data)
           if phMovies:
              phImage=url.replace(self.MAIN_URL + '/serial,', 'http://static.scs.pl/static/serials/').replace('.html', '.jpg')
              printDBG( 'Host listsItems phImage: '+phImage )
              for (phTitle) in phMovies:
                  printDBG( 'Host listsItems phTitle: '+phTitle )
                  valTab.append(CDisplayListItem('Sezon '+phTitle, 'Sezon '+phTitle, CDisplayListItem.TYPE_CATEGORY, [url,phTitle], 'seriale-odcinki', phImage, None))          
           printDBG( 'Host listsItems end' )
           return valTab
        if 'seriale-odcinki' == name:
           printDBG( 'Host listsItems begin name='+name )
           try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
           except:
              printDBG( 'Host listsItems query error' )
              printDBG( 'Host listsItems query error url:'+url )
              return valTab
           #printDBG( 'Host listsItems data: '+data )
           sezon = self.currList[Index].urlItems[1]
           r = re.compile('<meta itemprop="seasonNumber" content="' + sezon + '">(.+?)</ul></div>', re.DOTALL).findall(data)
           if not r: return []
           phMovies = re.compile('itemprop="episodeNumber">(.+?)<.+?class="aLink " href="(odcinek,.+?,.+?,.+?,.+?.html)"><span itemprop="name">(.+?)</span></a>').findall(r[0])
           if phMovies:
              phImage=url.replace(self.MAIN_URL + '/serial,', 'http://static.scs.pl/static/serials/').replace('.html', '.jpg')
              serial=url.replace(self.MAIN_URL + '/serial,','').replace('.html', '')
              printDBG( 'Host listsItems phImage: '+phImage )
              for (phEpizod, phUrl, phName) in phMovies:
                  printDBG( 'Host listsItems phEpizod: '+phEpizod )
                  printDBG( 'Host listsItems phUrl: '+phUrl )
                  phTitle = '%s S%sE%s - %s' % (serial, sezon, phEpizod, phName)
                  printDBG( 'Host listsItems phTitle: '+phTitle )
                  valTab.append(CDisplayListItem(phTitle, phTitle, CDisplayListItem.TYPE_CATEGORY, [self.MAIN_URL+'/'+phUrl,phTitle], 'seriale-odcinki-wersje', phImage, None))          
           printDBG( 'Host listsItems end' )
           return valTab
        if 'seriale-odcinki-wersje' == name:
           printDBG( 'Host listsItems begin name='+name )
           try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
           except:
              printDBG( 'Host listsItems query error' )
              printDBG( 'Host listsItems query error url:'+url )
              return valTab
           #printDBG( 'Host listsItems data: '+data )
           parse = re.search('Wersje:(.*?)Kopie:', data, re.S)
           if not parse: return []
           phMovies = re.findall('<a href="(.+?)">(.+?)<', parse.group(1), re.S)           
           if phMovies:
              phImage=url.replace(self.MAIN_URL + '/serial,', 'http://static.scs.pl/static/serials/').replace('.html', '.jpg')
              printDBG( 'Host listsItems phImage: '+phImage )
              for (phUrl, phWersja) in phMovies:
                  printDBG( 'Host listsItems phUrl: '+phUrl )
                  printDBG( 'Host listsItems phWersja: '+phWersja )
                  valTab.append(CDisplayListItem(phWersja, phWersja, CDisplayListItem.TYPE_CATEGORY, [self.MAIN_URL+'/'+phUrl], 'seriale-odcinki-kopie', phImage, None))          
           printDBG( 'Host listsItems end' )
           return valTab
        if 'seriale-odcinki-kopie' == name:
           printDBG( 'Host listsItems begin name='+name )
           try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
           except:
              printDBG( 'Host listsItems query error' )
              printDBG( 'Host listsItems query error url:'+url )
              return valTab
           #printDBG( 'Host listsItems data: '+data )
           parse = re.search('class="mirrors"(.*?)class="switch"', data, re.S)
           if not parse: return []
           phMovies = re.findall('= "(.+?)"; ccc.+?;.+?"(.+?)";.+?"(.+?)";.+?"(.+?)";', parse.group(1), re.S)           
           if phMovies:
              for (phUrl, phTime, phUser, phComment) in phMovies:
                  printDBG( 'Host listsItems phUrl: '+phUrl )
                  printDBG( 'Host listsItems phTime: '+phTime )
                  printDBG( 'Host listsItems phUser: '+phUser )
                  valTab.append(CDisplayListItem(phTime+' '+phUser, phTime+' '+phUser+' '+phComment, CDisplayListItem.TYPE_VIDEO, [CUrlItem('', phUrl, 1)], 0, '', None))          
           printDBG( 'Host listsItems end' )
           return valTab

        return valTab

    def getResolvedURL(self, url):
        printDBG( 'Host getResolvedURL begin' )
        printDBG( 'Host getResolvedURL url: '+url )
        postdata = {'f' : url }
        if self.PREMIUM:
           query_data = { 'url': 'http://scs.pl/getVideo.html', 'use_host': True, 'host': self.HOST, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': self.COOKIEFILE, 'use_post': True, 'return_data': True }
        else: 
           query_data = { 'url': 'http://scs.pl/getVideo.html', 'use_host': False, 'use_cookie': False, 'use_post': True, 'return_data': True }
        try: data = self.cm.getURLRequestData(query_data, postdata)
        except:
           printDBG( 'Host getResolvedURL query error premium' )
           printDBG( 'Host getResolvedURL query error premium url: '+url )
           return ''
        #printDBG( 'Host getResolvedURL premium data: ' +data)
        match = re.compile("url: '(.+?)',").findall(data)
        if len(match) > 0:
           linkVideo = match[0]
           printDBG( 'Host getResolvedURL linkVideo: ' + linkVideo)
           printDBG( 'Host getResolvedURL end premium' )
           return linkVideo
        printDBG( 'Host getResolvedURL end' )
        return ''

def decodeHtml(text):
	return  clean_html(text.decode("utf-8", 'ignore')).encode("utf-8")        