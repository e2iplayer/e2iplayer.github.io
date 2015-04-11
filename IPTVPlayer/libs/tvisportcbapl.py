# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
###################################################

###################################################
# FOREIGN import
###################################################
import re
############################################


class TvSportCdaApi:
    MAINURL      = 'http://tvisport.cba.pl/'
    HTTP_HEADER  = { 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:12.0) Gecko/20100101 Firefox/12.0', 'Referer': MAINURL }

    def __init__(self):
        self.cm = common()
        self.up = urlparser()

    def getCategoriesList(self):
        printDBG("TvSportCdaApi.getCategoriesList")
        sts,data = self.cm.getPage(TvSportCdaApi.MAINURL)
        if not sts: return []
        data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="nav">', '<div class="clear">', False)[1]
        catsList = []
        data = data.split('menu-item-ancestor">')
        if len(data): del data[0]
        for item in data:
            tmp = self.cm.ph.getSearchGroups(item, '<a[^>]*?>(.+?)</a>')[0]
            catsList.append( {'title':clean_html(tmp), 'url':tmp} )
        return catsList

    def getChannelsList(self, subMenuMarker):
        printDBG("TvSportCdaApi.getChannelsList subMenuMarker[%s]" % subMenuMarker )
        channelsList = []
        sts,data = self.cm.getPage(TvSportCdaApi.MAINURL)
        if not sts: return []
        
        data = self.cm.ph.getDataBeetwenMarkers(data, subMenuMarker, '</ul>', True)[1]
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="sub-menu">', '</ul>', True)[1]
        data = re.compile('<a href="(http[^"]+?)">([^<]+?)</a>').findall(data)
        for item in data:
            channelsList.append({'title':item[1], 'url':item[0], 'icon':''})
        return channelsList
    
    def getVideoLink(self, baseUrl):
        printDBG("TvSportCdaApi.getVideoLink url[%s]" % baseUrl)
        def _url_path_join(a, b):
            from urlparse import urljoin
            return urljoin(a, b)
        url  = baseUrl
        urls = []
        tries = 0
        while tries < 3:
            sts,data = self.cm.getPage(url)
            if not sts or 'wymagana jest wtyczka Silverlight' in data or 'x-silverlight-' in data: break
            if 0 == tries: data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="content-main"', '<div class="entry-footer', False)[1]
            urls = self.up.getAutoDetectedStreamLink(url, data)
            if len(urls): break
            url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"](http[^'^"]+?)['"]''')[0]
            tries += 1
        return urls
