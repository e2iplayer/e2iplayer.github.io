# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CDisplayListItem, RetHost, CUrlItem
import Plugins.Extensions.IPTVPlayer.libs.pCommon as pCommon
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSelOneLink, GetLogoDir
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
###################################################
# FOREIGN import
###################################################
import re, urllib
try:
    import simplejson as json
except:
    import json
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.wpDefaultformat = ConfigSelection(default = "2", choices = [("1", "Niska"), ("2", "Wysoka")])
config.plugins.iptvplayer.wpUseDF = ConfigYesNo(default = False)
config.plugins.iptvplayer.wpSortBy = ConfigSelection(default = "2", choices = [("1", "Najczęściej oglądane"), ("2", "Najnowsze"), ("3", "Najwyżej oceniane"), ("4", "Najczęściej komentowane")])

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Sort by:"), config.plugins.iptvplayer.wpSortBy))
    optionList.append( getConfigListEntry( "Domyślny jakość video:", config.plugins.iptvplayer.wpDefaultformat ) )
    optionList.append( getConfigListEntry( "Używaj domyślnej jakości video:", config.plugins.iptvplayer.wpUseDF ) )
    return optionList
###################################################

def gettytul():
    return 'WP.TV'

class WP():
    HOST = 'Mozilla/5.0 (Windows NT 6.1; rv:17.0) Gecko/20100101 Firefox/17.0'
    def __init__(self):
        self.cm = pCommon.common()
        self.currList = []
        
    def getCurrList(self):
        return self.currList

    def setCurrList(self, list):
        self.currList = list
        return 
    
    def getMainMenu(self):
        printDBG('getMainMenu start')
        list = []
        url = 'http://wp.tv/mindex.html'        
        sts, data = self.cm.getPage(url, {'host': self.HOST})
        if sts:
            # extract menu html
            idx = data.find('Strona główna')
            if idx <= 0: return list
            idx2 = data.find('Inne serwisy WP.PL', idx)
            if idx2 <= 0: return list
            data = data[idx:idx2]
            
            match = re.compile('<header class="grayBar round "><a class="a" href="([^"]+?mkategoria.html)">([^<]+?)</a>').findall(data)
            if len(match) <= 0: return list
            
            printDBG("---------------------------------------------")
            for i in range(len(match)):
                list.append({'name':match[i][1], 'url':match[i][0], 'type':'main_item'})
                printDBG("cat: " + match[i][1] + "\t: " + match[i][0])
            printDBG("---------------------------------------------")
        
        return list
        
    def getSubMenu(self, url):
        printDBG('getSubMenu start')
        list = []
        match = re.compile('http://wp.tv/type,([^,]+?),.+?.html').findall(url)
        if len(match) <= 0: return list
        jtype = match[0]
        
        sts, data = self.cm.getPage(url, {'host': self.HOST})
        if sts:
            match = re.compile('<option value="([0-9]+?)" >([^<]+?)</option>').findall(data)
            if len(match) <= 0: return list
            
            printDBG("---------------------------------------------")
            for i in range(len(match)):
                list.append({'name':match[i][1], 'id':match[i][0], 'type':'sub_item', 'jtype' : jtype})
                printDBG("\tcat: " + match[i][1] + '\t' + jtype + "\t: " + match[i][0])
            printDBG("---------------------------------------------")
        
        return list
        
    def getJsonList(self, type, jtype, id):
        printDBG('getJsonList start')
        list = []
        
        url = 'http://wp.tv/mlista.json'
        params = {'host': self.HOST }
        postdata = { 'type': jtype, 'filter': config.plugins.iptvplayer.wpSortBy.value, "cid": id, "wrapperName" :"wptv2_lib_wrapper_CategoryListSourceWrapper" }

        sts, data = self.cm.getPage(url, params, postdata)
        if not sts: return list
        #printDBG("+++++++++++++++++++++++++")
        #printDBG(data)
        #printDBG("+++++++++++++++++++++++++")
        try:
            result = json.loads(data)
            if None != result['subMenu'] and type == 'sub_item':
                printDBG( 'getJsonList get sub menu' )
                sel_id = str(result['subMenu']['menuListSelected']['cid'])
                printDBG( sel_id )
                dataChecked = False
                for item in result['subMenu']['menuList']:
                    cid = str(result['subMenu']['menuList'][item]['cid'])
                    name = result['subMenu']['menuList'][item]['name']
                    if cid == sel_id:
                        dataChecked = True
                    else:
                        printDBG("\t\t\t" + cid + "\t" + name)
                        list.append({'name':name.encode('utf-8'), 'id':cid, 'type':'sub_jitem', 'jtype' : jtype})
                if 0 < len(list) or not dataChecked:
                    return list
        except:
            printExc()
            return list
        #data = result["jsPagination"]
        #return self.getJsonPagesList(id, data)
        return self.setDirMenu(self.getItems("http://wp.tv/app/cliplist?catid=" + id))
            
    def getJsonPagesList(self, id, data):
        printDBG( 'getJsonPagesList id=%s  data=%s' % (id,data) )
        list = []
        try:
            match = re.compile('data-allresults="([0-9]+?)" data-onpage="([0-9]+?)"').findall(data)
            if len(match) > 0: 
                itemNum = int(match[0][0])
                numPerPage = int(match[0][1])
                pageNum = itemNum / numPerPage
                if itemNum % numPerPage > 0:
                    pageNum += 1
                
                for i in range(pageNum):
                    tmpItem = {'name': 'Strona %d' % (i+1), 'id':id, 'page': str(i+1), 'type':'page'}
                    list.append(tmpItem)
                    printDBG( tmpItem['name'] )
            
            if len(list) < 2:
                return self.getJsonVideoList('1', id)
            else:
                return list
        except: printExc()
        return list
        
    def getJsonVideoList(self, page, id):
        printDBG( 'getJsonVideoList page=%s  id=%s' % (page, id) )
        list = []
        url ="http://wp.tv/mlista.html?page=%s&filter=%s&cid=%s&subcid=%s&wrapperName=wptv2_lib_wrapper_CategoryListSourceWrapper" % (page, config.plugins.iptvplayer.wpSortBy.value, id, id)
        sts, data = self.cm.getPage(url, {'host': self.HOST})
        if sts:
            try:
                match = re.compile('<a href="([^"]+?)"><img src="([^"]+?)" alt=""><div class="matBox">([^<]+?)</div>').findall(data)
                if len(match) <= 0: return list
                
                for i in range(len(match)):
                    item = {'name':match[i][2], 'url':match[i][0], 'ico':match[i][1], 'type':'video'}
                    list.append(item)
                    printDBG( "name: " + item['name'].encode('utf-8') + " url: " + item["url"].encode('utf-8') + " ico: " + item['ico'].encode('utf-8'))
            except: printExc()
        return list
            
    def getVideoLinks(self, url, data = None):
        if data != None: url = data
        printDBG( 'getVideoLinks url=%s ' % url )
        list = []
        
        if data == None:
            url ="http://wp.tv/" + url
            sts, data = self.cm.getPage(url, {'host': self.HOST})
            if not sts: return list
        
        match = re.compile('(http://get\.wp\.tv/\?f=[0-9]+?\.[0-9]+?\.)').search(data)
        if None == match: return list
        
        list.append({'name':'Wysoka jakosc', 'url': match.group(0) + 'h.mp4'})
        list.append({'name':'Niska jakosc', 'url': match.group(0) + 'l.mp4'})
        #list.append({'name':'Domyslna jakosc', 'url': match.group(0) + 'm3.mp4'})
        
        return list
        
    # code based on (root)/trunk/xbmc-addons/src/plugin.video.polishtv.live/hosts/ @ 635 - Wersja 669 
    def getItems(self, url, clip = True):
        strTab = []
        valTab = []
        sts, data = self.cm.getPage(url, {'host': self.HOST})
        if sts:
            try:
                result = json.loads(data)
                if clip:
                    for item in result['clips']:
                        strTab.append(item['clipUrl'])
                        strTab.append(item['thumbnail'])            
                        strTab.append(item['title'])
                        strTab.append(item['description'])
                        valTab.append(strTab)
                        strTab = []
                    if result['page'] != result['pageCount']:
                        valTab.append([url + "&page=" + str(result['page']+1), '', 'Nastepna strona', 'nextpage'])
                else:
                    for item in result:
                        #skip {"catId":4050,"name":"Najnowsze","description":"","logo":null,"priority":0}
                        if item['name'] != 'Najnowsze':
                            strTab.append(item['catId'])
                            strTab.append(item['logo'])            
                            strTab.append(item['name'])
                            strTab.append(item['description'])
                            valTab.append(strTab)
                            strTab = []
            except:
                printExc()
        return valTab
        
    def setDirMenu(self, table):
        resList = []
        for i in range(len(table)):
            if self.cm.isNumeric(table[i][0]):
                #self.addDir(SERVICE,"sub-menu",str(table[i][0]),self.cm.html_entity_decode(table[i][2].encode('UTF-8')),table[i][3].encode('UTF-8'),"",table[i][1])
                printDBG("APP SUB MENU:")
                printDBG("\t: " + str(table[i][0]))
                printDBG("\t: " + self.cm.html_entity_decode(table[i][2].encode('UTF-8')))
                printDBG("\t: " + table[i][3].encode('UTF-8'))
                printDBG("\t: " + table[i][1])
            else:
                if table[i][3] == 'nextpage':
                    item = {'name':self.cm.html_entity_decode(table[i][2].encode('UTF-8')), 'url':table[i][0], 'type':'app_cat'}
                    resList.append(item)              
                else:
                    item = {'name':self.cm.html_entity_decode(table[i][2].encode('UTF-8')), 'url':table[i][0].encode('UTF-8'), 'ico':table[i][1], 'desc':table[i][3].encode('UTF-8'), 'type':'app_video'}
                    resList.append(item)
        return resList
    
    def handleService(self, index, refresh = 0, searchPattern = ''):
    
        if 0 == refresh:
            if len(self.currList) <= index:
                printDBG( "WP.handleService wrong index: %s, len(self.currList): %d" % (index, len(self.currList)) )
                return
        
            if -1 == index:
                self.type = None
                printDBG( "WP.handleService for first self.category" )
            else:
                item = self.currList[index]
                self.type = item['type']
                self.index = index
                self.url = ''
                if 'url' in self.currList[index]:
                    self.url = self.currList[index]['url']
                self.jtype = ''
                if 'jtype' in self.currList[index]:
                    self.jtype = self.currList[index]['jtype']
                self.id = ''
                if 'id' in self.currList[index]:
                    self.id = self.currList[index]['id']
                self.page = ''
                if 'page' in self.currList[index]:
                    self.page = self.currList[index]['page']
                    
                self.prevList = self.currList

                printDBG( "WP: |||||||||||||||||||||||||||||||||||| %s " % item['type'] )

    #MAIN MENU
        if self.type == None:
            self.currList = self.getMainMenu()
            self.currList.append({'name':"Polecane", 'url': "http://wp.tv/app/recommended?", 'type':'app_cat'})
            self.currList.append({'name':"TOP100 Tygodnia", 'url': "http://wp.tv/app/toprated?type=week", 'type':'app_cat'})
            self.currList.append({'name':"TOP100 Miesiąca", 'url': "http://wp.tv/app/toprated?type=month", 'type':'app_cat'})
            self.currList.append({'name':"Wyszukaj", 'url': "http://wp.tv/app/search?queryType=2&query=", 'type':'app_search'})
    #APP CATEGORY
        elif self.type == 'app_cat':
            self.currList = self.setDirMenu(self.getItems(self.url)) 
    #SUB CATEGORY
        elif self.type == 'main_item':
            self.currList = self.getSubMenu('http://wp.tv/' + self.url)
    #SUB_SUB_CATEGORY
        elif self.type == 'sub_item' or self.type == 'sub_jitem':
            self.currList = self.getJsonList(self.type, self.jtype, self.id)
    #VIDEOS per page
        elif self.type == 'page':
            self.currList = self.getJsonVideoList(self.page, self.id)
    #SEARCH
        elif self.type == 'app_search':
            self.currList = self.setDirMenu(self.getItems(self.url+ urllib.quote(searchPattern))) 
    # end handleService

