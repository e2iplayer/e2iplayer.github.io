# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, remove_html_markup, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, getF4MLinksWithMeta, MYOBFUSCATECOM_OIO, MYOBFUSCATECOM_0ll, \
                                                               unpackJS, TEAMCASTPL_decryptPlayerParams, SAWLIVETV_decryptPlayerParams
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html, compat_parse_qs
from Plugins.Extensions.IPTVPlayer.libs.teledunet import  TeledunetParser
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.filmonapi import FilmOnComApi, GetConfigList as FilmOn_GetConfigList
from Plugins.Extensions.IPTVPlayer.libs.videostar import VideoStarApi, GetConfigList as VideoStar_GetConfigList
from Plugins.Extensions.IPTVPlayer.libs.satlive   import SatLiveApi, GetConfigList as SatLiver_GetConfigList
from Plugins.Extensions.IPTVPlayer.libs.weebtv    import WeebTvApi, GetConfigList as WeebTv_GetConfigList
from Plugins.Extensions.IPTVPlayer.libs.vidtvpl   import VidTvApi
from Plugins.Extensions.IPTVPlayer.libs.looknijtv import LooknijTvApi
from Plugins.Extensions.IPTVPlayer.libs.tvisportcbapl import TvSportCdaApi
from Plugins.Extensions.IPTVPlayer.libs.nettvpw   import NettvPw
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
import re
import time
import urllib
try:    import simplejson as json
except: import json
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry

try:    from urlparse import urlsplit, urlunsplit
except: pass
from hashlib import md5
############################################

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.SortowanieWebstream              = ConfigYesNo(default = False)
config.plugins.iptvplayer.weatherbymatzgprohibitbuffering  = ConfigYesNo(default = True)
config.plugins.iptvplayer.weather_useproxy                 = ConfigYesNo(default = False)
config.plugins.iptvplayer.fake_separator = ConfigSelection(default = " ", choices = [(" ", " ")])

def GetConfigList():
    optionList = []
    
    optionList.append(getConfigListEntry("----------VideoStar-----------", config.plugins.iptvplayer.fake_separator))
    try:    optionList.extend( VideoStar_GetConfigList() )
    except: printExc()
    
    optionList.append(getConfigListEntry("----------WeebTV----------", config.plugins.iptvplayer.fake_separator))
    try:    optionList.extend( WeebTv_GetConfigList() )
    except: printExc()
    
    optionList.append(getConfigListEntry("----------FilmOn TV----------", config.plugins.iptvplayer.fake_separator))
    try:    optionList.extend( FilmOn_GetConfigList() )
    except: printExc()
    
    optionList.append(getConfigListEntry("----------Web-Live TV----------", config.plugins.iptvplayer.fake_separator))
    try:    optionList.extend( SatLiver_GetConfigList() )
    except: printExc()
    
    optionList.append(getConfigListEntry(_("----------Other----------"), config.plugins.iptvplayer.fake_separator))
    optionList.append(getConfigListEntry("Wyłączyć możliwość buforowania dla http://prognoza.pogody.tv/", config.plugins.iptvplayer.weatherbymatzgprohibitbuffering))
    optionList.append(getConfigListEntry(_("Use Polish proxy for http://prognoza.pogody.tv/"), config.plugins.iptvplayer.weather_useproxy))
    return optionList

###################################################
# "HasBahCa"
def gettytul():
    return '"Web" streams player'
    
###################################################
# ToDo: move this code to the lib dir
from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher.aes_cbc import AES_CBC
from hashlib import md5
import binascii

def CryptoJS_AES_decrypt(encrypted, password, key_length=32):
    def derive_key_and_iv(password, salt, key_length, iv_length):
        d = d_i = ''
        while len(d) < key_length + iv_length:
            d_i = md5(d_i + password + salt).digest()
            d += d_i
        return d[:key_length], d[key_length:key_length+iv_length]

    bs = 16
    salt = encrypted[len('Salted__'):bs]
    key, iv = derive_key_and_iv(password, salt, key_length, bs)
    cipher = AES_CBC(key=key, keySize=32)
    return cipher.decrypt(encrypted[bs:], iv)
###################################################

