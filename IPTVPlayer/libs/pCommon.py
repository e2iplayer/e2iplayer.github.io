# -*- coding: utf-8 -*-
# Based on (root)/trunk/xbmc-addons/src/plugin.video.polishtv.live/hosts/ @ 419 - Wersja 605

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, IsHttpsCertValidationEnabled

###################################################
# FOREIGN import
###################################################
import urllib
import urllib2
import ssl
import re
import htmlentitydefs
import cookielib
try:
    try: from cStringIO import StringIO
    except: from StringIO import StringIO 
    import gzip
except: pass
###################################################


class MultipartPostHandler(urllib2.BaseHandler):
    handler_order = urllib2.HTTPHandler.handler_order - 10

    def http_request(self, request):
        data = request.get_data()
        if data is not None and type(data) != str:
            content_type, data = self.encode_multipart_formdata( data )
            request.add_unredirected_header('Content-Type', content_type)
            request.add_data(data)
        return request
        
    def encode_multipart_formdata(self, fields):
        LIMIT = '-----------------------------14312495924498'
        CRLF = '\r\n'
        L = []
        for (key, value) in fields:
            L.append('--' + LIMIT)
            L.append('Content-Disposition: form-data; name="%s"' % key)
            L.append('')
            L.append(value)
        L.append('--' + LIMIT + '--')
        L.append('')
        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary=%s' % LIMIT
        return content_type, body
    
    https_request = http_request

class CParsingHelper:
    @staticmethod
    def getSearchGroups(data, pattern, grupsNum=1):
        tab = []
        match = re.search(pattern, data)
        
        for idx in range(grupsNum):
            try:    value = match.group(idx + 1)
            except: value = ''
            tab.append(value)
        return tab
        
    @staticmethod
    def getDataBeetwenReMarkers(data, pattern1, pattern2, withMarkers=True):
        match1 = pattern1.search(data)
        if None == match1 or -1 == match1.start(0): return False, ''
        match2 = pattern2.search(data[match1.end(0):])
        if None == match2 or -1 == match2.start(0): return False, ''
        
        if withMarkers:
            return True, data[match1.start(0): (match1.end(0) + match2.end(0)) ]
        else:
            return True, data[match1.end(0): (match1.end(0) + match2.start(0)) ]

        
    @staticmethod
    def getDataBeetwenMarkers(data, marker1, marker2, withMarkers=True, caseSensitive=True):
        if caseSensitive:
            idx1 = data.find(marker1)
        else:
            idx1 = data.lower().find(marker1.lower())
        if -1 == idx1: return False, ''
        if caseSensitive:
            idx2 = data.find(marker2, idx1 + len(marker1))
        else:
            idx2 = data.lower().find(marker2.lower(), idx1 + len(marker1))
        if -1 == idx2: return False, ''
        
        if withMarkers:
            idx2 = idx2 + len(marker2)
        else:
            idx1 = idx1 + len(marker1)

        return True, data[idx1:idx2]
        
    @staticmethod
    def getAllItemsBeetwenMarkers(data, marker1, marker2, withMarkers=True, caseSensitive=True):
        itemsTab = []
        if caseSensitive:
            sData = data
        else:
            sData = data.lower()
            marker1 = marker1.lower()
            marker2 = marker2.lower()
        idx1 = 0
        while True:
            idx1 = sData.find(marker1, idx1)
            if -1 == idx1: return itemsTab
            idx2 = sData.find(marker2, idx1 + len(marker1))
            if -1 == idx2: return itemsTab
            tmpIdx2 = idx2 + len(marker2) 
            if withMarkers:
                idx2 = tmpIdx2
            else:
                idx1 = idx1 + len(marker1)
            itemsTab.append(data[idx1:idx2])
            idx1 = tmpIdx2
        return itemsTab
        
    @staticmethod
    def rgetDataBeetwenMarkers(data, marker1, marker2, withMarkers = True):
        idx1 = data.rfind(marker1)
        if -1 == idx1: return False, ''
        idx2 = data.rfind(marker2, idx1 + len(marker1))
        if -1 == idx2: return False, ''
        
        if withMarkers:
            idx2 = idx2 + len(marker2)
        else:
            idx1 = idx1 + len(marker1)
        return True, data[idx1:idx2]
        
    @staticmethod    
    def removeDoubles(data, pattern):
        while -1 < data.find(pattern+pattern) and '' != pattern:
            data = data.replace(pattern+pattern, pattern)
        return data 

    @staticmethod
    def replaceHtmlTags(s, replacement=''):
        tag = False
        quote = False
        out = ""
        for c in s:
                if c == '<' and not quote:
                    tag = True
                elif c == '>' and not quote:
                    tag = False
                    out += replacement
                elif (c == '"' or c == "'") and tag:
                    quote = not quote
                elif not tag:
                    out = out + c
        return re.sub('&\w+;', ' ',out)        
        
    # this method is useful only for developers 
    # to dump page code to the file
    @staticmethod
    def writeToFile(file, data, mode = "w"):
        #helper to see html returned by ajax
        file_path = file
        text_file = open(file_path, mode)
        text_file.write(data)
        text_file.close()    