#list = getVideoLinks( list[0]['url'] )

def _getLinkQuality( itemLink ):
    if itemLink['name'].find('Niska') > -1:
        return 1
    return 2

class IPTVHost(IHost):

    def __init__(self):
        self.host = None
        self.currIndex = -1
        self.listOfprevList = [] 
        
        self.searchPattern = ''
    
    # return firs available list of item category or video or link
    def getInitList(self):
        self.host = WP()
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
        self.host.handleService(Index, refresh, self.searchPattern)
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
            if len(self.listOfprevList) > 0:
                hostList = self.listOfprevList.pop()
                self.host.setCurrList(hostList)
                return self.getListForItem(self.currIndex)
            else:
                return self.getInitList()           
                
        convList = self.convertList(self.host.getCurrList())
        return RetHost(RetHost.OK, value = convList)
    
    # return list of links for VIDEO with given Index
    # for given Index
    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            print "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index)
            return RetHost(RetHost.ERROR, value = [])
        
        selItem = self.host.currList[Index]
        if selItem['type'] != 'video':
            print "ERROR getLinksForVideo - current item has wrong type"
            return RetHost(RetHost.ERROR, value = [])
            
        retlist = []
        
        if None != selItem and 'url' in selItem and 1 < len(selItem['url']):
            tmpList = self.host.getVideoLinks( selItem['url'] )
            if config.plugins.iptvplayer.wpUseDF.value:
                maxRes = int(config.plugins.iptvplayer.wpDefaultformat.value)
                tmpList = CSelOneLink( tmpList, _getLinkQuality, maxRes ).getOneLink()
            
            for idx in range(len(tmpList)):
                retlist.append(CUrlItem(tmpList[idx]['name'], tmpList[idx]['url'], 0))
            
        return RetHost(RetHost.OK, value = retlist)
            
    def getSearchResults(self, searchpattern, searchType = None):
        self.isSearch = True
        retList = []
        self.searchPattern = searchpattern.replace(' ',  '%20')
        
        return self.getListForItem( len(self.host.getCurrList()) -1 )
            
    # return full path to player logo
    def getLogoPath(self):  
        return RetHost(RetHost.OK, value = [ GetLogoDir('wptvlogo.png') ])


    def convertList(self, cList):
        hostList = []
        possibleTypesOfSearch = []
        
        for cItem in cList:
            hostLinks = []
            type = CDisplayListItem.TYPE_UNKNOWN
            
            url = ''
            desc = ''
            sepReq = 0
            if cItem['type'] in ['main_item', 'sub_item',  'sub_item', 'sub_jitem', 'page', 'app_cat']:
                    type = CDisplayListItem.TYPE_CATEGORY
            elif cItem['type'] in ['video', 'app_video']:
                type = CDisplayListItem.TYPE_VIDEO
                url = cItem['url']
                hostLinks.append(CUrlItem('', url, 0))
            elif cItem['type']  == 'app_search':
                type = CDisplayListItem.TYPE_SEARCH
                
            name = ''
            if 'name' in cItem:
                name = cItem['name']
            ico = ''
            if 'ico' in cItem:
                ico = cItem['ico']
            desc = ' '
            if 'desc' in cItem:
                desc = cItem['desc']

            hostItem = CDisplayListItem(name = name,
                                        description = desc,
                                        type = type,
                                        urlItems = hostLinks,
                                        urlSeparateRequest = 1,
                                        iconimage = ico,
                                        possibleTypesOfSearch = possibleTypesOfSearch)
            hostList.append(hostItem)
        # end for
            
        return hostList
