# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, ArticleContent, RetHost, CUrlItem
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import CSelOneLink, printDBG, printExc, CSearchHistoryHelper, GetLogoDir, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.libs.groovesharkapi import GroovesharkApi
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import JS_toString, JS_DateValueOf
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config, ConfigInteger, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
from datetime import timedelta
import re
import urllib
import time
import random
try:    import simplejson as json
except: import json
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.grooveshark_premium  = ConfigYesNo(default = False)
config.plugins.iptvplayer.grooveshark_login    = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.grooveshark_password = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.grooveshark_station_fetch_size = ConfigInteger(2, (2,20))
config.plugins.iptvplayer.grooveshark_country_code = ConfigSelection(default = "0", choices = [ ("0", _("based on IP")), ("174", _("Poland")) ]) 


def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry(_("Country (changing may be illegal in your country)"), config.plugins.iptvplayer.grooveshark_country_code))
    optionList.append(getConfigListEntry(_("Number of songs fetched at once for the station"), config.plugins.iptvplayer.grooveshark_station_fetch_size))
    optionList.append(getConfigListEntry(_("Sin in to") + " Grooveshark", config.plugins.iptvplayer.grooveshark_premium))
    if config.plugins.iptvplayer.grooveshark_premium.value:
        optionList.append(getConfigListEntry(_("    Username or Email"), config.plugins.iptvplayer.grooveshark_login))
        optionList.append(getConfigListEntry(_("    Password"), config.plugins.iptvplayer.grooveshark_password))
    return optionList
###################################################

def gettytul():
    return 'Grooveshark'

