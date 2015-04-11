# -*- coding: utf-8 -*-

"""
Implementation of the GroovesharkApi
@author samsamsam@o2.pl
@version 0.1

All code on this file is copyrighted, and any part of it cannot be used without explicit permission by the author.
Questions should be sent at samsamsam@o2.pl.
"""


###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetCookieDir
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import hex_md5, JS_toString, JS_DateValueOf
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html, compat_parse_qs
from Plugins.Extensions.IPTVPlayer.libs.crypto.hash.sha1Hash import SHA1
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config
from binascii import hexlify
import math 
import random
import re
try:    import simplejson as json
except: import json

###################################################

class GroovesharkApi:
    HTTP_HEADER      = {'User-Agent':'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10',
                        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' }
    JSON_HTTP_HEADER = {'User-Agent':'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10',
                        'Accept':'application/json', 'Referer':'http://html5.grooveshark.com/', 'Pragma':'no-cache', 'Cache-Control':'no-cache'}
    MAINURL     = 'http://html5.grooveshark.com/'
    SSH_MAINURL = 'https://html5.grooveshark.com/'
    
    REQUEST_DATE_FORMAT  = {"header":{"client":"mobileshark","clientRevision":"20120830","privacy":0,"country":{},"uuid":"","session":""},"method":"","parameters":{}}
    
    STS_INVALID_CLIENT  = 1024
    STS_RATE_LIMITED    = 512
    STS_INVALID_TOKEN   = 256
    STS_INVALID_SESSION = 16
    STS_MAINTENANCE     = 10
    STS_MUST_BE_LOGGED_IN = 8
    STS_HTTP_TIMEOUT      = 6
    STS_STS_PARSE_ERROR   = 4
    STS_HTTP_ERROR        = 2
    STS_EMPTY_RESULT      = -256
    
    ICON_URL = {
        'albums_picSD':     "http://images.gs-cdn.net/static/albums/40_",
        'albums_picHD':     "http://images.gs-cdn.net/static/albums/80_",
        'albums_picHD2':    "http://images.gs-cdn.net/static/albums/120_",
        'albums_pic500':    "http://images.gs-cdn.net/static/albums/500_",
        'playlists_picHD':  "http://images.gs-cdn.net/static/playlists/70_",
        'users_picSD':      "http://images.gs-cdn.net/static/users/40_",
        'users_picHD':      "http://images.gs-cdn.net/static/users/80_",
        'artists_picSD':    "http://images.gs-cdn.net/static/artists/80_",
        'artists_picHD':    "http://images.gs-cdn.net/static/artists/120_",
        'broadcasts_picSD': "http://images.gs-cdn.net/static/broadcasts/80_",
        'broadcasts_picHD': "http://images.gs-cdn.net/static/broadcasts/120_"
    }
    
    URLS_MAP = {'getCommunicationToken'     : SSH_MAINURL +'more.php?getCommunicationToken', 
                'authenticateUser'          : SSH_MAINURL +'more.php?authenticateUser'
               }
    '''
    getCommunicationToken
    authenticateUser
    getFavorites
    userGetSongsInLibrary
    getUserRecentListens
    getUsersActiveBroadcast
    userGetPlaylists
    getTopBroadcastsCombined
    getTopBroadcasts
    getUserByID
    getPlaylistByID
    getAlbumByID
    startAutoplayTag
    getStreamKeyFromSongIDEx
    markSongDownloadedEx
    broadcastStatusPoll
    getMobileBroadcastURL
    popularGetSongs
    getResultsFromSearch
    initiateSession
    albumGetAllSongs
    '''
    def __init__(self):
        printDBG("GroovesharkApi.__init__")
        self.cm = common()
        self.cm.HEADER   = GroovesharkApi.JSON_HTTP_HEADER
        self.headerParams = {'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': GetCookieDir('Grooveshark.com'), 'raw_post_data': True}
        
        self.requestMacro = {}
        self.config = {}
        self.locales = {}
        self.loginData = {}
        self.secretKey = ""
        self.revToken = 'gooeyFlubber'
        self.currentToken   = ''
        self.lastRandomizer = ''
        self.tokenExpires = 0
        self.lastApiError = {'code':0, 'message':''}
        
        self.cache = {}
        
    def _randomize(self):
        save = 0
        while save < 100:
            save += 1
            e = ""
            t = 0
            while t < 6:
                t += 1
                e +=  JS_toString( int(math.floor(random.random() * 16)), 16)
            if e != self.lastRandomizer:
                return e
            
    def _getTmpToken(self, method):
        self.lastRandomizer = self._randomize()
        p = ":".join([method, self.currentToken, self.revToken, self.lastRandomizer])
        obj = SHA1()
        obj.update(p)
        p = hexlify(obj.digest())
        token = self.lastRandomizer + p
        #printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        #printDBG(token)
        #printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        return token
                    
    def _UUID(self):
        uuidFormat = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx"
        def _tmpFun(e):
            t = int(random.random() * 16)
            if e.group(1) == 'x':
                n = t
            else:
                n = t & 3 | 8
            return JS_toString(n, 16)
        return re.sub("([xy])", _tmpFun, uuidFormat).upper()
        
    def _callRemote(self, method, params, withToken=True, retry=0):
        printDBG('GroovesharkApi._callRemote method[%r]' % method)
        postData = dict(self.requestMacro)
        if withToken:
            postData['header']['token'] = self._getTmpToken(method)
        postData['method']     = method
        postData['parameters'] = params
        postData = json.dumps(postData, sort_keys=False, separators=(',', ':'))
        url = GroovesharkApi.URLS_MAP.get(method, GroovesharkApi.MAINURL +'more.php?' + method)
        sts,data = self.cm.getPage(url, self.headerParams, postData)
        printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        printDBG("                        GroovesharkApi._callRemote" + method)
        printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        printDBG(data)
        printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        try:
            data  = json.loads(data)
            if 'header' in data:
                if 'fault' in data:
                    printDBG("GroovesharkApi._callRemote ERROR: fault[%r]" % data['fault'])
                    if isinstance(data['fault'], dict): 
                        self.lastApiError = data['fault']
                        if 3 > retry:
                            sts = True 
                            if self.STS_INVALID_TOKEN == data['fault'].get('code'):
                                sts = self.getCommunicationToken(True)
                            if sts: return self._callRemote(method, params, True, retry+1)
                elif 'result' in data and False != data["result"]:
                    data = data["result"]
                    return sts,data
                else:
                    printDBG("GroovesharkApi._callRemote ERROR: no result or fault in JSON")
            else:
                printDBG("GroovesharkApi._callRemote ERROR: no no header in JSON")
        except:
            printExc()
        printDBG('GroovesharkApi._callRemote ERROR: invalid result')    
        sts = False
        data = {}
        return sts,data
        
    def _getStr(self, v, default=''):
        if None == v: return default
        elif type(v) == type(u''): return v.encode('utf-8')
        elif type(v) == type(''): return v
        
    def _cleanHtmlStr(self, str):
        str = str.replace('<', ' <').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        return self.cm.ph.removeDoubles(clean_html(str), ' ').strip()
        
    def getLocal(self, id, default):
        message = self._getStr(self.locales.get(id, default))
        if len(message): return clean_html(message)
        else: return default
        
    def getLoginData(self):
        return self.loginData
        
    def getLastApiError(self):
        self.lastApiError['message'] = clean_html(self._getStr(self.lastApiError['message'], ''))
        return self.lastApiError
        
    def getItemIconUrl(self, item):
        if 'SongID' in item or 'AlbumID' in item: iconSelOrder=[['CoverArtFilename', 'albums_picHD'], ['ArtistCoverArtFilename', 'artists_picHD'], ['Picture', 'playlists_picHD']]
        elif 'PlaylistID' in item: iconSelOrder=[['Picture', 'playlists_picHD'], ['CoverArtFilename', 'albums_picHD'], ['ArtistCoverArtFilename', 'artists_picHD']]
        elif 'BroadcastID' in item: iconSelOrder=[['i', 'broadcasts_picHD']]
        elif 'UserID' in item: iconSelOrder=[['Picture', 'users_picHD']]
        for type in iconSelOrder:
            url = self._getStr(item.get(type[0], ''))
            if '' != url: return GroovesharkApi.ICON_URL[type[1]] + url
        return GroovesharkApi.ICON_URL['albums_picHD'] + 'album.png'
        
    def getSongUrl(self, songID, mobile=False, XDomainRequest=True):
        '''
        "FileID": "25810000",
        "uSecs": "257280000",
        "FileToken": "2OFC1p",
        "ts": 1417139273,
        "isMobile": true,
        "SongID": 24704827,
        "streamKey": "d8ef3f6a20293f81a6416c96f7b9c2201f3d2539_5477db51_178f73b_189d450_162c29638_36_0",
        "Expires": 1417141073,
        "streamServerID": 32768,
        "ip": "stream196a-he.grooveshark.com"
        http://stream126a-he.grooveshark.com/stream.php?streamKey=b64855dc2ae22265523888adc375c5ac22fdcffd_5477db42_178f73b_189d450_162c29638_36_0
        '''
        sts,data = self.getStreamKeyFromSongIDEx(songID, mobile)
        if sts:
            try:
                t = data['ip']
                n = data['streamKey']
                r = "http://" + t + "/stream.php?streamKey=" + n;
                if XDomainRequest:
                    r = r.replace(".php", ".mp3")
                return self._getStr(r)
            except: printExc()
        return ''
        
    def getBroadcastUrl(self, BroadcastID):
        '''
        "broadcastID": "546ec5ed5d70676d408b4567",
        "url": "http:\/\/capn.grooveshark.com:80\/cast\/546ec5ed5d70676d408b4567",
        "key": "40bb5cb5769876f3a3a9652e22e21c57de610fde_f3f0592280671db92a8a120f1ad118a3_162c29638_54794767"
        '''
        sts,data = self.getMobileBroadcastURL(BroadcastID)
        if sts:
            try:
                t = data['url']
                n = data['key']
                if '' != t and '' != n:
                    r =  '%s?sid=%s' % (t, n)
                    return self._getStr(r)
            except: printExc()
        return ''
        
    def getBroadcastsTags(self, refresh=False):
        retData = self.cache.get('BroadcastsTag', [])
        if refresh or 0==len(retData):
            sts,data = self.cm.getPage(GroovesharkApi.MAINURL + '/build/app.min.js', self.headerParams)
            if sts:
                data = self.cm.ph.getSearchGroups(data, "e.GS.models.topTags[^=]*?=[^(]*?\(([^)]+?)\)")[0].strip()
                try:
                    data = re.sub('([^"^,^[^{]+?):', lambda x: '"%s":' % x.group(1), data)
                    data = '{"result":%s}' % data
                    #printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> data[%s]" % data)
                    data = json.loads(data)['result']
                    if len(data) and isinstance(data, list): 
                        retData = data
                        self.cache['BroadcastsTag'] = retData
                except: printExc()
        return retData
        
    def getStationsTags(self, refresh=False):
        retData = self.cache.get('StationsTags', [])
        if refresh or 0==len(retData):
            sts,data = self.cm.getPage(GroovesharkApi.MAINURL + '/build/app.min.js', self.headerParams)
            if sts: 
                data = self.cm.ph.getSearchGroups(data, "i[^=]*?=[ ]*?new[ ]*?r\(([^)]+?)\)")[0].strip()
                try:
                    data = re.sub('([^"^,^[^{]+?):', lambda x: '"%s":' % x.group(1), data)
                    data = '{"result":%s}' % data
                    #printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> data[%s]" % data)
                    data = json.loads(data)['result']
                    if len(data) and isinstance(data, list): 
                        retData = data
                        for item in retData: item.update({'title':self.getLocal(item['locale'], item['title'])})
                        self.cache['StationsTags'] = retData
                except: printExc()
        return retData
    
    def initSession(self, force=False, customCountry=0):
        printDBG('GroovesharkApi.initSession force[%r]' % force)
        headerParams = dict(self.headerParams)
        headerParams['load_cookie'] = False
        headerParams['header'] = GroovesharkApi.HTTP_HEADER
        sts, data = self.cm.getPage(GroovesharkApi.MAINURL, headerParams)
        if sts:
            content = self.cm.ph.getDataBeetwenMarkers(data, '<div id="content">', '</div>', False)[1]
            data    = self.cm.ph.getDataBeetwenMarkers(data, "var GS = {", "</script>", False)[1]
            config  = self.cm.ph.getSearchGroups(data, "GS.config[^=]*?=[ ]*?([^;]+?);")[0].strip()
            locales = self.cm.ph.getSearchGroups(data, "GS.locales[^=]*?=[ ]*?(\{.+?\});")[0].strip()
            try:
                try:    locales = json.loads(locales)
                except: locales = {"HOME":"Home","POPULAR":"Popular","STATIONS":"Stations","QUEUE":"Queue","SIGN_IN":"Sign in","SIGN_UP":"Sign up","SIGN_IN_SHORT":"Sign in","SIGN_OUT":"Sign out","DOWNLOAD_APP":"Download our app!","ABOUT":"About Grooveshark","PRIVACY":"Privacy Policy","COPYRIGHT":"Copyright","AUDIO_AD_MSG":"Your music will begin soon","GO_ADFREE":"Go Ad-Free","CLOSE_AD":"Close Ad","SKIP_AD":"Skip Ad","ADFREE_COPY":"Enjoy unlimited ad-free streaming with a premium Grooveshark subscription. Visit http://grooveshark.com/upgrade on your computer's web browser to upgrade.","EXPIRED_SITE_MSG":"There was an issue loading the site. Please try refreshing.","STATION_FAILED_MSG":"Something went wrong, please try another station.","QUEUE_DEGRADED_MSG":"Adding {number} songs to your queue may degrade performance over time.","STATION_CLEAR_MSG":"You have music in your queue. Would you like to clear those songs and start {station}?","STATION_LOADING_MSG":"Loading {station} Radio","IOS_PIN_TITLE":"Grooveshark on your homescreen","IOS_PIN_MSG":"Want quick and easy access to the Grooveshark HTML5 webapp? Touch below to pin it to your homescreen. Tap anywhere to close this notification.","GET_APP":"Looking for the Native {platform} App?","GET_IT_HERE":"Get it here","NUM_IN_QUEUE_SINGLE":"{number} song in Queue","NUM_IN_QUEUE_MULTI":"{number} songs in Queue","ADD_TO_QUEUE_SINGLE":"{number} song added to Queue","ADD_TO_QUEUE_MULTI":"{number} songs added to Queue","PLAY_NOW":"Play Now","BACK":"Back","DONE":"Done","ALL":"All","LOADING":"Loading...","RELEASE_TO_LOAD":"Release to load more","SHOW_MORE_SONGS":"Show more songs","SHOW_MORE_ALBUMS":"Show more albums","SHOW_MORE_PLAYLISTS":"Show more playlists","SEE_ALL_STATIONS":"See all stations","NUM_MORE":"{number} more","PLAY_NUM":"Play ({number})","SORT":"Sort","PROFILE":"Profile","NEW_USER":"New User","COLLECTION":"Collection","COLLECTION_EMPTY_OTHER":"hasn't collected any songs.","COLLECTION_EMPTY_SELF":"You haven't collected any songs.","FAVORITES":"Favorites","FAVORITES_EMPTY_OTHER":"hasn't favorited any songs.","FAVORITES_EMPTY_SELF":"You haven't favorited any songs.","PLAYLISTS":"Playlists","PLAYLISTS_EMPTY_OTHER":"hasn’t created any playlists yet","PLAYLISTS_EMPTY_SELF":"Playlists are awesome","PLAYLISTS_EMPTY_DESC_SELF":"You should make one, and share it with your friends. Open Grooveshark.com on your computer to create a playlist.","EMPTY_PLAYLIST_SELF":"Add songs to your playlist","EMPTY_PLAYLIST_DESC_SELF":"A full playlist is much more fun. Open Grooveshark.com on your computer to add songs to a playlist.","EMPTY_PLAYLIST_OTHER":"Looks like this playlist is still being worked on","EMPTY_PLAYLIST_DESC_OTHER":"There are no songs in this playlist.","UNFOLLOW":"Unfollow","FOLLOW":"Follow","FOLLOWING":"Following","FOLLOWING_EMPTY_OTHER":"isn't following anybody.","FOLLOWING_EMPTY_SELF":"You aren't following anybody.","RECENT_LISTENS":"Recent Listens","SEARCH_FOR_MUSIC":"Search for music","SONGS":"Songs","ALBUMS":"Albums","NO_SONGS_FOUND":"No songs found","NO_ALBUMS_FOUND":"No albums found","NO_PLAYLISTS_FOUND":"No playlists found","LOGIN_HEADER":"Sign in to Grooveshark","LOGIN_ERROR":"Oh no! Wrong username/password combination.","LOGIN_FORGOT":"Forgot your password?","LOGIN_SUBMIT":"Sign in!","RESET_PW_TITLE":"Reset Your Password","RESET_PW_SPINNER":"Requesting password reset...","RESET_PW_INVALID":"Passwords must match and be between 5 and 32 characters long.","RESET_PW_ERROR":"Either your password reset code is not valid, or it does not match the user provided.","RESET_PW_SUBMIT":"Submit","NEW_PASSWORD":"New Password","CONFIRM_PASSWORD":"Confirm Password","USERNAME_OR_EMAIL":"Username or Email","PASSWORD":"Password","FORGOT_PW_MSG":"Don't worry, we'll send an email with instructions to access your account.","FORGOT_PW_LOGIN":"Unless you remember?","FORGOT_PW_SUCCESS":"An email has been sent to your email address with login instructions.","FORGOT_PW_SUBMIT":"Reset password","EMAIL":"Email","DISPLAY_NAME":"User Name","VOTE_UP":"I Like This Song","VOTE_DOWN":"Skip It","CONFIRM_CLEAR_QUEUE":"Are you sure you want to empty your Current Songs?","CONFIRM_LEAVE_BROADCAST":"This will remove you from your current Broadcast. Do you want to continue?","NOW_PLAYING":"Now Playing","LOADING_SONG":"Loading song...","LOADING_ALBUM":"Loading album...","LOADING_ALBUMS":"Loading albums...","LOADING_PLAYLIST":"Loading playlist...","LOADING_PLAYLISTS":"Loading playlists...","SEARCHING_FOR":"Searching for {query}","LOGGING_IN":"Logging in...","FORGOT_PW_TITLE":"Forgot Password?","SIGNUP_TITLE":"Create Account","FORGOT_PW_SPINNER":"Requesting password reset...","LOADING_FOLLOWING":"Loading following list...","SORT_POPULARITY":"Popularity","SORT_SONG":"Song Title","SORT_ALBUM":"Album Name","SORT_ARTIST":"Artist Name","SORT_TRACK":"Track Number","SORT_DEFAULT":"Default Order","SORT_DATE":"Date Added","ALL_GENRES":"All Genres","SHARE":"Share","NOW_BROADCASTING":"Now Broadcasting:","NAVIGATION":"Navigation","MULTI_GENRE":"Multi-Genre","BROADCAST_JOIN":"Join Broadcast","TOP_BROADCASTS":"Top Broadcasts","NO_BROADCASTS_TITLE":"No active Broadcasts for this genre!","NO_BROADCASTS_DESC":"Try picking another genre.","BROADCAST_NOW_PLAYING":"Now Playing","BROADCAST_NOW_PLAYING_LIVE":"Live Broadcast by {user}","BROADCAST_NOW_PLAYING_NONE_TITLE":"No song is currently playing.","BROADCAST_NOW_PLAYING_NONE_DESC":"View other broadcasts.","BROADCAST_HISTORY":"History","BROADCAST_NO_HISTORY_TITLE":"No songs have played.","BROADCAST_NO_HISTORY_DESC":"Check back after a song has played","BROADCAST_LEAVE":"Leave","BROADCAST_PLAY":"Play","BROADCAST_PLAYS":"Plays","BROADCAST_LISTENER":"Listener","BROADCAST_LISTENERS":"Listeners","BROADCAST_RECONNECT":"It appears your connection status has changed. Would you like to attempt a reconnect?","BROADCAST_BYLINE":"by","SEE_MORE_BROADCASTS":"See more broadcasts","BROADCASTS":"Broadcasts","BROADCAST":"Broadcast","ST_INDIE":"Indie","ST_ELECTRONICA":"Electronica","ST_CLASSICAL":"Classical","ST_POP":"Pop","ST_RAP":"Rap","ST_COUNTRY":"Country","ST_ALTERNATIVE":"Alternative","ST_HIP_HOP":"Hip Hop","ST_CLASSIC_ROCK":"Classic Rock","ST_AMBIENT":"Ambient","ST_PUNK":"Punk","ST_90S_ALT_ROCK":"90's Alt Rock","ST_BLUES":"Blues","ST_ROCK":"Rock","ST_JAZZ":"Jazz","ST_RNB":"R&B","ST_FOLK":"Folk","ST_DUBSTEP":"Dubstep","ST_80S":"80's","ST_TRANCE":"Trance","ST_BLUEGRASS":"Bluegrass","ST_REGGAE":"Reggae","ST_METAL":"Metal","ST_OLDIES":"Oldies","ST_EXPERIMENTAL":"Experimental","ST_LATIN":"Latin","CONFIRM_PW":"Retype Password","SIGNUP_SUBMIT":"Sign up!","LOGIN_FROM_SIGNUP":"Already registered? Sign in.","NO_ACCOUNT":"No account yet?","SIGNUP_FROM_LOGIN":"Sign up for free.","TOS_AGREE":"By signing up you agree to the {link}","TOS":"Terms of Service","DESCRIPTION":"Description","AMOUNT":"Amount:","CONFIRM":"Confirm","CONTINUE":"Continue","REMOVE":"Remove","CANCEL":"Cancel","TAX":"Tax","TOTAL":"Total","SUPPORT":"Support","CREDIT_CARD":"Credit Card","PAYPAL":"PayPal","REDEEM_CODE":"Redeem Code","CARD_NUMBER":"Card Number","SECURITY_CODE":"Security Code","EXPIRATION_DATE":"Expiration Date","ENTER_REDEEM_CODE":"Enter your Grooveshark code into the box below to redeem:","BILLING_INFORMATION":"Billing Information","SUBSCRIPTION_RECURRING_COPY":"Subscription Recurring","GROOVESHARK_ANYWHERE":"Grooveshark VIP","GROOVESHARK_ANYWHERE_RECURRING":"Grooveshark VIP (Recurring)","GROOVESHARK_PAYMENTS":"Grooveshark Payments","GO_TO_ELLIPSIS":"Go to...","UPGRADE_NOW":"Upgrade Now","PAYMENTS_MUST_SIGN_IN":"Please login or sign up to upgrade to a premium Grooveshark account.","PAYMENTS_RECURRING_PARAGRAPH_1":"Your Grooveshark VIP Subscription is already recurring.","PAYMENTS_RECURRING_PARAGRAPH_2":"If you want to remove this subscription click below.","PAYMENTS_COMPLETE_PARAGRAPH_1":"You've just joined one of the most passionate groups of music lovers on the web, and helped us make Grooveshark an even better place for all of our sharks around the globe.","PAYMENTS_COMPLETE_PARAGRAPH_2":"You're a part of one of the most passionate groups of music lovers on the web, and you've helped us make Grooveshark an even better place for all of our sharks around the globe.","PAYMENTS_COMPLETE_PARAGRAPH_3":"Welcome -- and enjoy.","PAYMENTS_ERROR_REMOVE_RECURRING":"There was an error removing the recurring subscription.","LB_SIGNUP_LOGIN_DONT_HAVE_ACCOUNT":"No account? <a class=\"open-signup\">Sign up!</a>","VIP_ERROR_CARD_NUMBER":"Please ensure your credit card number is correct and try again.","VIP_ERROR_CVD":"Please ensure your security code is correct and try again.","VIP_ERROR_DATE":"Please ensure your expiration date is correct and try again.","ERROR_REDEEM_CODE_INVALID":"The code you entered was not found in our system. Please try again or contact support.","ERROR_REDEEM_CODE_TOO_MUCH":"The code you entered has been used too many times.","ERROR_REDEEM_FAILED":"We ran into a problem while redeeming that code. Please try again.","ERROR_REDEEM_CANCEL_REQUIRED":"In order to redeem your code, you must stop your recurring payments.","ERROR_EXTEND_CANCEL_REQUIRED":"In order to extend your subscription, you must stop your recurring payments.","ERROR_REDEEM_CODE_VERIFY_FAILED":"We ran into a problem while verifying that code. Please try again.","VIP_ERROR_INVALID":"Looks like there was a problem charging your credit card. Please check with your bank or contact support.","PAYPAL_INIT_ERROR_UNKNOWN":"Something went wrong while generating a PayPal transaction. Please try again.","HEADER_THANK_YOU":"Thank You!","IS_RECURRING":"Recurring?","FREE_MONTHS_ALT_SINGLE_LINE":"12 months for the price of 10!","SELL_MONTH_SUB_ALT":"Great low monthly price!","PRICE_PER_MONTH":"${price} / month (USD)","PRICE_PER_YEAR":"${price} / year (USD)","MONTHS":"January,February,March,April,May,June,July,August,September,October,November,December","DAY":"Day","MONTH":"Month","YEAR":"Year","YEAR_PLURAL":"Years","MONTH_PLURAL":"Months","OLDER_13":"You need to be at least 13 years old to sign up","REQUIRED_FIELD":"{fieldName} is a required field","PW_DONT_MATCH":"Passwords do not match","PW_LENGTH_ERR":"Please enter a password between 5 and 32 characters long","EMAIL_TAKEN":"Email already taken","USERNAME_TAKEN":"Username already taken","PREMIUM_REQUIRED":"You must have a Grooveshark VIP account to use this version of Grooveshark.","NO_MP3_SUPPORT":"It looks like your current browser doesn't support HTML5 audio and/or mp3 playback. If you have flash, you can use the full version of Grooveshark, or you can upgrade to a browser that supports HTML5 audio and MP3 playback.","UPGRADE":"Upgrade","CLOSE":"Close","PAYMENTS_BILLING":"Billing","SUBSCRIPTION":"Subscription","SUBSCRIBE":"Subscribe","ON_SALE":"On sale! Normally ${price}/month","SUPPORT_THANKS":"Thank you for your support","EXTEND_SUBSCRIPTION":"Extend Subscription","CANCEL_RECURRING":"Cancel Recurring","UPDATE_RECURRING":"Update Credit Card","CONTACT_BILLING":"Contact Billing Support","GET_GROOVESHARK_ANYWHERE":"Get Grooveshark VIP","ANYWHERE_PERK_1":"Unlimited ad-free streaming","ANYWHERE_PERK_2":"Android app &amp; jailbroken iOS app with <strong>continuous streaming</strong> and <strong>offline playback</strong>","ANYWHERE_PERK_3":"Extended space in your library","ANYWHERE_PERK_4":"Desktop app","MONTH_PRICE":"${price}/month","OR_YEAR_PRICE":"or ${price} a year (USD)","SUBSCRIPTION_ENDS_ON":"Your ${price}/{period} subscription is set to end on <strong>{date}</strong>.","SUBSCRIPTION_RENEWS_ON":"Your ${price}/{period} subscription is set to renew on <strong>{date}</strong>."}
                self.locales = locales
                if 0 < customCountry:
                    self.config = {"country": {"ID":customCountry,"CC1":0,"CC2":0,"CC3":0,"CC4":0,"DMA":0,"IPR":0}}
                else: 
                    self.config = json.loads(config)
                uuid = self._UUID()
                if 'sessionID' not in self.config:
                    self.config['sessionID'] = hex_md5(uuid)
                self.secretKey = hex_md5(self.config["sessionID"])
                self.requestMacro = dict(GroovesharkApi.REQUEST_DATE_FORMAT)
                self.requestMacro['header'].update({"country":self.config["country"], "session":self.config["sessionID"], "uuid":uuid})
            except:
                self.lastApiError = {'code':-1, 'message':self._cleanHtmlStr(content) + _("\nProbably Grooveshark is blocked for the country selected in config. \nPlease check this.")} 
                printExc()
                return False
        else:
            self.lastApiError = {'code':-1, 'message':_("%s connection error.") % GroovesharkApi.MAINURL} 
            return False
        return True
        
    #####################################################################################
    #                            Use grooveshark call
    #####################################################################################
        
    def initiateSession(self):
        printDBG('GroovesharkApi.initiateSession')
        # TODO: Please implement me
    
    def getCommunicationToken(self, force=False):
        printDBG('GroovesharkApi.getCommunicationToken force[%r]' % force)
        '''
        ToDo: if force == False request token only if refresh timeout meet
        '''
        s = JS_DateValueOf()
        if force or self.tokenExpires < s or '' == self.currentToken:
            sts,data = self._callRemote('getCommunicationToken', {"secretKey":self.secretKey}, False)
            if sts: 
                self.currentToken = data
                self.tokenExpires = s + 15e5
        else:
            sts = True
        if not sts:
            self.currentToken = ''
        return sts
    
    def authenticateUser(self, login, password):
        printDBG('GroovesharkApi.authenticateUser login[%r]' % login)
        sts = False
        if self.getCommunicationToken(True):
            params = {"username":login, "password":password}
            sts,data = self._callRemote('authenticateUser', params)
            if sts and 'userID'in data and 0 != data['userID']: self.loginData = data
            else: sts = False
        return sts
    
    def getFavorites(self, ofWhat, userID=None):
        printDBG('GroovesharkApi.getFavorites')
        ["Songs", "Users"]
        if None==userID: userID = self.loginData['userID']
        sts  = False
        result = []
        if self.getCommunicationToken():
            params = {"userID":userID,"ofWhat":ofWhat}
            sts,data = self._callRemote('getFavorites', params)
            if sts: result = data
        return sts,result
         
    def userGetSongsInLibrary(self, userID=None, page=0):
        printDBG('GroovesharkApi.userGetSongsInLibrary')
        sts  = False
        result = {}
        if self.getCommunicationToken():
            if None==userID: userID = self.loginData['userID']
            params = {"userID":userID, "page":page}
            sts,data = self._callRemote('userGetSongsInLibrary', params)
            if sts: result = data
        return sts,result

    def getUserRecentListens(self, userID=None):
        printDBG('GroovesharkApi.getUserRecentListens')
        sts  = False
        result = []
        if self.getCommunicationToken():
            if None==userID: userID = self.loginData['userID']
            params = {"userID":userID}
            sts,data = self._callRemote('getUserRecentListens', params)
            if sts: result = data
        return sts,result

    def getUsersActiveBroadcast(self, userID=None):
        printDBG('GroovesharkApi.getUsersActiveBroadcast')
        sts  = False
        result = False
        if self.getCommunicationToken():
            if None==userID: userID = self.loginData['userID']
            params = {"userID":userID}
            sts,data = self._callRemote('getUsersActiveBroadcast', params)
            if sts: result = data
        return sts,result
       
    def userGetPlaylists(self, userID=None):
        printDBG('GroovesharkApi.userGetPlaylists')
        sts  = False
        result = []
        if self.getCommunicationToken():
            if None==userID: userID = self.loginData['userID']
            params = {"userID":userID}
            sts,data = self._callRemote('userGetPlaylists', params)
            if sts: result = data
        return sts,result
    
    #######################################################################
    #######################################################################
    def getTopBroadcastsCombined(self):
        printDBG('GroovesharkApi.getTopBroadcastsCombined')
        sts  = False
        result = {}
        if self.getCommunicationToken():
            params = {}
            sts,data = self._callRemote('getTopBroadcastsCombined', params)
            if sts: result = data
        return sts,result
        
    def getTopBroadcasts(self, manateeTags=[]):
        printDBG('GroovesharkApi.getTopBroadcasts')
        sts  = False
        result = {}
        if self.getCommunicationToken():
            params = {'manateeTags':manateeTags}
            sts,data = self._callRemote('getTopBroadcasts', params)
            if sts: result = data
        return sts,result
        
    def getUserByID(self, userID):
        printDBG('GroovesharkApi.getUserByID')
        sts  = False
        result = []
        if self.getCommunicationToken():
            params = {"userID":userID}
            sts,data = self._callRemote('getUserByID', params)
            if sts: result = data
        return sts,result
        
    def startAutoplayTag(self, tagID):
        printDBG('GroovesharkApi.startAutoplayTag')
        {"Stations":[{"title":"80's", "id":55}]} # ToDo add function to category from app.jsp
        sts  = False
        result = []
        if self.getCommunicationToken():
            params = {"tagID":tagID}
            sts,data = self._callRemote('startAutoplayTag', params)
            if sts: result = data
        return sts,result
        
    def getStreamKeyFromSongIDEx(self, songID, mobile=False):
        printDBG('GroovesharkApi.getStreamKeyFromSongIDEx')
        sts  = False
        result = {}
        if self.getCommunicationToken():
            params = {"prefetch":False,"mobile":mobile,"songID":songID,"country":self.config["country"]}
            sts,data = self._callRemote('getStreamKeyFromSongIDEx', params)
            if sts: result = data
        return sts,result 

    def markSongDownloadedEx(self, streamKey, streamServerID, songID):
        printDBG('GroovesharkApi.markSongDownloadedEx')
        sts  = False
        result = False
        if self.getCommunicationToken():
            params = {"streamKey":streamKey,"streamServerID":streamServerID,"songID":songID}
            sts,data = self._callRemote('markSongDownloadedEx', params)
            if sts: result = data
        return sts,result 
    
    def broadcastStatusPoll(self, broadcastID):
        printDBG('GroovesharkApi.broadcastStatusPoll')
        sts  = False
        result = {}
        if self.getCommunicationToken():
            params = {"broadcastID":broadcastID}
            sts,data = self._callRemote('broadcastStatusPoll', params)
            if sts: result = data
        return sts,result 
    
    def getMobileBroadcastURL(self, broadcastID):
        printDBG('GroovesharkApi.getMobileBroadcastURL')
        sts  = False
        result = {}
        if self.getCommunicationToken():
            params = {"broadcastID":broadcastID}
            sts,data = self._callRemote('getMobileBroadcastURL', params)
            if sts: result = data
        return sts,result 
    
    def popularGetSongs(self, type="daily"):
        '''
        type in ["daily", "weekly", "monthly"]
        '''
        printDBG('GroovesharkApi.popularGetSongs')
        sts  = False
        result = {}
        if self.getCommunicationToken():
            params = {"type":type}
            sts,data = self._callRemote('popularGetSongs', params)
            if sts: result = data
        return sts,result 
    
    ###########################################################################
    # Search result
    ###########################################################################
    def getResultsFromSearch(self, query, types=["Songs","Playlists","Albums"]):
        printDBG('GroovesharkApi.getResultsFromSearch')
        sts  = False
        result = {}
        if self.getCommunicationToken():
            params = {"query":query,"type":types,"guts":0,"ppOverride":""}
            sts,data = self._callRemote('getResultsFromSearch', params)
            if sts and 'result' in data: result = data['result']
            else: sts = False
        return sts,result 
        
    def getPlaylistByID(self, playlistID):
        printDBG('GroovesharkApi.getPlaylistByID')
        sts  = False
        result = {}
        if self.getCommunicationToken():
            params = {"playlistID":playlistID}
            sts,data = self._callRemote('getPlaylistByID', params)
            if sts: result = data
        return sts,result 
    
    def albumGetAllSongs(self, albumID):
        printDBG('GroovesharkApi.albumGetAllSongs')
        sts  = False
        result = {}
        if self.getCommunicationToken():
            params = {"albumID":albumID}
            sts,data = self._callRemote('albumGetAllSongs', params)
            if sts: result = data
        return sts,result 

    def getAlbumByID(self, albumID):
        printDBG('GroovesharkApi.getAlbumByID')
        sts  = False
        result = {}
        if self.getCommunicationToken():
            params = {"albumID":albumID}
            sts,data = self._callRemote('getAlbumByID', params)
            if sts: result = data
        return sts,result 
