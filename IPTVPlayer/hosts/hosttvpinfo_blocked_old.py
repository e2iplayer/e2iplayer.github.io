# -*- coding: utf-8 -*-
# Based on (root)/trunk/xbmc-addons/src/plugin.video.polishtv.live/hosts/ @ 419 - Wersja 605

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CDisplayListItem, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, GetLogoDir
import Plugins.Extensions.IPTVPlayer.libs.pCommon as pCommon
###################################################
# FOREIGN import
###################################################
import urllib, urllib2
import xml.etree.cElementTree
try:
    import json
except:
    import simplejson as json
    

def gettytul():
    return 'TVP Info player'
    

class CItemList:
    TYPE_CATEGORY = "CATEGORY"
    TYPE_VIDEO = "VIDEO"
    #TYPE_NEXT_PAGE = "NEXT_PAGE"
    def __init__(self, name, url, mode, category, iconimage, type, description, page):
        self.name = name
        self.url  = url
        self.category = category
        self.mode = mode
        self.iconimage = iconimage
        self.type = type
        self.description = description
        self.page = page


class tvp:
    NEXT_PAGE_HTML = '?sort_by=POSITION&sort_desc=false&start_rec=6'
    PAGE_MOVIES = 12
    mode = 0
    
    TVP_MAIN_MENU_TABLE = [
        "Przegapiłes|xml|http://www.tvp.pl/pub/stat/missed?rec_count=" + str(PAGE_MOVIES),
        "Najcześciej oglądane|xml|http://www.tvp.pl/pub/stat/videolisting?src_id=1885&object_id=929547&object_type=video&child_mode=SIMPLE&rec_count=" + str(PAGE_MOVIES),
        "Teleexpress|xml|http://www.tvp.pl/pub/stat/videolisting?object_id=8811603&with_subdirs=true&sort_desc=true&sort_by=RELEASE_DATE&child_mode=SIMPLE&rec_count=" + str(PAGE_MOVIES),
        "Wiadomości|xml|http://www.tvp.pl/pub/stat/videolisting?object_id=7405772&with_subdirs=true&sort_desc=true&sort_by=RELEASE_DATE&child_mode=SIMPLE&rec_count=" + str(PAGE_MOVIES),
        "Panorama|xml|http://www.tvp.pl/pub/stat/videolisting?object_id=5513139&with_subdirs=true&sort_desc=true&sort_by=RELEASE_DATE&child_mode=SIMPLE&rec_count=" + str(PAGE_MOVIES),
        "Makłowicz w podróży|xml|http://www.tvp.pl/pub/stat/videolisting?object_id=1364&with_subdirs=true&sort_desc=true&sort_by=RELEASE_DATE&child_mode=SIMPLE&rec_count=" + str(PAGE_MOVIES),
        "Kraków - najczęściej oglądane|xml|http://www.tvp.pl/pub/stat/videolisting?src_id=1885&object_id=929711&object_type=video&child_mode=SIMPLE&sort_by=RELEASE_DATE&sort_desc=true&rec_count=" + str(PAGE_MOVIES),
        "Kronika|xml|http://www.tvp.pl/pub/stat/videolisting?object_id=1277349&object_type=video&child_mode=SIMPLE&sort_by=RELEASE_DATE&sort_desc=true&rec_count=" + str(PAGE_MOVIES),
        "Kabarety|xml|http://www.tvp.pl/pub/stat/videolisting?object_id=883&with_subdirs=true&sort_desc=true&sort_by=RELEASE_DATE&child_mode=SIMPLE&rec_count=" + str(PAGE_MOVIES),
        "Sport najnowsze|xml|http://www.tvp.pl/pub/stat/videolisting?object_id=1775930&object_type=video&child_mode=SIMPLE&sort_by=RELEASE_DATE&sort_desc=true&rec_count=" + str(PAGE_MOVIES),
        "Sport teraz oglądane|xml|http://www.tvp.pl/pub/stat/videolisting?object_id=928060&object_type=video&child_mode=SIMPLE&sort_by=RELEASE_DATE&sort_desc=true&rec_count=" + str(PAGE_MOVIES),
        "Sport najwyżej oceniane|xml|http://www.tvp.pl/pub/stat/videolisting?object_id=928062&object_type=video&child_mode=SIMPLE&sort_by=RELEASE_DATE&sort_desc=true&rec_count=" + str(PAGE_MOVIES),
        "Sport najczęściej oglądane|xml|http://www.tvp.pl/pub/stat/videolisting?object_id=928059&object_type=video&child_mode=SIMPLE&sort_by=RELEASE_DATE&sort_desc=true&rec_count=" + str(PAGE_MOVIES),
        "Kultura|xml|http://www.tvp.pl/pub/stat/videolisting?object_id=883&with_subdirs=true&sort_desc=true&sort_by=RELEASE_DATE&child_mode=SIMPLE&rec_count=" + str(PAGE_MOVIES),
        "Kultura teraz oglądane|xml|http://www.tvp.pl/pub/stat/listing?src_id=2&object_id=929222&object_type=video&child_mode=SIMPLE&list_mode=CURRENT&play_mode=VOD%3ALIVE&rec_count=" + str(PAGE_MOVIES),
        "Kultura najwyżej oceniane|xml|http://www.tvp.pl/pub/stat/listing?src_id=2&object_id=929223&object_type=video&child_mode=SIMPLE&list_mode=VOTES&play_mode=VOD&rec_count=" + str(PAGE_MOVIES),
        "Kultura najczęściej oglądane|xml|http://www.tvp.pl/pub/stat/listing?src_id=2&object_id=929221&object_type=video&child_mode=SIMPLE&list_mode=TOPLIST&play_mode=VOD&rec_count=" + str(PAGE_MOVIES),
        "Rozrywka teraz oglądane|xml|http://www.tvp.pl/pub/stat/listing?src_id=2&object_id=929212&object_type=video&child_mode=SIMPLE&list_mode=CURRENT&play_mode=VOD%3ALIVE&rec_count=" + str(PAGE_MOVIES),
        "Rozrywka najwyżej oceniane|xml|http://www.tvp.pl/pub/stat/listing?src_id=2&object_id=929213&object_type=video&child_mode=SIMPLE&list_mode=VOTES&play_mode=VOD&rec_count=" + str(PAGE_MOVIES),
        "Rozrywka najczęściej oglądane|xml|http://www.tvp.pl/pub/stat/listing?src_id=2&object_id=929211&object_type=video&child_mode=SIMPLE&list_mode=TOPLIST&play_mode=VOD&rec_count=" + str(PAGE_MOVIES),
        "TVP Parlament|xml|http://www.tvpparlament.pl/pub/stat/videolisting?object_id=4433578&with_subdirs=true&sort_desc=true&sort_by=RELEASE_DATE&child_mode=SIMPLE&rec_count=" + str(PAGE_MOVIES),
    ]

    def __init__(self):
        printDBG("Starting TVP.INFO")
        self.cm = pCommon.common()
        
        self.currList = []
        
        self.name = "None"
        self.title = "title"
        self.category = "category"
        self.url = "url"
        self.page = "0"

    def getCurrList(self):
        return self.currList
        
    def setCurrList(self, list):
        self.currList = list
        return 
        
    def addDir(self, name, url, mode, category, iconimage):
        item = CItemList(name, url, mode, category, iconimage, CItemList.TYPE_CATEGORY, "", "0")
        self.currList.append(item)
        
        return True

    def addVideoLink(self,prop,url,iconimage,listsize=0):
        ok=True
        if not 'description' in prop:
            prop['description'] = ''
        if not 'time' in prop:
            prop['time'] = 0
        if not 'aired' in prop:
            prop['aired'] = ''
        if not 'overlay' in prop:
            prop['overlay'] = 0
        if not 'TVShowTitle' in prop:
            prop['TVShowTitle'] = ''
        if not 'episode' in prop:
            prop['episode'] = 0

        #print "##############################################################"
        #print "%s" % url
        #print "%s" % iconimage
        #print "%s" % listsize
        #print "=============================================================="
        #print "%s" % prop['description']
        #print "%s" % prop['time']
        #print "%s" % prop['aired']
        #print "%s" % prop['overlay']
        #print "%s" % prop['TVShowTitle']
        #print "%s" % prop['episode']
        #print "%s" % prop['episode']
        #print "##############################################################"
        
        name = "%s %s %s" % (prop['title'], prop['episode'], prop['aired'])
        
        printDBG("name = %s" % name)
        
        item = CItemList(name, url, self.mode, self.category, iconimage, CItemList.TYPE_VIDEO, prop['description'], self.page)
        self.currList.append(item)
        
        return ok

    def listsCategories(self, mainList):
        for item in mainList:
            value = item.split('|')
            self.addDir(value[0],value[2],self.mode,value[1],'')
            
            
    def getVideoFormat(self, videoFormats, video_format_profile_id):
        try:
            if videoFormats:
                for format in videoFormats:
                    if format.attrib['video_format_profile_id'] == video_format_profile_id:
                        return format.attrib['bitrate']
        except:
            pass
        return '0'


    def getVideoListXML(self):
        print "getVideoListXML_________________________________________________________"
        findVideo=False
        paginationUrl = ''
        if self.page > 0:
            paginationUrl = "&start_rec=" + str(self.page * tvp.PAGE_MOVIES)
        try:
        #if 1:
            printDBG( "|||||||||||||||||||||||||||||: %s" % (self.url+paginationUrl) )
            elems = xml.etree.cElementTree.fromstring(urllib2.urlopen(self.url+paginationUrl).read())
            epgItems = elems.findall("epg_item")
            if not epgItems:
                epgItems = elems.findall("directory_stats/video")
            if not epgItems:
                epgItems = elems.findall("directory_standard/video")
            if not epgItems:
                epgItems = elems.findall("video")
            if not epgItems:
                epgItems = elems.findall("directory_video/video")
                

            pub = elems.findall("publication_status")
            if pub[0].attrib['publication_status_id']=='4':
                print "getVideoListXML BRAK VIDEO"

            listsize = len(epgItems)
            for epgItem in epgItems:
                prop = {
                    'title':  epgItem.find("title").text.encode('utf-8'),
                    'TVShowTitle': self.name
                }
                if epgItem.attrib['hptitle'] <> '':
                    prop['title'] = epgItem.attrib['hptitle'].encode('utf-8')
                if epgItem.attrib['release_date']:
                    prop['aired'] = epgItem.attrib['release_date']
                if epgItem.get('episode_number'):
                    prop['episode'] = epgItem.attrib['episode_number']
                prop['description'] = ''
                textNode = epgItem.find('text_paragraph_standard/text')
                #print "test[8]:" + textNode.text.encode('utf-8')
                if (textNode):
                    prop['description'] = textNode.text.encode('utf-8')
                    prop['description'] = prop['description'].replace("<BR/>", "")


                iconUrl = ''
                videoUrl = ''
                iconFileNode = epgItem.find('video/image')
                if not iconFileNode:
                    iconFileNode = epgItem.find('image')

                if iconFileNode:
                    iconFileName = iconFileNode.attrib['file_name']
                    iconFileName = iconFileName.split('.')
                    iconUrl = 'http://s.v3.tvp.pl/images/6/2/4/uid_%s_width_200.jpg' % iconFileName[0]
                    iconTitle = iconFileNode.find('title').text.encode('utf-8')
                    if len(iconTitle) > 4 and iconTitle <> prop['title']:
                        if iconTitle <> 'zdjecie domyślne' and iconTitle <> 'image' and iconTitle <> 'obrazek':
                            iconTitle = iconTitle.split(',')[0]
                            prop['title'] = iconTitle + " - " + prop['title']
                    #print "test[4]: " + iconUrl

                videMainNode = epgItem.find('video')
                if None == videMainNode:
                    videMainNode = epgItem 
                if None != videMainNode:
                    if videMainNode.attrib['release_date']:
                        prop['aired'] = videMainNode.attrib['release_date']
                    if videMainNode.attrib['episode_number']:
                        prop['episode'] = videMainNode.attrib['episode_number']

                    videoText = videMainNode.find('text_paragraph_lead/text')
                    if (videoText):
                        if len(prop['description']) < videoText.text.encode('utf-8'):
                            prop['description'] = videoText.text.encode('utf-8')

                    prop['time'] = int(videMainNode.attrib['duration'])
                    iconTitle = videMainNode.find('title').text.encode('utf-8')
                    if len(iconTitle) > 4 and iconTitle <> prop['title']:
                        if iconTitle <> 'zdjecie domyślne' and iconTitle <> 'image' and iconTitle <> 'obrazek':
                            iconTitle = iconTitle.split(',')[0]
                            prop['title'] = prop['title'] + " - " + iconTitle

                    self.addVideoLink(prop, videMainNode.attrib.get('video_id', '-1'), iconUrl, listsize)
                    findVideo = True
        #else:
        except:
            printDBG("getVideoListXML exception")

        if findVideo:
            if listsize == tvp.PAGE_MOVIES:
                self.addNextPage()


    #def watched(self, videoUrl):
    #    videoFile = videoUrl.split('/')[-1]
    #    shortVideoFile = videoFile[videoFile.find('.')+1:]
    #    sql_data = "select count(*) from files WHERE (strFilename ='%s' OR strFilename ='%s') AND playCount > 0" % (videoFile,shortVideoFile)
    #    xml_data = xbmc.executehttpapi( "QueryVideoDatabase(%s)" % urllib.quote_plus( sql_data ), )
    #    wasWatched = re.findall( "<field>(.*?)</field>", xml_data)[0]
    #    if wasWatched == "1":
    #        return True
    #    else :
    #        return False

    def handleService(self, index, refresh = 0):
        
        if 0 == refresh:
            if len(self.currList) <= index:
                print "handleService wrond index: %s, len(self.currList): %d" % (index, len(self.currList))
                return
        
            if -1 == index:
                self.name = 'None'
                self.page = "0"
                self.mode = 0
                print "handleService for first category"
            else:
                item = self.currList[index]
                self.name = item.name
                self.category = item.category
                self.url = item.url
                self.mode = item.mode
                self.page = item.page
                
                print "|||||||||||||||||||||||||||||||||||| %s " % item.name
               
                self.title = ""
            
        self.currList = []
 
        if not self.page:
            self.page = 0
        else:
            self.page = int(self.page)

        if self.name == 'None':
            self.listsCategories(tvp.TVP_MAIN_MENU_TABLE)
        elif self.name != 'None' and self.category == 'xml':
            self.getVideoListXML()
        else:
            printDBG( "________________________________________________" )

    def addNextPage(self):
        page = self.page
        if page == None:
            page = "0"
        else:
            page = "%s" % (int(self.page) + 1)
        ok = True

        item = CItemList("Następna strona [%s]" % page, self.url, self.mode, self.category, '', CItemList.TYPE_CATEGORY, '', page)
        self.currList.append(item)
        return ok
        
    def getHostingTable(self, url):
        vidTab = []
        try:
            from Plugins.Extensions.IPTVPlayer.hosts.hosttvpvod import TvpVod
            vidTab = TvpVod().getVideoLink(object_id)
        except: printExc()
        return vidTab