class GrooveShark(CBaseHostClass):
    MAIN_CAT_TAB = [{'category':'popular_cat',    'title':_('Popular')},
                    {'category':'broadcasts_cat', 'title':_('Broadcasts')},
                    {'category':'stations_cat',   'title':_('Stations')},
                    {'category':'search',         'title':_('Search'), 'search_item':True},
                    {'category':'search_history', 'title':_('Search history')} ]
    POPULAR_TAB = [{'popular_type': 'daily',   'title':_('Daily')},
                   {'popular_type': 'weekly',  'title':_('Weekly')},
                   {'popular_type': 'monthly', 'title':_('Monthly')} ]
    PROFILE_TAB = [{'category':'profile_collection', 'title':_('Collection')},
                   {'category':'profile_favorites',  'title':_('Favorites')},
                   {'category':'profile_playlists',  'title':_('Playlists')},
                   {'category':'profile_following',  'title':_('Following')} ]
    BROTCAST_TAB = [{'category':'broadcast_now_playing', 'title':_('Now playing')},
                    {'category':'broadcast_history',     'title':_('History')} ]
    
    def __init__(self):
        printDBG("GrooveShark.__init__")
        CBaseHostClass.__init__(self, {'history':'GrooveShark.com'})     
        self.api = GroovesharkApi()
        self.initiated = False
        self.loggedIn  = None
        self.url_cache = {'id':0, 'urlTab':[]}
    
    def _getNum(self, v, default=0):
        try: return int(v)
        except:
            try: return float(v)
            except: return default
        
    def _addItem(self, item, cItem):
        if None != item:
            try:
                if 'SongID' in item: params = self. _mapSongItem(item)
                #elif 'SongName' in item: params = self. _mapSongItem(item)
                elif 'PlaylistID' in item: params = self._mapPlaylistItem(item, cItem)
                elif 'AlbumID' in item: params = self._mapAlbumItem(item, cItem)
                elif 'BroadcastID' in item: params = self._mapBcastItem(item, cItem)
                elif 'UserID' in item: params = self._mapProfileItem(item, cItem)
                
                else: params = {}
                if {} != params and params not in self.currList:
                    self.currList.append(params)
                    return True
            except: printExc()
        return False
            
    def _mapProfileItem(self, item, cItem):
        printDBG(">>>> GrooveShark._mapProfileItem")
        retItem = dict(cItem)
        try:
            title = item.get('FName', '') + ' ' + item.get('LName', '')
            icon = self.api.getItemIconUrl(item)
            desc = item.get('t', {}).get('n', '')
            retItem['title']      = self.cleanHtmlStr(title)
            retItem['icon']       = icon
            retItem['desc']       = self.cleanHtmlStr(item.get('DateFavorited', ''))
            retItem['UserID']     = item['UserID']
            retItem['category']   = 'profile'
            retItem['type']       = 'category'
        except: 
            printExc()
            retItem = {}
        return retItem
            
    def _mapBcastItem(self, item, cItem):
        printDBG(">>>> GrooveShark._mapBcastItem")
        retItem = {}
        try:
            if 's' in item and 'ts' in item['s'] and (item['s']['ts'] + 72e4) < JS_DateValueOf():
                printDBG(">>>> GrooveShark._mapBcastItem rejected bcast too old")
                return retItem
            if item.get("owner_subscribed", True):
                retItem.update(cItem)
                title = item.get('n', '')
                icon = self.api.getItemIconUrl(item)
                try: desc = item.get('t', {}).get('n', '')
                except: desc = ''
                retItem['title']      = self.cleanHtmlStr(title)
                retItem['icon']       = icon
                retItem['desc']       = self.cleanHtmlStr(desc)
                retItem['BroadcastID']= item['BroadcastID']
                retItem['category']   = 'broadcast'
                retItem['type']       = 'category'
            else:
                printDBG(">>>> GrooveShark._mapBcastItem rejected bcast owner not subscribed")
        except: 
            printExc()
            retItem = {}
        return retItem
        
    def _mapSongItem(self, item):
        printDBG(">>>> GrooveShark._mapSongItem")
        retItem = {}
        try:
            title = item.get('Name', '')
            if '' == title: title = item.get('SongName', '')
            if ''==title: title = item.get('Name', '')
            if 'ArtistName' in item: title += ' (%s)' % item['ArtistName']
            icon = self.api.getItemIconUrl(item)
            duration = self._getNum(item.get('AvgDuration', 0))
            if 0 == duration: duration = self._getNum(item.get('EstimateDuration', 0))
            desc = item.get('AlbumName', '')
            if "Year" in item: 
                if ''!=desc: desc += ' '
                desc += '%s' % item["Year"]
            if 0 != duration: 
                if '' != desc: desc += ', '
                desc += str(timedelta(seconds=duration))
            retItem['SongID']   = self._getNum(item['SongID'])
            if 'Token' in item: retItem['Token'] = item['Token']
            retItem['title']    = self.cleanHtmlStr(title)
            retItem['desc']     = self.cleanHtmlStr(desc)
            retItem['duration'] = duration
            retItem['icon']     = icon
            retItem['type']     = 'audio'
        except: 
            printExc()
            retItem = {}
        return retItem
        
    def _mapPlaylistItem(self, item, cItem):
        printDBG(">>>> GrooveShark._mapPlaylistItem")
        retItem = dict(cItem)
        try:
            title = item.get('Name', '')
            if 'FName' in item: title += ' (%s)' % item['FName'].strip()
            icon = self.api.getItemIconUrl(item)
            desc = str(item.get('NumSongs', 0))
            if 'LName' in item: desc += ', %s' % item['LName'].strip()
            retItem['title']      = self.cleanHtmlStr(title)
            retItem['icon']       = icon
            retItem['desc']       = self.cleanHtmlStr(desc)
            retItem['PlaylistID'] = self._getNum(item['PlaylistID'])
            retItem['type']       = 'category'
            retItem['category']   = 'playlist'
        except: 
            printExc()
            retItem = {}
        return retItem
        
    def _mapAlbumItem(self, item, cItem):
        printDBG(">>>> GrooveShark._mapAlbumItem")
        retItem = dict(cItem)
        try:
            title = item.get('Name', '')
            if '' == title: title = item.get('AlbumName', '')
            if 'Year' in item: title += ' (%s)' % item['Year'].strip()
            icon = self.api.getItemIconUrl(item)
            # it's seems that API returns wrong value for TrackNum, so do not present it
            #desc = str(item.get('TrackNum', 0)) 
            desc = item.get('ArtistName', '') 
            retItem['title']      = self.cleanHtmlStr(title)
            retItem['icon']       = icon
            retItem['desc']       = self.cleanHtmlStr(desc)
            retItem['AlbumID']    = self._getNum(item['AlbumID'])
            retItem['type']       = 'category'
            retItem['category']   = 'album'
        except: 
            printExc()
            retItem = {}
        return retItem
        
    def doInit(self):
        printDBG("GrooveShark.doInit")
        if not self.initiated:
            self.loggedIn = None
            countryCode = int(config.plugins.iptvplayer.grooveshark_country_code.value)
            self.initiated = self.api.initSession(True, countryCode)
        if not self.initiated:
            message = _("Last error") + ': ' + self.api.getLastApiError().get('message', _('Unknown'))
            self.sessionEx.open(MessageBox, message, type = MessageBox.TYPE_INFO, timeout = 10 )
        else:
            premium  = config.plugins.iptvplayer.grooveshark_premium.value
            if premium and not self.loggedIn and self.initiated:
                login    = config.plugins.iptvplayer.grooveshark_login.value
                password = config.plugins.iptvplayer.grooveshark_password.value
                
                if None == self.loggedIn and premium:
                    self.loggedIn = self.api.authenticateUser(login, password)
                    if False == self.loggedIn:
                        message = _('User [%s] logon failure.') % login
                        message += '\n' + _("Last error") + ': ' + self.api.getLocal('LOGIN_ERROR', _('Unknown')) + ' ' + self.api.getLastApiError().get('message', '')
                        self.sessionEx.open(MessageBox, message, type = MessageBox.TYPE_INFO, timeout = 10 )

    def listsTab(self, tab, cItem):
        printDBG("GrooveShark.listsMainMenu")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            self.addDir(params)
            
    def _listBase(self, cItem, apiHandler, params, key=None):
        sts, data = apiHandler(*params)
        if sts:
            if None!=key: data = data.get(key, [])
            for item in data:
                self._addItem(item, cItem)
        return sts, data

    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("GrooveShark.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        searchPattern = searchPattern.replace(' ', '+')
        self._listBase(cItem, self.api.getResultsFromSearch, (searchPattern, [searchType]), searchType)
        
    def listPopular(self, cItem):
        printDBG("GrooveShark.listPopular cItem[%s]" % cItem)
        self._listBase(cItem, self.api.popularGetSongs, (cItem['popular_type'],), 'Songs')
        
    def listPlaylist(self, cItem):
        printDBG("GrooveShark.listPlaylist cItem[%s]" % cItem)
        self._listBase(cItem, self.api.getPlaylistByID, (cItem['PlaylistID'],), 'Songs')
        
    def listAlbum(self, cItem):
        printDBG("GrooveShark.listAlbum cItem[%s]" % cItem)
        self._listBase(cItem, self.api.albumGetAllSongs, (cItem['AlbumID'],))
        
    def listStation(self, cItem):
        printDBG("GrooveShark.listStation cItem[%s]" % cItem)
        tagID = cItem.get('id', -1)
        if -1 != tagID:
            fetchSize = config.plugins.iptvplayer.grooveshark_station_fetch_size.value
            for item in range(fetchSize):
                sts, data = self.api.startAutoplayTag(tagID)
                if sts and 'nextSong' in data:
                    self._addItem(data['nextSong'], cItem)
            if len(self.getCurrList()): self.addMore({'name':'category', 'category':'more', 'title':_('More')})
        
    def listBroadcasts(self, cItem):
        printDBG("GrooveShark.listBroadcasts cItem[%s]" % cItem)
        genre = cItem.get('tagID', -1)
        if -1 == genre:
            sts, data = self.api.getTopBroadcastsCombined()
        else:
            manateeTag = 'bcast_genre_%s' % genre
            sts, data = self.api.getTopBroadcasts([manateeTag])
            if sts: data = data[manateeTag]
        if sts:
            withIDNum = 0
            for item in data:
                if 'id' in data[item]:
                    withIDNum += 1
                    data[item].update({'BroadcastID':data[item]['id']})
                    self._addItem(data[item], cItem)
            printDBG("listBroadcasts >>>>>>>>> [%s]/[%s]" % (len(data), withIDNum))
        
    def listBroadcast(self, cItem):
        printDBG("GrooveShark.listBroadcast cItem[%s]" % cItem)
        self.listsTab(GrooveShark.BROTCAST_TAB, cItem)
        # add mobile stream
        urlTab = self.getLinksForVideo(cItem)
        if len(urlTab):
            params = dict(cItem)
            params.update({'title': params['title'] + _(' - mobile broadcast url')})
            self.addAudio(params)
            
    def _listBroadcastBase(self, cItem, type='active'):
        sts, data = self.api.broadcastStatusPoll(cItem['BroadcastID'])
        if sts:
            printDBG("listBroadcasts >>>>>>>>> data[%s]" % (data))
            if 'active' == type:
                for key in ['activeSong', 'nextSong']:
                    self._addItem(data[key], cItem)
                if len(self.getCurrList()): self.addMore({'name':'category', 'category':'more', 'title':_('More')})
            elif 'history' == type:
                for item in data['history']:
                    self._addItem(item, cItem)
        
    def listBroadcastNowPlaying(self, cItem):
        printDBG("GrooveShark.listBroadcastNowPlaying cItem[%s]" % cItem)
        self._listBroadcastBase(cItem,'active')
        # TODO add new item update (...) similar to Next Page, but without 
        # cleaning current list but only adding new items to it
        
    def listBroadcastHistory(self, cItem):
        printDBG("GrooveShark.listBroadcastHistory cItem[%s]" % cItem)
        self._listBroadcastBase(cItem,'history')
    
    def getLinksForVideo(self, cItem, baseName='grooveshark.com '):
        printDBG("GrooveShark.getLinksForVideo SongID[%s], BroadcastID[%s]" % (cItem.get('SongID', ''), cItem.get('BroadcastID', '')) )
        if 'SongID' in cItem: cache_key = cItem['SongID']
        elif 'Token' in cItem: cache_key = cItem['Token']
        elif 'BroadcastID' in cItem: cache_key = cItem['BroadcastID']
        else: return
        
        if self.url_cache['id'] ==  cache_key and 0 < len(self.url_cache['urlTab']):
            return self.url_cache['urlTab']
        else: self.url_cache = {'id':0, 'urlTab':[]}
        
        urlTab = []
        # FROM SongID
        if 'SongID' in cItem:
            url = self.api.getSongUrl(cItem['SongID'], False)
            name = baseName + _('PC')
            if '' == url: 
                url   = self.api.getSongUrl(cItem['SongID'], True)
                name = baseName + _('mobile')
        # FROM file Token
        #elif 'Token' in cItem:
        #    url = self.api.getBroadcastUrl(cItem['Token'])
        #    name = baseName + _('PC')
        # FROM mobile brodcast stream
        elif 'BroadcastID' in cItem:
            url = self.api.getBroadcastUrl(cItem['BroadcastID'])
            name = baseName + _('mobile broadcast')
        
        if '' != url: 
            urlTab.append({'name':name, 'url':url})
            self.url_cache = {'id':cache_key, 'urlTab':urlTab}
        return urlTab
    
    def listProfileCollection(self, cItem):
        printDBG("GrooveShark.listProfileCollection cItem[%s]" % cItem)
        # "method":"userGetSongsInLibrary","parameters":{"UserID":8475894,"page":0}}
        page   = cItem.get('page', 0)
        UserID = cItem['UserID']
        sts,data = self._listBase(cItem, self.api.userGetSongsInLibrary, (UserID,page), 'Songs')
        # TODO check and add nextPage item if needed
        
    def listProfileFavorites(self, cItem):
        printDBG("GrooveShark.listProfileFavorites cItem[%s]" % cItem)
        # "method":"getFavorites","parameters":{"UserID":8475894,"ofWhat":"Songs"}}
        UserID = cItem['UserID']
        sts,data = self._listBase(cItem, self.api.getFavorites, ('Songs', UserID))
        
    def listProfilePlaylists(self, cItem):
        printDBG("GrooveShark.listProfilePlaylists cItem[%s]" % cItem)
        # "method":"userGetPlaylists","parameters":{"UserID":8475894}}
        UserID = cItem['UserID']
        sts,data = self._listBase(cItem, self.api.userGetPlaylists, (UserID,), 'Playlists')
        
    def listProfileFollowing(self, cItem):
        printDBG("GrooveShark.listProfileFollowing cItem[%s]" % cItem)
        # "method":"getFavorites","parameters":{"UserID":8475894,"ofWhat":"Users"}}
        UserID = cItem['UserID']
        sts,data = self._listBase(cItem, self.api.getFavorites, ('Users', UserID))
    
    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('GrooveShark.handleService start')
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", None)
        category = self.currItem.get("category", '')
        printDBG( "GrooveShark.handleService: ---------> name[%s], category[%s] " % (name, category) )
        searchPattern = self.currItem.get("search_pattern", searchPattern)
        self.currList = [] 
        
        self.doInit()
        
        if None == name:
            loginData = self.api.getLoginData()
            if 'userID' in loginData:
                self.addDir({'name':'category', 'category':'profile', 'UserID':loginData['userID'], 'title':_('Profile')})
            self.listsTab(GrooveShark.MAIN_CAT_TAB, {'name':'category'})
    #PROFILE
        elif 'profile' == category:
            self.listsTab(GrooveShark.PROFILE_TAB, self.currItem)
    #PROFILE COLLECTION
        elif 'profile_collection' == category:
            self.listProfileCollection(self.currItem)
    #PROFILE FAVORITES
        elif 'profile_favorites' == category:
            self.listProfileFavorites(self.currItem)
    #PROFILE PLAYLISTS
        elif 'profile_playlists' == category:
            self.listProfilePlaylists(self.currItem)
    #PROFILE FOLLOWING
        elif 'profile_following' == category:
            self.listProfileFollowing(self.currItem)
    #POPULAT CATEGORIES
        elif 'popular_cat' == category:
            self.listsTab(GrooveShark.POPULAR_TAB, {'name':'category', 'category':'popular'})
    #POPULAR
        elif 'popular' == category:
            self.listPopular(self.currItem)
    #STATIONS CATEGORIES
        elif 'stations_cat' == category:
            cItem = {'name':'category', 'category':'station'}
            tmpTab = self.api.getStationsTags()
            self.listsTab(tmpTab, cItem)
    #STATION
        elif 'station' == category:
            self.listStation(self.currItem)
    #BRODCASTS CATEGORIES
        elif 'broadcasts_cat' == category:
            cItem = {'name':'category', 'category':'broadcasts', 'title':'All'}
            tmpTab = self.api.getBroadcastsTags()
            if len(tmpTab): self.addDir(cItem)
            self.listsTab(tmpTab, cItem)
    #BRODCASTS
        elif 'broadcasts' == category:
            self.listBroadcasts(self.currItem)
    #BRODCAST
        elif 'broadcast' == category:
            self.listBroadcast(self.currItem)
    #BRODCAST NOW PLAYING
        elif 'broadcast_now_playing' == category:
            self.listBroadcastNowPlaying(self.currItem)
    #BRODCAST HISTORY
        elif 'broadcast_history' == category:
            self.listBroadcastHistory(self.currItem)
    #PLAYLIST
        elif 'playlist' == category:
            self.listPlaylist(self.currItem)
    #PLAYLIST
        elif 'album' == category:
            self.listAlbum(self.currItem)
    #WYSZUKAJ
        elif category in ["search", "search_next_page"]:
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category'}) 
            self.listSearchResult(cItem, searchPattern, searchType)
    #HISTORIA WYSZUKIWANIA
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, GrooveShark(), True)

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('groovesharklogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        listLen = len(self.host.currList)
        if listLen < Index and listLen > 0:
            printDBG( "ERROR getLinksForVideo - current list is to short len: %d, Index: %d" % (listLen, Index) )
            return RetHost(RetHost.ERROR, value = [])
        
        if self.host.currList[Index]["type"] != 'audio':
            printDBG( "ERROR getLinksForVideo - current item has wrong type" )
            return RetHost(RetHost.ERROR, value = [])

        retlist = []
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            need_resolve = 0
            name = self.host.getStr( item["name"] )
            url  = self.host.getStr( item["url"] )
            retlist.append(CUrlItem(name, url, need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo

    def convertList(self, cList):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        searchTypesOptions.append((_("Songs"), "Songs"))
        searchTypesOptions.append((_("Playlists"), "Playlists"))
        searchTypesOptions.append((_("Albums"), "Albums"))
    
        for cItem in cList:
            hostLinks = []
            type = CDisplayListItem.TYPE_UNKNOWN
            possibleTypesOfSearch = None

            if 'category' == cItem['type']:
                if cItem.get('search_item', False):
                    type = CDisplayListItem.TYPE_SEARCH
                    possibleTypesOfSearch = searchTypesOptions
                else:
                    type = CDisplayListItem.TYPE_CATEGORY
            elif 'more' == cItem['type']:
                type = CDisplayListItem.TYPE_MORE
            elif 'audio' == cItem['type']:
                type = CDisplayListItem.TYPE_AUDIO
                url = cItem.get('url', '')
                if '' != url:
                    hostLinks.append(CUrlItem("Link", url, 1))
                
            title       =  self.host.getStr( cItem.get('title', '') )
            description =  self.host.getStr( cItem.get('desc', '') ).strip()
            icon        =  self.host.getStr( cItem.get('icon', '') )
            
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

    def getSearchItemInx(self):
        try:
            list = self.host.getCurrList()
            for i in range( len(list) ):
                if list[i]['category'] == 'search':
                    return i
        except:
            printDBG('getSearchItemInx EXCEPTION')
            return -1

    def setSearchPattern(self):
        try:
            list = self.host.getCurrList()
            if 'history' == list[self.currIndex]['name']:
                pattern = list[self.currIndex]['title']
                search_type = list[self.currIndex]['search_type']
                self.host.history.addHistoryItem( pattern, search_type)
                self.searchPattern = pattern
                self.searchType = search_type
        except:
            printDBG('setSearchPattern EXCEPTION')
            self.searchPattern = ''
            self.searchType = ''
        return
