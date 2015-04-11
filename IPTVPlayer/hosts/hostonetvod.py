# -*- coding: utf-8 -*-
# Based on (root)/trunk/xbmc-addons/src/plugin.video.polishtv.live/ @ 419 - Wersja 626

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CDisplayListItem, RetHost, CUrlItem
import Plugins.Extensions.IPTVPlayer.libs.crypto
import Plugins.Extensions.IPTVPlayer.libs.pCommon as pCommon
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSelOneLink, GetLogoDir
###################################################
# FOREIGN import
###################################################
import time, urllib, urllib2, re, math, random
try:   import json
except:import simplejson as json
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.onetvodDefaultformat = ConfigSelection(default = "450", choices = [("0", "bitrate: najgorszy"), ("200", "bitrate: 200p"), ("450", "bitrate: 450p"),("900", "bitrate: 900"),("1800", "bitrate: 1800"), ("9999", "bitrate: najlepszy")])
config.plugins.iptvplayer.onetvodUseDF = ConfigYesNo(default = False)
config.plugins.iptvplayer.proxyOnet = ConfigYesNo(default = False)

def GetConfigList():
    optionList = []
    optionList.append( getConfigListEntry( "Domyślny format video:", config.plugins.iptvplayer.onetvodDefaultformat ) )
    optionList.append( getConfigListEntry( "Używaj domyślnego format video:", config.plugins.iptvplayer.onetvodUseDF ) )
    optionList.append(getConfigListEntry( "Korzystaj z proxy?", config.plugins.iptvplayer.proxyOnet))
    return optionList
###################################################

def gettytul():
    return 'ONET VOD player'

class CListItem:
    TYPE_CATEGORY = "CATEGORY"
    TYPE_VIDEO = "VIDEO"
    def __init__(self,
                name = 'None',
                title = '',
                category = 'None',
                url = '',
                iconimage = ''):
        self.name = name
        self.title = title
        self.category = category
        self.url = url
        self.iconimage = iconimage
 
# CListItem