class IPTVHost(IHost):

    def __init__(self):
        self.host = None
        self.currIndex = -1
        self.listOfprevList = [] 
    
    # return firs available list of item category or video or link
    def getInitList(self):
        self.host = tvp()
        self.currIndex = -1
        self.listOfprevList = [] 
        
        self.host.handleService(self.currIndex)
        convList = self.convertTVPList(self.host.getCurrList())
        
        return RetHost(RetHost.OK, value = convList)
    
    # return List of item from current List
    # for given Index
    # 1 == refresh - force to read data from 
    #                server if possible 
    # server instead of cache 
    def getListForItem(self, Index = 0, refresh = 0, selItem = None):
        self.listOfprevList.append(self.host.getCurrList())
        
        self.currIndex = Index
        self.host.handleService(Index)
        convList = self.convertTVPList(self.host.getCurrList())
        
        
        return RetHost(RetHost.OK, value = convList)
        
    # return prev requested List of item 
    # for given Index
    # 1 == refresh - force to read data from 
    #                server if possible
    def getPrevList(self, refresh = 0):
        if(len(self.listOfprevList) > 0):
            tvpList = self.listOfprevList.pop()
            self.host.setCurrList(tvpList)
            convList = self.convertTVPList(tvpList)
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
        convList = self.convertTVPList(self.host.getCurrList())
        return RetHost(RetHost.OK, value = convList)
        
        
    # return full path to player logo
    def getLogoPath(self):  
        return RetHost(RetHost.OK, value = [ GetLogoDir('tvpinfologo.png') ])
                
    def convertTVPList(self, tvpList):
        hostList = []
        
        for tvpItem in tvpList:
            type = CDisplayListItem.TYPE_UNKNOWN
            if tvpItem.type == CItemList.TYPE_CATEGORY:
                type = CDisplayListItem.TYPE_CATEGORY
            else:
                type = CDisplayListItem.TYPE_VIDEO
 
            hostItem = CDisplayListItem(name = tvpItem.name,
                                        description = tvpItem.description,
                                        type = type, 
                                        urlItems = [],
                                        urlSeparateRequest = 1,
                                        iconimage = tvpItem.iconimage)
            hostList.append(hostItem)
            
        return hostList
        
    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index].type != CItemList.TYPE_VIDEO:
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])

        retlist = []
        urlList = self.host.getHostingTable(self.host.currList[Index].url)
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], 0))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
