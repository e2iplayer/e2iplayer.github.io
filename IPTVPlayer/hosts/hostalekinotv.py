# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
###################################################

###################################################
# FOREIGN import
###################################################
import re
import urllib
import time
try:
    import json
except:
    import simplejson as json
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
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
config.plugins.iptvplayer.alekinotv_premium = ConfigYesNo(default = False)
config.plugins.iptvplayer.alekinotv_login = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.alekinotv_password = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []

    optionList.append(getConfigListEntry("Użytkownik PREMIUM AleKinoTV?", config.plugins.iptvplayer.alekinotv_premium))
    if config.plugins.iptvplayer.alekinotv_premium.value:
        optionList.append(getConfigListEntry("  AleKinoTV login:", config.plugins.iptvplayer.alekinotv_login))
        optionList.append(getConfigListEntry("  AleKinoTV hasło:", config.plugins.iptvplayer.alekinotv_password))

    return optionList
###################################################

def gettytul():
    return 'AleKinoTV'

class AleKinoTV(CBaseHostClass):
    MAINURL = 'http://alekino.tv'
    # movies, series
    FILMS_URL = MAINURL + '/filmy?'
    FILMS_HD_URL = MAINURL + '/filmy/hd?'
    LAST_ADDED_URL = MAINURL + '/ajax/recent/'
    
    SERIALS_URL = MAINURL + '/seriale'
    TOP_100_URL = MAINURL + '/top100/'
    SEARCH_URL = MAINURL + '/szukaj?query='
    LOG_URL = MAINURL + '/auth/login'

    SERVICE_MENU_TABLE = {
        1: "Filmy",
        2: "Seriale",
        3: "Ostatnio dodane",
        #4: "Top 100",
        5: "Wyszukaj",
        6: "Historia wyszukiwania"
    }
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'AleKinoTV', 'cookie':'alekinotv.cookie'})
        
        #Login data
        self.PREMIUM = config.plugins.iptvplayer.alekinotv_premium.value
        self.LOGIN = config.plugins.iptvplayer.alekinotv_login.value
        self.PASSWORD = config.plugins.iptvplayer.alekinotv_password.value
        
        self.loggedIn = None
    
    def tryTologin(self):
        printDBG('tryTologin start')
        if '' == self.LOGIN.strip() or '' == self.PASSWORD.strip():
            printDBG('tryTologin wrong login data')
            return False
        HTTP_HEADER= { 'Host':'alekino.tv',
                       'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0',
                       'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                       'Referer':self.LOG_URL }
        post_data = {'username':self.LOGIN, 'password':self.PASSWORD, 'auto_login':'1', 'submit_login':'login', 'submit':''}
        params = {'header':HTTP_HEADER, 'cookiefile':self.COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        sts, data = self.cm.getPage( self.LOG_URL, params, post_data)
        if not sts:
            printDBG('tryTologin problem with login')
            return False
            
        if -1 != data.find('status: VIP'):
            printDBG('tryTologin user[%s] logged with VIP accounts' % self.LOGIN)
            return True
     
        printDBG('tryTologin user[%s] does not have status VIP' % self.LOGIN)
        return False


    def setTable(self):
        return self.SERVICE_MENU_TABLE

    def listsMainMenu(self, table):
        for num, val in table.items():
            params = {'name': 'main-menu', 'title': val, 'category': val}
            self.addDir(params)
    
    def listsSerialsABCMenu(self, cat):
        table = self.cm.makeABCList()
        for item in table:
            params = {'name': 'category', 'category': cat, 'title': item}
            self.addDir(params)
            
    def getSerialsListByLetter(self, baseUrl, cat, letter):
        letter = letter.replace(' ', '')
        printDBG("getSerialsListByLetter start letter=%s" % letter)
        sts, data = self.cm.getPage( baseUrl )
        if False == sts:
            printDBG("getSerialsListByLetter problem with getPage[%s]" % baseUrl)
            return
            
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, 'id="letter_%s">' % letter, '</ul>', False)
        if False == sts:
            printDBG("getSerialsListByLetter problem no data beetween markers")
            return

        data = re.compile('<a href="([^"]+?)" class="pl-corners">(.+?)</a>').findall(data)
        if len(data) > 0:
            for i in range(len(data)):
                title = remove_html_markup(data[i][1])
                url = self.MAINURL + data[i][0].strip() 
                params = {'name':'category', 'category':cat, 'title':title, 'url':url}
                self.addDir(params)

    def getSerialEpisods(self, baseUrl, cat, icon):
        printDBG("getSerialEpisods start baseUrl[%s]" % baseUrl)
        sts, data = self.cm.getPage( baseUrl )
        if False == sts:
            printDBG("getSerialEpisods problem")
            return
        # img
        match = re.search('<div class="span2">[^<]*?<img src="([^"]+?)" alt=""/>', data)
        if match: img = match.group(1)
        else: img = icon
        # plot
        match = re.search('<div class="span10 w">([^<]+?)</div>', data)
        if match: plot = match.group(1)
        else: plot = ''

        data = re.compile('>Sezon ([0-9]+?)</button>').findall(data)
        if len(data) > 0:
            for i in range(len(data)):
                params = {'name':'category', 'category':cat, 'title':'Sezon ' + data[i], 'url':baseUrl, 'page':data[i], 'icon': img, 'plot':plot}
                self.addDir(params)
                
    def getSerialEpisodItems(self, url, episode, icon):
        printDBG("getSerialEpisodItems start url=[%s] episode[%s]" % (url, episode) )
        sts, data = self.cm.getPage( url )
        if False == sts:
            printDBG("getSerialEpisodItems problem")
            return
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, 'id="sezon_%s"' % episode, '</div>', False)
        if False == sts:
            printDBG("getSerialEpisodItems problem no data beetween markers")
            return
            
        data = re.compile('<a class="o" href="([^"]+?)">([^<]+?)</a>').findall(data)
        if len(data) > 0:
            for i in range(len(data)):
                params = {'name':'category', 'title':data[i][1], 'url':self.MAINURL + data[i][0], 'icon': icon,}
                self.addVideo(params)
        
            
    def addMoviesFilter(self, baseUrl, cat, filter):
        printDBG("addMoviesFilter start filter=%s" % filter)
        sts, data = self.cm.getPage( baseUrl )
        if False == sts:
            printDBG("addMoviesFilter problem with getPage[%s]" % baseUrl)
            return

        # Add Filmy HD type
        if 'types' == filter:
            params = {'name': 'category', 'category': cat, 'title':'Filmy HD', 'url': baseUrl + 'quality[0]=hd&'}
            self.addDir(params)

        data = re.compile('<li class="filterParent"><a href="#" data-type="filter" data-value="([0-9]+?)" data-filter="' + filter + '\[\]">([^<]+?)</a>(.*?)</li>').findall(data)
        if len(data) > 0:
            for i in range(len(data)):
                title = data[i][1] + data[i][2].replace('<span class="w">', '').replace('</span>', '')
                url = "%s%s[0]=%s&" % (baseUrl, filter, data[i][0])
                params = {'name': 'category', 'category': cat, 'title':title, 'url': url }
                self.addDir(params)
    
    def addAllCategoryItem(self, url, cat):
        # wszystkie
        params = {'name': 'category', 'category': cat, 'title':'--Wszystkie--', 'url': url }
        self.addDir(params)

    def getLastAddedCatManu(self, LAST_ADDED_MENU_TABLE, url, cat):
        for item in LAST_ADDED_MENU_TABLE:
            params = {'name': 'category', 'category': cat, 'sub_cat':item['cat'], 'title': item['title'], 'url': url + item['mode'], 'mode':item['mode'] }
            self.addDir(params)
                        
    def getLastAdded(self, baseUrl, cat, sub_cat, mode, page):
        printDBG("getLastAdded for url[%s] page[%s]" % (baseUrl, page) )
        
        HTTP_HEADER= { 'Host':'alekino.tv',
                       'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0',
                       'Referer':self.MAINURL + '/',
                       'X-Requested-With':'XMLHttpRequest' }
        if page == '1':
            strPage = ''
            postPage = '0'
        else:
            strPage = '?page=' + page
            postPage = page
        post_data = { 'dostep' : 'true', 'mode':mode, 'days':'0', 'page':postPage }
        sts, data = self.cm.getPage( baseUrl + strPage, {'header':HTTP_HEADER}, post_data)
        if False == sts:
            printDBG("getLastAdded problem")
            return
        
        # next page?
        nextPage = False
        if -1 != data.find('rel="next"'):
            nextPage = True
            
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, '<div style="padding-bottom:0px;">', '<div class="pagination-recent">', True)
        if False == sts:
            printDBG("getLastAdded problem no data beetween markers")
            return
        data = data.split('<div style="padding-bottom:0px;">')
        if len(data) > 1:
            del data[0]
            for item in data:
                item = item.replace('<br/>', '')
                # url & title
                match = re.search('<a class="movie-title-hover" href="([^"]+?)"[^>]+?>([^<]+?)</a>', item)
                if match: 
                    url = self.MAINURL + match.group(1)
                    title = match.group(2).replace('\n', '').replace('\r', '').strip()
                else: continue
                # img
                match = re.search('<img src="([^"]+?)"', item)
                if match: img = match.group(1)
                else: img = ''
                # plot
                match = re.search('<div class="clearfix"></div>([^<]+?)</div>', item)
                if match: plot = match.group(1)
                else: plot = ''
                
                params = { 'title': title, 'url': url, 'icon': img, 'plot': plot}
                if sub_cat == '':
                    self.addVideo(params)
                else:
                    params['name']='category'
                    params['category']=sub_cat 
                    self.addDir(params)
        #pagination
        if nextPage:
            params = {'name': 'category', 'category': cat, 'sub_cat':sub_cat, 'title': 'Następna strona', 'url': baseUrl, 'mode':mode, 'page': str(int(page) + 1)}
            self.addDir(params)
        
         
    def getMoviesList(self, baseUrl, cat, page):
        printDBG("getMoviesList for url[%s], page[%s]" % (baseUrl, page))
        if page == '1':
            strPage = ''
        else:
            strPage = 'p=' + page
        sts, data = self.cm.getPage( baseUrl + strPage )
        if False == sts:
            printDBG("getMoviesList problem")
            return
            
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, '<!-- Listing film', 'Regulamin', False)
        if False == sts:
            printDBG("getMoviesList problem no data beetween markers")
            return
            
        data = data.split('movie-item')
        if len(data) > 1:
            del data[0]

            # next page?
            nextPage = False
            if -1 != data[-1].find('rel="next"'):
                nextPage = True
            
            for item in data:
                # url & title
                match = re.search('<a class="title" href="([^"]+?)">(.+?)</a>', item)
                if match: 
                    url = self.MAINURL + match.group(1)
                    title = match.group(2).replace('<small>', '').replace('</small>', '')
                else: continue
                # img
                match = re.search('style="background-image:url\(([^)]+?)\);"', item)
                if match: img = match.group(1)
                else: img = ''
                # plot
                match = re.search('<p class="desc">([^<]+?)</p>', item)
                if match: plot = match.group(1)
                else: plot = ''
                
                params = { 'title': title, 'url': url, 'icon': img, 'plot': plot}
                self.addVideo(params)
                
            #pagination
            if nextPage:
                params = {'name': 'category', 'category': cat, 'title': 'Następna strona', 'url': baseUrl, 'page': str(int(page) + 1)}
                self.addDir(params)
               
    def getTop100CatManu(self, LAST_ADDED_MENU_TABLE, url, cat):
        for item in LAST_ADDED_MENU_TABLE:
            params = {'name': 'category', 'category': cat, 'title': item['title'], 'url': url + item['mode'] }
            self.addDir(params)

    def getTop100Cat(self, baseUrl, cat):
        printDBG("getTop100Cat for url[%s]" % baseUrl)
        sts, data = self.cm.getPage( baseUrl )
        if False == sts:
            printDBG("getTop100Cat problem")
            return
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, '<form method="POST" id="changecat">', '</select>', False)
        if False == sts:
            printDBG("getTop100Cat problem no data beetween markers")
            return
            
        data = re.compile('<option value="([^"]+?)" >([^<]+?)</option>').findall(data)
        if len(data) > 0:
            for i in range(len(data)):
                params = {'name':'category', 'category':cat, 'title':data[i][1], 'url':baseUrl, 'mode':data[i][0]}
                self.addDir(params)
               
    def getTop100(self, baseUrl, mode): 
        printDBG("getTop100 for url[%s]" % baseUrl)
        post_data = { 'kategoria' : mode }
        sts, data = self.cm.getPage( baseUrl, {}, post_data)
        if False == sts:
            printDBG("getTop100 problem")
            return
            
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, '<div class="ew-top-100"', '</section></div>', True)
        if False == sts:
            printDBG("getTop100 problem no data beetween markers")
            return
        data = data.split('<div class="ew-top-100"')
        if len(data) > 1:
            del data[0]
            place = 1
            for item in data:
                # url & title
                match = re.search('<a href="([^"]+?)" class="en">([^<]+?)</a>[^<]*?<a href="[^"]+?" class="pl">([^<]*?)</a>', item)
                if match: 
                    url = self.MAINURL + match.group(1)
                    title = str(place) + '. ' + match.group(2) + ' / ' + match.group(3)
                    place = place + 1
                else: continue
                # img
                match = re.search('<img src="([^"]+?)"', item)
                if match: img = match.group(1)
                else: img = ''
                # plot
                match = re.search('<p[^>]*?>([^<]+?)</p>', item)
                if match: plot = match.group(1).strip()
                else: plot = ''
                
                params = { 'title': title, 'url': url, 'icon': img, 'plot': plot}
                self.addVideo(params)
            
    def getSearchResult(self, baseUrl, cat, searchType):
        printDBG("getSearchResult for url[%s] searchType[%s]" % (baseUrl, searchType) )

        sts, data = self.cm.getPage( baseUrl )
        if False == sts:
            printDBG("getSearchResult problem")
            return
        
        if 'filmy' == searchType:
            marer1 = '<div class="results_title">[^<]*?Filmy:[^<]*?</div>'
            marer2 = '<div class="results_title">'
        else:
            marer1 = '<div class="results_title">[^<]*?Seriale:[^<]*?</div>'
            marer2 = '<div class="results_title">'
        
        sts, data = CParsingHelper.getDataBeetwenReMarkers(data, re.compile(marer1), re.compile(marer2), False)
        if False == sts:
            printDBG("getSearchResult problem no data beetween markers")
            return

        data = data.split('<div class="result box pl-round"')
        if len(data) > 1:
            del data[0]
            for item in data:
                item = item.replace('<br/>', '')
                # url & title
                match = re.search('<a href="([^"]+?)" class="en pl-white">([^<]+?)</a>', item)
                if match: 
                    url = self.MAINURL + match.group(1)
                    title = match.group(2).replace('\n', '').replace('\r', '').strip()
                else: continue
                # img
                match = re.search('<img src="([^"]+?)"', item)
                if match: img = match.group(1)
                else: img = ''
                # plot
                match = re.search('<p>([^<]+?)</p>', item)
                if match: plot = match.group(1)
                else: plot = ''
                
                params = { 'title': title, 'url': url, 'icon': img, 'plot': plot}
                if cat == '':
                    self.addVideo(params)
                else:
                    params['name']='category'
                    params['category']=cat 
                    self.addDir(params)

    def getHostingTable(self, url):
        printDBG("getHostingTable for url[%s]" % url)

        links = []
        if self.loggedIn:
            printDBG("getHostingTablefor premium user")
            links = self.getLink(url, 'vip')
            
        if [] == links:
            printDBG("getHostingTablefor standard user")
            links = self.getLink(url)
            
        return links
            
    def getLink(self, url, type = 'standard'):
        printDBG('getLink type[%s] for url[%s]' % (type, url))
        
        HTTP_HEADER= { 'Host':'alekino.tv',
                       'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0',
                       'Accept':'*/*',
                       'X-Requested-With':'XMLHttpRequest',
                       'Referer':url }

        params = {}
        if type == 'vip':
            params = {'cookiefile':self.COOKIE_FILE, 'use_cookie': True, 'load_cookie':True, 'save_cookie':True} 
        params['header'] = HTTP_HEADER
      
        sts, data = self.cm.getPage( url, params )
        if False == sts:
            printDBG("getLink getPage problem")
            return []
            
        # get movie ID    
        match = re.search('data-type="player" data-version="%s" data-id="([^"]+?)">' % type, data)
        if None == match:
            printDBG("getLink a player for %s version not found!" % type)
            return []
        # get movie hash
        t = int(round(time.time() * 1000))
        initPlayerURL = self.MAINURL + '/players/init/' + match.group(1) + '?mobile=false&t=' + str(t)
        sts, data = self.cm.getPage( initPlayerURL, params )
        if False == sts:
            printDBG("getHostingTable get initPlayerURL problem")
            return []
        movieHash = ''
        waitTime = 0
        try:
            jsonObj = json.loads(data)
            movieHash = jsonObj.get('data').encode('utf-8')
            try:
                waitTime = int(jsonObj.get('ads').get('wait')) + 1
            except: 
                waitTime = 21
        except:
            printDBG('getHostingTable json problem')
            return []
            
        # get hosting URL
        playerURL = self.MAINURL + '/players/get?t=' + str(t + waitTime*1000)
        post = {'hash': movieHash}
        if type == 'vip':
            post['type'] = 'vip'
        sts, data = self.cm.getPage( playerURL, params, post)
        if False == sts:
            printDBG("getHostingTable problem with get page with playerURL")
            return []   
        #CParsingHelper.writeToFile("/home/test/testAleKino.html", data)
        direct_url = ''
        if type == 'vip':
            data = re.search("ShowNormalPlayer\('([^']+?)'", data)
            if data: direct_url = data.group(1) + '?start=0'
        else:
            data = re.search('src="([^"]+?)"', data)
            if data: direct_url = data.group(1)

        if '' == direct_url:
            printDBG("getHostingTable host URL not found!")
            return []
        
        printDBG('getHostingTable hostingURL |%s|' % direct_url)
        return [{'name':type, 'url': direct_url}]
        
    def getVideoLinks(self, url):
        printDBG("getVideoLinks url[%r]" % url)
        if 'alekino.tv' in url:
            try:
                query_data = { 'url': url, 'return_data': False }       
                response = self.cm.getURLRequestData(query_data)
                url = response.geturl() 
                response.close()
            except: 
                printExc()
                return []
        return self.up.getVideoLinkExt( url )
        
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        if None == self.loggedIn and self.PREMIUM:
            self.loggedIn = self.tryTologin()
            if not self.loggedIn:
                self.sessionEx.open(MessageBox, 'Problem z zalogowaniem użytkownika "%s" jako VIP.' % self.LOGIN, type = MessageBox.TYPE_INFO, timeout = 10 )
            else:
                self.sessionEx.open(MessageBox, 'Zostałeś poprawnie \nzalogowany jako VIP.', type = MessageBox.TYPE_INFO, timeout = 10 )
                
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        title    = self.currItem.get("title", '')
        category = self.currItem.get("category", '')
        sub_cat  = self.currItem.get("sub_cat", '')
        page     = self.currItem.get("page", '1')
        icon     = self.currItem.get("icon", '')
        url      = self.currItem.get("url", '')
        mode     = self.currItem.get("mode", '')
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsMainMenu(self.SERVICE_MENU_TABLE)
    #FILMY
        elif category == "Filmy":
            # filtr by category
            self.addAllCategoryItem(self.FILMS_URL, 'movies_category')
            self.addMoviesFilter(self.FILMS_URL, 'movies_category', 'genres')
        elif category == 'movies_category':
            # filtr by type
            self.addAllCategoryItem(url, 'movies_types')
            self.addMoviesFilter(url, "movies_types", 'types')
        elif category == "movies_types":
            # list movies in category
            self.getMoviesList(url, category, page)
    #SERIALE
        elif category == "Seriale":
            self.listsSerialsABCMenu('list_serials_abc')
        elif category == "list_serials_abc":
            self.getSerialsListByLetter(self.SERIALS_URL, 'list_serials_episods', title)
        elif category == 'list_serials_episods':
            self.getSerialEpisods(url, 'list_serials_episod_items', icon)
        elif category == 'list_serials_episod_items':
            self.getSerialEpisodItems(url, page, icon)
    #OSTATNIO DODANE
        elif category == "Ostatnio dodane":
            LAST_ADDED_MENU_TABLE = [ {'title':'Filmy', 'mode':'movie', 'cat':''}, 
                                      {'title':'Seriale', 'mode':'serie', 'cat':'list_serials_episods'},
                                      {'title':'Odcinki seriali', 'mode':'serie_episode', 'cat':''} ]
            self.getLastAddedCatManu(LAST_ADDED_MENU_TABLE, self.LAST_ADDED_URL, 'last_added')
        elif category == 'last_added':
            self.getLastAdded(url, category, sub_cat, mode, page)
    #TOP 100
        elif category == "Top 100":
            # add mode to url
            TOP_100_MENU_TABLE = [ {'title':'Najwyżej ocenione', 'mode':'rate'}, 
                                   {'title':'Najczęściej oglądane', 'mode':'views'},
                                   {'title':'Ulubione', 'mode':'views'} ] #total
            self.getTop100CatManu(TOP_100_MENU_TABLE, self.TOP_100_URL, 'top_100_cat')
        elif category == 'top_100_cat':
           self.addAllCategoryItem(url, 'top_100')
           self.getTop100Cat(url, 'top_100') 
        elif category == 'top_100':
           self.getTop100(url, mode) 
    #WYSZUKAJ
        elif category == "Wyszukaj":
            printDBG("Wyszukaj: " + searchType)
            pattern = urllib.quote_plus(searchPattern)
            if 'filmy' == searchType:
                self.getSearchResult(self.SEARCH_URL + pattern, '', searchType)
            elif 'seriale' == searchType:
                self.getSearchResult(self.SEARCH_URL + pattern, 'list_serials_episods', searchType)
            
    #HISTORIA WYSZUKIWANIA
        elif category == "Historia wyszukiwania":
            self.listsHistory()


