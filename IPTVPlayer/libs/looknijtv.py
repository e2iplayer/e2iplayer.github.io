# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, remove_html_markup
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
###################################################

###################################################
# FOREIGN import
###################################################
import re
############################################


class LooknijTvApi:
    MAINURL      = 'http://looknij.tv/'
    HTTP_HEADER  = { 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:12.0) Gecko/20100101 Firefox/12.0', 'Referer': MAINURL }

    def __init__(self):
        self.cm = common()
        self.channlesTree = []

    def getCategoriesList(self):
        printDBG("LooknijTvApi.getCategoriesList")
        #  FILM     
        catsList = [{'title':'ALL', 'url':'all'},
                    {'title':'DLA DZIECI', 'url':'dla-dzieci'},
                    {'title':'DLA KOBIET', 'url':'dla-kobiet'},
                    {'title':'FILM',       'url':'film'},
                    {'title':'INFORMACJE', 'url':'informacje'},
                    {'title':'ROZRYWKA',   'url':'rozrywka'},
                    {'title':'SERIALE',    'url':'seriale'},
                    {'title':'SPORT',      'url':'sport'}]

        return catsList

    def getChannelsList(self, url):
        printDBG("LooknijTvApi.getChannelsList url[%s]" % url )
        channelsList = []
        post_data = {'html_template':'Grid columns', 'now_open_works':'0', 'action':'get_portfolio_works','works_per_load':'40', 'category':url}
        sts,data = self.cm.getPage(LooknijTvApi.MAINURL + 'wp-admin/admin-ajax.php', {}, post_data)
        if sts:
            data = data.split('<div data-category=')
            if len(data): del data[0]
            for item in data:
                item = '<div data-category=' + item
                title = self.cm.ph.getDataBeetwenMarkers(item, '<h5>', '</h5>', False)[1]
                url   = self.cm.ph.getSearchGroups(item, 'href="([^"]+?)"')[0]
                icon  = self.cm.ph.getSearchGroups(item, 'src=(http[^"]+?)"')[0]
                channelsList.append({'title':title, 'url':url, 'icon':icon})
        return channelsList
    
    def getVideoLink(self, url):
        printDBG("LooknijTvApi.getVideoLink")
        sts,data = self.cm.getPage(url)
        if sts:
            tmp = self.cm.ph.getDataBeetwenMarkers(data, '<video>', '</video>', False)[1]
            r = self.cm.ph.getSearchGroups(tmp, '(rtmp://[^"]+?)"')[0]
            path = self.cm.ph.getSearchGroups(tmp, 'src="([^"]+?)"')[0]
            if r.startswith('rtmp'):
                return r + path + ' live=1' #swfUrl=%s
        return ''
