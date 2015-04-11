# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, GetLogoDir, CSearchHistoryHelper
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
###################################################
# FOREIGN import
###################################################
import re
###################################################

def gettytul():
    return 'SerialeOnline'
    
class CListItem:
    TYPE_CATEGORY = "CATEGORY"
    TYPE_VIDEO = "VIDEO"
    TYPE_SEARCH = "SEARCH"
    def __init__(self,
                name = 'None',
                title = 'None',
                tvshowtitle = '',
                category = 'None',
                iconimage = '',
                page = '',
                originaltitle = '',
                year = '', 
                plot = '',
                season = '',
                episode = '',
                searchPattern = '', 
                type = TYPE_CATEGORY):
        self.name = name
        self.title = title
        self.tvshowtitle = tvshowtitle
        self.category = category
        self.iconimage = iconimage
        self.page = page
        self.originaltitle = originaltitle
        self.year = year
        self.plot = plot
        self.type = type
        self.season = season
        self.episode = episode
        self.searchPattern = searchPattern


class serialeo:
    SERVICE = 'serialeo'
    mainUrl = 'http://serialeonline.org.pl/'
    NewUrl = 'http://serialeonline.org.pl/nowe-odcinki'
    SerchUrl = 'http://serialeonline.org.pl/index.php?menu=search&query='

    SERVICE_MENU_TABLE =  {
        1: "Kategorie seriali",
        2: "Ostatnio uzupełnione seriale",
        3: "Wyszukaj",
        4: "Historia wyszukiwania"
    }

    def __init__(self):

        
        printDBG('Loading ' + serialeo.SERVICE)
        

        self.cm = common()
        self.up = urlparser.urlparser()
        self.history = CSearchHistoryHelper('serialeo')
        

        self.tabMenu = []
        self.currList = []

    def getCurrList(self):
        return self.currList

    def setCurrList(self, list):
        self.currList = list
        return
    
    def setTable(self):
        return self.SERVICE_MENU_TABLE

    def listsMainMenu(self, table):
        tabMenu = []
        for num, val in table.items():
            tabMenu.append(val)
        for i in range(len(tabMenu)):
            type = CListItem.TYPE_CATEGORY
            if tabMenu[i] == 'Wyszukaj':
                type = CListItem.TYPE_SEARCH
                
            item = CListItem( name = 'main-menu',
                              title = tabMenu[i],
                              category = tabMenu[i],
                              iconimage = '',
                              type = type )
            
            self.currList.append(item)
        self.tabMenu = tabMenu

    def listsKATMenu(self, url):
        sts,data = self.cm.getPage(url)
        if not sts: return
        match = re.compile(self.mainUrl + 'tv-tagi/(.+?)">(.+?)</a>').findall(data)
        if len(match) > 0:
            for i in range(len(match)):
                page = self.mainUrl + 'tv-tagi/' + match[i][0]
                item = CListItem(   name = 'kat-menu',
                                    title = match[i][1],
                                    page = page,
                                    type = CListItem.TYPE_CATEGORY )
                self.currList.append(item)

    def getLastParts(self, url):
        sts,data = self.cm.getPage(url)
        if not sts: return
        match = re.compile('portfolio(.+?)pagination', re.DOTALL).findall(data)
        if len(match) > 0:
                match2 = re.compile('href="(.+?)" class="spec-border-ie.+?\n.+?php.+?src=(.+?)&amp').findall(match[0])
                match3 = re.compile('href="http://serialeonline.org.pl/index.php.+?title="(.+?)">').findall(match[0])
                match4 = re.compile('<p class="left">(.+?)</p>').findall(match[0])
                if len(match2) and len (match3) > 0:
                        for i in range(len(match2)):
                                item = CListItem(   title = match3[i] + ' - ' + match4[i],
                                                    page = match2[i][0],
                                                    iconimage = match2[i][1],
                                                    type =  CListItem.TYPE_VIDEO )
                                self.currList.append(item)

    def showKATParts(self, page , url, pager):
        sts,data = self.cm.getPage(url)
        if not sts: return
        match = re.compile('poster(.+?)clear:both', re.DOTALL).findall(data)
        if len(match) > 0:
                match2 = re.compile('href="(.+?)" title="(.+?)">').findall(match[0])
                match3 = re.compile('timthumb.+?src=(.+?)&amp').findall(match[0])
                if len(match2) and len (match3) > 0:
                        for i in range(len(match2)):
                            item = CListItem(   title = match2[i][1],
                                                name = 'kat-parts',
                                                page = match2[i][0],
                                                iconimage = match3[i],
                                                type =  CListItem.TYPE_CATEGORY )
                            self.currList.append(item)
        match = re.compile('<li><a href="(.+?)">&raquo;</a></li>').findall(data)
        if len(match) > 0:
            item = CListItem(   title = 'Następna strona',
                                name = 'kat-menu',
                                page = page,
                                season = str(int(pager) + 1),
                                type =  CListItem.TYPE_CATEGORY )
            self.currList.append(item)

    def listsSerial(self, url, img, sezon):
        sts,data = self.cm.getPage(url)
        if not sts: return
        match = re.compile(sezon+'(.+?)tv_container', re.DOTALL).findall(data.replace('stylesheet', 'tv_container'))
        if len(match) > 0:
                match2 = re.compile('href="(.+?)">(.+?) <span class="tv_episode_name">(.+?)</span></a>').findall(match[0])
                if len(match2) > 0:
                        for i in range(len(match2)):
                                item = CListItem(   title = match2[i][1] + match2[i][2],
                                                    page = match2[i][0],
                                                    iconimage = img,
                                                    type =  CListItem.TYPE_VIDEO )
                                self.currList.append(item)

    def showSeason(self, url, img):
        sts,data = self.cm.getPage(url)
        if not sts: return
        r = re.compile('<h2>Sezon(.+?)</h2>').findall(data)
        if len(r)>0:
                for i in range(len(r)):
                    item = CListItem(   title = 'Sezon' + r[i],
                                        name = 'sezon',
                                        page = url,
                                        iconimage = img,
                                        type =  CListItem.TYPE_CATEGORY )
                    self.currList.append(item)

    def getListsSearch(self, text):
        sts,data = self.cm.getPage(self.SerchUrl + text)
        if not sts: return
        match = re.compile('<a class="link" href="(.+?)/season.+?" title="(.+?)">').findall(data)
        match2 = re.compile('timthumb.+?src=(.+?)&amp').findall(data)
        if len(match) and len (match2) > 0:
                for i in range(len(match)):
                    item = CListItem(   title = match[i][1],
                                        name = 'kat-parts',
                                        page = match[i][0],
                                        iconimage = match2[i],
                                        type =  CListItem.TYPE_CATEGORY )
                    self.currList.append(item)

    def listsHistory(self):
        list = self.history.getHistoryList()
        for item in list:
            item = CListItem(   title = item,
                                name = 'history',
                                plot = 'Szukaj: "%s"' % item,
                                type =  CListItem.TYPE_CATEGORY )
            self.currList.append(item)

    def getPlayTable(self,url):
        valTab = []
        sts,data = self.cm.getPage(url)
        if not sts: return valTab
        r = re.compile('row-pages-wrapper(.+?)disqus_thread', re.DOTALL).findall(data)
        if len(r)>0:
            r2 = re.compile('href="(.+?)" target="_blank">Oglądaj').findall(r[0])
            r3 = re.compile('http://serialeonline.org.pl/templates/trakt/images/(.+?).gif').findall(r[0])
            if len(r2)>0:
                for i in range(len(r2)):
                    title = r3[i].replace('pl1', 'Napisy').replace('eng', 'Oryginał').replace('pol', 'Lektor') + ' - ' + self.up.getHostName(r2[i])
                    valTab.append(self.cm.setLinkTable(r2[i], title))
                return valTab


    def handleService(self, index, refresh = 0, searchPattern = ''):
        if 0 == refresh:
            if len(self.currList) <= index:
                printDBG( "handleService wrond index: %s, len(self.currList): %d" % (index, len(self.currList)) )
                return
        
            if -1 == index:
                self.name        = None
                self.seltitle    = ''
                self.category    = ''
                self.page        = ''
                self.icon        = ''
                self.link        = ''
                self.service     = ''
                self.action      = ''
                self.sezon       = ''
                self.epizod      = ''
                self.serial      = ''
                self.searchPattern = ''


                printDBG("serialeo: handleService for first self.category")
            else:
                item             = self.currList[index]
                
                self.name        = item.name
                self.title       = item.title
                self.category    = item.category
                self.page        = item.page
                self.icon        = item.iconimage
                self.link        = item.page
                self.sezon       = item.season
                self.epizod      = item.episode
                self.serial      = item.tvshowtitle
                self.searchPattern = item.searchPattern

                
                printDBG("serialeo: |||||||||||||||||||||||||||||||||||| %s " % item.name)
        self.currList = []

        if str(self.sezon)=='None' or self.sezon=='':
            self.sezon = '1'


        if self.name == None:
            self.listsMainMenu(self.SERVICE_MENU_TABLE)
        elif self.category == self.setTable()[1]:
            self.listsKATMenu(self.mainUrl)
        elif self.category == self.setTable()[2]:
            self.getLastParts(self.NewUrl)
        elif self.category == self.setTable()[3]:
            if self.searchPattern == '':
                text = searchPattern
            else:
                text = self.searchPattern
            self.history.addHistoryItem(text)
            self.getListsSearch(text)
        elif self.category == self.setTable()[4]:
            self.listsHistory()
        elif self.name == 'kat-menu':
            self.showKATParts(self.page ,self.page + '/abc/' + str(self.sezon), self.sezon)
        elif self.name == 'kat-parts':
            self.showSeason(self.page, self.icon)
        elif self.name == 'sezon':
            self.listsSerial(self.page, self.icon, self.title)
        elif self.name == 'history':
            self.getListsSearch(self.title)

    
        