class vodonet:
  MODULE_URL = {'content' : 'http://content.external.cms.onetapi.pl/l',
                'video'   : 'http://video.external.cms.onetapi.pl/l'}
                
  HEADER = {'X-Onet-App': 'vod.android.mobile-apps.onetapi.pl', 'Content-Type': 'application/json-rpc', 'User-Agent': 'Dalvik/1.6.0 (Linux; U; Android 4.1.1; Core 10.1 3G Build/JRO03H)', 'Connection': 'Keep-Alive', 'Accept-Encoding': 'gzip'}

  SERVICE_MENU_TABLE = { 1: "Polecamy",
                2: "Filmy",
                3: "Seriale",
                4: "TV",
                5: "Dokumenty",
                6: "Bajki",}

  FORMAT = 'mp4'

  def __init__(self):
    porxyUrl = config.plugins.iptvplayer.proxyurl.value
    useProxy = config.plugins.iptvplayer.proxyOnet.value
    self.cm = pCommon.common(porxyUrl, useProxy)
    self.api = API()
    
    # SULGE
    self.currList = []
    
  def getCurrList(self):
    return self.currList
    
  def setCurrList(self, list):
    self.currList = list
    return 
    
  def setTable(self):
    return vodonet.SERVICE_MENU_TABLE
    
    
  def getMenuTable(self):
    nTab = []
    for num, val in vodonet.SERVICE_MENU_TABLE.items():
      nTab.append(val)
    return nTab

    
  def listsAddDirMenu(self, table, name, category):
    for i in range(len(table)):
      try:
        if table[i][3] != '':
          iconImage = self.api.getPoster(table[i][3])
        else: iconImage = ''
      except:
        iconImage = ''
      
      if name == 'None':
        self.add('main-menu', table[i], category, '', '', True, False)
   
      if name == 'main-menu':
        if category == self.setTable()[3] or category == self.setTable()[4]:
          self.add('sub-menu', table[i][0].encode('UTF-8'),  str(table[i][1]), iconImage, str(table[i][2]), True, False)
        else:
          self.add('sub-menu', table[i][0].title().encode('UTF-8'), category, iconImage, '', True, False)
      
      if name == 'series':
        if category == 'None': self.add('series', table[i][0], str(table[i][1]), iconImage, str(table[i][2]), True, False)  
      
      if name == 'playSeries':
        self.add('playSelectedMovie', table[i][0].title().encode('UTF-8') + ', odcinek ' + str(table[i][2]), table[i][1], iconImage, '', True, False)      
      if name == 'movie':
        self.add('playSelectedMovie', table[i][0].title().encode('UTF-8'), table[i][1], iconImage, '', True, False)      
    

  def add(self, name, title, category, iconimage, url, folder = True, isPlayable = True):
    if '' == category:
        category = 'None'
    item = CListItem(name = name,
                    title = title,
                    category = category,
                    url = url,
                    iconimage = iconimage)
                    
    self.currList.append(item)


  def listsSeasons(self, seriesId, seasons):
    strTab = []
    valTab = []
    for i in range(int(seasons)):
      strTab.append('Sezon ' + str(i+1))
      strTab.append(i+1)
      strTab.append(int(seriesId))
      strTab.append('')
      valTab.append(strTab)
      strTab = []
    return valTab

 
  def listsItems(self, node, childs, alt_childs = []):
    valTab = []
    for items in node:
      strTab = []
      if childs[0] in items:
        for i in childs:
          if i != '' and i in items: strTab.append(items[i])
          else:
            strTab.append('')
      elif 0 < len(alt_childs):
         for i in alt_childs:
           if i != '': strTab.append(items[i])
           else: strTab.append('')
      if 0 < len(strTab):
          if 'poster' in items: strTab.append(items['poster']['imageId'])
          else:
            try: strTab.append(items['leadMedia']['imageId'])
            except: strTab.append('')
          valTab.append(strTab)
    return valTab


  def getVideoUrl(self, tab, videoFormat, videoQuality):
    indexTab = []
    url =''
    for i in range(len(tab)):
        if tab[i][0] == videoFormat: indexTab.append(i)  
    if videoQuality == 'Niska': url = tab[indexTab[0]][1]
    if videoQuality == 'Wysoka': url = tab[indexTab[-1]][1]
    if videoQuality == 'Średnia':
        length = len(indexTab)
        i = int(math.ceil(float((indexTab[length/2] + indexTab[-(length+1)/2]))/2))
        url = tab[i][1]
    return url

  def handleService(self, index, refresh = 0):

    if 0 == refresh:
        if len(self.currList) <= index:
            printDBG( "vodonet handleService wrond index: %s, len(self.currList): %d" % (index, len(self.currList)) )
            return
    
        if -1 == index:         
            self.name = 'None'
            self.title = ''
            self.category = 'None'
            self.url = ''

            printDBG( "vodonet handleService for first category" )
        else:
            item = self.currList[index]
            self.name = item.name
            self.title = item.title
            self.category = item.category
            self.url = item.url
            
            printDBG( "vodonet |||||||||||||||||||||||||||||||||||| name: %s, category: %s" % (item.name,self.category) )
        self.currList = []
       
    #MAINMENU
    if self.name == 'None':
      self.listsAddDirMenu(self.getMenuTable(), 'None', 'None')
      
    #POLECAMY
    if self.name == 'main-menu' and self.title == self.setTable()[1]:
      data = self.api.getAPIData('content', self.api.makeListQuery({"context":"onet/vod", "method":"guideListsByType", "sort":"DEFAULT", "type":"mobile-sg-polecane", "guidelistView":"listitem"}))
      try: self.listsAddDirMenu(self.listsItems(data['result']['data'][0]['contentLeads'], ['title','ckmId','videoId']), 'movie', 'None')
      except: printExc()      

    #BAJKI
    if self.name == 'main-menu' and self.title == self.setTable()[6]:    
      data = self.api.getAPIData('video', self.api.makeListQuery({"context":"onet/bajki", "method":"search", "sort":"DATE_DESC", "noSeriesGroup":"True"}))
      try: self.listsAddDirMenu(self.listsItems(data['result']['data'], ['title','ckmId','videoId']), 'movie', 'None')
      except: printExc()   
    #SERIALE
    if self.name == 'main-menu' and self.title == self.setTable()[3]:  
      data = self.api.getAPIData('video', self.api.makeListQuery({"context":"onet/vod", "method":"search", "sort":"DATE_DESC", "channel":"seriale"}))
      try: self.listsAddDirMenu(self.listsItems(data['result']['data'], ['seriesTitle','season','seriesId']), self.name, self.setTable()[3]) # sometimes in returnet data seriesTitle is missing
      except: printExc()
    #SERIALE
    if self.name == 'main-menu' and self.title == self.setTable()[4]:  
      data = self.api.getAPIData('video', self.api.makeListQuery({"context":"onet/vod", "method":"search", "sort":"DATE_DESC", "channel":"tv"}))
      try: self.listsAddDirMenu(self.listsItems(data['result']['data'], ['seriesTitle','season','seriesId']), self.name, self.setTable()[4])
      except: printExc()   
      
    #KATEGORIE FILMOWE
    if self.name == 'main-menu' and self.title == self.setTable()[2]:
      data = self.api.getAPIData('video', self.api.makeListQuery({"context":"onet/vod", "method":"aggregates", "sort":"TITLE_ASC", "channel":"filmy", "names":"genres"}))
      try: self.listsAddDirMenu(self.listsItems(data['result']['data'][0]['items'], ['name','','']), self.name, self.setTable()[2])
      except: printExc()
    #DOKUMENTY (moze zwracac items jako film lub jako serial)
    if self.name == 'main-menu' and self.title == self.setTable()[5]:
      data = self.api.getAPIData('video', self.api.makeListQuery({"context":"onet/vod", "method":"search", "sort":"POPULARITY_DESC", "channel":"dokumenty"}))
      try: self.listsAddDirMenu(self.listsItems(data['result']['data'], ['seriesTitle','ckmId','seriesId'], ['title','ckmId','videoId']), 'movie', 'None')
      except: printExc()
      
    #sub-menu
    #filmy w kategoriach
    if self.name == 'sub-menu' and self.category == self.setTable()[2]:
      printDBG( "filmy w kategoriach" )
      data = self.api.getAPIData('video', self.api.makeListQuery({"context":"onet/vod", "method":"search", "sort":"POPULARITY_DESC", "channel":"filmy", "genre":self.title}))
      try: self.listsAddDirMenu(self.listsItems(data['result']['data'], ['title','ckmId','videoId']), 'movie', 'None')
      except: printExc()
      
    #sezony w serialu
    if self.name == 'sub-menu' and self.cm.isNumeric(self.category):
      printDBG( "sezony w serialu" )
      self.listsAddDirMenu(self.listsSeasons(self.url, self.category), 'series','None')

    #serial bez sezonu
    if self.name == 'sub-menu' and self.category == 'None':
      printDBG( "sezony w serialu" )
      data = self.api.getAPIData('video', self.api.makeListQuery({"context":"onet/vod", "method":"episodes", "sort":"DATE_DESC", "seriesId":int(self.url)}))
      try: self.listsAddDirMenu(self.listsItems(data['result']['data'], ['title','ckmId','episode']), 'playSeries', 'None')     
      except: printExc()
      
    #odcinki w sezonie
    if self.name == 'series':
      printDBG( "odcinki w sezonie" )
      data = self.api.getAPIData('video', self.api.makeListQuery({"context":"onet/vod", "method":"episodes", "sort":"DATE_DESC", "seriesId":int(self.url), "season":int(self.category)}))
      try: self.listsAddDirMenu(self.listsItems(data['result']['data'], ['title','ckmId','episode']), 'playSeries', 'None')
      except: printExc()
        
    printDBG("vodonet.handleService NO_ENTRY")

