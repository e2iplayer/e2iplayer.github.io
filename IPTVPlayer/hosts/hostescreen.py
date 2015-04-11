# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, getF4MLinksWithMeta
###################################################

###################################################
# FOREIGN import
###################################################
import re
from Components.config import config, ConfigYesNo, ConfigText, getConfigListEntry, ConfigSelection
try:    import json
except: import simplejson as json
import urllib
from datetime import timedelta
import base64
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
config.plugins.iptvplayer.escreenHD        = ConfigYesNo(default = False)
config.plugins.iptvplayer.escreen_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.escreen_password = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.escreen_m3u1     = ConfigText(default = "http://iptv.e-screen.tv/?uid=", fixed_size = False)
config.plugins.iptvplayer.escreen_server   = ConfigSelection(default = "auto", choices = [("auto", "auto"),("0", _("1")),("1", _("2")),("2", _("3")),("list", _("lista"))])

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Kanały w jakości HD?"), config.plugins.iptvplayer.escreenHD))
    optionList.append(getConfigListEntry(_("Server:"), config.plugins.iptvplayer.escreen_server))
    optionList.append(getConfigListEntry(_("Escreen login:"), config.plugins.iptvplayer.escreen_login))
    optionList.append(getConfigListEntry(_("Escreen hasło:"), config.plugins.iptvplayer.escreen_password))
    optionList.append(getConfigListEntry(_("Adres listy M3U:"), config.plugins.iptvplayer.escreen_m3u1))
    return optionList
###################################################

def gettytul():
    return 'E-screenTV new'