class IPTVHost(IHost):

    def __init__(self):
        self.host = None
        self.currIndex = -1
        self.listOfprevList = []

        self.searchPattern = ''
        
    
    def getInitList(self):
        self.isSearch = False
        self.host = serialeo()
        self.currIndex = -1
        self.listOfprevList = [] 
        
        self.host.handleService(self.currIndex)
        convList = self.convertList(self.host.getCurrList())
        
        return RetHost(RetHost.OK, value = convList)
 
    def getListForItem(self, Index = 0, refresh = 0, selItem = None):
        self.listOfprevList.append(self.host.getCurrList())
        
        self.currIndex = Index
        self.host.handleService(Index, refresh, self.searchPattern)
        convList = self.convertList(self.host.getCurrList())
        
        return RetHost(RetHost.OK, value = convList)

    def getPrevList(self, refresh = 0):
        if(len(self.listOfprevList) > 0):
            hostList = self.listOfprevList.pop()
            self.host.setCurrList(hostList)
            convList = self.convertList(hostList)
            return RetHost(RetHost.OK, value = convList)
        else:
            return RetHost(RetHost.ERROR, value = [])

    def getCurrentList(self, refresh = 0):      
        if refresh == 1:
            self.host.handleService(self.currIndex, refresh, self.searchPattern)
        convList = self.convertList(self.host.getCurrList())
        return RetHost(RetHost.OK, value = convList)

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG("ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index))
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index].type != CListItem.TYPE_VIDEO:
            printDBG("ERROR getLinksForVideo - current item has wrong type")
            return RetHost(RetHost.ERROR, value = [])
            
        retlist = []
        tab = self.host.getPlayTable(self.host.currList[Index].page)
        for item in tab:
            nameLink = item[1]
            url = item[0]
            retlist.append(CUrlItem(nameLink, url, 1))

        return RetHost(RetHost.OK, value = retlist)

    def getResolvedURL(self, url):
        if url != None and url != '':
        
            ret = self.host.up.getVideoLink(url)
            list = []
            if ret:
                list.append(ret)
            
            return RetHost(RetHost.OK, value = list)
            
        else:
            return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
            
    def getLogoPath(self):  
        return RetHost(RetHost.OK, value = [GetLogoDir('serialeologo.png')])


    def convertList(self, weebList):
        hostList = []
        
        for weebItem in weebList:
            hostLinks = []
                
            type = CDisplayListItem.TYPE_UNKNOWN
            if weebItem.type == CListItem.TYPE_CATEGORY:
                type = CDisplayListItem.TYPE_CATEGORY
            elif weebItem.type == CListItem.TYPE_VIDEO:
                type = CDisplayListItem.TYPE_VIDEO
            else:
                type = CDisplayListItem.TYPE_SEARCH
            

            description = weebItem.plot
            hostItem = CDisplayListItem(name = weebItem.title,
                                        description = description,
                                        type = type,
                                        urlItems = hostLinks,
                                        urlSeparateRequest = 1,
                                        iconimage = weebItem.iconimage)
            hostList.append(hostItem)
            
        return hostList

    def getSearchResults(self, searchpattern, searchType = None):
        self.isSearch = True
        retList = []
        self.searchPattern = searchpattern
        
        #3: Wyszukaj
        return self.getListForItem(2)