class API:
  def __init__(self):
    porxyUrl = config.plugins.iptvplayer.proxyurl.value
    useProxy = config.plugins.iptvplayer.proxyOnet.value
    self.cm = pCommon.common(porxyUrl, useProxy)

  def getVideoTab(self, ckmId):
    #MD5('gastlich') = d2dd64302895d26784c706717a1996b0
    #contentUrl = 'http://vod.pl/' + ckmId + ',d2dd64302895d26784c706717a1996b0.html?dv=aplikacja_androidVOD%2Ffilmy&back=onetvod%3A%2F%2Fback'     
    tm = str(int(time.time() * 1000))
    jQ = str(random.randrange(562674473039806,962674473039806))
    authKey = '22D4B3BC014A3C200BCA14CDFF3AC018'
    contentUrl = 'http://qi.ckm.onetapi.pl/?callback=jQuery183040'+ jQ + '_' + tm + '&body%5Bid%5D=' + authKey + '&body%5Bjsonrpc%5D=2.0&body%5Bmethod%5D=get_asset_detail&body%5Bparams%5D%5BID_Publikacji%5D=' + ckmId + '&body%5Bparams%5D%5BService%5D=vod.onet.pl&content-type=application%2Fjsonp&x-onet-app=player.front.onetapi.pl&_=' + tm
    valTab = []
    query_data = {'url': contentUrl, 'use_host': False, 'use_cookie': False, 'use_post': False, 'return_data': True}
    try: 
        data = self.cm.getURLRequestData(query_data)
        #extract json
        result = json.loads(data[data.find("(")+1:-2])
        strTab = []
        for items in result['result']['0']['formats']['wideo']:
            for i in range(len(result['result']['0']['formats']['wideo'][items])):
                strTab.append(items)
                strTab.append(result['result']['0']['formats']['wideo'][items][i]['url'].encode('UTF-8'))
                if result['result']['0']['formats']['wideo'][items][i]['video_bitrate']:
                    strTab.append(int(float(result['result']['0']['formats']['wideo'][items][i]['video_bitrate'])))
                else:
                    strTab.append(0)
                valTab.append(strTab)
                strTab = []
    except: 
        printExc()
    return valTab
    
  def getPoster(self, h):
    posterUrl = 'http://m.ocdn.eu/_m/' + h + ',10,1.jpg'
    return posterUrl

  def getAPIData(self, module, post_data):
    query_data = {'url': vodonet.MODULE_URL[module], 'use_host': False, 'use_header': True, 'header': vodonet.HEADER, 'use_cookie': False, 'use_post': True, 'raw_post_data': True, 'return_data': True}
    result = {}
    try:
        data = self.cm.getURLRequestData(query_data, post_data)
        result = json.loads(data)
        #printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        #printDBG(data)
        #printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    except: printExc()
    return result

  def makeListQuery(self, p):
    args =   {"device":"mobile", "withoutDRM":"True", "payment":["-svod","-ppv"]}
    params = {"context":"", "method":"", "sort":"", "range":[0,10000], "args":args}
    dict =   {"id":"query_cmsQuery", "jsonrpc":"2.0", "method":"cmsQuery", "params":params}
    for key in p.keys():
        if any(key in s for s in ['context','method','sort']): 
            dict['params'][key] = p[key]
        else:
            dict['params']['args'][key] = p[key]
    return json.dumps(dict)

  def makeVideoDetailsQuery(self, p):
    args =   {"device":"mobile", "withoutDRM":"True", "payment":["-svod","-ppv"]}
    params = {"id":0, "context":"", "object":"Video", "WithoutDRM":"True", "args":args}
    dict =   {"id":"query_cmsGet", "jsonrpc":"2.0", "method":"cmsGet", "params":params}
    for key in p.keys():
        dict['params'][key] = p[key]
    return json.dumps(dict)

