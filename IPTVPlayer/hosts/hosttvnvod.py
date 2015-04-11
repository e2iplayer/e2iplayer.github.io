# -*- coding: utf-8 -*-
# Based on (root)/trunk/xbmc-addons/src/plugin.video.polishtv.live/hosts/ @ 419 - Wersja 605

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher import aes_cbc, base
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
import re
import urllib
import time
import binascii
try:    import simplejson as json
except: import json
from os import urandom as os_urandom
try:
    from hashlib import sha1
except ImportError:
    import sha
    sha1 = sha.new
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.TVNDefaultformat = ConfigSelection(default = "4", choices = [("0", "Najgorsza"), ("1", "Bardzo niska"), ("2", "Niska"),  ("3", "Średnia"), ("4", "Standard"), ("5", "Wysoka"), ("6", "Bardzo wysoka"), ("7", "HD"), ("9999", "Najlepsza")])
config.plugins.iptvplayer.TVNUseDF = ConfigYesNo(default = False)
config.plugins.iptvplayer.TVNdevice = ConfigSelection(default = "Samsung TV", choices = [("Mobile (Android)", "Mobile (Android)"),("Samsung TV", "Samsung TV")])
config.plugins.iptvplayer.proxyenable = ConfigYesNo(default = False)
   
def GetConfigList():
    optionList = []

    optionList.append(getConfigListEntry("Domyślna jakość video:", config.plugins.iptvplayer.TVNDefaultformat))
    optionList.append(getConfigListEntry("Używaj domyślnej jakości video:", config.plugins.iptvplayer.TVNUseDF))
    optionList.append(getConfigListEntry("TVN-Przedstaw się jako:", config.plugins.iptvplayer.TVNdevice))
    optionList.append(getConfigListEntry("TVN-korzystaj z proxy?", config.plugins.iptvplayer.proxyenable))

    return optionList
###################################################

def gettytul():
    return 'TVN Player'

