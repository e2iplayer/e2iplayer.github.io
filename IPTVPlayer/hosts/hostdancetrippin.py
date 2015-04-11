# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CDisplayListItem, RetHost, CUrlItem
import Plugins.Extensions.IPTVPlayer.libs.pCommon as pCommon
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, GetLogoDir
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
###################################################
# FOREIGN import
###################################################
import re, urllib, urllib2, base64, math 
try:
    import simplejson
except:
    import json as simplejson   
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################

###################################################
# Config options for HOST
###################################################
def GetConfigList():
    optionList = []
    return optionList
###################################################

###################################################
# Title of HOST
###################################################
def gettytul():
    return 'Dancetrippin'

class IPTVHost(IHost):
    LOGO_NAME = 'dancetrippinlogo.png'

    def __init__(self):
        printDBG( "init begin" )
        self.host = Host()
        self.prevIndex = []
        self.currList = []
        self.prevList = []
        printDBG( "init end" )
        
    def isProtectedByPinCode(self):
        return False
    
    def getLogoPath(self):  
        return RetHost(RetHost.OK, value = [GetLogoDir(self.LOGO_NAME)])

    def getInitList(self):
        printDBG( "getInitList begin" )
        self.prevIndex = []
        self.currList = self.host.getInitList()
        self.host.setCurrList(self.currList)
        self.prevList = []
        printDBG( "getInitList end" )
        return RetHost(RetHost.OK, value = self.currList)

    def getListForItem(self, Index = 0, refresh = 0, selItem = None):
        printDBG( "getListForItem begin" )
        self.prevIndex.append(Index)
        self.prevList.append(self.currList)
        self.currList = self.host.getListForItem(Index, refresh, selItem)
        #self.currList = [ self.prevList[-1][Index] ]
        printDBG( "getListForItem end" )
        return RetHost(RetHost.OK, value = self.currList)

    def getPrevList(self, refresh = 0):
        printDBG( "getPrevList begin" )
        if(len(self.prevList) > 0):
            self.prevIndex.pop()
            self.currList = self.prevList.pop()
            self.host.setCurrList(self.currList)
            printDBG( "getPrevList end OK" )
            return RetHost(RetHost.OK, value = self.currList)
        else:
            printDBG( "getPrevList end ERROR" )
            return RetHost(RetHost.ERROR, value = [])

    def getCurrentList(self, refresh = 0):
        printDBG( "getCurrentList begin" )
        #if refresh == 1
        #self.prevIndex[-1] #ostatni element prevIndex
        #self.prevList[-1]  #ostatni element prevList
        #tu pobranie listy dla dla elementu self.prevIndex[-1] z listy self.prevList[-1]  
        printDBG( "getCurrentList end" )
        return RetHost(RetHost.OK, value = self.currList)

    def getLinksForVideo(self, Index = 0, item = None):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
        
    def getResolvedURL(self, url):
        printDBG( "getResolvedURL begin" )
        if url != None and url != '':        
            ret = self.host.getResolvedURL(url)
            if ret != None and ret != '':        
               printDBG( "getResolvedURL ret: "+ret)
               list = []
               list.append(ret)
               printDBG( "getResolvedURL end OK" )
               return RetHost(RetHost.OK, value = list)
            else:
               printDBG( "getResolvedURL end" )
               return RetHost(RetHost.NOT_IMPLEMENTED, value = [])                
        else:
            printDBG( "getResolvedURL end" )
            return RetHost(RetHost.NOT_IMPLEMENTED, value = [])

    def getSearchResults(self, pattern, searchType = None):
        return RetHost(RetHost.NOT_IMPLEMENTED, value = [])

    ###################################################
    # Additional functions on class IPTVHost
    ###################################################