class common:
    HOST   = 'Mozilla/5.0 (Windows NT 6.1; rv:17.0) Gecko/20100101 Firefox/17.0'
    HEADER = None
    ph = CParsingHelper
    
    @staticmethod
    def getParamsFromUrlWithMeta(url):
        HANDLED_HTTP_HEADER_PARAMS = ['Host', 'User-Agent', 'Referer', 'Cookie', 'Accept']
        headerOutParams = {}
        tmpParams = {}
        postData = None
        if isinstance(url, strwithmeta):
            tmpParams['header'] = {}
            for key in url.meta:
                if key in HANDLED_HTTP_HEADER_PARAMS:
                    tmpParams['header'][key] = url.meta[key]
            if 0 < len(tmpParams['header']):
                headerOutParams = tmpParams
        return headerOutParams, postData
    
    def __init__(self, proxyURL= '', useProxy = False):
        self.proxyURL = proxyURL
        self.useProxy = useProxy
        
    def getCookieItem(self, cookiefile, item):
        ret = ''
        cj = cookielib.LWPCookieJar()
        cj.load(cookiefile, ignore_discard = True)
        for cookie in cj:
            if cookie.name == item: ret = cookie.value
        return ret

    def html_entity_decode_char(self, m):
        ent = m.group(1)
        if ent.startswith('x'):
            return unichr(int(ent[1:],16))
        try:
            return unichr(int(ent))
        except:
            if ent in htmlentitydefs.name2codepoint:
                return unichr(htmlentitydefs.name2codepoint[ent])
            else:
                return ent

    def html_entity_decode(self, string):
        string = string.decode('UTF-8')
        s = re.compile("&#?(\w+?);").sub(self.html_entity_decode_char, string)
        return s.encode('UTF-8')
    
    def getPage(self, url, addParams = {}, post_data = None):
        ''' wraps getURLRequestData '''
        try:
            addParams['url'] = url
            if 'return_data' not in addParams:
                addParams['return_data'] = True
            response = self.getURLRequestData(addParams, post_data)
            status = True
        except:
            printExc()
            response = None
            status = False
        return (status, response)
        
    def saveWebFile(self, file_path, url, addParams = {}, post_data = None):
        bRet = False
        downDataSize = 0
        dictRet = {}
        try:
            if 'header' not in addParams and 'host' not in addParams:
                host = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.18) Gecko/20110621 Mandriva Linux/1.9.2.18-0.1mdv2010.2 (2010.2) Firefox/3.6.18'
                header = {'User-Agent': host, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
                addParams['header'] = header
            addParams['return_data'] = False
            sts, downHandler = self.getPage(url, addParams, post_data)

            if addParams.get('ignore_content_length', False):
                meta = downHandler.info()
                contentLength = int(meta.getheaders("Content-Length")[0])
            else:
                contentLength = None

            if 'maintype' in addParams and addParams['maintype'] != downHandler.headers.maintype:
                downHandler.close()
                printDBG("common.getFile wrong maintype! requested[%r], retrieved[%r]" % (addParams['maintype'], downHandler.headers.maintype))
            else:
                blockSize = addParams.get('block_size', 8192)
                fileHandler = file(file_path, "wb")
                while True:
                    buffer = downHandler.read(blockSize)
                    if not buffer:
                        break
                    downDataSize += len(buffer)
                    fileHandler.write(buffer)
                fileHandler.close()
                downHandler.close()
                if None != contentLength and contentLength == downDataSize:
                    bRet = True
        except:
            printExc("common.getFile download file exception")
        dictRet.update( {'sts': True, 'fsize': downDataSize} )
        return dictRet
    
    def getURLRequestData(self, params = {}, post_data = None):
        
        def urlOpen(req, customOpeners):
            no_ssl_cert_check = False
            try:
                if req.get_full_url().startswith("http") and not IsHttpsCertValidationEnabled():
                    no_ssl_cert_check = True
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
            except:
                no_ssl_cert_check = False
                printExc()
            
            if len(customOpeners) > 0:
                opener = urllib2.build_opener( *customOpeners )
                if no_ssl_cert_check: response = opener.open(req, context=ctx)
                else: response = opener.open(req)
            else:
                if no_ssl_cert_check: response = urllib2.urlopen(req, context=ctx)
                else: response = urllib2.urlopen(req)
            return response
        
        cj = cookielib.LWPCookieJar()

        response = None
        req      = None
        out_data = None
        opener   = None
        
        if 'host' in params:
            host = params['host']
        else:
            host = self.HOST

        if 'header' in params:
            headers = params['header']
        elif None != self.HEADER:
            headers = self.HEADER
        else:
            headers = { 'User-Agent' : host }

        printDBG('pCommon - getURLRequestData() -> params: ' + str(params))
        printDBG('pCommon - getURLRequestData() -> headers: ' + str(headers)) 

        customOpeners = []
        #cookie support
        if 'use_cookie' not in params and 'cookiefile' in params and ('load_cookie' in params or 'save_cookie' in params):
            params['use_cookie'] = True 
        
        if params.get('use_cookie', False):
            if params.get('load_cookie', False):
                try:
                    cj.load(params['cookiefile'], ignore_discard = True)
                except:
                    printExc()
            try:
                for cookieKey in params.get('cookie_items', {}).keys():
                    printDBG("cookie_item[%s=%s]" % (cookieKey, params['cookie_items'][cookieKey]))
                    cookieItem = cookielib.Cookie(version=0, name=cookieKey, value=params['cookie_items'][cookieKey], port=None, port_specified=False, domain='', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
                    cj.set_cookie(cookieItem)
            except:
                printExc()
            customOpeners.append( urllib2.HTTPCookieProcessor(cj) )
        # debug 
        #customOpeners.append(urllib2.HTTPSHandler(debuglevel=1))
        #customOpeners.append(urllib2.HTTPHandler(debuglevel=1))
        #proxy support
        if self.useProxy:
            http_proxy = self.proxyURL
        else:
            http_proxy = ''
        #proxy from parameters (if available) overwrite default one
        if 'http_proxy' in params:
            http_proxy = params['http_proxy']
        if '' != http_proxy:
            printDBG('getURLRequestData USE PROXY')
            customOpeners.append( urllib2.ProxyHandler({"http":http_proxy}) )
            customOpeners.append( urllib2.ProxyHandler({"https":http_proxy}) )

        if None != post_data:
            printDBG('pCommon - getURLRequestData() -> post data: ' + str(post_data))
            if params.get('raw_post_data', False):
                dataPost = post_data
            elif params.get('multipart_post_data', False):
                customOpeners.append( MultipartPostHandler() )
                dataPost = post_data
            else:
                dataPost = urllib.urlencode(post_data)
            req = urllib2.Request(params['url'], dataPost, headers)
        else:
            req = urllib2.Request(params['url'], None, headers)

        if not params.get('return_data', False):
            out_data = urlOpen(req, customOpeners)
        else:
            gzip_encoding = False
            try:
                response = urlOpen(req, customOpeners)
                if response.info().get('Content-Encoding') == 'gzip':
                    gzip_encoding = True
                data = response.read()
                response.close()
            except urllib2.HTTPError, e:
                if e.code == 404:
                    printDBG('!!!!!!!! 404: getURLRequestData - page not found handled')
                    if e.fp.info().get('Content-Encoding', '') == 'gzip':
                        gzip_encoding = True
                    data = e.fp.read()
                    #e.msg
                    #e.headers
                else:
                    if e.code in [300, 302, 303, 307] and params.get('use_cookie', False) and params.get('save_cookie', False):
                        new_cookie = e.fp.info().get('Set-Cookie', '')
                        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> new_cookie[%s]" % new_cookie)
                        #for cookieKey in params.get('cookie_items', {}).keys():
                        #    cj.clear('', '/', cookieKey)
                        cj.save(params['cookiefile'], ignore_discard = True)
                    raise e
            try:
                if gzip_encoding:
                    printDBG('Content-Encoding == gzip')
                    buf = StringIO(data)
                    f = gzip.GzipFile(fileobj=buf)
                    out_data = f.read()
                else:
                    out_data = data
            except:
                out_data = data
 
        if params.get('use_cookie', False) and params.get('save_cookie', False):
            cj.save(params['cookiefile'], ignore_discard = True)

        return out_data 


    def makeABCList(self):
        strTab = []
        strTab.append('0 - 9');
        for i in range(65,91):
            strTab.append(str(unichr(i)))    
        return strTab

    def isNumeric(self,s):
        try:
            float(s)
            return True
        except ValueError:
            return False
        
    def setLinkTable(self, url, host):
        strTab = []
        strTab.append(url)
        strTab.append(host)
        return strTab
    
class Chars:
    def __init__(self):
        pass
    
    def setCHARS(self):
        return CHARS
    
    def replaceString(self, array, string):
        out = string
        for i in range(len(array)):
            out = string.replace(array[i][0], array[i][1])
            string = out
        return out    
    
    def replaceChars(self, string):
        out = string
        for i in range(len(CHARS)):
            out = string.replace(CHARS[i][0], CHARS[i][1])
            string = out
        return out