def _getLinkQuality( itemLink ):
    return int(itemLink[2])

class IPTVHost(IHost):

    def __init__(self):
        self.onet = None
        self.currIndex = -1
        self.listOfprevList = [] 
    
    # return firs available list of item category or video or link
    def getInitList(self):
        self.onet = vodonet()
        self.currIndex = -1
        self.listOfprevList = [] 
        
        self.onet.handleService(self.currIndex)
        convList = self.convertList(self.onet.getCurrList())
        
        return RetHost(RetHost.OK, value = convList)
    
    # return List of item from current List
    # for given Index
    # 1 == refresh - force to read data from 
    #                server if possible 
    # server instead of cache 
    def getListForItem(self, Index = 0, refresh = 0, selItem = None):
        self.listOfprevList.append(self.onet.getCurrList())
        
        self.currIndex = Index
        self.onet.handleService(Index)
        convList = self.convertList(self.onet.getCurrList())
        
        return RetHost(RetHost.OK, value = convList)
        
    # return prev requested List of item 
    # for given Index
    # 1 == refresh - force to read data from 
    #                server if possible
    def getPrevList(self, refresh = 0):
        if(len(self.listOfprevList) > 0):
            onetList = self.listOfprevList.pop()
            self.onet.setCurrList(onetList)
            convList = self.convertList(onetList)
            return RetHost(RetHost.OK, value = convList)
        else:
            return RetHost(RetHost.ERROR, value = [])
        
    # return current List
    # for given Index
    # 1 == refresh - force to read data from 
    #                server if possible
    def getCurrentList(self, refresh = 0):
        if refresh == 1:
            self.onet.handleService(self.currIndex, refresh)
        convList = self.convertList(self.onet.getCurrList())
        return RetHost(RetHost.OK, value = convList)
        
    # return list of links for VIDEO with given Index
    # for given Index
    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.onet.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
            
        if self.onet.currList[Index].name != 'playSelectedMovie':
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])
            
        retlist = []
        videoID = self.onet.currList[Index].category
        
        tab = self.onet.api.getVideoTab(self.onet.currList[Index].category)
        if config.plugins.iptvplayer.onetvodUseDF.value:
            maxRes = int(config.plugins.iptvplayer.onetvodDefaultformat.value) * 1.1
            tab = CSelOneLink( tab, _getLinkQuality, maxRes ).getOneLink()

        for item in tab:
            if item[0] == vodonet.FORMAT:
                nameLink = "type: %s \t bitrate: %s" % (item[0], item[2])
                url = item[1]
                retlist.append(CUrlItem(nameLink.encode('utf-8'), url.encode('utf-8'), 0))
            
        return RetHost(RetHost.OK, value = retlist)
        
    # return resolved url
    # for given url
    def getResolvedURL(self, url):
        if url != None and url != '':
            ret = self.onet.resolveUrl(url)
            list = []
            list.append(ret)
            return RetHost(RetHost.OK, value = list)
        else:
            return RetHost(RetHost.NOT_IMPLEMENTED, value = [])
            
    # return full path to player logo
    def getLogoPath(self):  
        return RetHost(RetHost.OK, value = [GetLogoDir('onetvodlogo.png')])

    def convertList(self, onetList):
        hostList = []
        
        for onetItem in onetList:
            hostLinks = []
                
            type = CDisplayListItem.TYPE_UNKNOWN
            if onetItem.name != 'playSelectedMovie':
                type = CDisplayListItem.TYPE_CATEGORY
            else:
                type = CDisplayListItem.TYPE_VIDEO
 
            hostItem = CDisplayListItem(name = onetItem.title, \
                                        description = '', \
                                        type = type, \
                                        urlItems = hostLinks, \
                                        urlSeparateRequest = 1, \
                                        iconimage = onetItem.iconimage)
            hostList.append(hostItem)
        return hostList