class Host:
    currList = []
    MAIN_URL = ''
    
    def __init__(self):
        printDBG( 'Host __init__ begin' )
        self.cm = pCommon.common()
        self.currList = []
        printDBG( 'Host __init__ end' )
        
    def getStr(self, v, default=''):
        if None == v:
            return default
        elif isinstance(v, int):
            return str(v)
        return str(v.encode('utf-8'))
        
    def setCurrList(self, list):
        printDBG( 'Host setCurrList begin' )
        self.currList = list
        printDBG( 'Host setCurrList end' )
        return 

    def getInitList(self):
        printDBG( 'Host getInitList begin' )
        #self.currList = self.MAIN_MENU
        self.currList = self.listsItems(-1, '', 'main-menu')
        printDBG( 'Host getInitList end' )
        return self.currList

    def getListForItem(self, Index = 0, refresh = 0, selItem = None):
        printDBG( 'Host getListForItem begin' )
        valTab = []
        if len(self.currList[Index].urlItems) == 0:
           return valTab
        valTab = self.listsItems(Index, self.currList[Index].urlItems[0], self.currList[Index].urlSeparateRequest)
        self.currList = valTab
        printDBG( 'Host getListForItem end' )
        return self.currList

    def listsItems(self, Index, url, name = ''):
        printDBG( 'Host listsItems begin' )
        printDBG( 'Host listsItems url: '+url )
        valTab = []
        if name == 'main-menu':
           printDBG( 'Host listsItems begin name='+name )
           valTab.append(CDisplayListItem('Episodes',     'http://player.dancetrippin.tv/#dj',    CDisplayListItem.TYPE_CATEGORY, ['http://player.dancetrippin.tv/video/list/dj/'],    'episodes', '', None)) 
           valTab.append(CDisplayListItem('Sol sessions', 'http://player.dancetrippin.tv/#sol',   CDisplayListItem.TYPE_CATEGORY, ['http://player.dancetrippin.tv/video/list/sol/'],   'episodes', '', None)) 
           valTab.append(CDisplayListItem('Other videos', 'http://player.dancetrippin.tv/#other', CDisplayListItem.TYPE_CATEGORY, ['http://player.dancetrippin.tv/video/list/other/'], 'episodes', '', None)) 
           valTab.append(CDisplayListItem('Ibiza Global Radio', 'http://player.dancetrippin.tv/#igr', CDisplayListItem.TYPE_CATEGORY, ['http://player.dancetrippin.tv/video/list/igr/'], 'episodes', '', None))
           return valTab

        # ########## #
        if 'episodes' == name:
           printDBG( 'Host listsItems begin name='+name )
           self.MAIN_URL = 'http://player.dancetrippin.tv' 
           try: data = self.cm.getURLRequestData({ 'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True })
           except:
              printDBG( 'Host listsItems query error' )
              printDBG( 'Host listsItems query error url:'+url )
              return valTab
           #printDBG( 'Host listsItems data: '+data )
           result = simplejson.loads(data)
           if result:
              for item in result:
                  '''
                  printDBG( 'Host listsItems number: '+str(item["number"]) )
                  printDBG( 'Host listsItems title: '+str(item["title"]) )
                  printDBG( 'Host listsItems venue: '+str(item["venue"]) )
                  printDBG( 'Host listsItems location: '+str(item["location"]) )
                  printDBG( 'Host listsItems party: '+str(item["party"]) )
                  printDBG( 'Host listsItems description: '+str(item["description"]) )
                  printDBG( 'Host listsItems dj: '+str(item["dj"]) )
                  '''
                  if self.getStr(item["image"]) <> "":
                     phImage = 'http://www.dancetrippin.tv/media/'+self.getStr(item["image"])
                  else:
                     phImage = "http://player.dancetrippin.tv/media/static/img/system/default_video.png"
                  #printDBG( 'Host listsItems phImage: '+phImage )
                  phUrl = self.MAIN_URL+'/video/'+self.getStr(item["slug"])+'/'
                  #printDBG( 'Host listsItems phUrl: '+phUrl )      
                  desc = '['+self.getStr(item["venue"])+']['+self.getStr(item["dj"])+']['+self.getStr(item["location"])+']['+self.getStr(item["party"])+']['+self.getStr(item["description"])
                  desc = clean_html(desc.decode("utf-8")).encode("utf-8")
                  valTab.append(CDisplayListItem(self.getStr(item["number"])+' '+self.getStr(item["title"]),desc,CDisplayListItem.TYPE_VIDEO, [CUrlItem('HIGH', phUrl+'?q=hd', 1),CUrlItem('MEDIUM', phUrl+'?q=sd', 1)], 0, phImage, None)) 
           printDBG( 'Host listsItems end' )
           return valTab

        return valTab

    def getResolvedURL(self, url):
        printDBG( 'Host getResolvedURL begin' )
        printDBG( 'Host getResolvedURL url: '+url )
        videoUrl = ''
        valTab = []
        try: data = self.cm.getURLRequestData({'url': url, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True})
        except:
           printDBG( 'Host getResolvedURL query error' )
           printDBG( 'Host getResolvedURL query error url: '+url )
           return ''
        #printDBG( 'Host getResolvedURL data: '+data )   
        parse = re.search('<div class=player>.*?href="(.*?)"', data, re.S)
        if parse: 
           if parse.group(1) == "#":
              parse = re.search('<div class=player>.*?src="(.*?)"', data, re.S)
              try: data = self.cm.getURLRequestData({'url': parse.group(1), 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True})
              except:
                 printDBG( 'Host getResolvedURL query error' )
                 printDBG( 'Host getResolvedURL query error url: '+url )
                 return ''
              #printDBG( 'Host getResolvedURL data2: '+data )  
              if url[-2:] == 'hd':
                 parse = re.search('"hd".*?"url":"(.*?)"', data, re.S)
              if url[-2:] == 'sd':
                 parse = re.search('"sd".*?"url":"(.*?)"', data, re.S)
              if parse:
                 return parse.group(1)
              else:
                 return ''
        if parse:
           videoUrl = parse.group(1)
           printDBG( 'Host getResolvedURL videoUrl: '+ videoUrl )
           return videoUrl
        printDBG( 'Host getResolvedURL end' )
        return videoUrl
