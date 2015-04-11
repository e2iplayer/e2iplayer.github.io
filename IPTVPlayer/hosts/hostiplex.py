# -*- coding: utf-8 -*-
# Based on information provided by @jatrn: http://sd-xbmc.org/pl/content/iplexpl-zrodlo-apki-z-samsunga-smart-tv

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher import blowfish
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
from datetime import timedelta
import re
import urllib
import time
import binascii
import base64
import codecs
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

###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.iplex_proxy = ConfigYesNo(default = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("Iplex korzystaj z proxy?", config.plugins.iptvplayer.iplex_proxy))
    return optionList
###################################################

def gettytul():
    return 'Iplex'

class Iplex(CBaseHostClass):
    USER_AGENT = 'Mozilla/5.0 (SmartHub; SMART-TV; U; Linux/SmartTV; Maple2012) AppleWebKit/534.7 (KHTML, like Gecko) SmartTV Safari/534.7'
    
    def __init__(self):
        printDBG("Iplex.__init__")
        CBaseHostClass.__init__(self, {'proxyURL': config.plugins.iptvplayer.proxyurl.value, 'useProxy': config.plugins.iptvplayer.iplex_proxy.value})        
        self.cm.HEADER = {'User-Agent': Iplex.USER_AGENT, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        
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
        
        
    def _decodeUrl(self, url, key='-S75dbb-QB?<nE_['):
        '''
        Author: http://sd-xbmc.org/, @jatrn
        '''
        ret = ''
        #-------- decoding -----------
        match = re.search('(http:\/\/.*)\/(\d{1,5}|pre_adv|post_adv)\/(.*)\.mp4', url)

        #check if valid url
        if match:
            url_path = match.group(1) + '/' + match.group(2) + '/'
            s1 = codecs.encode(match.group(3), 'rot_13') 
            s2 = base64.b64decode(s1)
            s3 = ''
            cipher = blowfish.Blowfish(key)
            for index in range(0, len(s2)/16):
                chunk = s2[index*16:index*16+16]
                s3 += cipher.decrypt(chunk.decode("hex"))
            s4 = s3.replace("$","")
            ret = url_path + s4 + '.mp4'
        return ret
        
    def listsCategories(self, url):
        printDBG("Iplex.listsCategories url[%s]" % url)
        
        sts, data = self.cm.getPage(url)
        if not sts:
            printExc()
            return
        
        try:
            data = json.loads(data)
            if 'series' in data:
                sts, data = self.cm.getPage(data['series'])
                if not sts:
                    printExc()
                    return
                data = json.loads(data)
            for item in data['feeds']:
                if item.get('license', '') in ['FREE', '']: #'PAID'
                    type  = self._getJItemStr(item, 'type')
                    if 'account' == type: continue
                    url   = self._getJItemStr(item, 'url')
                    title = self._getJItemStr(item, 'caption')
                    if '' == title: title = self._getJItemStr(item, 'title')
                    icon  = self._getJItemStr(item, 'img')   
                    desc  = '' 
                    duration = self._getJItemNum(item, 'duration', -1)
                    rating   = self._getJItemStr(item, 'rating', 'brak oceny')
                    if 0 < duration:             desc += str(timedelta(minutes=duration)) + '|'
                    if 'brak oceny' != rating:   desc += rating + '|'
                    
                    params = { 'url'      : url,
                               'title'    : title,
                               'desc'     : desc,
                               'icon'     : icon,
                               'category' : type,
                             }
                    if 'movie_card' == type:
                        self.addVideo(params)
                    else:
                        self.addDir(params)
        except: 
            printExc()
    
    def resolveLink(self, url):
        printDBG("Iplex.resolveLink url[%s]" % url)
        sts, data = self.cm.getPage(url)
        if not sts:
            return
        try:
            data = json.loads(data)
            url = self._decodeUrl(self._getJItemStr(data['movie'], 'url'))
            if type(url) == type(u''):
                url = url.encode('utf-8')
            return url
        except:
            printExc()
        return ''

    def getLinks(self, url):
        printDBG("Iplex.getLinks url[%r]" % url )
        videoUrls = []
        sts, data = self.cm.getPage(url)
        if sts:
            try:
                data = json.loads(data)
                printDBG(data)
                VER_TABLE = [{'type':'lector', 'name':'Lektor'}, {'type':'subtitles', 'name':'Napisy'}]
                for item in VER_TABLE:
                    if item['type'] in data:
                        videoUrls.append({'name': item['name'], 'url':self._getJItemStr(data, item['type'])})
            except:
                printExc()
        return videoUrls
        
    def getDescription(self, url):
        printDBG("Iplex.getDescription url[%r]" % url )
        content = {}
        sts, data = self.cm.getPage(url)
        if sts:
            try:
                data = json.loads(data)
                printDBG(data)
                content = { 'title': self._getJItemStr(data, 'title'),
                            'desc' : self._getJItemStr(data, 'description'),
                            'icon' : self._getJItemStr(data, 'img'),
                          }
                if 10 < len(content['desc']):
                    return content
            except:
                printExc()
        return content
        

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('Iplex..handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        
        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        url      = self.currItem.get("url", 'http://samsung.iplex.pl/tv/main.menu?api=v4')
        printDBG( "Iplex.handleService: ---------> name[%s], category[%s] " % (name, category) )
        self.currList = []
        
        self.listsCategories(url)


class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Iplex(), False)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('iplexlogo.png')])
        
    def getArticleContent(self, Index = 0):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getArticleContent - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
            
        content = self.host.getDescription(self.host.currList[Index]['url'])
        title  = content.get('title', '')
        text   = content.get('desc' '')
        images = [ {'title':'', 'author': '', 'url': content.get('icon', '')} ]
        
        return RetHost(RetHost.OK, value = [ArticleContent(title = title, text = text, images =  images)])

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] != 'video':
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])

        retlist = []
        urlList = self.host.getLinks(self.host.currList[Index]['url'])
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

    def convertList(self, cList):
        hostList = []
        searchTypesOptions = []
        
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
            description =  clean_html(cItem.get('desc', ''))
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
