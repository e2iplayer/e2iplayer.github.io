# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
from base64 import b64decode
import re
import urllib
try:    import json
except: import simplejson as json
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.kinopecetowiec_filmssort = ConfigSelection(default = "data-premiery", choices = [("data-premiery", "dacie premiery"),("ocena", "ocenie"),("komentarze", "ilości komentarzy")]) 
config.plugins.iptvplayer.kinopecetowiec_premium   = ConfigYesNo(default = False)
config.plugins.iptvplayer.kinopecetowiec_login     = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.kinopecetowiec_password  = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("Sortuj filmy po: ", config.plugins.iptvplayer.kinopecetowiec_filmssort))
    optionList.append(getConfigListEntry("Użytkownik PREMIUM KinoPecetowiec?", config.plugins.iptvplayer.kinopecetowiec_premium))
    if config.plugins.iptvplayer.kinopecetowiec_premium.value:
        optionList.append(getConfigListEntry("  " + _("login") + ":", config.plugins.iptvplayer.kinopecetowiec_login))
        optionList.append(getConfigListEntry("  " + _("hasło") + ":", config.plugins.iptvplayer.kinopecetowiec_password))
    return optionList
###################################################

def gettytul():
    return 'KinoPecetowiec'

class KinoPecetowiec(CBaseHostClass):
    HOST = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.18) Gecko/20110621 Mandriva Linux/1.9.2.18-0.1mdv2010.2 (2010.2) Firefox/3.6.18'
    HEADER = {'User-Agent': HOST, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
    AJAX_HEADER = dict(HEADER)
    AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Cache-Control': 'no-cache'} )
    
    MAINURL = 'http://www.kino.pecetowiec.pl/'
    SERIALS_URL = MAINURL + 'seriale-online.html'
    
    #"Seriale",
    SERVICE_MENU_TABLE = [
        "Filmy",
        "Seriale",
        "Wyszukaj",
        "Historia wyszukiwania"
    ]
    
    # cat, lang, qual
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'KinoPecetowiec', 'cookie':'kinopecetowiec.cookie'})

        #Login data
        self.PREMIUM         = config.plugins.iptvplayer.kinopecetowiec_premium.value
        self.LOGIN           = config.plugins.iptvplayer.kinopecetowiec_login.value
        self.PASSWORD        = config.plugins.iptvplayer.kinopecetowiec_password.value
        self.filmssortField  = 'sort_field=%s&sort_method=desc' % config.plugins.iptvplayer.kinopecetowiec_filmssort.value
        self.loggedIn = None        
        self.linksCacheCache = {}
        self.serialCache     = []
        self.informedAboutLoginRequirements = False
            
    def _getfromJson(self, data, type='films'):
        try:
            data = json.loads(data)
            if  isinstance(data, dict):
                data['html'] = data['html'].encode('utf-8')
                if type == 'films':
                    data['moviesCount'] = int(data['moviesCount'])
                    data['promotedCount'] = int(data['moviesCount'])
                if 'lastPage' in data and None == data['lastPage']:
                    data['lastPage'] = False
                return True,data
        except:
            printExc()
        return False,{}
        
    def _getFullUrl(self, url):
        if 0 < len(url) and not url.startswith('http'):
            url =  self.MAINURL + url
        return url
        
    def listFilmsCategories(self, item, nextCategory):
        printDBG('KinoPecetowiec.listFilmsCategories')
        sts, data = self.cm.getPage(self.MAINURL + "kategorie.html")
        if False == sts:
            return
        params = {'name': 'category', 'title': '-- Wszystkie --', 'category': nextCategory, 'cat': 'kategorie'}
        self.addDir(params)

        data  = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="videosCategories">', '</ul>', False)[1]
        data  = re.compile('href="/?(filmy,[^,]+?)\.[^>]+?>(.+?)</a>', re.DOTALL).findall(data)
        for item in data:
            params = {'name': 'category', 'title': self.cleanHtmlStr(item[1]), 'category': nextCategory, 'cat': item[0]}
            self.addDir(params)
            
    def listFilmsFilters(self, cItem, nextCategory): 
        printDBG('KinoPecetowiec.listFilmsFilters cat[%s]' % cItem['cat'])
        sts, data = self.cm.getPage(self.MAINURL + cItem['cat'] + ".html")
        if False == sts:
            return
        data  = self.cm.ph.getDataBeetwenMarkers(data, '<div class="filter">', '</div>', False)[1]
        rawQFilters  = re.compile('href="/?%s,0,([^,]+?),wszystkie,dowolny-rok,,([^,.]+?)\..+?<b>([^<>"]+?)</b>.+?lass="number">([0-9]+?)<' % cItem['cat'], re.DOTALL).findall(data)
        rawLFilters  = re.compile('href="/?%s,0,([^,.]+?)\..+?<b>([^<>"]+?)</b>.+?lass="number">([0-9]+?)<' % cItem['cat'], re.DOTALL).findall(data)
        del data
        baseParams = dict(cItem)
        baseParams.update({'category': nextCategory, 'qual':'wszystkie', 'lang':'wszystkie'})
        
        params = dict(baseParams)
        params.update({'title': '-- Wszystkie --'})
        self.addDir( params )
        
        for item in rawQFilters:
            if 'Wszystkie' not in item[2] and 0 < int(item[3]):
                params = dict(baseParams)
                params.update({'title': self.cleanHtmlStr(item[2]) + ' (%s)' % item[3], 'lang': item[0], 'qual': item[1]})
                self.addDir( params )
        for item in rawLFilters:
            params = dict(baseParams)
            params.update({'title': self.cleanHtmlStr(item[1]) + ' (%s)' % item[2], 'lang': item[0]})
            self.addDir( params )
        
    def listFilms(self, cItem):
        printDBG("KinoPecetowiec.listFilms cItem[%r]" % cItem)
        page = cItem.get('page', '0')
        url = self.MAINURL + '%s,0,%s,wszystkie,dowolny-rok,,%s.html' % (cItem['cat'], cItem['lang'], cItem['qual']) + '?' + self.filmssortField + '&load=1&moviesCount=%s&promotedCount=%s' % (cItem.get('moviesCount', 0), cItem.get('promotedCount', 0),)
        HEADER = dict(self.AJAX_HEADER)
        HEADER['Referer'] = url
        http_params = {'header': HEADER}
        sts, data = self.cm.getPage( url, http_params, {'page':page} )
        if False == sts: return
        sts, data = self._getfromJson(data)
        if sts:
            nextPageItem = None
            # Unfortunately nextPage can not be checked based on filed 'lastPage'
            # because its contain wrong information sometimes
            #if False == data.get('lastPage', True):
            try:
                url = self.MAINURL + '%s,0,%s,wszystkie,dowolny-rok,,%s.html' % (cItem['cat'], cItem['lang'], cItem['qual']) + '?' + self.filmssortField + '&load=1&moviesCount=%s&promotedCount=%s' % (data.get('moviesCount', 0), data.get('promotedCount', 0),)
                sts, data2 = self.cm.getPage( url, http_params, {'page':str(int(page)+1)} )
                sts, data2 = self._getfromJson(data2)
                data2 = data2['html']
                if '</li>' in data2:
                    page = str(int(page)+1)
                    nextPageItem = dict(cItem)
                    nextPageItem['page'] = page
                    nextPageItem['title'] = 'Następna strona'
                    nextPageItem['moviesCount'] = data['moviesCount']
                    nextPageItem['promotedCount'] = data['promotedCount']
                del data2
            except:
                printExc()

            data = data['html'].split('</li>')
            self.listItems(itemsTab=data, itemType='video', nextPageItem=nextPageItem, addParams= {'lang': cItem['lang'], 'qual': cItem['qual']})
        
    def listItems(self, itemsTab, itemType, nextPageItem=None, getPlot=None, addParams={}):
        printDBG("KinoPecetowiec.listItems itemsTab.len[%d]" % (len(itemsTab)) )
        for item in itemsTab:
            icon  = self.cm.ph.getSearchGroups(item, 'src="([^"]+?jpg)"')[0]
            if '' == icon:
                icon  = self.cm.ph.getSearchGroups(item, "background-image: url\('([^']+?\.jpg)'")[0].replace('_vertical', '').replace('_horizontal', '').replace('_promo', '')
            url   = self.cm.ph.getSearchGroups(item, 'data-url="([^"]+?)"')[0]
            #if '' == url: url   = self.cm.ph.getSearchGroups(item, 'data-landing="([^"]+?)"')[0]
            #title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<h2>', '</h2>', False)[1] )
            #subTitle = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<h3>', '</h3>', False)[1] )
            title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<div class="t1">', '</div>', False)[1] )
            subTitle = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<div class="t2">', '</div>', False)[1] )
            if '' != subTitle:
                title += " (%s)" % subTitle

            if None == getPlot: plot = self.cm.ph.getDataBeetwenMarkers(item, '<div class="description">', '<a', False)[1]
            else:               plot = getPlot(item)
            plot  = self.cleanHtmlStr(plot)
            # validate data
            if '' == url or '' == title: continue
            url = self._getFullUrl(url)
            icon = self._getFullUrl(icon)
            
            if 'video' == itemType:
                params = {'title':title, 'url':url, 'icon':icon, 'plot': plot}
                params.update(addParams)
                self.addVideo(params)
            else:
                params = {'name': 'category', 'title':title, 'category': itemType, 'url':url, 'icon':icon, 'plot': plot}
                params.update(addParams)
                self.addDir(params)

        if None != nextPageItem:
            self.addDir(nextPageItem)
            
    def listsMainMenu(self, tab):
        for item in tab:
            params = {'name': 'category', 'title': item, 'category': item}
            self.addDir(params)
            
    def listSerialsAlphabeticallyMenu(self, cItem, nextCategory):
        printDBG("KinoPecetowiec.listSerialsAlphabeticallyMenu")
        sts, data = self.cm.getPage( self.SERIALS_URL )
        if not sts: 
            return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="filter">', '</ul>', False)[1]
        data = re.compile('<a href="/?(seriale-online,[^"]+?)">[^>]*?<b>([^<]+?)</b>[^>]*?<span[^>]+?class="number">([0-9]+?)<').findall(data)
        for item in data:
            url =  self._getFullUrl( item[0] )
            params = {'name': 'category', 'title': item[1] + ' (%s)' % item[2], 'category': nextCategory, 'url': url}
            self.addDir(params)
            
    def listSerials(self, cItem, nextCategory):
        printDBG("KinoPecetowiec.listSerialSeasons cItem[%r]" % cItem)
        sts, data = self.cm.getPage( cItem.get('url', '') )
        if False == sts: return
        url = cItem['url']
        page = cItem.get('page', '-1')
        if page != '-1':
            url += '&load'
            HEADER = dict(self.AJAX_HEADER)
        else:
            HEADER = dict(self.HEADER)
        HEADER['Referer'] = url
        http_params = {'header': HEADER}
        sts, data = self.cm.getPage( url, http_params, {'page':page} )
        if False == sts:
            return
        if page == '-1':
            tmp = {}
            if 'class="loadMore"' in data: 
                tmp['lastPage'] = False
            else:
                tmp['lastPage'] = True
            tmp['html'] = self.cm.ph.getDataBeetwenMarkers(data, '<a href="/seriale-online,wszystkie,0,data-dodania,desc.html">', '<div id="subNav">', False)[1]
            data = tmp
            del tmp
            sts = True
        else:
            sts, data = self._getfromJson(data, 'serials')
        if sts:
            nextPageItem = None
            if False == data.get('lastPage', True):
                page = str(int(page)+1)
                nextPageItem = dict(cItem)
                nextPageItem['page'] = page
                nextPageItem['title'] = 'Następna strona'
            data = data['html'].split('<li>')
            del data[0]
            self.listItems(itemsTab=data, itemType=nextCategory, nextPageItem=nextPageItem)
            
    def listSerialSeasons(self, cItem, category):
        printDBG("KinoPecetowiec.listSerialSeasons cItem[%r]" % cItem)
        self.serialCache = []
        sts, data = self.cm.getPage( cItem.get('url', '') )
        if False == sts: return
        plot = self.cm.ph.getDataBeetwenMarkers(data, 'itemprop="description">', '</p>', False)[1]
        plot = self.cleanHtmlStr(plot)
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="season">', '<div class="right">', False)[1]
        data = data.split('<div class="season">')

        season_idx = 0
        for idx in range(len(data)):
            seasonTitle = self.cm.ph.getDataBeetwenMarkers(data[idx], '<h3>', '</h3>', False)[1].strip()
            if seasonTitle.startswith('Sezon'):
                self.serialCache.append(data[idx])
                params = dict(cItem)
                params.update({'title': seasonTitle, 'plot':plot, 'season_idx': season_idx, 'category':category})
                self.addDir(params)
                season_idx += 1
            
    def listSerialEpisodes(self, cItem):
        printDBG("listSerialEpisodes")
        if cItem['season_idx'] < len(self.serialCache):
            data = self.serialCache[cItem['season_idx']].split('</li>')
            for item in data:
                item = re.search('href="/?([^"]+?)">[^<]*?<span class="number">([^<]+?)</span>([^<]+?)<', item)
                if item:
                    url   = self._getFullUrl(item.group(1))
                    title = self.cleanHtmlStr(item.group(2) + ". " + item.group(3))
                    params = dict(cItem)
                    params.update({'title': title, 'url':url})
                    self.addVideo(params)
        
    def listSearchResults(self, pattern, searchType):
        printDBG("KinoPecetowiec.listSearchResults pattern[%s], searchType[%s]" % (pattern, searchType))
        url = self.MAINURL + 'szukaj.html?query=%s&mID=' % pattern
        sts, data = self.cm.getPage( url )
        if False == sts: return
        
        if 'filmy' == searchType:
            sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'id="movies-res"', 'res">', False)
            category = 'video'
        else:
            sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'id="serials-res"', 'res">', False)
            category = 'serial_seasons_list'
        data = data.split('<li>')
        self.listItems(data, category)  

    def getLinks(self, verItem, playerType, prevTab=[]):
        printDBG("getLinks verItem[%r], playerType[%r]" % (verItem, playerType) )
        hostingTab = []
        HEADER = dict(self.HEADER)
        HEADER['Referer'] = verItem['url']
        params = {  'action'    :'getPlayer',
                    'playerType':playerType['val'],
                    'fileId'    :'' }
        if 'hosting' in verItem: params['hId'] = verItem['hosting']
        if 'version' in verItem: params['fileLang'] = verItem['version']
        if 'quality' in verItem: params['fileType'] = verItem['quality']
        if 'changed' in verItem: params['changed'] = verItem['changed']

        if 'free' == playerType['val']: http_params = {'header': HEADER}
        else: http_params = {'header': HEADER, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE}
        sts, data = self.cm.getPage(verItem['url'], http_params, params)

        if not sts or 'Player premium jest dostępny tylko dla' in data: 
            return hostingTab
        
        uniqueId = ''
        tmp = re.compile('<span class="dropdown--selected">([^<]+?)</span>').findall(data)
        for item in tmp: uniqueId += item 
        
        # check if already not exists
        for item in prevTab:
            if uniqueId == item['uniqueId']: return hostingTab
        
        try:
            quality = self.cleanHtmlStr(tmp[1])
            version = self.cleanHtmlStr(tmp[2])
        except: quality, version = verItem['quality'], verItem['version']
        
        #self.cm.ph.writeToFile('/tmp/test_%s_%s_%s.html' % (playerType['title'], verItem['lang'], verItem['type']), data)
        
        data = self.cm.ph.getSearchGroups(data, '<div id="player-element"[^>]+?data-key="([^>]+?)"[^>]+?>')[0]
        try: data = b64decode(data[2:]).replace('\\/', '/')
        except: data = ''
        if 'stream.streamo.tv' in data:
            videoUrl = self.cm.ph.getSearchGroups(data, '"url":"([^"]+?)"')[0]
            urlTitle = '%s %s' % (version, quality) #, playerType['val']
            hostingTab.append( {'name': urlTitle, 'url': videoUrl, 'uniqueId':uniqueId} )
        return hostingTab
        
            
    def getHostingTable(self, urlItem):
        printDBG("getHostingTable url[%s]" % urlItem['url'])
        hostingTab = []
        verTab = []
        if self.loggedIn: http_params = {'header': self.HEADER, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE}
        else: http_params = {'header': self.HEADER}
        
        sts, data = self.cm.getPage(urlItem['url'], http_params )
        if False == sts: return hostingTab
        
        # Get hosting table - hosting
        tmp = re.compile('<li[^<]+?data-s="([^"]+?)"[^<]+?data-hid="([^"]+?)"[^<]*?>([^<]+?)</li>').findall( self.cm.ph.getDataBeetwenMarkers(data, 'data-prop="hosting">', '</ul>', False)[1] )
        for item in tmp: 
            hostingTab.append( {'name':self.cleanHtmlStr(item[2]), 'url':strwithmeta(urlItem['url'], {'hosting':item[1]})} )
        return hostingTab
    
    def getVideoLinks(self, url):
        printDBG("kinopecetowiec.getVideoLinks url[%r]" % url)
        if not isinstance(url, strwithmeta): return []
        if 'hosting' not in url.meta: return []
        
        hosting = url.meta['hosting']
        hostingTab = []

        if self.loggedIn: http_params = {'header': self.HEADER, 'use_cookie': True, 'save_cookie': False, 'load_cookie': True, 'cookiefile': self.COOKIE_FILE}
        else: http_params = {'header': self.HEADER}
        
        sts, data = self.cm.getPage( url, http_params )
        if False == sts: return hostingTab
        
        # Get quality table - quality
        qualityTable = []
        tmp = re.compile('<li[^<]+?data-value="([^"]+?)"[^<]*?>([^<]+?)</li>').findall( self.cm.ph.getDataBeetwenMarkers(data, 'data-prop="quality">', '</ul>', False)[1] )
        for item in tmp: qualityTable.append({'name':self.cleanHtmlStr(item[1]), 'fileType':item[0]})
        
        # Get lang table - version
        langTable = []
        tmp = re.compile('<li[^<]+?data-value="([^"]+?)"[^<]*?>([^<]+?)</li>').findall( self.cm.ph.getDataBeetwenMarkers(data, 'data-prop="version">', '</ul>', False)[1] )
        for item in tmp: langTable.append({'name':self.cleanHtmlStr(item[1]), 'fileLang':item[0]})
        
        channged = ''
        for version in langTable:
            if '' == channged: channged = 'version'
            for quality in qualityTable:
                if '' == channged: channged = 'quality'
                verItem = {'url':url, 'hosting':hosting, 'quality':quality['fileType'], 'version':version['fileLang'], 'channged':channged}
                tmpTab = []
                if self.loggedIn:
                    tmpTab = self.getLinks(verItem, {'val': 'premium', 'title':'Premium'}, hostingTab)
                if 0 == len(tmpTab):
                    tmpTab = self.getLinks(verItem, {'val': 'free', 'title':'Free'}, hostingTab)
                hostingTab.extend(tmpTab)
                channged = ''
            channged = ''
        return hostingTab
        
    def tryTologin(self):
        printDBG('tryTologin start')
        if '' == self.LOGIN.strip() or '' == self.PASSWORD.strip():
            printDBG('tryTologin wrong login data')
            return False
        
        post_data = {'email':self.LOGIN, 'password':self.PASSWORD}
        params = {'header':self.HEADER, 'cookiefile':self.COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        sts, data = self.cm.getPage( self.MAINURL + "logowanie.html", params, post_data)
        if not sts:
            printDBG('tryTologin problem with login')
            return False
            
        if 'wyloguj.html' in data:
            printDBG('tryTologin user[%s] logged with VIP accounts' % self.LOGIN)
            return True
     
        printDBG('tryTologin user[%s] does not have status VIP' % self.LOGIN)
        return False
        
    def getArticleContent(self, idx):
        printDBG('KinoPecetowiec.getArticleContent idx[%s]' % idx)
        retList = []
        
        sts, data = self.cm.getPage( self.currList[idx]['url'] )
        if sts:
            title = self.cleanHtmlStr( self.cm.ph.getSearchGroups(data, 'property="og:title" content="([^"]+?)"')[0] )
            desc  = self.cleanHtmlStr( self.cm.ph.getSearchGroups(data, 'property="og:description" content="([^"]+?)"')[0] )
            icon  = self._getFullUrl( self.cm.ph.getSearchGroups(data, 'property="og:image" content="([^"]+?)"')[0] )
            if '' != desc:
                item = {}
                item['title']  = title
                item['text']   = desc
                item['images'] = [ {'title':'', 'author': '', 'url': icon} ]
                retList.append( item )
        return retList
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        if None == self.loggedIn and self.PREMIUM:
            self.loggedIn = self.tryTologin()
        
        return self.getHostingTable({'url':fav_data})

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('KinoPecetowiec.handleService start')
        
        if None == self.loggedIn and self.PREMIUM:
            self.loggedIn = self.tryTologin()
            if not self.loggedIn:
                self.sessionEx.open(MessageBox, 'Problem z zalogowaniem użytkownika "%s".' % self.LOGIN, type = MessageBox.TYPE_INFO, timeout = 10 )
            else:
                self.sessionEx.open(MessageBox, 'Zostałeś poprawnie \nzalogowany.', type = MessageBox.TYPE_INFO, timeout = 10 )
        
        if True != self.loggedIn and not self.informedAboutLoginRequirements:
            self.informedAboutLoginRequirements = True
            self.sessionEx.open(MessageBox, 'Aby móc oglądać video musisz być zalogowany, jesli nie masz konta zarejestruj się.\nhttp://www.kino.pecetowiec.pl/rejestracja.html', type = MessageBox.TYPE_INFO, timeout = 10 )
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        
        # clear hosting tab cache
        self.linksCacheCache = {}

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        printDBG( "KinoPecetowiec.handleService: ---------> name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsMainMenu(self.SERVICE_MENU_TABLE)           
    #FILMY
        elif category == "Filmy": # add sort filter
            self.listFilmsCategories(self.currItem, 'films_filters')
        elif category == 'films_filters':
            self.listFilmsFilters(self.currItem, 'films_list')
        elif category == "films_list":
            self.listFilms(self.currItem)
    #SERIALE
        elif category == "Seriale":
            self.listSerialsAlphabeticallyMenu(self.currItem, 'serials_list')
        elif category == "serials_list":
            self.listSerials(self.currItem, 'serial_seasons_list')
        elif category == "serial_seasons_list":
            self.listSerialSeasons(self.currItem, 'serial_episodes_list')
        elif category == "serial_episodes_list":
            self.listSerialEpisodes(self.currItem)
    #WYSZUKAJ
        elif category == "Wyszukaj":
            printDBG("Wyszukaj: " + searchType)
            pattern = urllib.quote_plus(searchPattern)
            self.listSearchResults(pattern, searchType)
    #HISTORIA WYSZUKIWANIA
        elif category == "Historia wyszukiwania":
            self.listsHistory()


class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, KinoPecetowiec(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('kinopecetowieclogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): RetHost(retCode, value=retlist)
        
        urlList = self.host.getHostingTable(self.host.currList[Index])
        for item in urlList:
            need_resolve = 1
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
        
    def getArticleContent(self, Index = 0):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): RetHost(retCode, value=retlist)

        hList = self.host.getArticleContent(Index)
        for item in hList:
            title  = self.host.cleanHtmlStr( item.get('title', '') )
            text   = self.host.cleanHtmlStr( item.get('text', '') )
            images = item.get("images", [])
            retlist.append( ArticleContent(title = title, text = text, images =  images) )
        return RetHost(RetHost.OK, value = retlist)

    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        searchTypesOptions.append(("Filmy", "filmy"))
        searchTypesOptions.append(("Seriale", "seriale"))
    
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
        description =  self.host.cleanHtmlStr(cItem.get('plot', ''))
        icon        =  cItem.get('icon', '')
        
        return CDisplayListItem(name = title,
                                description = description,
                                type = type,
                                urlItems = hostLinks,
                                urlSeparateRequest = 1,
                                iconimage = icon,
                                possibleTypesOfSearch = possibleTypesOfSearch)
    # end converItem

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
