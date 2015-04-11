# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CDisplayListItem, RetHost, CUrlItem
import Plugins.Extensions.IPTVPlayer.libs.pCommon as pCommon
import Plugins.Extensions.IPTVPlayer.libs.drnuapi as drnuapi
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, GetLogoDir
from Plugins.Extensions.IPTVPlayer.libs.dk_channels import CHANNELS, CATEGORIES, QUALITIES

###################################################
# FOREIGN import
###################################################
import re, urllib2
try:
    import simplejson
except:
    import json as simplejson

from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry, ConfigInteger

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.drnuShowStreamSelector = ConfigYesNo(default = False)

def GetConfigList():
    optionList = []
    optionList.append( getConfigListEntry( "Show stream selector:", config.plugins.iptvplayer.drnuShowStreamSelector ) )
    return optionList
###################################################

###################################################
# Title of HOST
###################################################
def gettytul():
    return 'DR.nu player'
    
class CListItem:
    TYPE_CATEGORY = "CATEGORY"
    TYPE_VIDEO = "VIDEO"
    TYPE_VIDEO_RES = "VIDEO_RES"    
    TYPE_CHANNEL = "CHANNEL"

    def __init__(self,
                name = None,
                title = '',
                category = '',
                page = '',
                videoUrl = '',
                description = '',
                type = TYPE_CATEGORY):
                
        self.name = name
        self.title = title
        self.videoUrl = videoUrl
        self.category = category
        self.page = page
        self.description = description
        self.type = type

