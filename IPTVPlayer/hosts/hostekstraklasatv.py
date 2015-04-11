# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
import re
import urllib
import time
import random
try:    import json
except: import simplejson as json
from os import urandom as os_urandom

###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################

###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.ekstraklasa_defaultformat = ConfigSelection(default = "450", choices = [("0", "bitrate: najgorszy"), ("200", "bitrate: 200p"), ("450", "bitrate: 450p"),("900", "bitrate: 900"),("1800", "bitrate: 1800"), ("9999", "bitrate: najlepszy")])
config.plugins.iptvplayer.ekstraklasa_usedf = ConfigYesNo(default = False)
config.plugins.iptvplayer.ekstraklasa_proxy = ConfigYesNo(default = False)

def GetConfigList():
    optionList = []
    optionList.append( getConfigListEntry( "Domyślny format video:", config.plugins.iptvplayer.ekstraklasa_defaultformat ) )
    optionList.append( getConfigListEntry( "Używaj domyślnego format video:", config.plugins.iptvplayer.ekstraklasa_usedf ) )
    optionList.append( getConfigListEntry( "Ekstraklasa korzystaj z proxy?", config.plugins.iptvplayer.ekstraklasa_proxy) )
    return optionList
###################################################

def gettytul():
    return 'Ekstraklasa'

