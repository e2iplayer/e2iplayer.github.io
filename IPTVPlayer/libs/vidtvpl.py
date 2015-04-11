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


class VidTvApi:
    MAINURL      = 'http://vidtv.pl/'
    HTTP_HEADER  = { 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:12.0) Gecko/20100101 Firefox/12.0', 'Referer': MAINURL }

    def __init__(self):
        self.cm = common()
        self.channlesTree = []

    def getCategoriesList(self):
        printDBG("VidTvApi.getCategoriesList")
        catsList = []
        sts,data = self.cm.getPage(VidTvApi.MAINURL + 'index.php')
        if sts:
            data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="accordion clr">', '<script>', False)[1]
            data = data.split('<div class="accordion clr">')
            cat_id = 0
            for item in data:
                title = self.cm.ph.getDataBeetwenMarkers(item, '<div class="title">', '</div>', False)[1]
                channelList = []
                tmp = re.findall('href="([^"]+?)">([^<]+?)<', item)
                for channel in tmp:
                    channelList.append({'title':channel[1], 'url':VidTvApi.MAINURL + channel[0]})
                self.channlesTree.append({'title':title, 'channel_list':channelList})
                catsList.append({'title':title, 'url':str(cat_id)})
                cat_id += 1
        return catsList

    def getChannelsList(self, url):
        printDBG("VidTvApi.getChannelsList url[%s]" % url)
        cat_id = int(url)
        if cat_id < len(self.channlesTree):
            return self.channlesTree[cat_id]['channel_list']
        else: return []
    
    def getVideoLink(self, url):
        printDBG("VidTvApi.getVideoLink")
        sts,data = self.cm.getPage(url)
        if sts:
            r = self.cm.ph.getSearchGroups(data, '(rtmp://[^"]+?)"')[0]
            if r.startswith('rtmp'):
                return r + ' live=1' #swfUrl=%s
        return ''