class DRnu:    
    NEWEST        = 0
    SERIES_AZ     = 1
    LIVETV        = 2

    def __init__(self):
        self.cm = pCommon.common()
        self.api = drnuapi.DrNuApi(config.plugins.iptvplayer.NaszaTMP.value,60)
        
        self.valTab = None
        self.currList = []

        self.showStreamSelector = config.plugins.iptvplayer.drnuShowStreamSelector.value       
        self.warning = self.imInDenmark()
        
    def imInDenmark(self):
        try:
            u = urllib2.urlopen('http://www.dr.dk/nu/api/estoyendinamarca.json', timeout=30)
            response = u.read()
            u.close()
            imInDenmark = 'true' == response
        except Exception:
            # If an error occurred assume we are not in Denmark
            imInDenmark = False

        if not imInDenmark:
            return 'Warning! It looks like you are not in Denmark. One or more videos may not be playable or other unexpected errors may occur.'     
        else:
            return ''
        
    def getCurrList(self):
        return self.currList

    def setCurrList(self, list):
        self.currList = list
        return 

    def getMenuTable(self):
        valTab = []
        
        if None == self.valTab:
            self.valTab = []
            self.valTab.append('Latest videos')
            self.valTab.append('Programs A-Z')
            self.valTab.append('Danish Live TV')        
        return self.valTab

    def getChannelsTab(self):
        strTab = []
        valTab = []
        
        for channel in CHANNELS:
            strTab = []
            strTab.append(channel.id)
            strTab.append(channel.title)
            
            if self.showStreamSelector:
                links = channel.get_all_urls()   
                hostLinks = list()
                for quality in links.keys():
                    linkTab = []
                    linkTab.append(quality)
                    linkTab.append(links[quality])
                    hostLinks.append(linkTab)
                    
                strTab.append(hostLinks)
            else:   
                link = channel.get_url() 
                strTab.append(link)
                        
            valTab.append(strTab)

        return valTab

    def getNewestTab(self):
        strTab = []
        valTab = []
        
        try:
            programs = self.api.getNewestVideos()
        except:
            return valTab
            
        for program in programs:
            strTab = []
            strTab.append(program['programSerieSlug'])
            strTab.append(program['title'].encode('UTF-8'))
            strTab.append(program['description'].encode('UTF-8'))
            valTab.append(strTab)
                
        return valTab

    def getSeriesAZTab(self):
        valTab = []
        
        try:
            programs = self.api.getProgramSeries()
        except:
            return valTab
            
        for program in programs:
            strTab = []
            letter = program['title'].encode('UTF-8')[0].upper()
            if letter not in valTab:
                valTab.append(letter)
                
        return valTab

    def getSeriesTab(self, letter):
        strTab = []
        valTab = []
        
        try:
            programs = self.api.getProgramSeries()
        except:
            return valTab
            
        for program in programs:
            if program['title'].encode('UTF-8').upper().startswith(letter):
                strTab = []
                strTab.append(program['slug'])
                strTab.append(program['title'].encode('UTF-8'))
                strTab.append(program['description'].encode('UTF-8'))
                valTab.append(strTab)
                
        return valTab

    def getVideoTab(self, slug):
        valTab = []
        strTab = []
        
        try:
            videos = self.api.getProgramSeriesVideos(slug)
        except:
            return valTab;
            
        for video in videos:
            strTab = []
            strTab.append(video['id'])
            strTab.append(video['title'].encode('UTF-8') 
                + ' (' + video['formattedBroadcastTimeForTVSchedule'].encode('UTF-8') 
                + ', ' + video['formattedBroadcastHourForTVSchedule'].encode('UTF-8') + ')')
            
            strTab.append(video['videoResourceUrl'])
            strTab.append(video['videoManifestUrl'])
                    
            strTab.append(video['description'].encode('UTF-8'))

            valTab.append(strTab)
                    
        return valTab

    def addList(self, table, category):
                
        if category == 'video':
            for i in range(len(table)):
                if self.showStreamSelector:
                    item = CListItem(   name = table[i][1],
                                        title = table[i][1],
                                        category = category,
                                        videoUrl = table[i][2],
                                        description = table[i][4],
                                        type = CListItem.TYPE_VIDEO_RES)
                else:
                    item = CListItem(   name = table[i][1],
                                        title = table[i][1],
                                        category = category,
                                        videoUrl = table[i][3],
                                        description = table[i][4],
                                        type = CListItem.TYPE_VIDEO)
                
                self.currList.append(item)
                
        elif category == 'series':
            for i in range(len(table)):
                item = CListItem(   name = table[i][0],
                                    title = table[i][1],
                                    category = category,
                                    description = table[i][2],
                                    type = CListItem.TYPE_CATEGORY)
                
                self.currList.append(item)

        elif category == 'series-az':
            for i in range(len(table)):
                item = CListItem(   name = table[i],
                                    title = table[i],
                                    category = category,
                                    type = CListItem.TYPE_CATEGORY)
                
                self.currList.append(item)

        elif category == 'newest':
            for i in range(len(table)):
                item = CListItem(   name = table[i][0],
                                    title = table[i][1],
                                    category = category,
                                    description = table[i][2],
                                    type = CListItem.TYPE_CATEGORY)
                
                self.currList.append(item)

        elif category == 'livetv':
            for i in range(len(table)):
                item = CListItem(   name = table[i][0],
                                    title = table[i][1],
                                    category = category,
                                    videoUrl = table[i][2],
                                    type = CListItem.TYPE_CHANNEL)

                self.currList.append(item)

        elif category == 'main-menu':
            for i in range(len(table)):
                item = CListItem(   name = table[i],
                                    title = table[i],
                                    category = category,
                                    description = self.warning,
                                    type = CListItem.TYPE_CATEGORY)
                
                self.currList.append(item)

    def handleService(self, index, refresh = 0):
    
        if 0 == refresh:
            if len(self.currList) <= index:
                print( "handleService wrong index: %s, len(self.currList): %d" % (index, len(self.currList)) )
                return
        
            if -1 == index:               
                self.name = None
                self.title = ''
                self.category = ''
                self.description = ''
                self.videoUrl = ''
                self.page = 0
                print( "dr.nu: handleService for first self.category" )
            else:
                item = self.currList[index]
                self.name = item.name
                self.title = item.title
                self.category = item.category
                self.videoUrl = item.videoUrl
                self.description = item.description
                self.page = item.page
                print( "dr.nu: |||||||||||||||||||||||||||||||||||| %s " % item.name )
        
        self.currList = []

        if self.name == None:
            self.addList(self.getMenuTable(),'main-menu')
        if self.category == 'main-menu':
            if self.SERIES_AZ == index:
                self.addList(self.getSeriesAZTab(),'series-az')
            elif self.NEWEST == index:
                self.addList(self.getNewestTab(),'newest')
            elif self.LIVETV == index:
                self.addList(self.getChannelsTab(),'livetv')
        if self.category == 'newest':
            self.addList(self.getVideoTab(self.name),'video')
        if self.category == 'series-az':
            self.addList(self.getSeriesTab(self.name),'series')
        if self.category == 'series':
            self.addList(self.getVideoTab(self.name),'video')
            
        return
        