class Ekstraklasa(CBaseHostClass):

    EORG_MAIN_URL = 'http://ekstraklasa.org/'
    EORG_MAIN_MENU = [ {'name': 'Nowości', 'navi': 'nowosci'},
                       {'name': 'Bramki i skróty', 'navi': 'galeria-i-wideo'},
                     ]
    
    ETV_MAIN_URL  = 'http://ekstraklasa.tv/'
    ETV_MAIN_MENU = [ {'name': 'Bramki', 'navi': 'bramki'},
                      {'name': 'Skróty', 'navi': 'skroty'},
                      {'name': 'Bramka kolejki', 'navi': 'bramka-kolejki'},
                      {'name': 'Magazyn', 'navi': 'magazyn-t-mobile-ekstraklasy'},
                    ]
    ETV_CATEGORY  = 'etv_category'
    ETV_FORMAT    = 'mp4'
    def __init__(self):
        printDBG("Ekstraklasa.__init__")
        CBaseHostClass.__init__(self, {'proxyURL': config.plugins.iptvplayer.proxyurl.value, 'useProxy': config.plugins.iptvplayer.ekstraklasa_proxy.value})
    
    def listsCategories_ETV(self):
        printDBG("Ekstraklasa.listsCategories_ETV")
        
        for item in Ekstraklasa.ETV_MAIN_MENU:
            params = { 'name'     : 'category',
                       'category' : Ekstraklasa.ETV_CATEGORY,
                       'url'      : Ekstraklasa.ETV_MAIN_URL + item['navi'],
                       'title'    : item['name'],
                       'desc'     : 'ekstraklasa.tv',
                       'icon'     : '',
                       'depth'    : 0,
                       'host'     : 'ekstraklasa.tv'
                     }  
            self.addDir(params)

    def listsCategory_ETV(self, cItem):
        printDBG("Ekstraklasa.listsCategory_ETV")
        ITEM_MARKER = '<div class="listItem'
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        printDBG('----------------------------------------')
        
        # check if we should check for sub categories
        if 0 == cItem['depth']:
            subMenuData  = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="subMenu">', '</ul>', False)[1]
            subMenuData  = re.compile('<a[ ]+?href="(http[^">]+?)"[ ]*?>([^<]+?)</a>').findall(subMenuData)
            if 0 < len(subMenuData):
                params = dict(cItem)
                params.update({'title':'Najnowsze', 'depth':1})
                self.addDir(params)
                for item in subMenuData:
                    params = dict(cItem)
                    params.update({'url':item[0], 'title': self.cleanHtmlStr(item[1]), 'depth':1, })
                    self.addDir(params)
                return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, ITEM_MARKER, '<script')[1]
        moreData = self.cm.ph.getSearchGroups(data, "id=\"moredata\" value='([^']+?)'")[0]
        
        data = data.split(ITEM_MARKER)
        del data[0]
        for item in data:
            icon  = self.cm.ph.getSearchGroups(item, '<img[^>]+?data-original="([^"]+?)"')[0]
            title = self.cm.ph.getDataBeetwenMarkers(item, '<h3 class="itemTitle">', '</h3>', False)[1].strip() + ', ' +self.cm.ph.getDataBeetwenMarkers(item, '<div class="datePublished">', '</div>', False)[1].strip()
            # self.cm.ph.getDataBeetwenMarkers(item, '<div class="itemLead hyphenate">', '</div>', False)[1]
            desc  = self.cleanHtmlStr(ITEM_MARKER + item)
            url   = self.cm.ph.getSearchGroups(item, '<a href="([^"]+?)" title="([^"]+?)"', 2)[0]
            params = {'title':title, 'url':url, 'icon':icon, 'desc': desc, 'host':'ekstraklasa.tv'}
            self.addVideo(params)
            #if "mediaType mediaVideo" in item:
            #    self.addVideo(params)
            #else:
            #    self.addArticle(params)
        # checkNewItemsAvailability
        a = len(data)
        if '' != moreData and 0 < a:
            try:
                # check if there are more data
                moreData  = json.loads(moreData)
                prevLimit = moreData['limit']
                moreData['offset'] += a
                moreData['limit']   = 1 
                moreData = {'params':moreData}
                url = urllib.quote(json.dumps(moreData, sort_keys=False, separators=(',', ':')))
                url = Ekstraklasa.ETV_MAIN_URL + '_cdf/api?json=' + url + '&____presetName=liststream'
                sts, data = self.cm.getPage(url)
                if ITEM_MARKER in data:
                    moreData['params']['limit']   = prevLimit 
                    url = urllib.quote(json.dumps(moreData, sort_keys=False, separators=(',', ':')))
                    url = Ekstraklasa.ETV_MAIN_URL + '_cdf/api?json=' + url + '&____presetName=liststream'
                    params = dict(cItem)
                    params.update({'title':'Następna strona', 'url':url })
                    self.addDir(params)
            except:
                printExc()
        # list items
        
    def getVideoTab_ETV(self, ckmId):
        printDBG("Ekstraklasa.getVideoTab_ETV ckmId[%r]" % ckmId )
        tm = str(int(time.time() * 1000))
        jQ = str(random.randrange(562674473039806,962674473039806))
        authKey = 'FDF9406DE81BE0B573142F380CFA6043'
        contentUrl = 'http://qi.ckm.onetapi.pl/?callback=jQuery183040'+ jQ + '_' + tm + '&body%5Bid%5D=' + authKey + '&body%5Bjsonrpc%5D=2.0&body%5Bmethod%5D=get_asset_detail&body%5Bparams%5D%5BID_Publikacji%5D=' + ckmId + '&body%5Bparams%5D%5BService%5D=ekstraklasa.onet.pl&content-type=application%2Fjsonp&x-onet-app=player.front.onetapi.pl&_=' + tm
        sts, data = self.cm.getPage(contentUrl)
        if sts:
            try:
                #extract json
                result = json.loads(data[data.find("(")+1:-2])
                strTab = []
                valTab = []
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

    def getLinks_ETV(self, url):
        printDBG("Ekstraklasa.getLinks_ETV url[%r]" % url )
        videoUrls = []
        sts, data = self.cm.getPage(url)
        if not sts: return videoUrls
        ckmId = self.cm.ph.getSearchGroups(data, 'data-params-mvp="([^"]+?)"')[0]
        if '' == ckmId: ckmId = self.cm.ph.getSearchGroups(data, 'id="mvp:([^"]+?)"')[0]
        if '' != ckmId: videoUrls = self.getVideoTab_ETV(ckmId)
        return videoUrls
        
    def getDescription_ETV(self, url):
        printDBG("Ekstraklasa.getDescription url[%r]" % url )
        content = {}
        sts, data = self.cm.getPage(url)
        if sts:
            desc  = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<div id="lead">', '</div>', False)[1])
            title = self.cm.ph.getDataBeetwenMarkers(data, '<title>', '</title>', False)[1].strip()
            data  = self.cm.ph.getDataBeetwenMarkers(data, '<div id="leadMedia">', '</div>', False)[1].strip()
            icon  = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
            content = { 'title': title,
                        'desc' : desc,
                        'icon' : icon,
                      }
        return content
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('Ekstraklasa..handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "Ekstraklasa.handleService: ---------> name[%s], category[%s] " % (name, category) )
        self.currList = []
        
        if None == name:
            self.listsCategories_ETV()
        elif Ekstraklasa.ETV_CATEGORY == category:
            self.listsCategory_ETV(self.currItem)


class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Ekstraklasa(), False)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('ekstraklasatvlogo.png')])
        
    def getArticleContent(self, Index = 0):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getArticleContent - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        if 'ekstraklasa.tv' in self.host.currList[Index].get('host', ''): 
            content = self.host.getDescription_ETV(self.host.currList[Index]['url'])
        elif 'ekstraklasa.org' in self.host.currList[Index].get('host', ''):
            content = {}
        
        title  = content.get('title', '')
        text   = content.get('desc', '')
        images = [ {'title':'', 'author': '', 'url': content.get('icon', '')} ]
        
        return RetHost(RetHost.OK, value = [ArticleContent(title = title, text = text, images =  images)])

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        retlist = []
        if 'ekstraklasa.tv' in self.host.currList[Index].get('host', ''):        
            tab = self.host.getLinks_ETV(self.host.currList[Index].get('url', ''))
            if config.plugins.iptvplayer.ekstraklasa_usedf.value:
                maxRes = int(config.plugins.iptvplayer.ekstraklasa_defaultformat.value) * 1.1
                def _getLinkQuality( itemLink ):
                    return int(itemLink[2])
                tab = CSelOneLink( tab, _getLinkQuality, maxRes ).getOneLink()

            for item in tab:
                if item[0] == Ekstraklasa.ETV_FORMAT:
                    nameLink = "type: %s \t bitrate: %s" % (item[0], item[2])
                    url = item[1]
                    retlist.append(CUrlItem(nameLink.encode('utf-8'), url.encode('utf-8'), 0))
        elif 'ekstraklasa.org' in self.host.currList[Index].get('host', ''):
            pass
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
            elif cItem['type'] == 'article':
                type = CDisplayListItem.TYPE_ARTICLE
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