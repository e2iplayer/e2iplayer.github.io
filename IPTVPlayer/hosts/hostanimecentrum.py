# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, GetLogoDir
import Plugins.Extensions.IPTVPlayer.libs.pCommon as pCommon
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
###################################################

###################################################
# Config options for HOST
###################################################
# None


def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'Anime-Centrum'


class AnimeCentrum(CBaseHostClass):
    MAINURL = 'http://anime-centrum.net'
    SERVICE_MENU_TABLE = {
        1: "Lista anime (alfabetycznie)",
    }

    def __init__(self):
        CBaseHostClass.__init__(self)

    def setTable(self):
        return self.SERVICE_MENU_TABLE

    def getVideoUrl(self, url):
        printDBG("getVideoUrl url[%s]" % url)
        sts,data = self.cm.getPage(url)
        if not sts: return ''
        
        match = re.search('file: "(.+?)"', data)
        if match:
            return match.group(1)
        else:
            printDBG('nie znaleziono mp4 link')
        return ''

    def listsMainMenu(self, table):
        for num, val in table.items():
            params = {'name': 'main-menu', 'category': val, 'title': val, 'icon': ''}
            self.addDir(params)

    def listsABCMenu(self, table):
        for i in range(len(table)):
            params = {'name': 'abc-menu', 'category': table[i], 'title': table[i], 'icon': ''}
            self.addDir(params)

    def listsGenre(self, url):
        sts,data = self.cm.getPage(url)
        if not sts: return
        r = re.compile('<input id=".+?"  type="checkbox" name="genre.." value="(.+?)">').findall(data)
        if len(r) > 0:
            for i in range(len(r)):
                params = {'name': 'genset', 'title': r[i].replace('+', ' '), 'page': r[i], 'icon': ''}
                self.addDir(params)

# LISTOWANIE TYTUŁOW
    def getAnimeList(self, url):
        sts,data = self.cm.getPage(self.MAINURL + url)
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="episodes-list">', '</section>', False)[1]
        data = data.split('<div class="push-left th-1">')
        if len(data): del data[0]
        for item in data:
            tmp    = self.cm.ph.getSearchGroups(item, 'href="http://anime-centrum.net/([^"]+?)"[^>]*?>([^<]+?)<', 2)
            url    = tmp[0]
            title  = tmp[1]
            desc   = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<span class="tip-text">', '</a>', False)[1] )
            icon   = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            title  = self.cleanHtmlStr(title + ' ' + item.split('</a>')[-1])
            if '' != url:
                params = {'name': 'episodelist', 'title': title, 'page': url, 'icon': icon, 'plot': desc}
                self.addDir(params)

# LISTOWANIE ODCINKOW
    def getEpisodeList(self, url):
        sts,data = self.cm.getPage(url)
        if not sts: return
# cover
        grafika = re.search('<meta property="og:image" content="(.+?)" />', data)
        if grafika: icon = grafika.group(1)
        else: icon = ''
# description
        opis = re.search('<strong>Opis:</strong>(.+)', data)
        if opis: plot = self.cleanHtmlStr(opis.group(1))
        else: plot = ''
        match = re.compile('<div class="info">(.+?)<div id="screens">', re.DOTALL).findall(data)
        if len(match) > 0:
            match2 = re.compile('<a href="http://(.+?)">Odcinek(.+?)</a>').findall(match[0])
            if len(match2) > 0:
                for i in range(len(match2)):
                    value = match2[i]
                    value2 = 'http://' + urllib.quote(value[0])
                    if '<!--' not in value[1]:
                        params = {'title': "Odcinek " + value[1], 'page': value2, 'icon': icon, 'plot': plot}
                        self.addVideo(params)

    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('handleService start')
        if 0 == refresh:
            if len(self.currList) <= index:
                printDBG("handleService wrong index: %s, len(self.currList): %d" % (index, len(self.currList)))
                return
            if -1 == index:
                # use default value
                self.currItem = {"name": None}
                printDBG("handleService for first self.category")
            else:
                self.currItem = self.currList[index]

        name = self.currItem.get("name", '')
        title    = self.currItem.get("title", '')
        category = self.currItem.get("category", '')
        page = self.currItem.get("page", '')
        icon     = self.currItem.get("icon", '')

        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| [%s] " % name )
        self.currList = []

        if str(page)=='None' or page=='': page = '0'

    #MAIN MENU
        if name is None:
            self.listsMainMenu(self.SERVICE_MENU_TABLE)
    #LISTA ANIME (Alfabetycznie)
        elif category == self.setTable()[1]:
            self.listsABCMenu(self.cm.makeABCList())
        elif name == 'abc-menu':
            self.getAnimeList('/anime-online/' + category + '.html')
    #LISTA ODCINKÓW
        elif name == 'episodelist':
            url = self.MAINURL + '/' + page
            self.getEpisodeList(url)


class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, AnimeCentrum(), False)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value=[GetLogoDir('animecentrumlogo.png')])

    def getLinksForVideo(self, Index=0, selItem=None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG("ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index))
            return RetHost(RetHost.ERROR, value=[])

        if self.host.currList[Index]["type"] != 'video':
            printDBG("ERROR getLinksForVideo - current item has wrong type")
            return RetHost(RetHost.ERROR, value=[])

        retlist = []

        urlItem = self.host.getVideoUrl(self.host.currList[Index]["page"])
        if '' != urlItem:
            retlist.append(CUrlItem("anime-centrum", urlItem, 0))

        return RetHost(RetHost.OK, value=retlist)
    # end getLinksForVideo

    def getResolvedURL(self, url):
#        if url != None and url != '':
        if url is not None and url is not '':
            ret = self.host.up.getVideoLink(url)
            list = []
            if ret:
                list.append(ret)
            return RetHost(RetHost.OK, value=list)
        return RetHost(RetHost.NOT_IMPLEMENTED, value=[])

    def convertList(self, cList):
        hostList = []

        for cItem in cList:
            hostLinks = []
            type = CDisplayListItem.TYPE_UNKNOWN

            if cItem['type'] == 'category':
                type = CDisplayListItem.TYPE_CATEGORY
            elif cItem['type'] == 'video':
                type = CDisplayListItem.TYPE_VIDEO
                page = cItem.get('page', '')
                if '' != page:
                    hostLinks.append(CUrlItem("Link", page, 1))

            title = cItem.get('title', '')
            description = cItem.get('plot', '')
            icon = cItem.get('icon', '')

            hostItem = CDisplayListItem(name=title,
                                        description=description,
                                        type=type,
                                        urlItems=hostLinks,
                                        urlSeparateRequest=1,
                                        iconimage=icon)
            hostList.append(hostItem)

        return hostList
    # end convertList

