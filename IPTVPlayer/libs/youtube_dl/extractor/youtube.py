#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib, urllib2, re
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import *
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.jsinterp import JSInterpreter

try:
    import json
except:
    import simplejson as json

SignAlgoExtractorObj = None

class CVevoSignAlgoExtractor:
    # MAX RECURSION Depth for security
    MAX_REC_DEPTH = 5

    def __init__(self):
        self.algoCache = {}
        self._cleanTmpVariables()

    def _cleanTmpVariables(self):
        self.fullAlgoCode = ''
        self.allLocalFunNamesTab = []
        self.playerData = ''

    def _jsToPy(self, jsFunBody):
        pythonFunBody = jsFunBody.replace('function', 'def').replace('{', ':\n\t').replace('}', '').replace(';', '\n\t').replace('var ', '')
        pythonFunBody = pythonFunBody.replace('.reverse()', '[::-1]')

        lines = pythonFunBody.split('\n')
        for i in range(len(lines)):
            # a.split("") -> list(a)
            match = re.search('(\w+?)\.split\(""\)', lines[i])
            if match:
                lines[i] = lines[i].replace( match.group(0), 'list(' + match.group(1)  + ')')
            # a.length -> len(a)
            match = re.search('(\w+?)\.length', lines[i])
            if match:
                lines[i] = lines[i].replace( match.group(0), 'len(' + match.group(1)  + ')')
            # a.slice(3) -> a[3:]
            match = re.search('(\w+?)\.slice\(([0-9]+?)\)', lines[i])
            if match:
                lines[i] = lines[i].replace( match.group(0), match.group(1) + ('[%s:]' % match.group(2)) )
            # a.join("") -> "".join(a)
            match = re.search('(\w+?)\.join\(("[^"]*?")\)', lines[i])
            if match:
                lines[i] = lines[i].replace( match.group(0), match.group(2) + '.join(' + match.group(1) + ')' )
        return "\n".join(lines)

    def _getLocalFunBody(self, funName):
        # get function body
        match = re.search('(function %s\([^)]+?\){[^}]+?})' % re.escape(funName), self.playerData)
        if match:
            # return jsFunBody
            return match.group(1)
        return ''

    def _getAllLocalSubFunNames(self, mainFunBody):
        #match = re.compile('[ =(,](\w+?)\([^)]*?\)').findall( mainFunBody )
        #printDBG("|||||||||||||||||||||| ALL FUNCTION NAMES:")
        match = re.compile('[ =(,]([a-zA-Z$]+?)\([a-z0-9,]*?\)').findall( mainFunBody )
        if len(match):
            # first item is name of main function, so omit it
            funNameTab = set( match[1:] )
            #printDBG("|||||||||||||||||||||| ALL FUNCTION NAMES: [%r]\n" % funNameTab)
            return funNameTab
        return set()

    def decryptSignature(self, s, playerUrl):
        printDBG("decrypt_signature sign_len[%d] playerUrl[%s]" % (len(s), playerUrl) )

        # clear local data
        self._cleanTmpVariables()

        # use algoCache
        if playerUrl not in self.algoCache:
            # get player HTML 5 sript
            request = urllib2.Request(playerUrl)
            try:
                self.playerData = urllib2.urlopen(request).read()
                self.playerData = self.playerData.decode('utf-8', 'ignore')
            except:
                printExc('Unable to download playerUrl webpage')
                self._cleanTmpVariables()
                return ''
        
            #match = re.search("signature=([$a-zA-Z]+)", self.playerData)
            #if not match:
            match = re.search(r'\.sig\|\|([a-zA-Z0-9\$]+)\(', self.playerData)
            if match:
                mainFunName = match.group(1)
                printDBG('Main signature function name = "%s"' % mainFunName)
            else: 
                printDBG('Can not get main signature function name')
                self._cleanTmpVariables()
                return ''
                
            # get main function name 
            jsi = JSInterpreter(self.playerData)
            initial_function = jsi.extract_function(mainFunName)
            algoCodeObj = lambda s: initial_function([s])
            
        else:
            # get algoCodeObj from algoCache
            printDBG('Algo taken from cache')
            algoCodeObj = self.algoCache[playerUrl]

        # for security alow only flew python global function in algo code
        vGlobals = {"__builtins__": None, 'len': len, 'list': list}

        # local variable to pass encrypted sign and get decrypted sign
        vLocals = { 'inSignature': s, 'outSignature': '' }

        # execute prepared code
        try:
            sig = algoCodeObj(s)
        except:
            printExc('decryptSignature exec code EXCEPTION')
            self._cleanTmpVariables()
            return ''
        
        printDBG('Decrypted signature = [%s]' % vLocals['outSignature'])
        # if algo seems ok and not in cache, add it to cache
        if playerUrl not in self.algoCache and '' != sig:
            printDBG('Algo from player [%s] added to cache' % playerUrl)
            self.algoCache[playerUrl] = algoCodeObj
            
        # free not needed data
        self._cleanTmpVariables()

        return sig

    # Note, this method is using a recursion
    def _getfullAlgoCode( self, mainFunName, recDepth = 0 ):
        if self.MAX_REC_DEPTH <= recDepth:
            printDBG('_getfullAlgoCode: Maximum recursion depth exceeded')
            return 
            
        printDBG("============================================")
        printDBG(mainFunName)
        printDBG("============================================")
        funBody = self._getLocalFunBody( mainFunName )
        printDBG(funBody)
        printDBG("============================================")
        if '' != funBody:
            funNames = self._getAllLocalSubFunNames(funBody)
            if len(funNames):
                for funName in funNames:
                    if funName not in self.allLocalFunNamesTab:
                        self.allLocalFunNamesTab.append(funName)
                        printDBG("Add local function %s to known functions" % mainFunName)
                        self._getfullAlgoCode( funName, recDepth + 1 )

            # conver code from javascript to python 
            funBody = self._jsToPy(funBody)
            self.fullAlgoCode += '\n' + funBody + '\n'
        return

