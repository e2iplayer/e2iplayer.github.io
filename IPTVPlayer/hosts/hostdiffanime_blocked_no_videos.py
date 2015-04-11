# -*- coding: utf-8 -*-
# Based on (root)/trunk/xbmc-addons/src/plugin.video.polishtv.live/self.HOSTs/ @ 419 - Wersja 636

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, GetLogoDir, GetCookieDir, printExc
from Plugins.Extensions.IPTVPlayer.libs.youtubeparser import YouTubeParser
import Plugins.Extensions.IPTVPlayer.libs.pCommon as pCommon
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
###################################################

###############################################################################
# E2 GUI COMMPONENTS
###############################################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###############################################################################

###################################################
# FOREIGN import
###################################################
import re
from Components.config import config, ConfigYesNo, ConfigText, getConfigListEntry
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.diffanime_premium = ConfigYesNo(default = False)
config.plugins.iptvplayer.diffanime_login = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.diffanime_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []

    optionList.append(getConfigListEntry("Użytkownik Diffanime", config.plugins.iptvplayer.diffanime_premium))
    if config.plugins.iptvplayer.diffanime_premium.value:
        optionList.append(getConfigListEntry("  Diffanime login:", config.plugins.iptvplayer.diffanime_login))
        optionList.append(getConfigListEntry("  Diffanime hasło:", config.plugins.iptvplayer.diffanime_password))
    return optionList
###############################################################################


def gettytul():
    return 'Diff-anime'


class diffanime:
    HOST = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.18) Gecko/20110621 Mandriva Linux/1.9.2.18-0.1mdv2010.2 (2010.2) Firefox/3.6.18'
    HEADER = {'User-Agent': HOST, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}

    MAINURL = 'http://diff-anime.pl'
    SERVICE_MENU_TABLE = {
        1: "Lista anime (alfabetycznie)",
#        2: "Lista anime (wg. gatunku)",
        2: "Ranking",
        3: "Ulubione",
        4: "Aktualności"
    }

    def __init__(self):
        self.up = urlparser.urlparser()
        self.cm = pCommon.common()
        self.sessionEx = MainSessionWrapper()
        self.ytp = YouTubeParser()
        self.ytformats = config.plugins.iptvplayer.ytformat.value
        # Temporary data
        self.currList = []
        self.currItem = {}
        # Login data
        self.COOKIEFILE = GetCookieDir('Diff-anime.cookie')
        self.usePremiumAccount = config.plugins.iptvplayer.diffanime_premium.value
        self.username = config.plugins.iptvplayer.diffanime_login.value
        self.password = config.plugins.iptvplayer.diffanime_password.value

    def getCurrList(self):
        return self.currList

    def setCurrList(self, list):
        self.currList = list

    def getCurrItem(self):
        return self.currItem

    def setCurrItem(self, item):
        self.currItem = item