class IPTVHost(IHost):

    def __init__(self):
        self.host = None
        self.currIndex = -1
        self.listOfprevList = [] 
    
    # return first available list of item category or video or link
    def getInitList(self):
        self.host = DRnu()
        self.currIndex = -1
        self.listOfprevList = [] 
        
        self.host.handleService(self.currIndex)
        
        convList = self.convertList(self.host.getCurrList())
        
        return RetHost(RetHost.OK, value = convList)
    
    # return List of item from current List
    # for given Index
    # 1 == refresh - force to read data from 
    #                server if possible 
    # server instead of cache 
    def getListForItem(self, Index = 0, refresh = 0, selItem = None):
        self.listOfprevList.append(self.host.getCurrList())
        
        self.currIndex = Index
        self.host.handleService(Index, refresh)
        convList = self.convertList(self.host.getCurrList())
        
        return RetHost(RetHost.OK, value = convList)
        
    # return prev requested List of item 
    # for given Index
    # 1 == refresh - force to read data from 
    #                server if possible
    def getPrevList(self, refresh = 0):
        if(len(self.listOfprevList) > 0):
            hostList = self.listOfprevList.pop()
            self.host.setCurrList(hostList)
            convList = self.convertList(hostList)
            return RetHost(RetHost.OK, value = convList)
        else:
            return RetHost(RetHost.ERROR, value = [])
        
    # return current List
    # for given Index
    # 1 == refresh - force to read data from 
    #                server if possible
    def getCurrentList(self, refresh = 0):      
        if refresh == 1:
            self.host.handleService(self.currIndex, refresh)
        convList = self.convertList(self.host.getCurrList())
        return RetHost(RetHost.OK, value = convList)

    def getLinksForVideo(self, Index = 0, item = None):
        hostLinks = []
        try:
            url = item.urlItems[0].url
            if url.startswith('http://www.dr.dk/handlers/GetResource.ashx'):
                resources = self.host.api._call_api(url)
                links = sorted(resources['links'], key=lambda link: link['bitrateKbps'], reverse=True)
                for link in links:
                    uri = link['uri'].encode('UTF-8')
                    fileType = link['fileType'].encode('UTF-8')
                    bitrate = str(link['bitrateKbps'])
                    linkType = link['linkType'].encode('UTF-8')
                    resolution = str(link['width']) + ' x ' + str(link['height'])
                    name = resolution + ", " + bitrate + " Kbps, " + fileType
                    hostLinks.append(CUrlItem(name, uri, 1))
            else:
                hostLinks.append(CUrlItem('', url, 1))
        except:
            return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
            
        return RetHost(RetHost.OK, hostLinks)
        
    # return resolved url
    # for given url
    def getResolvedURL(self, url):
        printDBG("drnu.getResolvedURL: %s" % url)
        if url != None and url != '' and url.find('://') >= 0 :
            if url.startswith('http://www.dr.dk/Forms/Published/PlaylistGen.aspx'):
                rtmpUrl = self.host.api._http_request(url)
            else:
                rtmpUrl = url

            if rtmpUrl.startswith('rtmp://vod.dr.dk/cms'):
                m = re.search('(rtmp://vod.dr.dk/cms)/([^\?]+)(\?.*)', rtmpUrl)
                rtmpUrl = m.group(1) + m.group(3)
                rtmpUrl += ' playpath=' + m.group(2) + m.group(3)
                rtmpUrl += ' app=cms' + m.group(3)                
                
            printDBG("drnu.getResolvedurl.append: %s" % rtmpUrl)
            list = []
            if rtmpUrl.find('://') >= 0 :
                list.append(rtmpUrl)

            return RetHost(RetHost.OK, value = list)
            
        else:
            return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
            
    # return full path to player logo
    def getLogoPath(self):  
        return RetHost(RetHost.OK, value = [GetLogoDir('drnulogo.png')])

    def convertList(self, cList):
        hostList = []
        
        for cItem in cList:
            hostLinks = []
                
            urlSeparateRequest = 0         
            type = CDisplayListItem.TYPE_UNKNOWN
            if cItem.type == CListItem.TYPE_CATEGORY:
                type = CDisplayListItem.TYPE_CATEGORY
            elif cItem.type == CListItem.TYPE_VIDEO:
                type = CDisplayListItem.TYPE_VIDEO
                hostLinks.append(CUrlItem('', cItem.videoUrl, 1))
            elif cItem.type == CListItem.TYPE_VIDEO_RES:
                type = CDisplayListItem.TYPE_VIDEO
                hostLinks.append(CUrlItem('', cItem.videoUrl, 1))
                urlSeparateRequest = 1
            elif cItem.type == CListItem.TYPE_CHANNEL:
                type = CDisplayListItem.TYPE_VIDEO
                links = cItem.videoUrl
                if isinstance(links, list):
                    for link in links:
                        name = link[0]
                        urls = link[1]
                        if isinstance(urls, list):
                            for url in urls:
                                hostLinks.append(CUrlItem(name, url, 0))
                        else:
                            hostLinks.append(CUrlItem(name, urls, 0))
                else:
                    hostLinks.append(CUrlItem('', links, 0))
                        
            hostItem = CDisplayListItem(name = cItem.title,
                                        description = cItem.description,
                                        type = type,
                                        urlItems = hostLinks,
                                        urlSeparateRequest = urlSeparateRequest,
                                        iconimage = '')
            hostList.append(hostItem)
            
        return hostList