class InfoExtractor(object):
    """Information Extractor class.

    Information extractors are the classes that, given a URL, extract
    information about the video (or videos) the URL refers to. This
    information includes the real video URL, the video title, author and
    others. The information is stored in a dictionary which is then
    passed to the FileDownloader. The FileDownloader processes this
    information possibly downloading the video to the file system, among
    other possible outcomes.

    The dictionaries must include the following fields:

    id:             Video identifier.
    url:            Final video URL.
    title:          Video title, unescaped.
    ext:            Video filename extension.

    The following fields are optional:

    format:         The video format, defaults to ext (used for --get-format)
    thumbnail:      Full URL to a video thumbnail image.
    description:    One-line video description.
    uploader:       Full name of the video uploader.
    upload_date:    Video upload date (YYYYMMDD).
    uploader_id:    Nickname or id of the video uploader.
    location:       Physical location of the video.
    player_url:     SWF Player URL (used for rtmpdump).
    subtitles:      The subtitle file contents.
    urlhandle:      [internal] The urlHandle to be used to download the file,
                    like returned by urllib.request.urlopen

    The fields should all be Unicode strings.

    Subclasses of this one should re-define the _real_initialize() and
    _real_extract() methods and define a _VALID_URL regexp.
    Probably, they should also be added to the list of extractors.

    _real_extract() must return a *list* of information dictionaries as
    described above.

    Finally, the _WORKING attribute should be set to False for broken IEs
    in order to warn the users and skip the tests.
    """

    _ready = False
    _downloader = None
    _WORKING = True

    def __init__(self, downloader=None):
        """Constructor. Receives an optional downloader."""
        self._ready = False
        self.set_downloader(downloader)

    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""
        return re.match(cls._VALID_URL, url) is not None

    @classmethod
    def working(cls):
        """Getter method for _WORKING."""
        return cls._WORKING

    def initialize(self):
        """Initializes an instance (authentication, etc)."""
        if not self._ready:
            self._real_initialize()
            self._ready = True

    def extract(self, url):
        """Extracts URL information and returns it in list of dicts."""
        self.initialize()
        return self._real_extract(url)

    def set_downloader(self, downloader):
        """Sets the downloader for this IE."""
        self._downloader = downloader

    def _real_initialize(self):
        """Real initialization process. Redefine in subclasses."""
        pass

    def _real_extract(self, url):
        """Real extraction process. Redefine in subclasses."""
        pass

    @property
    def IE_NAME(self):
        return type(self).__name__[:-2]

    def _request_webpage(self, url_or_request, video_id, note=None, errnote=None):
        """ Returns the response handle """
        if note is None:
            self.report_download_webpage(video_id)
        elif note is not False:
            printDBG(u'%s: %s' % (video_id, note))
        try:
            return compat_urllib_request.urlopen(url_or_request)
        except:
            printDBG('ERROR _request_webpage')
            raise ExtractorError(u'ERROR _request_webpage')

    def _download_webpage_handle(self, url_or_request, video_id, note=None, errnote=None):
        """ Returns a tuple (page content as string, URL handle) """
        urlh = self._request_webpage(url_or_request, video_id, note, errnote)
        content_type = urlh.headers.get('Content-Type', '')
        m = re.match(r'[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+\s*;\s*charset=(.+)', content_type)
        if m:
            encoding = m.group(1)
        else:
            encoding = 'utf-8'
        webpage_bytes = urlh.read()

        try:
            url = url_or_request.get_full_url()
        except AttributeError:
            url = url_or_request
        #printDBG(u'Dumping request to ' + url)
        #dump = base64.b64encode(webpage_bytes).decode('ascii')
        #printDBG(dump)
        content = webpage_bytes.decode(encoding, 'replace')
        return (content, urlh)

    def _download_webpage(self, url_or_request, video_id, note=None, errnote=None):
        """ Returns the data of the page as a string """
        return self._download_webpage_handle(url_or_request, video_id, note, errnote)[0]

    def to_screen(self, msg):
        """Print msg to screen, prefixing it with '[ie_name]'"""
        printDBG(u'[%s] %s' % (self.IE_NAME, msg))

    def report_extraction(self, id_or_name):
        """Report information extraction."""
        printDBG(u'%s: Extracting information' % id_or_name)

    def report_download_webpage(self, video_id):
        """Report webpage download."""
        printDBG(u'%s: Downloading webpage' % video_id)

    def report_age_confirmation(self):
        """Report attempt to confirm age."""
        printDBG(u'Confirming age')

    #Methods for following #608
    #They set the correct value of the '_type' key
    def video_result(self, video_info):
        """Returns a video"""
        video_info['_type'] = 'video'
        return video_info
    def url_result(self, url, ie=None):
        """Returns a url that points to a page that should be processed"""
        #TODO: ie should be the class used for getting the info
        video_info = {'_type': 'url',
                      'url': url,
                      'ie_key': ie}
        return video_info
    def playlist_result(self, entries, playlist_id=None, playlist_title=None):
        """Returns a playlist"""
        video_info = {'_type': 'playlist',
                      'entries': entries}
        if playlist_id:
            video_info['id'] = playlist_id
        if playlist_title:
            video_info['title'] = playlist_title
        return video_info