# Login in to the site
    def requestLoginData(self):
        if False == self.usePremiumAccount:
            printDBG("diffanime niezalogowany")
        else:
            self.usePremiumAccount = False
            url = self.MAINURL
            query_data = {'url': url, 'header': self.HEADER, 'use_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIEFILE, 'return_data': True}
            postdata = {'user_name': self.username, 'user_pass': self.password, 'remember_me': 'y', "login": "Zaloguj"}
            try:
                data = self.cm.getURLRequestData(query_data, postdata)
            except:
                printDBG("diffanime requestLoginData exception")
                return
            if 'Wyloguj' in data:
                printDBG("diffanime Notification(" + self.username + ", Zostales poprawnie zalogowany)")
                self.usePremiumAccount = True
            else:
                self.sessionEx.waitForFinishOpen(MessageBox, 'Błąd logowania. Sprawdź dane.\nlogin - ' + self.username + ' \nhasło - ' + self.password, type=MessageBox.TYPE_INFO, timeout=10)
                printDBG("diffanime Notification(Blad logowania)")
# end login

    def addDir(self, params):
        params['type'] = 'category'
        self.currList.append(params)
        return

    def addVideo(self, params):
        params['type'] = 'video'
        self.currList.append(params)
        return

    def setTable(self):
        return self.SERVICE_MENU_TABLE

# Get YT link
    def getYTVideoUrl(self, url):
        printDBG("getYTVideoUrl url[%s]" % url)
        tmpTab = self.ytp.getDirectLinks(url, self.ytformats)

        movieUrls = []
        for item in tmpTab:
            movieUrls.append({'name': item['format'] + '\t' + item['ext'], 'url': item['url']})

        return movieUrls

    def getVideoUrlforYTube(self, url):
        printDBG("getVideoUrl url[%s]" % url)
        query_data = {'url': url, 'use_host': True, 'host': self.HOST, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': self.COOKIEFILE, 'use_post': False, 'return_data': True}
        try:
            data = self.cm.getURLRequestData(query_data)
        except:
            printDBG('getVideoUrl exception')
            return ''
        match = re.search('src="//www.youtube.com/(.+?)"', data)
        if match:
            printDBG('www.youtube.com/' + match.group(1))
            return self.getYTVideoUrl('www.youtube.com/' + match.group(1))
        else:
            printDBG('nie znaleziono YT link')
        return ''
# end Get YT link

# Get mp4 link
    def getVideoUrl(self, url):
        printDBG("getVideoUrl url[%s]" % url)
        query_data = {'url': url, 'use_host': True, 'host': self.HOST, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': self.COOKIEFILE, 'use_post': False, 'return_data': True}
        try:
            data = self.cm.getURLRequestData(query_data)
        except:
            printDBG('getVideoUrl exception')
            return ''
        match = re.search("'file': '(.+?)',", data)
        if match:
            return match.group(1)
        else:
            printDBG('nie znaleziono mp4 link')
        return ''
# end Get mp4 link

    def listsMainMenu(self, table):
        query_data = {'url': self.MAINURL + '/newsy', 'return_data': True}
        try:
            data = self.cm.getURLRequestData(query_data)
        except:
            printDBG('listAbcItem exception')
            return
        match = re.compile("div class='sRight'><div class='panel news'>(.+?)<div class='left'><div>Czytań:", re.DOTALL).findall(data)
        if len(match) > 0:
            match2 = re.search(".png' alt=([^<]+?)class='news-category'", match[0])
            if match2:
                plot = match2.group(1)
            else:
                plot = ''
            match3 = re.search("class='news-category' />([^<]+?)</div>", match[0])
            if match3:
                plot2 = match3.group(1)
            else:
                plot2 = ''
            icon = re.compile("<div class='content'><img src='(.+?)' alt='").findall(match[0])

        for num, val in table.items():
                params = {'name': 'main-menu', 'category': val, 'title': val, 'icon': self.MAINURL + icon[0], 'plot': self.cm.html_entity_decode(plot + plot2)}
                self.addDir(params)

    def listsABCMenu(self, table):
        for i in range(len(table)):
            params = {'name': 'abc-menu', 'category': table[i], 'title': table[i], 'icon': ''}
            self.addDir(params)

# "AKTUALNOŚCI"
    def getlistsNews(self, url):
        query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
        try:
            data = self.cm.getURLRequestData(query_data)
        except:
            printDBG('listsGenre EXCEPTION')
        r2 = re.compile("<div class='head'><h2><a href='/news/(.+?)'>(.+?)</a>").findall(data)
        if len(r2) > 0:
                for i in range(len(r2)):
                    value = r2[i]
                    title = self.cm.html_entity_decode(value[1])
                    data = self.MAINURL + '/news/' + value[0]
                    data2 = self.cm.getURLRequestData({'url': data, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True})
                    value = re.search("<div class='content'><img src='(.+?)' alt='(.+?)' class='news-category' />(.+?).<br />", data2)
                    if value:
                        icon = self.MAINURL + value.group(1)
                        plot = self.cm.html_entity_decode(value.group(2) + value.group(3))
                    else:
                        icon = ''
                        plot = ''
                    params = {'name': 'news', 'title': title, 'icon': icon, 'plot': plot, 'page': data}
                    self.addVideo(params)

# "ULUBIONE"
    def getlistsUlubione(self, url):
        query_data = {'url': url + '/odcinki', 'use_host': True, 'host': self.HOST, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': self.COOKIEFILE, 'use_post': False, 'return_data': True}
        try:
            data = self.cm.getURLRequestData(query_data)
        except:
            printDBG('listsGenre EXCEPTION')
        r = re.compile("<div id='pUAL' class='panel pDef'>(.+?)<div id='footer'>", re.DOTALL).findall(data)
        if len(r) > 0:
            x1 = re.compile("W trakcie<(.+?)>Ukończone<", re.DOTALL).findall(data)
            if len(x1) > 0:
                rx1 = re.compile("'sTitle'><a href='(.+?)'>(.+?)</a>").findall(x1[0])
                if len(rx1) > 0:
                    for i in range(len(rx1)):
                        value = rx1[i]
                        title = self.cm.html_entity_decode("W trakcie - " + value[1])
                        page = self.MAINURL + value[0]
                        params = {'name': 'ulubione', 'title': title, 'page': page, 'icon': ''}
                        self.addDir(params)
            x2 = re.compile("Ukończone<(.+?)>Wstrzymane<", re.DOTALL).findall(data)
            if len(x2) > 0:
                rx2 = re.compile("'sTitle'><a href='(.+?)'>(.+?)</a>").findall(x2[0])
                if len(rx2) > 0:
                    for i in range(len(rx2)):
                        value = rx2[i]
                        title = self.cm.html_entity_decode("Ukończone - " + value[1])
                        page = self.MAINURL + value[0]
                        params = {'name': 'ulubione', 'title': title, 'page': page, 'icon': ''}
                        self.addDir(params)
            x3 = re.compile("Wstrzymane<(.+?)>Porzucone<", re.DOTALL).findall(data)
            if len(x3) > 0:
                rx3 = re.compile("'sTitle'><a href='(.+?)'>(.+?)</a>").findall(x3[0])
                if len(rx3) > 0:
                    for i in range(len(rx3)):
                        value = rx3[i]
                        title = self.cm.html_entity_decode("Wstrzymane - " + value[1])
                        page = self.MAINURL + value[0]
                        params = {'name': 'ulubione', 'title': title, 'page': page, 'icon': ''}
                        self.addDir(params)
            x4 = re.compile("Porzucone<(.+?)>W planach<", re.DOTALL).findall(data)
            if len(x4) > 0:
                rx4 = re.compile("'sTitle'><a href='(.+?)'>(.+?)</a>").findall(x4[0])
                if len(rx4) > 0:
                    for i in range(len(rx4)):
                        value = rx4[i]
                        title = self.cm.html_entity_decode("Porzucone - " + value[1])
                        page = self.MAINURL + value[0]
                        params = {'name': 'ulubione', 'title': title, 'page': page, 'icon': ''}
                        self.addDir(params)
            x5 = re.compile("W planach<(.+?)='footer'>", re.DOTALL).findall(data)
            if len(x5) > 0:
                rx5 = re.compile("'sTitle'><a href='(.+?)'>(.+?)</a>").findall(x5[0])
                if len(rx5) > 0:
                    for i in range(len(rx5)):
                        value = rx5[i]
                        title = self.cm.html_entity_decode("W planach - " + value[1])
                        page = self.MAINURL + value[0]
                        params = {'name': 'ulubione', 'title': title, 'page': page, 'icon': ''}
                        self.addDir(params)
# "RANKING"
    def getlistsRanks(self, url):
        query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
        try:
            data = self.cm.getURLRequestData(query_data)
        except:
            printDBG('listsGenre EXCEPTION')
        r = re.compile("<h2>Ranking anime</h2>(.+?)</table>", re.DOTALL).findall(data)
        if len(r) > 0:
            r2 = re.compile("<td class='td2'><a href='/(.+?)'><img src='(.+?)' class='img' /></a><div class='con'><a href='(.+?)'>(.+?)</a><p>").findall(r[0])
            if len(r2) > 0:
                for i in range(len(r2)):
                    value = r2[i]
                    title = self.cm.html_entity_decode(value[3])
                    page = self.MAINURL + value[2]
                    icon = self.MAINURL + value[1]
                    params = {'name': 'ranks', 'title': title, 'page': page, 'icon': icon}
                    self.addDir(params)

# "KATEGORIE"
    def getlistsGenre(self, url):
        query_data = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
        try:
            data = self.cm.getURLRequestData(query_data)
        except:
            printDBG('listsGenre EXCEPTION')
        r = re.compile("</div><div id='pSettings' class='panel'>(.+?)</div></div>", re.DOTALL).findall(data)
        if len(r) > 0:
            r2 = re.compile("<a href='(.+?)'>(.+?)</a>").findall(r[0])
            if len(r2) > 0:
                for i in range(len(r2)):
                    value = r2[i]
                    title = self.cm.html_entity_decode(value[1])
                    page = value[0] + '&rowstart=00'
                    params = {'name': 'genset', 'title': title, 'page': page, 'plot': title, 'icon': ''}
                    self.addDir(params)

# ANIME TITLES
    def getAnimeList(self, url):
        query_data = {'url': self.MAINURL + url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
        try:
            data = self.cm.getURLRequestData(query_data)
        except:
            printDBG('getAnimeList EXCEPTION')
            nextPage = False
        if -1 != data.find("div class='pagenav") and -1 != data.find("class='img"):
            nextPage = True
        else:
            nextPage = False
        r = re.compile("</div><div id='pSeries' class='panel'>(.+?)<div id='footer'>", re.DOTALL).findall(data)
        if len(r) > 0:
            r2 = re.compile("</a><div class='con'><a href='/(.+?)'>(.+?)</a><p>").findall(r[0])

            if len(r2) > 0:
                for i in range(len(r2)):
                    value = r2[i]
                    title = self.cm.html_entity_decode(value[1])
                    page = value[0]
                    data = self.MAINURL + "/" + value[0]
                    data2 = self.cm.getURLRequestData({'url': data, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True})
    #Cover
                    grafika = re.search("</div><div class='content'><div class='con'><a href='(.+?)' class='fbox'>", data2)
                    if grafika:
                        icon = self.MAINURL + grafika.group(1)
                    else: icon =''
    #Description
                    match = re.search("<h2>Opis anime</h2></div><div class='content'><div class='con'>(.+?)</div>", data2)
                    if match:
                        plot = match.group(1)
                    else:
                        match = re.search("<h2>Opis anime</h2></div><div class='content'><div class='con'>(.+?)<", data2)
                        if match:
                            plot = match.group(1)
                        else:
                            match = re.search("<h2>Opis anime</h2></div><.+?>(.+?)<", data2)
                            if match:
                                plot = match.group(1)
                            else:
                                plot = ''
                    params = {'name': 'episodelist', 'title': title, 'page': page, 'icon': icon, 'plot': self.cm.html_entity_decode(plot)}
                    self.addDir(params)
        if nextPage is True:
                        nextpage = url[:-2] + str(int(url[-2:]) + 10)

                        params = {'name': 'nextpage', 'title': 'Next page', 'page': nextpage}
                        self.addDir(params)

# EPISODES LIST
    def getEpisodeList(self, url):
        query_data = {'url': url + '/odcinki', 'use_host': True, 'host': self.HOST, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': self.COOKIEFILE, 'use_post': False, 'return_data': True}
        query_data1 = {'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
        try:
            data = self.cm.getURLRequestData(query_data)  # episodes data
            data2 = self.cm.getURLRequestData(query_data1)  # cover, desc. data
        except:
            printExc()
    # Description
        match = re.search("<h2>Opis anime</h2></div><div class='content'><div class='con'>(.+?)</div>", data2)
        if match:
            plot = match.group(1)
        else:
            match = re.search("<h2>Opis anime</h2></div><div class='content'><div class='con'>(.+?)<", data2)
            if match:
                plot = match.group(1)
            else:
                match = re.search("<h2>Opis anime</h2></div><.+?>(.+?)<", data2)
                if match:
                    plot = match.group(1)
                else:
                    plot = ''
    # Cover
        grafika = re.search("</div><div class='content'><div class='con'><a href='(.+?)' class='fbox'>", data2)
        if grafika:
            icon = self.MAINURL + grafika.group(1)
        else: icon =''
    # Episodes
        match = re.compile("<span class='head2'>Statystyki:</span>(.+?)<div class='mainCon'>", re.DOTALL).findall(data)
        if len(match) > 0:
            match2 = re.compile("#(.+?)</div><div class=.+?</div><div class='con3'><a href='(.+?)' class='i'>").findall(match[0])
            if len(match2) > 0:
                for i in range(len(match2)):
                    value = match2[i]
                    page = self.MAINURL + value[1]
                    title = 'Odcinek ' + value[0]
                    params = {'title': title, 'page': page, 'plot': self.cm.html_entity_decode(plot), 'icon': icon}
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
        title = self.currItem.get("title", '')
        category = self.currItem.get("category", '')
        page = self.currItem.get("page", '')
        icon = self.currItem.get("icon", '')

        printDBG("handleService: |||||||||||||||||||||||||||||||| [%s] " % name)
        self.currList = []

        if str(page) == 'None' or page == '':
            page = '0'

# Fill the Menu

    #MAIN MENU
        if name is None:
            #logowanie
            if self.usePremiumAccount:
                self.requestLoginData()
            self.listsMainMenu(self.SERVICE_MENU_TABLE)

    #LISTA ANIME (Alfabetycznie)
        elif category == self.setTable()[1]:
            self.listsABCMenu(self.cm.makeABCList())
        elif name == 'abc-menu':
            url = '/lista-anime?letter=' + category + '&rowstart=00'
            self.getAnimeList(url)
        elif name == 'nextpage':
            self.getAnimeList(page)

    #LISTA ANIME (wg. Gatunku)
#        elif category == self.setTable()[2]:
#            url = self.MAINURL + '/lista-anime'
#            self.getlistsGenre(url)
#        elif name == 'genset':
#            self.getAnimeList(page)

    #LISTA ANIME (wg. Rankingu)
        elif category == self.setTable()[2]:
            url = self.MAINURL + '/ranking-anime'
            self.getlistsRanks(url)
        elif name == 'ranks':
            self.getEpisodeList(page)

    #ULUBIONE
        elif category == self.setTable()[3]:
            url = self.MAINURL + '/moja-lista/' + self.username
            self.getlistsUlubione(url)
        elif name == 'ulubione':
            self.getEpisodeList(page)

    #AKTUALNOŚCI
        elif category == self.setTable()[4]:
            url = self.MAINURL + '/newsy'
            self.getlistsNews(url)
        elif name == 'news':
            self.getlistsNews(page)

    #Episodes will not display without this:
    #Episodes list
        elif name == 'episodelist':
            url = self.MAINURL + '/' + page
            self.getEpisodeList(url)


class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, diffanime(), False)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value=[GetLogoDir('diffanimelogo.png')])

    def getLinksForVideo(self, Index=0, selItem=None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG("ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index))
            return RetHost(RetHost.ERROR, value=[])

        if self.host.currList[Index]["type"] != 'video':
            printDBG("ERROR getLinksForVideo - current item has wrong type")
            return RetHost(RetHost.ERROR, value=[])
        urlItem = self.host.getVideoUrl(self.host.currList[Index]["page"])
        urlsTab = self.host.getVideoUrlforYTube(self.host.currList[Index]["page"])
        if config.plugins.iptvplayer.ytUseDF.value:
            def __getLinkQuality(itemLink):
                tab = itemLink['name'].split('x')
                return int(tab[0])
            urlsTab = urlsTab
        retlist = []
        if '' != urlItem:
            retlist.append(CUrlItem("diffanime", urlItem, 0))
        else:
            for urlItem in urlsTab:
                retlist.append(CUrlItem(urlItem['name'], urlItem['url'], 0))
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