class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, AleKinoTV(), True)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('alekinotvlogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] != 'video':
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])

        retlist = []
        urlList = self.host.getHostingTable(self.host.currList[Index]["url"])
        for item in urlList:
            need_resolve = 1
            if 'vip' == item["name"]:
                need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
    def getResolvedURL(self, url):
        # resolve url to get direct url to video file
        retlist = []
        urlList = self.host.getVideoLinks(url)
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    
        # resolve url to get direct url to video file
        url = self.host.up.getVideoLink( url )
        urlTab = []

        if isinstance(url, basestring) and url.startswith('http'):
            urlTab.append(url)

        return RetHost(RetHost.OK, value = urlTab)

    def convertList(self, cList):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        searchTypesOptions.append(("Seriale", "seriale"))
        searchTypesOptions.append(("Filmy", "filmy"))
    
        for cItem in cList:
            hostLinks = []
            type = CDisplayListItem.TYPE_UNKNOWN
            possibleTypesOfSearch = None

            if cItem['type'] == 'category':
                if cItem['title'] == 'Wyszukaj':
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
            description = clean_html(description.decode("utf-8")).encode("utf-8")
            icon        =  cItem.get('icon', '')
            
            hostItem = CDisplayListItem(name = title,
                                        description = description,
                                        type = type,
                                        urlItems = hostLinks,
                                        urlSeparateRequest = 1,
                                        iconimage = icon,
                                        possibleTypesOfSearch = possibleTypesOfSearch)
            hostList.append(hostItem)

        return hostList
    # end convertList

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