class SearchInfoExtractor(InfoExtractor):
    """
    Base class for paged search queries extractors.
    They accept urls in the format _SEARCH_KEY(|all|[0-9]):{query}
    Instances should define _SEARCH_KEY and _MAX_RESULTS.
    """

    @classmethod
    def _make_valid_url(cls):
        return r'%s(?P<prefix>|[1-9][0-9]*|all):(?P<query>[\s\S]+)' % cls._SEARCH_KEY

    @classmethod
    def suitable(cls, url):
        return re.match(cls._make_valid_url(), url) is not None

    def _real_extract(self, query):
        mobj = re.match(self._make_valid_url(), query)
        if mobj is None:
            printDBG('Invalid search query "%s"' % query)
            raise ExtractorError(u'Invalid search query "%s"' % query)

        prefix = mobj.group('prefix')
        query = mobj.group('query')
        if prefix == '':
            return self._get_n_results(query, 1)
        elif prefix == 'all':
            return self._get_n_results(query, self._MAX_RESULTS)
        else:
            n = int(prefix)
            if n <= 0:
                printDBG('invalid download number %s for query "%s"' % (n, query))
                raise ExtractorError(u'invalid download number %s for query "%s"' % (n, query))
            elif n > self._MAX_RESULTS:
                self._downloader.report_warning(u'%s returns max %i results (you requested %i)' % (self._SEARCH_KEY, self._MAX_RESULTS, n))
                n = self._MAX_RESULTS
            return self._get_n_results(query, n)

    def _get_n_results(self, query, n):
        """Get a specified number of results for a query"""
        printDBG("This method must be implemented by sublclasses")
        raise NotImplementedError("This method must be implemented by sublclasses")
        


