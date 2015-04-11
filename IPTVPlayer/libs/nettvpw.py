# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, byteify
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist, getF4MLinksWithMeta
###################################################

###################################################
# FOREIGN import
###################################################
import re
try: import json
except: import simplejson
############################################


class NettvPw:
    MAINURL      = 'http://www.nettv.pw/'
    HTTP_HEADER  = { 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:12.0) Gecko/20100101 Firefox/12.0', 'Referer': MAINURL }

    def __init__(self):
        self.cm = common()
        self.up = urlparser()

    def getChannelsList(self, url=''):
        printDBG("NettvPw.getChannelsList url[%s]" % url )
        channelsList = []
        sts,data = self.cm.getPage(NettvPw.MAINURL)
        if not sts: return channelsList
        data = self.cm.ph.getDataBeetwenMarkers(data, 'var programs = [', ']', False)[1]
        try:            
            data = byteify(json.loads("[%s]" % data))
            for item in data:            
                url   = item['link']
                icon  = item['image_color']
                title = item['title']
                if '' == url: continue
                if not url.startswith('http'): url = NettvPw.MAINURL + url
                if '' == icon: continue
                if not icon.startswith('http'): icon = NettvPw.MAINURL + icon
                channelsList.append({'title':title, 'url':url, 'icon':icon})
        except:
            printExc()
        return channelsList
    
    def getVideoLink(self, baseUrl):
        printDBG("NettvPw.getVideoLink url[%s]" % baseUrl)
        def _url_path_join(a, b):
            from urlparse import urljoin
            return urljoin(a, b)
        
        sts,data = self.cm.getPage(baseUrl)
        if not sts: return []
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="player">', '</div>', False)[1]
        url  = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="([^"]+?)"')[0]
        if not url.startswith('http'): url = _url_path_join(baseUrl, url)
        
        sts,data = self.cm.getPage(url)
        if not sts: return []
        data = self.cm.ph.getDataBeetwenMarkers(data, '<body>', '</body>', False)[1]
        
        return self.up.getAutoDetectedStreamLink(url, data)