class HasBahCa(CBaseHostClass):
    HTTP_HEADER= { 'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3' }
    # {'name': 'meczhd.tv',       'title': 'MeczHH TV',                         'url': 'http://meczhd.tv/',                                                  'icon': 'http://meczhd.tv/theme/img/logo.png'}, \
    # New links for webstream prepared by user @matzg
    MAIN_GROUPED_TAB = [#{'name': 'team-cast.pl',    'title': 'Team Cast',                         'url': '',                                                                   'icon': 'http://wrzucaj.net/images/2014/09/12/logo.png'}, \
                        #{'name': 'vidtv.pl',        'title': 'VidTV.pl',                          'url': '',                                                                   'icon': 'http://vidtv.pl/img/logotype4.png'}, \
                        {'name': 'weeb.tv',         'title': 'WeebTV',                            'url': '',                                                                   'icon': 'http://static.weeb.tv/images/weebtv-santahat1.png'}, \
                        {'name': 'videostar.pl',    'title': 'VideoStar',                         'url': '',                                                                   'icon': 'https://videostar.pl/assets/images/logo-40-cropped.jpg'}, \
                        {'name': 'goldvod.tv',      'title': 'Goldvod TV',                        'url': 'http://goldvod.tv/lista-kanalow.html',                               'icon': 'http://goldvod.tv/img/logo.png'}, \
                        {'name': 'web-live.tv',     'title': 'Web-Live TV',                       'url': '',                                                                   'icon': 'http://web-live.tv/themes/default/img/logo.png'}, \
                        #{'name': 'looknij.tv',      'title': 'Looknij.tv',                        'url': '',                                                                   'icon': 'http://looknij.tv/wp-content/uploads/2015/02/logosite.png'}, \
                        #{'name': 'tvisport.cba.pl', 'title': 'tvisport.cba.pl',                   'url': '',                                                                   'icon': 'http://tvisport.cba.pl/wp-content/uploads/2015/01/logonastrone.png'}, \
                        {'name': 'nettv.pw',        'title': 'NetTV.PW',                          'url': '',                                                                   'icon': 'http://i.imgur.com/djEZKmy.png'}, \
                        {'name': 'm3u',             'title': 'Kanały IPTV_matzgPL',               'url': 'http://matzg2.prv.pl/Lista_matzgPL.m3u',                             'icon': 'http://matzg2.prv.pl/Iptv_matzgPL.png'}, \
                        {'name': 'm3u',             'title': 'Kanały @gienektv',                  'url': 'https://www.dropbox.com/s/bk9tksbotr0e4dq/tunek.m3u?dl=1',           'icon': 'https://www.dropbox.com/s/eb6edvyh40b4dw3/gtv.jpg?dl=1'}, \
                        {'name': 'prognoza.pogody.tv','title': 'prognoza.pogody.tv',              'url': 'http://prognoza.pogody.tv',                                          'icon': 'http://s2.manifo.com/usr/a/A17f/37/manager/pogoda-w-chorwacji-2013.png'}, \
                        {'name': 'm3u',             'title': 'Prognoza Pogody matzg',             'url': 'http://matzg2.prv.pl/lista_pogoda.m3u',                              'icon': 'http://matzg2.prv.pl/pogoda.png'}, \
                        {'name': 'm3u',             'title': 'Pogoda METEOROGRAMY matzg',         'url': 'http://matzg2.prv.pl/Pogoda_METEOROGRAMY.m3u',                       'icon': 'http://matzg2.prv.pl/pogoda_logo.png'}, \
                        {'name': 'webcamera.pl',    'title': 'WebCamera PL',                      'url': 'http://www.webcamera.pl/',                                           'icon': 'http://www.webcamera.pl/img/logo80x80.png'}, \
                        {'name': 'm3u',             'title': 'Różne Kanały IPTV_matzg',           'url': 'http://matzg2.prv.pl/inne_matzg.m3u',                                'icon': 'http://matzg2.prv.pl/iptv.png'}, \
                        {'name': 'filmon_groups',   'title': 'FilmOn TV',                         'url': 'http://www.filmon.com/',                                             'icon': 'http://static.filmon.com/theme/img/filmon_tv_logo_white.png'}, \
                        {'name': 'm3u',             'title': 'Polskie Kamerki internetowe',       'url': 'http://database.freetuxtv.net/playlists/playlist_webcam_pl.m3u'}, \
                        {'name': 'HasBahCa',        'title': 'HasBahCa',                          'url': 'http://hasbahcaiptv.com/',                                           'icon': 'http://hasbahcaiptv.com/xml/iptv.png'}, \
                        {'name': 'm3u',             'title': 'Angielska TV',                      'url': 'http://database.freetuxtv.net/playlists/playlist_programmes_en.m3u'}, \
                        {'name': 'm3u',             'title': 'Radio-OPEN FM i inne',              'url':'http://matzg2.prv.pl/radio.m3u',                                      'icon': 'http://matzg2.prv.pl/openfm.png'}, \
                       ]
    def __init__(self):
        self.up = urlparser()
        self.cm = common()
        # temporary data
        self.currList = []
        self.currItem = {}
        
        #Login data
        self.sort = config.plugins.iptvplayer.SortowanieWebstream.value
        self.sessionEx = MainSessionWrapper()
        self.filmOnApi    = None
        self.videoStarApi = None
        self.satLiveApi   = None
        self.vidTvApi     = None
        self.looknijTvApi = None
        self.tvSportCdaApi= None
        self.nettvpwApi   = None
        self.weebTvApi    = None
        self.teamCastTab  = {}
        
    def _cleanHtmlStr(self, str):
        str = str.replace('<', ' <').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        return self.cm.ph.removeDoubles(clean_html(str), ' ').strip()
        
    def _getJItemStr(self, item, key, default=''):
        v = item.get(key, None)
        if None == v:
            return default
        return clean_html(u'%s' % v).encode('utf-8')
  
    def getCurrList(self):
        return self.currList

    def setCurrList(self, list):
        self.currList = list
        
    def getCurrItem(self):
        return self.currItem

    def setCurrItem(self, item):
        self.currItem = item

    def addDir(self, params):
        params['type'] = 'category'
        self.currList.append(params)
        return
        
    def playVideo(self, params):
        params['type'] = 'video'
        self.currList.append(params)
        return

    def listsMainMenu(self, tab, forceParams={}):
        for item in tab:
            params = dict(item)
            params.update(forceParams)
            self.addDir(params)
            
    def _listHasBahCaPromoted(self, cItem):
        url = cItem['url']
        printDBG("_listHasBahCaPromoted url[%s]" % url)
        sts,data = self.cm.getPage(url)
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, cItem['m1'], cItem['m2'], False)[1]
        data = data.split('</tr>')
        if len(data): del data[-1]
        for item in data:
            if 'm3u/IPTV' in item:
                url = self.cleanHtmlStr( self.cm.ph.getSearchGroups(item, "location.href='([^']+?)'")[0] )
                if not url.startswith('http'): url = 'http://hasbahcaiptv.com/' + url
                title = self.cleanHtmlStr(item)
                desc = self.cleanHtmlStr( self.cm.ph.getSearchGroups(item, 'title="([^"]+?)"')[0] )
                params = {'name': 'HasBahCa', 'category':'hasbahca_list', 'title':title, 'url':url, 'desc':desc}
                self.addDir(params)
            
    def _listHasBahCaList(self, cItem):
        printDBG("_listHasBahCaList")
        sts,data = self.cm.getPage(cItem['url'], {}, cItem.get('post', None))
        if not sts: return
        data = self.cm.ph.getDataBeetwenMarkers(data, '<table class="inhalt">', '<div class="box_oben_r">Login</div>', True)[1]
        data = data.split('<table class="inhalt">')
        if len(data): del data[0]
        for item in data:
            rows = item.split('</tr>')
            if 0 == len(rows): continue
            title = self.cleanHtmlStr(rows[0])
            del rows[0]
            if '' == title: title = self.cleanHtmlStr(rows[0])
            del rows[0]
            desc = ''
            for tr in rows:
                tmp = self.cleanHtmlStr(tr)
                if '' == tmp: continue
                desc += tmp + ', '
            url = self.cm.ph.getSearchGroups(item, ' title="DOWNLOAD"  href="([^"]+?)"')[0]
            if '' != url:
                if '' != desc: desc = desc[:-2]
                params = {'name': 'HasBahCa', 'category':'hasbahca_resolve', 'title':title, 'url':url, 'desc':desc}
                self.addDir(params)
        if 1 == len(self.currList):
            item = self.currList[0]
            self.currList = []
            self._listHasBahCaResolve(item)
            
    def _listHasBahCaFromTar(self, progress_key):
        sts, data = self.cm.getPage('http://www.convertfiles.com/convertrogressbar.php?progress_key=%s&i=1' % progress_key)
        if not sts: return
        url = self.cm.ph.getSearchGroups(data, 'href="([^"]+?\.tar)"')[0]
        if '' == url: return False
        self.m3uList(url)
        if len(self.currList): return True
        else: return False

    def _listHasBahCaResolve(self, cItem):
        url = cItem['url']
        printDBG("_listHasBahCaResolve url[%s]" % url)
        tmp = self.cm.ph.getSearchGroups(url+'"', '(http[^"]+?)"')[0]
        if '' != tmp: url = tmp
        
        query_data = { 'url': url, 'return_data': False }       
        response = self.cm.getURLRequestData(query_data)
        redirectUrl = response.geturl() 
        response.close()
        if redirectUrl != url: url = redirectUrl

        if url.startswith('http://adf.ly/'):
            sts, url = self.cm.getPage('http://www.bypassshorturl.com/get.php', {}, {'url':tmp})
            if not sts: return
            url = url.strip()
            printDBG("adf.ly [%s] -> [%s]" % (tmp, url))
        if url.endswith('.rar'):
            progress_key = md5(url+cItem['title']).hexdigest()[:14] #'a2yas1htyel27e' #url.split('/')[-1][:14]
            tries = 0
            while tries < 10:
                if self._listHasBahCaFromTar(progress_key): return
                post_data = [('APC_UPLOAD_PROGRESS', progress_key), ('MAX_FILE_SIZE', ''), ('storedOpt', '56'), ('FileOrURLFlag', 'url'), ('http_referer', ''),\
                             ('aid', ''), ('fakefilepc', ''), ('file_or_url', 'url'), ('download_url', url), ('youtube_mode', 'default'),\
                             ('input_format', '.rar'), ('output_format', '.tar'), ('email', '')]
                sts, data = self.cm.getPage('http://www.convertfiles.com/converter.php', {'multipart_post_data':True}, post_data)
                if not sts: continue
                while tries < 10:
                    time.sleep(1)
                    sts, data = self.cm.getPage('http://www.convertfiles.com/getprogress.php?progress_key=%s' % progress_key)
                    if not sts: continue
                    if '100' in data:
                        if not self._listHasBahCaFromTar(progress_key): break
                        return
                    tries += 1
                time.sleep(1)
                tries += 1
        if url.endswith('.m3u') or 'm3u' in url: self.m3uList(url)
    
    def listHasBahCa(self, cItem):
        url = cItem['url']
        category = cItem.get('category', 'hasbahca_main')
        printDBG("listHasBahCa url[%s]" % url)
        
        if 'hasbahca_main' == category:
            main = [{'category':'hasbahca_promoted',      'title':'New Links',      'url':'http://hasbahcaiptv.com/download.php', 'icon':'', 'm1':'<b>&nbsp;&nbsp;New Links </b>', 'm2':'</table>'},
                    {'category':'hasbahca_promoted',      'title':'Top Links',      'url':'http://hasbahcaiptv.com/download.php', 'icon':'', 'm1':'<b>&nbsp;&nbsp;Top Links</b', 'm2':'</table>'},
                    {'category':'hasbahca_list',          'title':'IPTV',           'url':'http://hasbahcaiptv.com/download.php', 'icon':'', 'post':{'action':'kategorie','kat_u':'','kat1':'1','kat_1':'2','kat_id':'1','spalte':'datum','sort':'ASC','dps':'150'}},
                    {'category':'hasbahca_list',          'title':'Movies-FILMLER', 'url':'http://hasbahcaiptv.com/download.php', 'icon':'', 'post':{'action':'kategorie','kat_u':'','kat1':'3','kat_1':'2','kat_id':'1','spalte':'datum','sort':'ASC','dps':'150'}},
                    ]
            self.listsMainMenu(main, {'name':'HasBahCa'})
        elif 'hasbahca_promoted' == category:
            self._listHasBahCaPromoted(cItem)
        elif 'hasbahca_list' == category:
            self._listHasBahCaList(cItem)
        elif 'hasbahca_resolve' == category:
            self._listHasBahCaResolve(cItem)
            
    def getDirectVideoHasBahCa(self, name, url):
        printDBG("getDirectVideoHasBahCa name[%s], url[%s]" % (name, url))
        videoTabs = []
        sts, data = self.cm.getPage( url )
        if sts:
            data = data.strip()
            if data.startswith('http'):
                videoTabs.append({'name':name, 'url':data})
        return videoTabs
            
    def __getFilmOnIconUrl(self, item):
        icon = u''
        try:
            icon = item.get('big_logo', '')
            if '' == icon: icon = item.get('logo_148x148_uri', '')
            if '' == icon: icon = item.get('logo', '')
            if '' == icon: icon = item.get('logo_uri', '')
        except:
            printExc()
        return icon.encode('utf-8')

    def __setFilmOn(self):
        if None == self.filmOnApi:
            self.filmOnApi = FilmOnComApi()
            
    def getFilmOnLink(self, channelID):
        self.__setFilmOn()
        return self.filmOnApi.getUrlForChannel(channelID)

    def getFilmOnGroups(self):
        self.__setFilmOn()
        tmpList = self.filmOnApi.getGroupList()
        for item in tmpList:
            try:
                params = { 'name'     : 'filmon_channels', 
                           'title'    : item['title'].encode('utf-8'), 
                           'desc'     : item['description'].encode('utf-8'), 
                           'group_id' : item['group_id'],
                           'icon'     : self.__getFilmOnIconUrl(item)
                           }
                self.addDir(params)
            except:
                printExc()

    def getFilmOnChannels(self):        
        self.__setFilmOn()
        tmpList = self.filmOnApi.getChannelsListByGroupID(self.currItem['group_id'])
        for item in tmpList:
            try:
                params = { 'name'     : 'filmon_channel', 
                           'title'    : item['title'].encode('utf-8'), 
                           'url'      : item['id'], 
                           'desc'     : item['group'].encode('utf-8'), 
                           'seekable' : item['seekable'],
                           'icon'     : self.__getFilmOnIconUrl(item)
                           }
                self.playVideo(params)
            except:
                printExc()
    
    def m3uList(self, listURL):
        printDBG('m3uList entry')
        params = {'header': self.HTTP_HEADER}
        sts, data = self.cm.getPage(listURL, params)
        if not sts:
            printDBG("getHTMLlist ERROR geting [%s]" % listURL)
            return
        data = data.replace("\r","\n").replace('\n\n', '\n').split('\n')
        #printDBG("[\n%s\n]" % data)
        title = ''
        for item in data:
            if item.startswith('#EXTINF:'):
                try:    title = item.split(',')[1]
                except: title = item
            else:
                if 0 < len(title):
                    item = item.replace('rtmp://$OPT:rtmp-raw=', '')
                    urlMeta = {}
                    itemUrl = self.up.decorateUrl(item, urlMeta)
                    params = {'title': title, 'url': itemUrl, 'desc': 'Protokół: ' + itemUrl.meta.get('iptv_proto', '')}
                    self.playVideo(params)
                    title = ''

    def getGoldvodList(self, url):
        printDBG('getGoldvodList entry url[%s]' % url)
        sts, data = self.cm.getPage(url)
        if not sts: return
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, 'id="liveTV-channels">', '</nav>', False)
        
        data = data.split('<li>')
        for item in data:
            printDBG("item [%r]" % item)
            try:
                params = {}
                params['url']   = "http://goldvod.tv" + re.search('href="([^"]+?)"', item).group(1) 
                params['icon']  = re.search('src="([^"]+?)"', item).group(1) 
                params['title'] = re.search('title="([^"]+?)"', item).group(1)
                params['desc']  = url
                self.playVideo( params )
            except:
                printExc()
        
    def getGoldvodLink(self, videoUrl):
        urlItems = self.up.getVideoLinkExt(videoUrl)
        if 0 < len(urlItems):
            return urlItems[0]['url']
        return ''
        
    def getSatLiveList(self, url):
        printDBG('getSatLiveList start')
        if None == self.satLiveApi:
            self.satLiveApi = SatLiveApi()
        tmpList = self.satLiveApi.getChannelsList()
        for item in tmpList:
            self.playVideo(item)
            
    def getSatLiveLink(self, url):
        printDBG("getSatLiveLink url[%s]" % url)
        return self.satLiveApi.getVideoLink(url)
        
    def getVidTvList(self, url):
        printDBG('getVidTvList start')
        if None == self.vidTvApi:
            self.vidTvApi = VidTvApi()
        if '' == url:
            tmpList = self.vidTvApi.getCategoriesList()
            for item in tmpList:
                params = dict(item)
                params.update({'name':'vidtv.pl'})
                self.addDir(params)
        else:
            tmpList = self.vidTvApi.getChannelsList(url)
            for item in tmpList: self.playVideo(item)
            
    def getVidTvLink(self, url):
        printDBG("getVidTvLink url[%s]" % url)
        return self.vidTvApi.getVideoLink(url)
        
    def getLooknijTvList(self, url):
        printDBG('getLooknijTvList start')
        if None == self.looknijTvApi:
            self.looknijTvApi = LooknijTvApi()
        if '' == url:
            tmpList = self.looknijTvApi.getCategoriesList()
            for item in tmpList:
                params = dict(item)
                params.update({'name':'looknij.tv'})
                self.addDir(params)
        else:
            tmpList = self.looknijTvApi.getChannelsList(url)
            for item in tmpList: self.playVideo(item)
            
    def getLooknijTvLink(self, url):
        printDBG("getLooknijTvLink url[%s]" % url)
        return self.looknijTvApi.getVideoLink(url)
        
    def getTvSportCdaList(self, url):
        printDBG('getTvSportCdaList start')
        if None == self.tvSportCdaApi:
            self.tvSportCdaApi = TvSportCdaApi()
        if '' == url:
            tmpList = self.tvSportCdaApi.getCategoriesList()
            for item in tmpList:
                params = dict(item)
                params.update({'name':'tvisport.cba.pl'})
                self.addDir(params)
        else:
            tmpList = self.tvSportCdaApi.getChannelsList(url)
            for item in tmpList: self.playVideo(item)
            
    def getTvSportCdaLink(self, url):
        printDBG("getTvSportCdaLink url[%s]" % url)
        return self.tvSportCdaApi.getVideoLink(url)
        
    def getNettvpwList(self, url):
        if None == self.nettvpwApi: self.nettvpwApi = NettvPw()
        tmpList = self.nettvpwApi.getChannelsList(url)
        for item in tmpList: self.playVideo(item)
            
    def getNettvpwLink(self, url):
        return self.nettvpwApi.getVideoLink(url)
    
    def getWeebTvList(self, url):
        printDBG('getWeebTvList start')
        if None == self.weebTvApi:
            self.weebTvApi = WeebTvApi()
        if '' == url:
            tmpList = self.weebTvApi.getCategoriesList()
            for item in tmpList:
                params = dict(item)
                params.update({'name':'weeb.tv'})
                self.addDir(params)
        else:
            tmpList = self.weebTvApi.getChannelsList(url)
            for item in tmpList: 
                item.update({'name':'weeb.tv'})
                self.playVideo(item)
            
    def getWeebTvLink(self, url):
        printDBG("getWeebTvLink url[%s]" % url)
        return self.weebTvApi.getVideoLink(url)

    def getTeamCastList(self, cItem):
        printDBG('getTeamCastList start')
        #http://team-cast.pl.cp-21.webhostbox.net/kanalyFlash/
        #http://team-cast.pl.cp-21.webhostbox.net/
        #src="http://team-cast.pl.cp-21.webhostbox.net/kanalyFlash/film/hbo.html"
        url = cItem['url']
        # list categories
        if '' == url :
            self.teamCastTab = {}
            url = 'http://team-cast.pl.cp-21.webhostbox.net/'
            sts, data = self.cm.getPage(url)
            if not sts: return
            data = CParsingHelper.getDataBeetwenMarkers(data, '<div id="stream-frame">', '<div id="now-watching">', False)[1]
            # remove commented channels
            data = re.sub('<!--[^!]+?-->', '', data)
            data = data.split('<li class="menu_right">')
            del data[0]
            for cat in data:
                catName  = CParsingHelper.getDataBeetwenMarkers(cat, '<a href="#" class="drop">', '</a>', False)[1].strip()
                channels = re.findall('<a href="([^"]+?)">([^<]+?)<img src="http://wrzucaj.net/images/2014/09/12/flash-player-icon.png"', cat)
                if len(channels): 
                    self.teamCastTab[catName] = channels
                    newItem = dict(cItem)
                    newItem.update({'url':catName, 'title':catName + ' (%d)' % len(channels)})
                    self.addDir(newItem)
        elif url in self.teamCastTab:
            # List channels
            for item in self.teamCastTab[url]:
                newItem = dict(cItem)
                newItem.update({'url':item[0], 'title':item[1]})
                self.playVideo(newItem)
        else:
            printExc()
                
    def getTeamCastLink(self, url):
        printDBG("getTeamCastLink url[%s]" % url)
        url = 'http://team-cast.pl.cp-21.webhostbox.net/' + url
        sts, data = self.cm.getPage(url)
        if not sts: return []
        url = self.cm.ph.getSearchGroups(data, """src=['"](http://team-cast.pl.cp-21.webhostbox.net[/]+?kanalyFlash/[^'^"]+?)['"]""")[0]
        
        sts, data = self.cm.getPage(url)
        if sts:
            O1I = self.cm.ph.getSearchGroups(data, "='([^']+?)'")[0] 
            if '' != O1I:
                try:
                    data2 = data
                    printDBG('-------------------------------------------')
                    printDBG('getTeamCastLink javascript pack detected')
                    printDBG('-------------------------------------------')
                    data = MYOBFUSCATECOM_OIO(MYOBFUSCATECOM_0ll(O1I))
                    data = data.strip()
                    data = data[data.find('}(')+2:-2]
                    data = unpackJS(data, TEAMCASTPL_decryptPlayerParams)
                    data = data[data.find('}(')+2:-2]
                    data = unpackJS(data, SAWLIVETV_decryptPlayerParams)
                    data = data[data.find('}(')+2:-2]
                    data = unpackJS(data, TEAMCASTPL_decryptPlayerParams)
                    data = self.cm.ph.getSearchGroups(data, "_escape='([^']+?)'")[0]
                    data = data.replace('%', '\\u00').decode('unicode-escape').encode("utf-8")
                    #printDBG("=======================================================================")
                    #printDBG(data)
                    #printDBG("=======================================================================")
                except:
                    printExc()
                    data = data2
                data2 = ''
                    
            if "goodcast.co" in data:
                id = self.cm.ph.getSearchGroups(data, "id='([0-9]+?)';")[0]
                if '' != id:
                    videoUrl = 'http://goodcast.co/stream.php?id='+id+'&width=640&height=480'
                    videoUrl = strwithmeta(videoUrl, {'Referer':url})
                    return self.up.getVideoLinkExt(videoUrl)
            elif "yukons.net" in data:
                channel = CParsingHelper.getDataBeetwenMarkers(data, 'channel="', '"', False)[1]
                videoUrl = strwithmeta('http://yukons.net/watch/'+channel, {'Referer':url})
                return self.up.getVideoLinkExt(videoUrl)
            elif "privatestream.tv" in data:
                videoUrl = self.cm.ph.getSearchGroups(data, '"(http://privatestream.tv/[^"]+?)"')[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.up.getVideoLinkExt(videoUrl)
            elif "ustream.tv" in data:
                videoUrl = self.cm.ph.getSearchGroups(data, 'src="([^"]+?ustream.tv[^"]+?)"')[0]
                if videoUrl.startswith('//'):
                    videoUrl = 'http:' + videoUrl
                    videoUrl = strwithmeta(videoUrl, {'Referer':url})
                    return self.up.getVideoLinkExt(videoUrl)
            elif 'rtmp://' in data:
                tmp = self.cm.ph.getSearchGroups(data, """(rtmp://[^'^"]+?)['"]""")[0]
                tmp = tmp.split('&amp;')
                r = tmp[0]
                if 1 < len(tmp)and tmp[1].startswith('c='):
                    playpath = tmp[1][2:]
                else:
                    playpath = self.cm.ph.getSearchGroups(data, """['"]*url['"]*[ ]*?:[ ]*?['"]([^'^"]+?)['"]""")[0]
                if '' != playpath:
                    r += ' playpath=%s' % playpath.strip()
                swfUrl = self.cm.ph.getSearchGroups(data, """['"](http[^'^"]+?swf)['"]""")[0]
                r += ' swfUrl=%s pageUrl=%s' % (swfUrl, url)
                return [{'name':'team-cast', 'url':r}]
            elif 'abcast.biz' in data:
                file = self.cm.ph.getSearchGroups(data, "file='([^']+?)'")[0]
                if '' != file:
                    videoUrl = 'http://abcast.biz/embed.php?file='+file+'&width=640&height=480'
                    videoUrl = strwithmeta(videoUrl, {'Referer':url})
                    return self.up.getVideoLinkExt(videoUrl)
            elif 'shidurlive.com' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """src=['"](http[^'^"]+?shidurlive.com[^'^"]+?)['"]""")[0]
                if '' != videoUrl:
                    videoUrl = strwithmeta(videoUrl, {'Referer':url})
                    return self.up.getVideoLinkExt(videoUrl)
            elif 'sawlive.tv' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """src=['"](http[^'^"]+?sawlive.tv[^'^"]+?)['"]""")[0]
                if '' != videoUrl:
                    videoUrl = strwithmeta(videoUrl, {'Referer':url})
                    return self.up.getVideoLinkExt(videoUrl)
            elif "castalba.tv" in data:
                id = self.cm.ph.getSearchGroups(data, """id=['"]([0-9]+?)['"];""")[0]
                if '' != id:
                    videoUrl = 'http://castalba.tv/embed.php?cid='+id+'&wh=640&ht=400&r=team-cast.pl.cp-21.webhostbox.net'
                    videoUrl = strwithmeta(videoUrl, {'Referer':url})
                    return self.up.getVideoLinkExt(videoUrl)
            elif "fxstream.biz" in data:
                file = self.cm.ph.getSearchGroups(data, """file=['"]([^'^"]+?)['"];""")[0]
                if '' != file:
                    videoUrl = 'http://fxstream.biz/embed.php?file='+file+'&width=640&height=400'
                    videoUrl = strwithmeta(videoUrl, {'Referer':url})
                    return self.up.getVideoLinkExt(videoUrl)
            else:
                file = self.cm.ph.getSearchGroups(data, """['"]([^'^"]+?\.m3u8)['"]""")[0]
                if '' != file:
                    return getDirectM3U8Playlist(file, checkExt=False)
                printDBG("=======================================================================")
                printDBG(data)
                printDBG("=======================================================================")
        return []
        
    def getWebCamera(self, cItem):
        printDBG("getWebCamera start")
        sts, data = self.cm.getPage(cItem['url'])
        if sts:
            if cItem['title'] == 'WebCamera PL':
                params = dict(cItem)
                params.update({'title':'Polecane kamery'})
                self.addDir(params)
                data = CParsingHelper.getDataBeetwenMarkers(data, '<h4>Kamery wg kategorii</h4>', '</div>', False)[1]
                data = data.split('</a>')
                del data[-1]
                for item in data:
                    url = self.cm.ph.getSearchGroups(item, """href=['"](http[^'^"]+?)['"]""")[0]
                    if '' != url:
                        params = dict(cItem)
                        params.update({'title':self._cleanHtmlStr(item), 'url':url})
                        self.addDir(params)
            else:
                data = CParsingHelper.getDataBeetwenMarkers(data, '<div class="inlinecam', '<div id="footerbar">', False)[1]
                data = data.split('<div class="inlinecam')
                for item in data:
                    item = CParsingHelper.getDataBeetwenMarkers(item, '<a', '</div>', True)[1]
                    url = self.cm.ph.getSearchGroups(item, """href=['"](http[^'^"]+?)['"]""")[0]
                    if '' != url:
                        title = self._cleanHtmlStr(CParsingHelper.getDataBeetwenMarkers(item, '<div class="bar">', '</div>', False)[1])
                        icon  = self.cm.ph.getSearchGroups(item, """data-src=['"](http[^'^"]+?)['"]""")[0]
                        params = dict(cItem)
                        params.update({'title':title, 'url':url, 'icon':icon})
                        self.playVideo(params)
                       
    def getWebCameraLink(self, videoUrl):
        printDBG("getWebCameraLink start")
        return self.up.getVideoLinkExt(videoUrl)
    
    def getVideostarList(self):
        printDBG("getVideostarList start")
        if None == self.videoStarApi:
            self.videoStarApi = VideoStarApi()
            
        tmpList = self.videoStarApi.getChannelsList(True)
        for item in tmpList:
            try:
                params = { 'name'       : 'videostar_channels', 
                           'title'      : item['name'].encode('utf-8'), 
                           'desc'       : 'Access status: ' + item['access_status'].encode('utf-8'), 
                           'url'        : item['id'],
                           'icon'       : item['thumbnail'],
                           }
                self.playVideo(params)
            except:
                printExc()
        
    def getVideostarLink(self, channelID):
        urlsTab = self.videoStarApi.getVideoLink(channelID)
        if 0 < len(urlsTab):
            if 'hls' == urlsTab[0]['type']:
                tmpList = getDirectM3U8Playlist(urlsTab[0]['url'], checkExt=False)
            else:
                tmpList = urlsTab
                
            for item in tmpList:
                if self.videoStarApi.getDefaultQuality() == item['bitrate']:
                    return [dict(item)]
            return [dict(tmpList[0])]
        return urlsTab
        
        
    def prognozaPogodyList(self, url):
        printDBG("prognozaPogodyList start")
        if config.plugins.iptvplayer.weather_useproxy.value: params = {'http_proxy':config.plugins.iptvplayer.proxyurl.value}
        else: params = {}
        sts,data = self.cm.getPage(url, params)
        if not sts: return
        data = CParsingHelper.getDataBeetwenMarkers(data, '<div id="items">', '</div>', False)[1]    
        data = data.split('</a>')
        if len(data): del data[-1]
        for item in data:
            params = {'name':"prognoza.pogody.tv"}
            params['url'] = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
            params['icon'] = self.cm.ph.getSearchGroups(item, 'src="([^"]+?)"')[0]
            params['title'] = self.cleanHtmlStr(item)
            if len(params['icon']) and not params['icon'].startswith('http'): params['icon'] = 'http://prognoza.pogody.tv/'+params['icon']
            if len(params['url']) and not params['url'].startswith('http'): params['url'] = 'http://prognoza.pogody.tv/'+params['url']
            self.playVideo(params)
            
    def prognozaPogodyLink(self, url):
        printDBG("prognozaPogodyLink url[%r]" % url)
        if config.plugins.iptvplayer.weather_useproxy.value: params = {'http_proxy':config.plugins.iptvplayer.proxyurl.value}
        else: params = {}
        sts,data = self.cm.getPage(url, params)
        if not sts: return []
        url = self.cm.ph.getSearchGroups(data, 'src="([^"]+?\.mp4[^"]*?)"')[0]
        
        urlMeta = {}
        if config.plugins.iptvplayer.weatherbymatzgprohibitbuffering.value:
            urlMeta['iptv_buffering'] = 'forbidden'
        if config.plugins.iptvplayer.weather_useproxy.value:
            urlMeta['http_proxy'] = config.plugins.iptvplayer.proxyurl.value
            
        url = self.up.decorateUrl(url, urlMeta)
        return [{'name':'prognoza.pogody.tv', 'url':url}]

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        if 0 == refresh:
            if len(self.currList) <= index:
                printDBG( "handleService wrong index: %s, len(self.currList): %d" % (index, len(self.currList)) )
                return
            if -1 == index:
                # use default value
                self.currItem = { "name": None }
                printDBG( "handleService for first self.category" )
            else:
                self.currItem = self.currList[index]

        name     = self.currItem.get("name", '')
        title    = self.currItem.get("title", '')
        icon     = self.currItem.get("icon", '')
        url      = self.currItem.get("url", '')
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s]" % (name) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsMainMenu(self.MAIN_GROUPED_TAB)
    #HasBahCa list
        elif name == "HasBahCa":
            self.listHasBahCa(self.currItem)
    #m3u items
        elif name == "m3u":
            self.m3uList(url)
    #prognoza.pogody.tv items
        elif name == "prognoza.pogody.tv":
            self.prognozaPogodyList(url)
    #goldvod.tv items
        elif name == "goldvod.tv":
            self.getGoldvodList(url)
    #videostar.pl items
        elif name == "videostar.pl":
            self.getVideostarList()
    #sat-live.tv items
        elif name == "web-live.tv":
            self.getSatLiveList(url)
    #vidtv.pl items
        elif name == "vidtv.pl":
            self.getVidTvList(url)
    #looknij.tv items
        elif name == "looknij.tv":
            self.getLooknijTvList(url)
    #tvisport.cba.pl items
        elif name == "tvisport.cba.pl":
            self.getTvSportCdaList(url)
    #nettv.pw items
        elif name == "nettv.pw":
            self.getNettvpwList(url)
    #weeb.tv items
        elif name == 'weeb.tv':
            self.getWeebTvList(url)
    #team-cast.pl items
        elif name == "team-cast.pl":
            self.getTeamCastList(self.currItem)
    #webcamera.pl items
        elif name == "webcamera.pl":
            self.getWebCamera(self.currItem)
    # filmon.com groups
        elif name == "filmon_groups":
            self.getFilmOnGroups()
    # filmon.com channels
        elif name == "filmon_channels":
            self.getFilmOnChannels()

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, HasBahCa(), withSearchHistrory = False)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('webstreamslogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] != 'video':
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])

        retlist = []
        url = self.host.currList[Index].get("url", '')
        name = self.host.currList[Index].get("name", '')
        
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> [%s] [%s]" % (name, url))
        urlList = None
        
        if -1 != url.find('teledunet'):
            new_url = TeledunetParser().get_rtmp_params(url)
            if 0 < len(url): retlist.append(CUrlItem("Własny link", new_url))
        elif url.startswith('http://goldvod.tv/'):
            url = self.host.getGoldvodLink(url)
        elif 'web-live.tv' in url:
            url = self.host.getSatLiveLink(url)
        elif 'vidtv.pl' in url:
            url = self.host.getVidTvLink(url)
        elif 'looknij.tv' in url:
            url = self.host.getLooknijTvLink(url)
        elif 'tvisport.cba.pl' in url:
            urlList = self.host.getTvSportCdaLink(url)
        elif 'nettv.pw' in url:
            urlList = self.host.getNettvpwLink(url)
        elif 'weeb.tv' in name:
            url = self.host.getWeebTvLink(url)
        elif name == "team-cast.pl":
            urlList = self.host.getTeamCastLink(url)
        elif "filmon_channel" == name:
            urlList = self.host.getFilmOnLink(channelID=url)
        elif "videostar_channels" == name:
            urlList = self.host.getVideostarLink(channelID=url)
            #if 1 < len(tmpList):
            #    for item in tmpList:
            #        retlist.append(CUrlItem(item['name'], item['url']))
            #elif 1 == len(tmpList):
            #    url =  tmpList[0]['url']
        elif name == "webcamera.pl":
            urlList = self.host.getWebCameraLink(url)
        elif name == "prognoza.pogody.tv":
            urlList = self.host.prognozaPogodyLink(url)
            
        if isinstance(urlList, list):
            for item in urlList:
                retlist.append(CUrlItem(item['name'], item['url']))
        elif isinstance(url, basestring):
            if url.endswith('.m3u'):
                tmpList = self.host.getDirectVideoHasBahCa(name, url)
                for item in tmpList:
                    retlist.append(CUrlItem(item['name'], item['url']))
            else:
                iptv_proto = urlparser.decorateUrl(url).meta.get('iptv_proto', '')
                if 'm3u8' == iptv_proto:
                    tmpList = getDirectM3U8Playlist(url, checkExt=False)
                    for item in tmpList:
                        retlist.append(CUrlItem(item['name'], item['url']))
                elif 'f4m' == iptv_proto:
                    tmpList = getF4MLinksWithMeta(url, checkExt=False)
                    for item in tmpList:
                        retlist.append(CUrlItem(item['name'], item['url']))
                else:
                    if '://' in url:
                        retlist.append(CUrlItem("Link", url))
            
        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo

    def convertList(self, cList):
        hostList = []

        for cItem in cList:
            hostLinks = []
            type = CDisplayListItem.TYPE_UNKNOWN

            if cItem['type'] == 'category':
                type = CDisplayListItem.TYPE_CATEGORY
            elif cItem['type'] == 'video':
                type = CDisplayListItem.TYPE_VIDEO
                url = cItem.get('url', '')
                if url.endswith(".jpeg") or url.endswith(".jpg") or url.endswith(".png"):
                    type = CDisplayListItem.TYPE_PICTURE
                else:
                    type = CDisplayListItem.TYPE_VIDEO
                if '' != url:
                    hostLinks.append(CUrlItem("Link", url, 1))
                
            title       =  self.host._cleanHtmlStr( cItem.get('title', '') )
            description =  self.host._cleanHtmlStr( cItem.get('desc', '') )
            icon        =  self.host._cleanHtmlStr( cItem.get('icon', '') )
            
            hostItem = CDisplayListItem(name = title,
                                        description = description,
                                        type = type,
                                        urlItems = hostLinks,
                                        urlSeparateRequest = 1,
                                        iconimage = icon,
                                        possibleTypesOfSearch = [])
            hostList.append(hostItem)

        return hostList
    # end convertList