class YoutubeIE(InfoExtractor):
    """Information extractor for youtube.com."""

    _VALID_URL = r"""^
                     (
                         (?:https?://)?                                       # http(s):// (optional)
                         (?:youtu\.be/|(?:\w+\.)?youtube(?:-nocookie)?\.com/|
                            tube\.majestyc\.net/)                             # the various hostnames, with wildcard subdomains
                         (?:.*?\#/)?                                          # handle anchor (#/) redirect urls
                         (?:                                                  # the various things that can precede the ID:
                             (?:(?:v|embed|e)/)                               # v/ or embed/ or e/
                             |(?:                                             # or the v= param in all its forms
                                 (?:watch(?:_popup)?(?:\.php)?)?              # preceding watch(_popup|.php) or nothing (like /?v=xxxx)
                                 (?:\?|\#!?)                                  # the params delimiter ? or # or #!
                                 (?:.*?&)?                                    # any other preceding param (like /?s=tuff&v=xxxx)
                                 v=
                             )
                         )?                                                   # optional -> youtube.com/xxxx is OK
                     )?                                                       # all until now is optional -> you can pass the naked ID
                     ([0-9A-Za-z_-]+)                                         # here is it! the YouTube video ID
                     (?(1).+)?                                                # if we found the ID, everything can follow
                     $"""
    _LANG_URL = r'https://www.youtube.com/?hl=en&persist_hl=1&gl=US&persist_gl=1&opt_out_ackd=1'
    _LOGIN_URL = 'https://accounts.google.com/ServiceLogin'
    _AGE_URL = 'http://www.youtube.com/verify_age?next_url=/&gl=US&hl=en'
    _NEXT_URL_RE = r'[\?&]next_url=([^&]+)'
    _NETRC_MACHINE = 'youtube'
    # Listed in order of quality
    _available_formats = ['38', '37', '46', '22', '45', '35', '44', '34', '18', '43', '6', '5', '36', '17', '13',
                          # Apple HTTP Live Streaming
                          '96', '95', '94', '93', '92', '132', '151',
                          # 3D
                          '85', '84', '102', '83', '101', '82', '100',
                          # Dash video
                          '138', '137', '248', '136', '247', '135', '246',
                          '245', '244', '134', '243', '133', '242', '160',
                          # Dash audio
                          '141', '172', '140', '171', '139',
                          ]
    _available_formats_prefer_free = ['38', '46', '37', '45', '22', '44', '35', '43', '34', '18', '6', '5', '36', '17', '13',
                                      # Apple HTTP Live Streaming
                                      '96', '95', '94', '93', '92', '132', '151',
                                      # 3D
                                      '85', '102', '84', '101', '83', '100', '82',
                                      # Dash video
                                      '138', '248', '137', '247', '136', '246', '245',
                                      '244', '135', '243', '134', '242', '133', '160',
                                      # Dash audio
                                      '172', '141', '171', '140', '139',
                                      ]
    _video_formats_map = {
        'flv': ['35', '34', '6', '5'],
        '3gp': ['36', '17', '13'],
        'mp4': ['38', '37', '22', '18'],
        'webm': ['46', '45', '44', '43'],
    }
    _video_extensions = {
        '13': '3gp',
        '17': '3gp',
        '18': 'mp4',
        '22': 'mp4',
        '36': '3gp',
        '37': 'mp4',
        '38': 'mp4',
        '43': 'webm',
        '44': 'webm',
        '45': 'webm',
        '46': 'webm',

        # 3d videos
        '82': 'mp4',
        '83': 'mp4',
        '84': 'mp4',
        '85': 'mp4',
        '100': 'webm',
        '101': 'webm',
        '102': 'webm',

        # Apple HTTP Live Streaming
        '92': 'mp4',
        '93': 'mp4',
        '94': 'mp4',
        '95': 'mp4',
        '96': 'mp4',
        '132': 'mp4',
        '151': 'mp4',

        # Dash mp4
        '133': 'mp4',
        '134': 'mp4',
        '135': 'mp4',
        '136': 'mp4',
        '137': 'mp4',
        '138': 'mp4',
        '160': 'mp4',

        # Dash mp4 audio
        '139': 'm4a',
        '140': 'm4a',
        '141': 'm4a',

        # Dash webm
        '171': 'webm',
        '172': 'webm',
        '242': 'webm',
        '243': 'webm',
        '244': 'webm',
        '245': 'webm',
        '246': 'webm',
        '247': 'webm',
        '248': 'webm',
    }
    _video_dimensions = {
        '5': '240x400',
        '6': '???',
        '13': '???',
        '17': '144x176',
        '18': '360x640',
        '22': '720x1280',
        '34': '360x640',
        '35': '480x854',
        '36': '240x320',
        '37': '1080x1920',
        '38': '3072x4096',
        '43': '360x640',
        '44': '480x854',
        '45': '720x1280',
        '46': '1080x1920',
        '82': '360p',
        '83': '480p',
        '84': '720p',
        '85': '1080p',
        '92': '240p',
        '93': '360p',
        '94': '480p',
        '95': '720p',
        '96': '1080p',
        '100': '360p',
        '101': '480p',
        '102': '720p',
        '132': '240p',
        '151': '72p',
        '133': '240p',
        '134': '360p',
        '135': '480p',
        '136': '720p',
        '137': '1080p',
        '138': '>1080p',
        '139': '48k',
        '140': '128k',
        '141': '256k',
        '160': '192p',
        '171': '128k',
        '172': '256k',
        '242': '240p',
        '243': '360p',
        '244': '480p',
        '245': '480p',
        '246': '480p',
        '247': '720p',
        '248': '1080p',
    }

    _special_itags = {
        '82': '3D',
        '83': '3D',
        '84': '3D',
        '85': '3D',
        '100': '3D',
        '101': '3D',
        '102': '3D',
        '133': 'DASH Video',
        '134': 'DASH Video',
        '135': 'DASH Video',
        '136': 'DASH Video',
        '137': 'DASH Video',
        '138': 'DASH Video',
        '139': 'DASH Audio',
        '140': 'DASH Audio',
        '141': 'DASH Audio',
        '160': 'DASH Video',
        '171': 'DASH Audio',
        '172': 'DASH Audio',
        '242': 'DASH Video',
        '243': 'DASH Video',
        '244': 'DASH Video',
        '245': 'DASH Video',
        '246': 'DASH Video',
        '247': 'DASH Video',
        '248': 'DASH Video',
    }
    IE_NAME = u'youtube'

    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""
        if YoutubePlaylistIE.suitable(url): return False
        return re.match(cls._VALID_URL, url, re.VERBOSE) is not None

    def report_lang(self):
        """Report attempt to set language."""
        printDBG(u'Setting language')

    def report_login(self):
        """Report attempt to log in."""
        printDBG(u'Logging in')

    def report_video_webpage_download(self, video_id):
        """Report attempt to download video webpage."""
        printDBG(u'%s: Downloading video webpage' % video_id)

    def report_video_info_webpage_download(self, video_id):
        """Report attempt to download video info webpage."""
        printDBG(u'%s: Downloading video info webpage' % video_id)

    def report_video_subtitles_download(self, video_id):
        """Report attempt to download video info webpage."""
        printDBG(u'%s: Checking available subtitles' % video_id)

    def report_video_subtitles_request(self, video_id, sub_lang, format):
        """Report attempt to download video info webpage."""
        printDBG(u'%s: Downloading video subtitles for %s.%s' % (video_id, sub_lang, format))

    def report_video_subtitles_available(self, video_id, sub_lang_list):
        """Report available subtitles."""
        sub_lang = ",".join(list(sub_lang_list.keys()))
        printDBG(u'%s: Available subtitles for video: %s' % (video_id, sub_lang))

    def report_information_extraction(self, video_id):
        """Report attempt to extract video information."""
        printDBG(u'%s: Extracting video information' % video_id)

    def report_unavailable_format(self, video_id, format):
        """Report extracted video URL."""
        printDBG(u'%s: Format %s not available' % (video_id, format))

    def report_rtmp_download(self):
        """Indicate the download will use the RTMP protocol."""
        printDBG(u'RTMP download detected')

    def _print_formats(self, formats):
        printDBG('Available formats:')
        for x in formats:
            printDBG('%s\t:\t%s\t[%s]' %(x, self._video_extensions.get(x, 'flv'), self._video_dimensions.get(x, '???')))

    def _real_initialize(self):

        # Set language
        request = compat_urllib_request.Request(self._LANG_URL)
        try:
            self.report_lang()
            compat_urllib_request.urlopen(request).read()
        except:
            self._downloader.report_warning(u'unable to set language')
            return

        # No authentication to be performed
        if username is None:
            return

        request = compat_urllib_request.Request(self._LOGIN_URL)
        try:
            login_page = compat_urllib_request.urlopen(request).read().decode('utf-8')
        except:
            self._downloader.report_warning(u'unable to fetch login page')
            return

        galx = None
        dsh = None
        match = re.search(re.compile(r'<input.+?name="GALX".+?value="(.+?)"', re.DOTALL), login_page)
        if match:
          galx = match.group(1)

        match = re.search(re.compile(r'<input.+?name="dsh".+?value="(.+?)"', re.DOTALL), login_page)
        if match:
          dsh = match.group(1)

        # Log in
        login_form_strs = {
                u'continue': u'https://www.youtube.com/signin?action_handle_signin=true&feature=sign_in_button&hl=en_US&nomobiletemp=1',
                u'Email': username,
                u'GALX': galx,
                u'Passwd': password,
                u'PersistentCookie': u'yes',
                u'_utf8': u'霱',
                u'bgresponse': u'js_disabled',
                u'checkConnection': u'',
                u'checkedDomains': u'youtube',
                u'dnConn': u'',
                u'dsh': dsh,
                u'pstMsg': u'0',
                u'rmShown': u'1',
                u'secTok': u'',
                u'signIn': u'Sign in',
                u'timeStmp': u'',
                u'service': u'youtube',
                u'uilel': u'3',
                u'hl': u'en_US',
        }
        # Convert to UTF-8 *before* urlencode because Python 2.x's urlencode
        # chokes on unicode
        login_form = dict((k.encode('utf-8'), v.encode('utf-8')) for k,v in login_form_strs.items())
        login_data = compat_urllib_parse.urlencode(login_form).encode('ascii')
        request = compat_urllib_request.Request(self._LOGIN_URL, login_data)
        try:
            self.report_login()
            login_results = compat_urllib_request.urlopen(request).read().decode('utf-8')
            printDBG(login_results)
            if re.search(r'(?i)<form[^>]* id="gaia_loginform"', login_results) is not None:
                self._downloader.report_warning(u'unable to log in: bad username or password')
                return
        except:
            self._downloader.report_warning(u'unable to log in')
            return

        # Confirm age
        age_form = {
                'next_url':     '/',
                'action_confirm':   'Confirm',
                }
        request = compat_urllib_request.Request(self._AGE_URL, compat_urllib_parse.urlencode(age_form))
        try:
            self.report_age_confirmation()
            age_results = compat_urllib_request.urlopen(request).read().decode('utf-8')
        except:
            printDBG('Unable to confirm age')
            raise ExtractorError(u'Unable to confirm age')

    def _extract_id(self, url):
        mobj = re.match(self._VALID_URL, url, re.VERBOSE)
        if mobj is None:
            printDBG('Invalid URL: %s' % url)
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group(2)
        return video_id

    def _real_extract(self, url, ):
        # Extract original video URL from URL with redirection, like age verification, using next_url parameter
        mobj = re.search(self._NEXT_URL_RE, url)
        if mobj:
            #https
            url = 'http://www.youtube.com/' + compat_urllib_parse.unquote(mobj.group(1)).lstrip('/')
        video_id = self._extract_id(url)
        
        # Get video webpage
        self.report_video_webpage_download(video_id)
        url = 'http://www.youtube.com/watch?v=%s&gl=US&hl=en&has_verified=1' % video_id
        request = compat_urllib_request.Request(url)
        try:
            video_webpage_bytes = compat_urllib_request.urlopen(request).read()
        except:
            printDBG('Unable to download video webpage')
            raise ExtractorError('Unable to download video webpage')

        video_webpage = video_webpage_bytes.decode('utf-8', 'ignore')
        
        # Attempt to extract SWF player URL
        mobj = re.search(r'swfConfig.*?"(http:\\/\\/.*?watch.*?-.*?\.swf)"', video_webpage)
        if mobj is not None:
            player_url = re.sub(r'\\(.)', r'\1', mobj.group(1))
        else:
            player_url = ''

        # Get video info
        self.report_video_info_webpage_download(video_id)

        if re.search(r'player-age-gate-content">', video_webpage) is not None:
            self.report_age_confirmation()
            age_gate = True
            # We simulate the access to the video from www.youtube.com/v/{video_id}
            # this can be viewed without login into Youtube
            data = compat_urllib_parse.urlencode({'video_id': video_id,
                                                  'el': 'embedded',
                                                  'gl': 'US',
                                                  'hl': 'en',
                                                  'eurl': 'https://youtube.googleapis.com/v/' + video_id,
                                                  'asv': 3,
                                                  'sts':'1588',
                                                  })
            video_info_url = 'https://www.youtube.com/get_video_info?' + data
            video_info_webpage = self._download_webpage(video_info_url, video_id,
                                    note=False,
                                    errnote='unable to download video info webpage')
            video_info = compat_parse_qs(video_info_webpage)
        else:
            age_gate = False
            for el_type in ['&el=embedded', '&el=detailpage', '&el=vevo', '']:
                #https
                video_info_url = ('http://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en'
                        % (video_id, el_type))
                video_info_webpage = self._download_webpage(video_info_url, video_id,
                                        note=False,
                                        errnote='unable to download video info webpage')
                video_info = compat_parse_qs(video_info_webpage)
                if 'token' in video_info:
                    break
        if 'token' not in video_info:
            if 'reason' in video_info:
                printDBG('YouTube said: %s' % video_info['reason'][0])
                raise ExtractorError(u'YouTube said: %s' % video_info['reason'][0])
            else:
                printDBG('"token" parameter not in video info for unknown reason')
                raise ExtractorError(u'"token" parameter not in video info for unknown reason')

        # Check for "rental" videos
        if 'ypc_video_rental_bar_text' in video_info and 'author' not in video_info:
            printDBG('"rental" videos not supported')
            raise ExtractorError(u'"rental" videos not supported')

        # Start extracting information
        self.report_information_extraction(video_id)

        # uploader
        if 'author' not in video_info:
            printDBG('Unable to extract uploader name')
            raise ExtractorError(u'Unable to extract uploader name')
        video_uploader = compat_urllib_parse.unquote_plus(video_info['author'][0])


        # title
        if 'title' not in video_info:
            printDBG('Unable to extract video title')
            raise ExtractorError(u'Unable to extract video title')
        video_title = compat_urllib_parse.unquote_plus(video_info['title'][0])

        # thumbnail image
        if 'thumbnail_url' not in video_info:
            self._downloader.report_warning(u'unable to extract video thumbnail')
            video_thumbnail = ''
        else:   # don't panic if we can't find it
            video_thumbnail = compat_urllib_parse.unquote_plus(video_info['thumbnail_url'][0])

        # subtitles
        if 'length_seconds' not in video_info:
            self._downloader.report_warning(u'unable to extract video duration')
            video_duration = ''
        else:
            video_duration = compat_urllib_parse.unquote_plus(video_info['length_seconds'][0])

        # Decide which formats to download
        try:
            mobj = re.search(r';ytplayer.config = ({.*?});', video_webpage)
            if not mobj:
                raise ValueError('Could not find vevo ID')
            ytplayer_config = json.loads(mobj.group(1))
            args = ytplayer_config['args']
            # Easy way to know if the 's' value is in url_encoded_fmt_stream_map
            # this signatures are encrypted
            if 'url_encoded_fmt_stream_map' not in args:
                raise ValueError(u'No stream_map present') # caught below
            re_signature = re.compile(r'[&,]s=')
            m_s = re_signature.search(args['url_encoded_fmt_stream_map'])
            if m_s is not None:
                self.to_screen(u'%s: Encrypted signatures detected.' % video_id)
                video_info['url_encoded_fmt_stream_map'] = [args['url_encoded_fmt_stream_map']]
            m_s = re_signature.search(args.get('adaptive_fmts', u''))
        except ValueError:
            pass

        # Decide which formats to download
        req_format = 'all'
        
        is_m3u8 = 'no'

        #if 'conn' in video_info and video_info['conn'][0].startswith('rtmp'):
        #    self.report_rtmp_download()
        #    video_url_list = [(None, video_info['conn'][0])]
        if len(video_info.get('url_encoded_fmt_stream_map', [])) >= 1 or len(video_info.get('adaptive_fmts', [])) >= 1:
            encoded_url_map = video_info.get('url_encoded_fmt_stream_map', [''])[0] + ',' + video_info.get('adaptive_fmts',[''])[0]
            if 'rtmpe%3Dyes' in encoded_url_map:
                printDBG('rtmpe downloads are not supported, see https://github.com/rg3/youtube-dl/issues/343 for more information.')
                raise
            url_map = {}
            for url_data_str in encoded_url_map.split(','):
                url_data = compat_parse_qs(url_data_str)
                add = True
                if 'itag' in url_data and 'url' in url_data:
                    url = url_data['url'][0]
                    if 'sig' in url_data:
                        signature = url_data['sig'][0]
                        url += '&signature=' + signature
                    elif 's' in url_data:
                        encrypted_sig = url_data['s'][0]
                        signature = ''
                        match = re.search('"([^"]+?html5player-[^"]+?\.js)"', video_webpage)
                        if match:
                            playerUrl = match.group(1).replace('\\', '').replace('https:', 'http:')
                            if not playerUrl.startswith('http'):
                                playerUrl = 'http:' + playerUrl
                            global SignAlgoExtractorObj
                            if None == SignAlgoExtractorObj:
                                SignAlgoExtractorObj = CVevoSignAlgoExtractor()
                            signature = SignAlgoExtractorObj.decryptSignature( encrypted_sig, playerUrl )
                        else:
                            printDBG("YT HTML PLAYER not available!")
                        if 0 == len(signature):
                            printDBG("YT signature description problem")
                            add = False
                        url += '&signature=' + signature
                    

                    if not 'ratebypass' in url:
                        url += '&ratebypass=yes'
                    if add: url_map[url_data['itag'][0]] = url
               
            video_url_list = self._get_video_url_list(url_map)
            if not video_url_list:
                return []
   
        elif video_info.get('hlsvp'):
            is_m3u8 = 'yes'
            manifest_url = video_info['hlsvp'][0]
            url_map = self._extract_from_m3u8(manifest_url, video_id)
            video_url_list = self._get_video_url_list(url_map)
            if not video_url_list:
                return []

        else:
            printDBG('no conn, hlsvp or url_encoded_fmt_stream_map information found in video info')
            raise

        results = []
        for format_param, video_real_url in video_url_list:
            # Extension
            video_extension = self._video_extensions.get(format_param, 'flv')

            #video_format = '{0} - {1}'.format(format_param if format_param else video_extension,
            #                                  self._video_dimensions.get(format_param, '???'))
            video_format = self._video_dimensions.get(format_param, '???')

            results.append({
                'id':       video_id,
                'url':      video_real_url,
                'uploader': video_uploader,
                'title':    video_title,
                'ext':      video_extension,
                'format':   video_format,
                'thumbnail':    video_thumbnail,
                'duration':     video_duration,
                'player_url':   player_url,
                'm3u8'      :   is_m3u8,
            })
            
        return results
        

    def _extract_from_m3u8(self, manifest_url, video_id):
        url_map = {}
        def _get_urls(_manifest):
            lines = _manifest.split('\n')
            urls = filter(lambda l: l and not l.startswith('#'),
                            lines)
            return urls
        manifest = self._download_webpage(manifest_url, video_id, u'Downloading formats manifest')
        formats_urls = _get_urls(manifest)
        for format_url in formats_urls:
            itag = self._search_regex(r'itag/(\d+?)/', format_url, 'itag')
            url_map[itag] = format_url
        return url_map

    def _search_regex(self, pattern, string, name, default=None, fatal=True, flags=0):
        compiled_regex_type = type(re.compile(''))
        if isinstance(pattern, (str, compat_str, compiled_regex_type)):
            mobj = re.search(pattern, string, flags)
        else:
            for p in pattern:
                mobj = re.search(p, string, flags)
                if mobj: break

        if mobj:
            # return the first matching group
            return next(g for g in mobj.groups() if g is not None)
        elif default is not None:
            return default
        elif fatal:
            printDBG('Unable to extract %s' % name)
            raise
        else:
            printDBG('unable to extract %s; please report this issue on http://yt-dl.org/bug' % name)
            return None
            
    def _get_video_url_list(self, url_map):
        format_list = self._available_formats_prefer_free # available_formats
        existing_formats = [x for x in format_list if x in url_map]
        
        return [(f, url_map[f]) for f in existing_formats] # All formats

        