class Escreen(CBaseHostClass):
    HEADER      = { 'User-Agent': 'XBMC', 'ContentType': 'application/x-www-form-urlencoded' }
    DEFPARAMS   = {'header':HEADER}
    MAINURLS    = 'https://xbmc.e-screen.tv/api'
    MAINURL     = 'http://xbmc.e-screen.tv/api'
    VERSION_URL = MAINURLS + '/version'
    LOGIN_URL   = MAINURLS + '/verify'
    MESSAGE_URL = MAINURLS + '/getmessage'
    MOVIE_TOKEN_URL = MAINURL + '/gettokenformovies'
    SERVERS_URL = MAINURL + '/getservers'
    EPG_URL = MAINURL + '/epg'
    #VERSION     = 2014121601
    #VERSION     = 2015011101
    VERSION      = 2015030101
    MAIN_TAB  = [{'category':'tv',            'title':_('Telewizja ONLINE'), 'url':MAINURLS+'/channels'},
                 {'category':'serialeonline', 'title':_('Seriale ONLINE'),   'url':MAINURL+'/getserialsonline'},
                 {'category':'filmy',         'title':_('FILMY'),            },
                 {'category':'bajki',         'title':_('BAJKI'),            'url':MAINURL+'/getbajki'}]
                 
    FILMS_CAT_TAB  = [{'category':'filmy_kategorie',      'title':_('Kategorie filmowe'), 'url':MAINURL+'/getmoviescategories'},
                     {'category': 'filmy_ostatniododane', 'title':_('Ostatnio dodane'),   'url':MAINURL+'/getmovieslatest'},
                     {'category': 'filmy_alfabetycznie',  'title':_('Alfabetycznie'),     'url':MAINURL+'/getmoviesalphabetically'},
                     {'category':'search',                'title':_('Search'), 'search_item':True},
                     {'category':'search_history',        'title':_('Search history')}]

   
    def __init__(self):
        printDBG("Escreen.__init__")
        CBaseHostClass.__init__(self, {'cookie':'escreen.cookie', 'history':'escreen.tv'})
        self.versionnet = 0
        
    def addM3UListCategory(self):
        printDBG("Escreen.addM3UListCategory")
        if 'http://iptv.e-screen.tv/?uid=' != config.plugins.iptvplayer.escreen_m3u1.value:
            params = {'name':'category', 'title':'Lista M3U', 'category':'m3u_list'}
            self.addDir(params)
                
    def listM3uLists(self, cItem):
        printDBG("Escreen.listM3uLists")
        sts,data = self.cm.getPage( config.plugins.iptvplayer.escreen_m3u1.value )
        if not sts: return
        data = data.split('#EXTINF:-1')
        if len(data): del data[0]
        tmpTab = []
        for item in data:
            idx = item.find('rtmp://')
            if -1 == idx: idx = item.find('http://')
            if -1 == idx: idx = item.find('https://')
            if -1 != idx:
                url = item[idx:].strip()
                if url != 'http://e-screen.tv':
                    icon  = self.cm.ph.getSearchGroups(item, 'tvg-logo="([^"]+?)"')[0]
                    title = self.cm.ph.getSearchGroups(item, 'tvg-id="([^"]+?)"')[0].strip()
                    server  = self.cm.ph.getSearchGroups(item, 'group-title="([^"]+?)"')[0]
                    added = False
                    for tmp in tmpTab:
                        printDBG(">>> [%s] [%s]" % (tmp['title'], title) )
                        if tmp['title'] == title: 
                            tmp['desc'] += server + ' '
                            exists = False
                            for tmpUrl in tmp['urls']: 
                                if tmpUrl['url'] == url: 
                                    exists = True
                                    break
                            if not exists: tmp['urls'].append({'name':server+' ', 'url':url})
                            added = True
                            break
                    if added: continue
                    params = {'title':title, 'urls':[{'name':server, 'url':url}], 'url':'', 'desc':server, 'icon':icon}
                    tmpTab.append(params)
        for params in tmpTab:
            params.update({'link_type':'m3u'})
            self.addVideo(params)
            
    def getPosterID(self):
        printDBG("Escreen.getPosterID")
        self.hash = self.login(True)
        if len(self.hash) > 3:
            postdata = { 'user': self.username, 'pass': self.hash, 'token': 'XBMC' } 
            sts, data = self.cm.getPage(Escreen.MOVIE_TOKEN_URL, Escreen.DEFPARAMS, postdata)
            if not sts: return None
            return self.getStr(data)
        return None
    
    def getServers(self):
        printDBG("Escreen.getServers")
        rtmpservers = []
        self.hash = self.login(True)
        if len(self.hash) > 3:
            postdata = { 'user': self.username, 'pass': self.hash } 
            sts, data = self.cm.getPage(Escreen.SERVERS_URL, Escreen.DEFPARAMS, postdata)
            if not sts: return None
            try:
                data = byteify(json.loads(data))
                for item in data: rtmpservers.append({'name':item['servername'], 'url':item['serverurl']})
            except: printExc()
        return rtmpservers
        
    def selectServers(self, servers, autoRtmpserver=''):
        printDBG("Escreen.selectServers")
        if '' == autoRtmpserver: 
            if len(servers): rtmpservers = [servers[0]]
            else: return []
        else: rtmpservers = [{'name':'auto', 'url':autoRtmpserver}]
        if 'auto' == config.plugins.iptvplayer.escreen_server.value: return rtmpservers
        try:
            if 'list' == config.plugins.iptvplayer.escreen_server.value and len(servers): rtmpservers = servers
            elif config.plugins.iptvplayer.escreen_server.value in ['0','1','2']: return [servers[int(config.plugins.iptvplayer.escreen_server.value)]]
        except: printExc()
        return rtmpservers

    def getStr(self, v, default=''):
        if type(v) == type(u''): return v.encode('utf-8')
        elif type(v) == type(''):  return v
        return default
        
    def listsTab(self, tab, cItem):
        printDBG("Escreen.listsMainMenu")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            self.addDir(params)
    
    def checkVersion(self):
        printDBG("Escreen.checkVersion")
        msg = _('Problem z pobraniem wersji online.')
        sts,data = self.cm.getPage(Escreen.VERSION_URL, Escreen.DEFPARAMS, {})
        if sts:
            try:
                data = json.loads(data)
                self.versionnet = data
                printDBG("Escreen.checkVersion versionnet[%s]" % self.versionnet)
                if self.versionnet > Escreen.VERSION:
                    msg = _('e-screen.tv wydał nowy plugin dla XBMC w wersji "%s".\nObecna wersja Twojego plugina to "%s".\nMoże to prowadzić do błędów w jego działaniu.' % (self.versionnet, Escreen.VERSION) )
                    sts = False
                else: msg = ''
            except: printExc()
        return sts,msg
        
    def checkMessage(self):
        printDBG("Escreen.checkMessage")
        msg = ''
        sts,data = self.cm.getPage(Escreen.MESSAGE_URL, Escreen.DEFPARAMS, { 'version': Escreen.VERSION})
        if not sts: return msg
        try:
            data = json.loads(data)
            for item in data:
                if '1' == item['active']:
                    msg += '\n' + item['msg_pl']
                    #msg += item['msg_en
            msg = self.getStr(msg)
        except: printExc()
        return msg
        
    def _showInfoMessage(self, msg, silent):
        if silent: return
        self.sessionEx.waitForFinishOpen(MessageBox, msg, type=MessageBox.TYPE_INFO, timeout=10)
        
    def login(self, silent=False):
        printDBG("Escreen.login")
        hash = ''
        postdata = { 'user': self.username, 'pass': self.password } 
        premiumInfo, msg = self.checkPremium()
        msg = '\n' + msg
        sts, data = self.cm.getPage(Escreen.LOGIN_URL, Escreen.DEFPARAMS, postdata)
        if sts:
            hash = self.cm.ph.getSearchGroups(data, '"hash":"([^"]+?)"')[0]
            if '' == hash: self._showInfoMessage( _('Problem z zalogowaniem użytkownika "%s".%s') % (self.username, msg), silent )
            else: self._showInfoMessage( _('Użytkownik "%s" zalogowany poprawnie.\n%s\n%s') % (self.username, msg, premiumInfo), silent )
        else: self._showInfoMessage( _('Brak polaczenia z Internetem lub blad serwera.%s') % msg, silent )
        return hash
        
    def checkPremium(self):
        printDBG("Escreen.checkPremium")
        premiumInfo = _('PREMIUM: nieznane')
        msg = _('Łącza są zbyt obciążone. Musisz posiadać konto premium.')
        url = 'http://pl.e-screen.tv/logowanie'
        HOST = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.18) Gecko/20110621 Mandriva Linux/1.9.2.18-0.1mdv2010.2 (2010.2) Firefox/3.6.18'
        HEADER = {'User-Agent': HOST, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Referer':url}
        
        http_params = {'header': HEADER, 'use_cookie': True, 'save_cookie': False, 'load_cookie': False, 'cookiefile': self.COOKIE_FILE}
        postdata = {'email':self.username, 'password':self.password, 'remember_me':'0'}
        sts, data = self.cm.getPage(url, http_params, postdata)
        if sts:
            tmp = self.cm.ph.getDataBeetwenMarkers(data, 'id="status" href="#">', '</a>', False)[1]
            msg = self.cm.ph.getSearchGroups(tmp, 'title="([^"]+?)"')[0]
            data = self.cm.ph.getSearchGroups(data, '(<p>Premium: <span class.+?</p>)')[0]
            if '' != data:
                premiumInfo = self.cleanHtmlStr(data)
        return premiumInfo, msg
        
    def _mapChannelItem(self, item):
        try:
            if config.plugins.iptvplayer.escreenHD.value:
                hdquality = "true"
            else: hdquality = "false"
            url        = ''
            channelname = self.getStr(item['channel'])
            icon       = self.getStr(item['icon'])
            sd         = self.getStr(item['sd'])
            hd         = self.getStr(item['hd'])
            rtmpserver = self.getStr(item['rtmpserver'])
            live       = self.getStr(item['live'])
            sendauth   = self.getStr(item['sendauth'])
            provider   = self.getStr(item['provider'])
            app        = self.getStr(item['app'])
            
            if 0 == len(sd) and 0 < len(hd): stream = hd
            else: stream = sd
            
            autoRtmpserver = rtmpserver
            rtmpserver = '%s'
            if (provider == "0"):
                urlbase2 = rtmpserver+'/'+app+'/'
                if (sendauth == "yes"):
                    urlbase2 = rtmpserver+'/'+app+'?user='+self.username+'#pass='+self.hash+'/'
                urlparams=' swfUrl=flowplayer.swf pageUrl=http://pl.e-screen.tv flashVer=XBMC live='+live #' swfVfy=true'
                if ((hdquality == "true") and (len(hd)>0)):
                    url = urlbase2+hd+urlparams
                else:
                    url = urlbase2+sd+urlparams
            elif (provider == "1"):
                if ((hdquality == "true") and (len(hd)>0)):
                    channelquality = hd
                else:
                    if ((len(sd) == 0) and (len(hd)>0)):
                        channelquality = hd
                    else:
                        channelquality = sd
                token = 'XBMC'+str(Escreen.VERSION)
                urlbase2 = rtmpserver+'/'+app+'/'+channelquality
                if (sendauth == "yes"):
                    urlbase2 = rtmpserver+'/'+app+'/'+channelquality+'?user='+self.username+'&pass='+self.hash+'&token='+token
                
                urlparams=' swfUrl=flowplayer.swf pageUrl=http://pl.e-screen.tv flashVer=XBMC live='+live #' swfVfy=true'
                url = urlbase2+urlparams
            elif (provider == "2"):
                url = rtmpserver+'/'+app+'/'+sd
            if len(url):
                self.addVideo({'title':channelname, 'stream':stream, 'icon':icon, 'url':url, 'link_type':'channel', 'rtmpserver':autoRtmpserver})
        except: printExc()
            
    def _mapSeriesItem(self, item):
        try:
            if config.plugins.iptvplayer.escreenHD.value:
                hdquality = "true"
            else: hdquality = "false"
            channelname = self.getStr(item['channel'])
            icon        = self.getStr(item['icon'])
            url         = self.getStr(item['url'])
            rtmpserver  = self.getStr(item['rtmpserver'])
            live        = self.getStr(item['live'])
            sendauth    = self.getStr(item['sendauth'])
            provider    = self.getStr(item['provider'])
            app         = self.getStr(item['app'])
            if (provider == "1"):
                token = 'XBMC'+str(Escreen.VERSION)
                urlbase2 = rtmpserver+'/'+app+'/'+url
                if (sendauth == "yes"):
                    urlbase2 = rtmpserver+'/'+app+'/'+url+'?user='+self.username+'&pass='+self.hash+'&token='+token
                urlparams=' swfUrl=flowplayer.swf pageUrl=http://pl.e-screen.tv flashVer=XBMC live='+live #' swfVfy=true'
                url = urlbase2+urlparams
            elif (provider == "2"):
                url = rtmpserver+'/'+app+'/'+url
            if len(url):
                self.addVideo({'title':channelname, 'icon':icon, 'url':url, 'link_type':'series'})
        except: printExc()
        
    def _mapBajkiItem(self, item):
        try:
            if config.plugins.iptvplayer.escreenHD.value:
                hdquality = "true"
            else: hdquality = "false"
            
            title    = self.getStr(item['title'])
            videourl = self.getStr(item['videourl'])
            cover    = self.getStr(item['cover'])
            server   = self.getStr(item['server'])
            provider = self.getStr(item['provider'])
            protocol = self.getStr(item['protocol'])
            token = 'XBMC'+str(Escreen.VERSION)
            if (provider == "0"):
                urlbase2 = protocol+server+'/'+videourl+'?user='+self.username+'&pass='+self.hash+'&token='+token
                urlparams=' swfUrl=flowplayer.swf pageUrl=http://pl.e-screen.tv flashVer=XBMC live=0 '# swfVfy=true'
                url = urlbase2+urlparams
            elif (provider == "1"): url = protocol + server+'/' + videourl
            if len(url):
                self.addVideo({'title':title, 'icon':cover, 'url':url, 'link_type':'cartoon'})
        except: printExc()
        
    def _mapFilmyKategorieItem(self, item):
        try:
            genre    = self.getStr(item['genre'])
            title    = genre.capitalize()
            url      = Escreen.MAINURL+'/getmoviesbycategory'
            postdata = {'kategoria': genre} 
            self.addDir({'name':'category', 'category':'filmy_kategorie_lista', 'postdata':postdata, 'title':title, 'icon':'', 'url':url})
        except: printExc()
        
    def _mapFilmyVideoItem(self, item):
        try:
            title       = self.getStr(item['title'])
            server      = self.getStr(item['server'])
            videourl    = self.getStr(item['url'])
            cover       = self.getStr(item['cover'])
            year        = self.getStr(item['year'])
            description = self.getStr(item['description'])
            duration    = self.getStr(item['duration'])
            desc        = "Rok: %s | Czas trwania: %s | %s" % (year, str(timedelta(minutes=int(duration))), description)
            url         = 'http://'+server+'/'+videourl
            self.addVideo({'title':title, 'icon':cover, 'url':url, 'desc':desc, 'link_type':'movie'})
        except: printExc()
    
    def _mapFilmyAlfabetycznie(self, item):
        try:
            letter   = self.getStr(item['letter'])
            title    = letter.capitalize()
            url      = Escreen.MAINURL+'/getmoviesbyletter'
            postdata = {'letter': letter} 
            self.addDir({'name':'category', 'category':'filmy_kategorie_lista', 'postdata':postdata, 'title':title, 'icon':'', 'url':url})
        except: printExc()
        
    def listBase(self, cItem, mapFun, post={}):
        printDBG("Escreen.listTVChannels")
        url = cItem['url']
        sts, msg = self.checkVersion()
        msg = self.checkMessage()
        self.hash = self.login(True)
        postdata = cItem.get('postdata', {})
        postdata.update({ 'user': self.username, 'pass': self.hash })
        sts, data = self.cm.getPage(url, Escreen.DEFPARAMS, postdata)
        if sts:
            try:
                data = json.loads(data)
                for item in data:
                    mapFun(item)
            except: printExc()
            
    def getLinksForVideo(self, cItem):
        printDBG("Escreen.getLinksForVideo")
        urlsTab = []
        urls = cItem.get('urls', [])
        if 0 == len(urls): 
            url = cItem.get('url', '')
            type = cItem.get('link_type', '')
            if type in ['cartoon', 'movie']: 
                url += str(self.getPosterID()).strip()
                urls = [{'name':'e-screener.tv', 'url':url}]
            elif type == 'channel':
                serwers = self.selectServers( self.getServers(), cItem.get('rtmpserver', '') )
                for serv in serwers: urlsTab.append({'name':serv['name'], 'url':url % serv['url']})
            else: urls = [{'url':url}]
        else: urls = self.selectServers(urls)
        for item in urls:
            url = item.get('url', '')
            name = item.get('name', 'e-screener.tv')
            if '' == url: continue
            if '.m3u8' in url: urlsTab.extend( getDirectM3U8Playlist(url) )
            else: urlsTab.append({'name':name, 'url':url})
        return urlsTab
        
    def getArticleContent(self, cItem):
        printDBG("Escreen.getArticleContent")
        ret = []
        if 'stream' in cItem:
            postdata = { 'token': 'qwerty', 'stream': cItem['stream'] }
            sts, data = self.cm.getPage(Escreen.EPG_URL, Escreen.DEFPARAMS, postdata)
            if not sts: return ret
            printDBG(data)
            data = re.sub('(\[[^]]+?\])', '', data)
            ret = [ {'title':cItem['title'], 'text':self.getStr( data )} ]
        return ret
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('Escreen.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        self.currList = []
        
        self.username = config.plugins.iptvplayer.escreen_login.value
        self.password = config.plugins.iptvplayer.escreen_password.value
        
        if None == name:
            self.addM3UListCategory()
            sts, msg = self.checkVersion()
            if not sts: self.sessionEx.waitForFinishOpen(MessageBox, msg, type=MessageBox.TYPE_INFO, timeout=10)
            msg = self.checkMessage()
            if len(msg): self.sessionEx.waitForFinishOpen(MessageBox, msg, type=MessageBox.TYPE_INFO, timeout=10)
            if '@' in self.username and '' != self.password:
                self.hash = self.login()
                if '' !=  self.hash:
                    self.listsTab(Escreen.MAIN_TAB, {'name':'category'})
            else:
                self.sessionEx.waitForFinishOpen(MessageBox, _('Niepoprawne dane do logowania.\nProszę uzupełnić login i hasło.'), type=MessageBox.TYPE_INFO, timeout=10)
    # TV
        elif category == 'm3u_list':
            self.listM3uLists(self.currItem)
        elif category == 'tv':
            self.listBase(self.currItem, self._mapChannelItem)
    # SERIALE
        elif category == 'serialeonline':
            self.listBase(self.currItem, self._mapSeriesItem)
    # FILMY
        elif category == 'filmy':
            self.listsTab(Escreen.FILMS_CAT_TAB, {'name':'category'})
        elif category == 'filmy_kategorie':
            self.listBase(self.currItem, self._mapFilmyKategorieItem)
        elif category == 'filmy_kategorie_lista':
            self.listBase(self.currItem, self._mapFilmyVideoItem)
        elif category == 'filmy_ostatniododane':
            self.listBase(self.currItem, self._mapFilmyVideoItem)
        elif category == 'filmy_alfabetycznie':
            self.listBase(self.currItem, self._mapFilmyAlfabetycznie)
    # BAJKI
        elif category == 'bajki':
            self.listBase(self.currItem, self._mapBajkiItem)
    #WYSZUKAJ
        elif category in ["search"]:
            cItem = dict(self.currItem)
            searchfor = urllib.quote_plus(searchPattern)
            cItem.update({'search_item':False, 'name':'category', 'postdata':{'search': searchfor}, 'url':Escreen.MAINURL+'/getmoviesbysearch'}) 
            self.listBase(cItem, self._mapFilmyVideoItem)
    #HISTORIA WYSZUKIWANIA
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()
        CBaseHostClass.endHandleService(self, index, refresh)


class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Escreen(), True)

    def getLogoPath(self):  
        return RetHost(RetHost.OK, value = [GetLogoDir('escreenlogo.png')])
        
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
    def getArticleContent(self, Index = 0):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): RetHost(retCode, value=retlist)

        hList = self.host.getArticleContent(self.host.currList[Index])
        for item in hList:
            title  = item.get('title', '')
            text   = item.get('text', '')
            images = item.get("images", [])
            retlist.append( ArticleContent(title = title, text = text, images =  images) )
        return RetHost(RetHost.OK, value = retlist)
    # end getArticleContent

    def convertList(self, cList):
        hostList = []
        searchTypesOptions = []
    
        for cItem in cList:
            hostLinks = []
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
                url = cItem.get('url', '')
                if '' != url:
                    hostLinks.append(CUrlItem("Link", url, 0))
                
            title       =  cItem.get('title', '')
            description =  self.host.cleanHtmlStr(cItem.get('desc', ''))
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
        try:
            list = self.host.getCurrList()
            for i in range( len(list) ):
                if list[i]['category'] == 'search':
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