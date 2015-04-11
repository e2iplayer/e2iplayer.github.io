# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.extractor.youtube import YoutubeIE
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html, unescapeHTML
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, remove_html_markup
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _

from datetime import timedelta
###################################################

###################################################
# FOREIGN import
###################################################
import re
from xml.etree import cElementTree
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.ytformat        = ConfigSelection(default = "mp4", choices = [("flv, mp4", "flv, mp4"),("flv", "flv"),("mp4", "mp4")]) 
config.plugins.iptvplayer.ytDefaultformat = ConfigSelection(default = "360", choices = [("0", _("the worst")), ("144", "144p"), ("240", "240p"), ("360", "360p"),("720", "720"),("1080", "1080"), ("9999", _("the best"))])
config.plugins.iptvplayer.ytUseDF         = ConfigYesNo(default = True)
config.plugins.iptvplayer.ytSortBy        = ConfigSelection(default = "", choices = [("", _("Relevance")),("video_date_uploaded", _("Upload date")),("video_view_count", _("View count")),("video_avg_rating", _("Rating"))]) 


class YouTubeParser():
    HOST = 'Mozilla/5.0 (Windows NT 6.1; rv:17.0) Gecko/20100101 Firefox/17.0'
    def __init__(self):
        self.cm = common()
        return

    def getDirectLinks(self, url, formats = 'flv, mp4'):
        printDBG('YouTubeParser.getDirectLinks')
        list = []
        try:
            list = YoutubeIE()._real_extract(url)
        except:
            printExc('YouTubeParser.getDirectLinks Exception')
            return []

        retList = []
        for item in list:
            #printDBG("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
            #printDBG( item )
            #printDBG("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
            if -1 < formats.find( item['ext'] ):
                if 'yes' == item['m3u8']:
                    format = re.search('([0-9]+?)p$', item['format'])
                    if format != None:
                        item['format'] = format.group(1) + "x"
                        item['ext']  = item['ext'] + "_M3U8"
                        retList.append(item)
                else:
                    format = re.search('([0-9]+?x[0-9]+?$)', item['format'])
                    if format != None:
                        item['format'] = format.group(1)
                        retList.append(item)
                    
        # onverts all keys
        for idx  in range(len(retList)):
            for key in retList[idx].keys():
                retList[idx][key] = retList[idx][key].encode('utf-8')
                
        return retList
        
    ########################################################
    # List Base PARSER
    ########################################################
    def parseListBase(self, data, type='video'):
        printDBG("parseListBase----------------")
        urlPatterns = { 'video'    :    ['video'   , 'href="[ ]*?(/watch\?v=[^"]+?)"'            , ''], 
                        'channel'  :    ['category', 'href="(/[^"]+?)"'                     , ''],
                        'playlist' :    ['category', 'list=([^"]+?)"'                       , '/playlist?list='],
                        'movie'    :    ['video'   , 'data-context-item-id="([^"]+?)"'      , '/watch?v='],
                        'live'     :    ['video'   , 'href="(/watch\?v=[^"]+?)"'            , ''],
                        'tray'     :    ['video'   , 'data-video-id="([^"]+?)"'             , '/watch?v='], }
        currList = []
        for i in range(len(data)):
            #printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            # get requaired params
            url   = urlPatterns[type][2] + self.getAttributes(urlPatterns[type][1], data[i])
            
            # get title
            title = '' #self.getAttributes('title="([^"]+?)"', data[i])
            if '' == title: title = self.getAttributes('data-context-item-title="([^"]+?)"', data[i])
            if '' == title: title = self.getAttributes('data-video-title="([^"]+?)"', data[i])
            if '' == title: sts,title = CParsingHelper.getDataBeetwenMarkers(data[i], '<h3 class="yt-lockup-title">', '</h3>', False) 
            if '' == title: sts,title = CParsingHelper.getDataBeetwenReMarkers(data[i], re.compile('<span [^>]*?class="title[^>]*?>'), re.compile('</span>'), False) 
            if '' == title: sts,title = CParsingHelper.getDataBeetwenReMarkers(data[i], re.compile('class="pl-video-title-link[^>]*?>'), re.compile('<'), False)
            
            if '' != title: title = CParsingHelper.removeDoubles(remove_html_markup(title, ' '), ' ')
                
            img   = self.getAttributes('data-thumb="([^"]+?\.jpg)"', data[i])
            if '' == img:  img = self.getAttributes('src="([^"]+?\.jpg)"', data[i])
            time  = self.getAttributes('data-context-item-time="([^"]+?)"', data[i])
            if '' == time: time  = self.getAttributes('class="video-time">([^<]+?)</span>', data[i])
            if '' == time: sts, time = CParsingHelper.getDataBeetwenReMarkers(data[i], re.compile('pl-video-time"[^>]*?>'), re.compile('<'), False)
            if '' == time: sts, time = CParsingHelper.getDataBeetwenReMarkers(data[i], re.compile('timestamp"[^>]*?>'), re.compile('<'), False)
            time = time.strip()
            # desc
            sts,desc  = CParsingHelper.getDataBeetwenReMarkers(data[i], re.compile('class="video-description[^>]+?>'), re.compile('</p>'), False)
            if '' == desc: sts,desc = CParsingHelper.getDataBeetwenReMarkers(data[i], re.compile('class="yt-lockup-description[^>]+?>'), re.compile('</div>'), False)
            desc = CParsingHelper.removeDoubles(remove_html_markup(desc, ' '), ' ')
            
            urlTmp = url.split(';')
            if len(urlTmp) > 0: url = urlTmp[0]
            if type == 'video': url = url.split('&')[0] 
                
            # printDBG('url   [%s] ' % url)
            # printDBG('title [%s] ' % title)
            # printDBG('img   [%s] ' % img)
            # printDBG('time  [%s] ' % time)
            # printDBG('desc  [%s] ' % desc)
            if title != '' and url != '' and img != '':
                correctUrlTab = [url, img]
                for i in range(len(correctUrlTab)):
                    if not correctUrlTab[i].startswith('http:') and not correctUrlTab[i].startswith('https:'):
                        if correctUrlTab[i].startswith("//"):
                            correctUrlTab[i] = 'http:' + correctUrlTab[i]
                        else:
                            correctUrlTab[i] = 'http://www.youtube.com' + correctUrlTab[i]
                    else:
                        if correctUrlTab[i].startswith('https:'):
                            correctUrlTab[i] = "http:" + correctUrlTab[i][6:]

                title = clean_html(title.decode("utf-8")).encode("utf-8")
                desc  = clean_html(desc.decode("utf-8")).encode("utf-8")
                params = {'type': urlPatterns[type][0], 'category': type, 'title': title, 'url': correctUrlTab[0], 'icon': correctUrlTab[1], 'time': time, 'desc': desc}
                currList.append(params)

        return currList
    #end parseListBase
    
    ########################################################
    # Tray List PARSER
    ########################################################
    def getVideosFromTraylist(self, url, category, page, cItem):
        printDBG('YouTubeParser.getVideosFromTraylist')
        return self.getVideosApiPlayList(url, category, page, cItem)

        currList = []
        try:
            sts,data =  self.cm.getPage(url, {'host': self.HOST})
            if sts:
                sts,data = CParsingHelper.getDataBeetwenMarkers(data, 'class="playlist-videos-container', '<div class="watch-sidebar-body">', False)
                data = data.split('class="yt-uix-scroller-scroll-unit')
                del data[0]
                return self.parseListBase(data, 'tray')
        except:
            printExc()
            return []
            
        return currList
    # end getVideosFromPlaylist
       
    ########################################################
    # PLAYLIST PARSER
    ########################################################
    def getVideosFromPlaylist(self, url, category, page, cItem):
        printDBG('YouTubeParser.getVideosFromPlaylist')
        currList = []
        try:
            sts,data =  self.cm.getPage(url, {'host': self.HOST})
            if sts:
                if '1' == page:
                    sts,data = CParsingHelper.getDataBeetwenMarkers(data, 'id="pl-video-list"', 'footer-container', False)
                else:
                    data = unescapeHTML(data.decode('unicode-escape')).encode('utf-8').replace('\/', '/')
                    
                # nextPage
                match = re.search('data-uix-load-more-href="([^"]+?)"', data)
                if not match: 
                    nextPage = ""
                else: 
                    nextPage = match.group(1).replace('&amp;', '&')
                
                itemsTab = data.split('<tr class="pl-video')
                currList = self.parseListBase(itemsTab)
                if '' != nextPage:
                    item = dict(cItem)
                    item.update({'title': 'Następna strona', 'page': str(int(page) + 1), 'url': 'http://www.youtube.com' + nextPage})
                    currList.append(item)
        except:
            printExc()
            
        return currList
    # end getVideosFromPlaylist

    ########################################################
    # CHANNEL LIST PARSER
    ########################################################
    def getAttributes(self, regx, data, num=1):
        match = re.search(regx, data)
        if not match: return ''
        else: return match.group(1)
        
    def getVideosFromChannelList(self, url, category, page, cItem):
        printDBG('YouTubeParser.getVideosFromChannelList page[%s]' % (page) )
        currList = []
        try:
            sts,data =  self.cm.getPage(url, {'host': self.HOST})
            if sts:
                if '1' == page:
                    sts,data = CParsingHelper.getDataBeetwenMarkers(data, 'feed-item-container', 'footer-container', False)
                else:
                    data = unescapeHTML(data.decode('unicode-escape')).encode('utf-8').replace('\/', '/')
                    
                # nextPage
                match = re.search('data-uix-load-more-href="([^"]+?)"', data)
                if not match: nextPage = ""
                else: nextPage = match.group(1).replace('&amp;', '&')
    
                data = data.split('feed-item-container')
                currList = self.parseListBase(data)
                
                if '' != nextPage:
                    item = dict(cItem)
                    item.update({'title': _("Next page"), 'page': str(int(page) + 1), 'url': 'http://www.youtube.com' + nextPage})
                    currList.append(item)
        except:
            printExc()
            return []
        return currList
    # end getVideosFromChannel

    ########################################################
    # SEARCH PARSER
    ########################################################
    #def getVideosFromSearch(self, pattern, page='1'):
    def getSearchResult(self, pattern, searchType, page, nextPageCategory, sortBy=''):
        printDBG('YouTubeParser.getSearchResult pattern[%s], searchType[%s], page[%s]' % (pattern, searchType, page))
        currList = []
        try:
            url = 'http://www.youtube.com/results?search_query=%s&filters=%s&search_sort=%s&page=%s' % (pattern, searchType, sortBy, page) 
            sts,data =  self.cm.getPage(url, {'host': self.HOST})
            if sts:
                if data.find('data-page="%d"' % (int(page) + 1)) > -1: nextPage = True
                else: nextPage = False
        
                sts,data = CParsingHelper.getDataBeetwenMarkers(data, '<li><div class="yt-lockup', '</ol>', False)
                
                data = data.split('<li><div class="yt-lockup')
                #del data[0]
                currList = self.parseListBase(data, searchType)
        
                if nextPage:
                    item = {'name': 'history', 'type': 'category', 'category': nextPageCategory, 'pattern':pattern, 'search_type':searchType, 'title': _("Next page"), 'page': str(int(page) + 1)}
                    currList.append(item)
        except:
            printExc()
            return []
        return currList
    # end getVideosFromSearch
    
    
    ########################################################
    # PLAYLIST API
    ########################################################
    def getVideosApiPlayList(self, url, category, page, cItem):
        printDBG('YouTubeParser.getVideosApiPlayList url[%s]' % url)
        xmlns       ='{http://www.w3.org/2005/Atom}' 
        xmlns_media ='{http://search.yahoo.com/mrss/}'
        xmlns_yt    ='{http://gdata.youtube.com/schemas/2007}'
        
        def getText(item):
            if item.text != None:
                return item.text.encode('utf-8')
            return ''
            
        def getTextAttrib(item, v):
                return item.get(v,'').encode('utf-8')
      
        currList = []
        if page == '1':
            playlistID = re.search('list=([^&]+?)&', url + '&')
            if playlistID: 
                baseUrl = "http://gdata.youtube.com/feeds/api/playlists/%s?v=2" % playlistID.group(1)
        else:
            baseUrl = url
            
        if baseUrl != '':
            sts,data =  self.cm.getPage(baseUrl, {'host': self.HOST})
            try:
                data = cElementTree.fromstring(data)
                '''
                for node in data.iter():
                    print node.tag, node.attrib
                '''
                
                # get next page
                nextPage = ''
                items = data.findall(xmlns + 'link')
                for item in items:
                    if getTextAttrib(item.attrib, 'rel') == 'next':
                        nextPage = getTextAttrib(item.attrib, 'href')
                        
                # get entries
                items = data.findall(xmlns + 'entry')
                for entry in items:
                    item = entry.find(xmlns_media+"group")
                    url = item.find(xmlns_yt + "videoid")
                    if cElementTree.iselement(url) and getText(url) != '':
                        url   = 'http://www.youtube.com/watch?v=' + getText(url)
                        title = getText(entry.find(xmlns+"title"))
                        
                        img = ''
                        images = item.findall(xmlns_media+"thumbnail")
                        for imgItem in images:
                            if getTextAttrib(imgItem.attrib, xmlns_yt+'name') == 'default':
                                img  = getTextAttrib(imgItem.attrib, 'url')
                                break
                        time  = getTextAttrib(item.find(xmlns_yt+"duration").attrib, 'seconds')
                        if '' != time: time = str( timedelta( seconds = int(time) ) )
                        if time.startswith("0:"): time = time[2:]
                        desc  = getText(item.find(xmlns_media+"description"))
                        params = {'type': 'video', 'category': 'video', 'title': title, 'url': url, 'icon': img, 'time': time, 'desc': desc}
                        currList.append(params)
                if nextPage != '':
                    match = re.search('start-index=([0-9]+?)[^0-9]', nextPage)
                    try:
                        if int(match.group(1)) < 100:
                            item = dict(cItem)
                            item.update({'title': _("Next page"), 'page': str(int(page) + 1), 'url': nextPage})
                            currList.append(params)
                    except:
                        pass
            except:
                printExc()
        return currList    
        
'''
                xmlDoc.findall(method + "/" + groupName + "/row")
        countItemNode = xmlDoc.find(method + "/count_items")
        showNextPage = False
'''