class TvnVod(CBaseHostClass):
    HOST         = 'Mozilla/5.0 (SmartHub; SMART-TV; U; Linux/SmartTV; Maple2012) AppleWebKit/534.7 (KHTML, like Gecko) SmartTV Safari/534.7'
    HOST_ANDROID = 'Apache-HttpClient/UNAVAILABLE (java 1.4)'
    ICON_URL     = 'http://redir.atmcdn.pl/scale/o2/tvn/web-content/m/%s?quality=50&dstw=290&dsth=287&type=1'
    
    QUALITIES_TABLE = { 
        'HD'            : 7,
        'Bardzo wysoka' : 6,
        'Wysoka'        : 5,
        'Standard'      : 4,
        'Średnia'       : 3,
        'Niska'         : 2,
        'Bardzo niska'  : 1,
    }
        
    SERVICE_MENU_TABLE = [
        "Kategorie",
        "Wyszukaj",
        "Historia wyszukiwania"
    ]
    
    def __init__(self):
        printDBG("TvnVod.__init__")
        CBaseHostClass.__init__(self, {'history':'TvnVod', 'proxyURL': config.plugins.iptvplayer.proxyurl.value, 'useProxy': config.plugins.iptvplayer.proxyenable.value})
        
        if config.plugins.iptvplayer.TVNdevice.value == 'Samsung TV':
            self.baseUrl = 'https://api.tvnplayer.pl/api?platform=ConnectedTV&terminal=Samsung&format=json&v=3.0&authKey=ba786b315508f0920eca1c34d65534cd'
            userAgent = TvnVod.HOST
        else:
            self.baseUrl = 'https://api.tvnplayer.pl/api?platform=Mobile&terminal=Android&format=json&v=3.1&authKey=4dc7b4f711fb9f3d53919ef94c23890c' #b4bc971840de63d105b3166403aa1bea
            userAgent = TvnVod.HOST_ANDROID
        
        self.cm.HEADER = {'User-Agent': userAgent, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        self.itemsPerPage = 30 # config.plugins.iptvplayer.tvp_itemsperpage.value
        self.loggedIn = None
        self.ACCOUNT  = False
        
    def _getJItemStr(self, item, key, default=''):
        v = item.get(key, None)
        if None == v:
            return default
        return clean_html(u'%s' % v).encode('utf-8')
        
    def _getJItemNum(self, item, key, default=0):
        v = item.get(key, None)
        if None != v:
            try:
                NumberTypes = (int, long, float, complex)
            except NameError:
                NumberTypes = (int, long, float)
                
            if isinstance(v, NumberTypes):
                return v
        return default
        
    def _getIconUrl(self, cItem):
        iconUrl = ''
        try:
            thumbnails = cItem.get('thumbnail', [])
            if None != thumbnails:
                # prefer jpeg files
                pngUrl = ''
                for item in thumbnails:
                    tmp = self._getJItemStr(item, 'url')
                    if tmp.endswith('jpg') or tmp.endswith('jpeg'):
                        iconUrl = tmp
                        break
                    if tmp.endswith('png'): pngUrl = tmp
                if '' == iconUrl: iconUrl = pngUrl
                if '' != iconUrl: iconUrl = TvnVod.ICON_URL % iconUrl
        except:
            printExc()
        return iconUrl
        
    def _generateToken(self, url):
        url = url.replace('http://redir.atmcdn.pl/http/','')
        SecretKey = 'AB9843DSAIUDHW87Y3874Q903409QEWA'
        iv = 'ab5ef983454a21bd'
        KeyStr = '0f12f35aa0c542e45926c43a39ee2a7b38ec2f26975c00a30e1292f7e137e120e5ae9d1cfe10dd682834e3754efc1733'
        salt = sha1()
        salt.update(os_urandom(16))
        salt = salt.hexdigest()[:32]
        tvncrypt = aes_cbc.AES_CBC(SecretKey, base.noPadding(), keySize=32)
        key = tvncrypt.decrypt(binascii.unhexlify(KeyStr), iv=iv)[:32]
        expire = 3600000L + long(time.time()*1000) - 946684800000L
        unencryptedToken = "name=%s&expire=%s\0" % (url, expire)
        pkcs5_pad = lambda s: s + (16 - len(s) % 16) * chr(16 - len(s) % 16)
        pkcs5_unpad = lambda s : s[0:-ord(s[-1])]
        unencryptedToken = pkcs5_pad(unencryptedToken)
        tvncrypt = aes_cbc.AES_CBC(binascii.unhexlify(key), padding=base.noPadding(), keySize=16)
        encryptedToken = tvncrypt.encrypt(unencryptedToken, iv=binascii.unhexlify(salt))
        encryptedTokenHEX = binascii.hexlify(encryptedToken).upper()
        return "http://redir.atmcdn.pl/http/%s?salt=%s&token=%s" % (url, salt, encryptedTokenHEX)
        
    def listsCategories(self, cItem):
        printDBG("TvnVod.listsCategories cItem[%s]" % cItem)
        
        searchMode = False
        page = 1 + cItem.get('page', 0)
        if 'search' == cItem.get('category', None):
            #https://api.tvnplayer.pl/api/?v=3.1&platform=Mobile&terminal=Android&format=json&authKey=4dc7b4f711fb9f3d53919ef94c23890c&limit=30&sort=&m=getSearchItems&isUserLogged=0&page=1&query=film
            searchMode = True
            urlQuery  = '&sort=newest&m=getSearchItems&page=%d&query=%s' % (page, cItem['pattern'])
        elif None != cItem.get('category', None) and None != cItem.get('id', None):
            groupName = 'items'
            urlQuery = '&type=%s&id=%s&limit=%s&page=%s&sort=newest&m=getItems' % (cItem['category'], cItem['id'], self.itemsPerPage, page)
            if 0 < cItem.get('season', 0):
                urlQuery += "&season=%d" % cItem.get('season', 0)
        else:
            groupName = 'categories'
            urlQuery = '&m=mainInfo'
        
        try:
            url = self.baseUrl + urlQuery
            sts, data = self.cm.getPage(url)
            data = json.loads(data)
            
            if 'success' != data['status']:
                printDBG("TvnVod.listsCategories status[%s]" % data['status'])
                return 
                
            countItem = self._getJItemNum(data, 'count_items', None)
            if None != countItem and countItem > self.itemsPerPage * page:
                showNextPage = True
            else:
                showNextPage = False
            
            catalogs = False
            if searchMode:
                seasons = None
                tmp = []
                for resItem in data.get('vodProgramItems', {}).get('category', []):
                    tmp.extend(resItem.get('items', []))
                for resItem in data.get('vodArticleItems', {}).get('program', []):
                    tmp.extend(resItem.get('items', []))
                data = tmp
                tmp = None
            else:
                seasons  = data.get('seasons', None)
                # some fix for sub-categories
                # and 0 < len(data.get('items', []))
                if 0 < len(data.get('categories', [])) and cItem.get('previd', '') != cItem.get('id', ''):
                    catalogs = True
                    groupName = 'categories'
                    showNextPage = False
                data = data[groupName]
            
            showSeasons = False
            if None != seasons and 0 == cItem.get('season', 0):
                showSeasons = True
                numSeasons = len(seasons)
            else:
                numSeasons = 0

            if 0 != cItem.get('season', 0) or cItem.get('season', 0) == numSeasons:
                for item in data:
                    category = self._getJItemStr(item, 'type', '')
                    id       = self._getJItemStr(item, 'id', '')
                    # some fix for sub-categories
                    if catalogs:
                        if 'category' == category:
                            category = 'catalog'
                        if '0' == id:
                            id = cItem['id']
                    
                    # get title 
                    title = self._getJItemStr(item, 'name', '')
                    if '' == title: title = self._getJItemStr(item, 'title', _('Brak nazwy'))
                    tmp = self._getJItemStr(item, 'episode', '')
                    if tmp not in ('', '0'): title += _(", odcinek ") + tmp
                    tmp = self._getJItemStr(item, 'season', '')
                    if tmp not in ('', '0'): title += _(", sezon ") + tmp
                    try:
                        tmp = self._getJItemStr(item, 'start_date', '')
                        if '' != tmp:
                            tmp = time.strptime(tmp, "%Y-%m-%d %H:%M")
                            if tmp > time.localtime():
                                title += _(" (planowany)")
                    except:
                        printExc()
                    
                    # get description
                    desc = self._getJItemStr(item, 'lead', '')
                    # get icon
                    icon = self._getIconUrl(item)
                
                    params = { 'id'       : id,
                               'previd'   : cItem.get('id', ''),
                               'title'    : title,
                               'desc'     : desc,
                               'icon'     : icon,
                               'category' : category,
                               'season'   : 0,
                             }
                    if 'episode' == category:
                        self.addVideo(params)
                    else:
                        self.addDir(params)
            else:
                showNextPage = False
            
            if showSeasons:
                for season in seasons:
                    params = { 'id'       : cItem['id'],
                               'previd'   : cItem.get('id', ''),
                               'title'    : self._getJItemStr(season, 'name', ''),
                               'desc'     : '',
                               'icon'     : self._getIconUrl(season),
                               'category' : cItem['category'], #self._getJItemStr(season, 'type', ''),
                               'season'   : self._getJItemNum(season, 'id', 0),
                             }
                    self.addDir(params)
            if showNextPage:
                params = dict(cItem)
                params.update({'title':_('Następna strona'), 'page': page, 'icon':'', 'desc':''})
                self.addDir(params)
        except: 
            printExc()

        
    def listSearchResults(self, pattern, searchType):
        printDBG("TvnVod.listSearchResults pattern[%s], searchType[%s]" % (pattern, searchType))
        params = { 'id'       : 0,
                   'title'    : '',
                   'desc'     : '',
                   'icon'     : '',
                   'category' : 'search',
                   'pattern'  : pattern,
                   'season'   : 0,
                 }
        self.listsCategories(params)

    def listsMainMenu(self):
        for item in TvnVod.SERVICE_MENU_TABLE:
            params = {'name': 'category', 'title': item, 'category': item}
            self.addDir(params)
    
    def resolveLink(self, url):
        printDBG("TvnVod.resolveLink url[%s]" % url)
        videoUrl = ''
        if len(url) > 0:
            if config.plugins.iptvplayer.TVNdevice.value == 'Mobile (Android)':
                videoUrl = self._generateToken(url).encode('utf-8')
            elif config.plugins.iptvplayer.TVNdevice.value == 'Samsung TV':
                sts, data  = self.cm.getPage(url)
                if sts and data.startswith('http'):
                    videoUrl =  data.encode('utf-8')
        return videoUrl
            
    def getLinksForVideo(self, cItem):
        return self.getLinks(cItem['id'])
    
    def getLinks(self, id):
        printDBG("TvnVod.getLinks cItem.id[%r]" % id )
        videoUrls = []
        
        url = self.baseUrl + '&type=episode&id=%s&limit=%d&page=1&sort=newest&m=%s' % (id, self.itemsPerPage, 'getItem')
        sts, data = self.cm.getPage(url)
        if sts:
            try:
                data = json.loads(data)
                if 'success' == data['status']:
                    data = data['item']
                    # videoTime = 0
                    # tmp = self._getJItemStr(data, 'run_time', '')
                    # if '' != tmp:
                        # tmp = tmp.split(":")
                        # videoTime = int(tmp[0])*60*60+int(tmp[1])*60+int(tmp[2])
                     
                    plot = self._getJItemStr(data, 'lead', '')
                    printDBG("data:\n%s\n" % data)
                    videos = data['videos']['main']['video_content']

                    for video in videos:
                        url = self._getJItemStr(video, 'url', '')
                        #if '' == url:
                        #    url = self._getJItemStr(video, 'src', '')
                        if '' != url:
                            qualityName = self._getJItemStr(video, 'profile_name', '')
                            videoUrls.append({'name':qualityName, 'profile_name':qualityName, 'url':url, 'need_resolve':1})
                    if  1 < len(videoUrls):
                        max_bitrate = int(config.plugins.iptvplayer.TVNDefaultformat.value)
                        def __getLinkQuality( itemLink ):
                            return int(TvnVod.QUALITIES_TABLE.get(itemLink['profile_name'], 9999))
                        videoUrls = CSelOneLink(videoUrls, __getLinkQuality, max_bitrate).getSortedLinks()
                        if config.plugins.iptvplayer.TVNUseDF.value:
                            videoUrls = [videoUrls[0]]
            except: printExc()
        return videoUrls
        
    def getFavouriteData(self, cItem):
        return str(cItem['id'])
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinks(fav_data)

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
        

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('TvnVod..handleService start')
        
        if None == self.loggedIn and self.ACCOUNT:
            self.loggedIn = self.tryTologin()
            if not self.loggedIn:
                self.sessionEx.open(MessageBox, 'Problem z zalogowaniem użytkownika "%s".' % self.LOGIN, type = MessageBox.TYPE_INFO, timeout = 10 )
            else:
                self.sessionEx.open(MessageBox, 'Zostałeś poprawnie \nzalogowany.', type = MessageBox.TYPE_INFO, timeout = 10 )
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        
        # clear hosting tab cache
        self.linksCacheCache = {}

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        printDBG( "TvnVod.handleService: ---------> name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsMainMenu()           
    #WYSZUKAJ
        elif category == "Wyszukaj":
            pattern = urllib.quote_plus(searchPattern)
            printDBG("Wyszukaj: " + pattern)
            self.listSearchResults(pattern, searchType)
    #HISTORIA WYSZUKIWANIA
        elif category == "Historia wyszukiwania":
            self.listsHistory()
    #KATEGORIE
        else:
            self.listsCategories(self.currItem)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, TvnVod(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('tvnvodlogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): RetHost(retCode, value=retlist)

        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            need_resolve = 1
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
    def getResolvedURL(self, url):
        # resolve url to get direct url to video file
        url = self.host.resolveLink(url)
        urlTab = []
        if isinstance(url, basestring) and url.startswith('http'):
            urlTab.append(url)
        return RetHost(RetHost.OK, value = urlTab)

    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = []
        
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
        description =  clean_html(cItem.get('desc', ''))
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
            printExc()
            return -1

    def setSearchPattern(self):
        try:
            list = self.host.getCurrList()
            if 'history' == list[self.currIndex].get('name', ''):
                pattern = list[self.currIndex]['title']
                search_type = ''
                self.host.history.addHistoryItem( pattern, search_type)
                self.searchPattern = pattern
                self.searchType = search_type
        except:
            printExc()
            self.searchPattern = ''
            self.searchType = ''
        return
