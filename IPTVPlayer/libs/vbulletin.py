# -*- coding: utf-8 -*-
#!/usr/bin/python
# based on : vBulletinLogin.py
# Created by Python (30/09/11)
# Xtremeroot.net

import urllib, urllib2, cookielib, hashlib, time, re
global WebPageCharSet
global ClearDBGfile
global outsidePLI
ClearDBGfile = True

try:
    from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
    outsidePLI = False
except:
    outsidePLI = True
    def printDBG( DBGtxt ):
        global ClearDBGfile, outsidePLI
        if ClearDBGfile == True:
            f = open('/tmp/iptv.dbg', 'w')
            ClearDBGfile = False
        else:
            f = open('/tmp/iptv.dbg', 'a')
        f.write(DBGtxt)
        f.close
        if outsidePLI == True and len(DBGtxt) < 800:
            print DBGtxt.encode('utf-8')

def GetFullThread(WebPage = -1):
    if WebPage == -1:
        WebPage = GetWebPage(url = 'forum.dvhk.pl', vdir = '/showthread.php?t=649501&page=9999')
    if WebPage == -1:
        printDBG("Brak WebPage, koniec\n")
        return -1
    PostsInThread = 'BŁAD'
    WebPage = WebPage.encode('utf8')
    if WebPage.find('<title>') > 0 and WebPage.find('</title>') > 0:
        PostsInThread = WebPage[WebPage.find('<title>')+len('<title>'):WebPage.find('</title>')] + '\n\n'
        
    printDBG("Tytul:" + PostsInThread)
    WebPage = WebPage[WebPage.find('<td class="thead" style="font-weight:normal" >'):]
    WebPage = WebPage.replace('\r','').replace('\n','').replace('<td class="thead" style="font-weight:normal" >','\nPostBegin=') #kazdy post w jednej linii
    WebPage = WebPage.replace('<div class="smallfont">','')
    WebPage = WebPage.replace('<img src="images/ranks/star-blue.png"','')
    WebPage = WebPage.replace('<img src="images/ranks/star-gold.png"','')
    WebPage = WebPage.replace('alt="" border="" />','')
    #zamiana emotikon na standardowe
    WebPage = WebPage.replace('<img src="images/smilies/newtongue.gif" border="0" alt="" title="Stick Out Tongue" class="inlineimg" />',':P')
    WebPage = WebPage.replace('<img src="images/smilies/newwink.gif" border="0" alt="" title="Wink" class="inlineimg" />',';)')
    WebPage = WebPage.replace('<img src="images/smilies/newbiggrin.gif" border="0" alt="" title="Big Grin" class="inlineimg" />',':D')
    WebPage = WebPage.replace('<img src="images/smilies/newblink.gif" border="0" alt="" title="EEK!" class="inlineimg" />',':o')
    WebPage = WebPage.replace('<img src="images/smilies/newsmile.gif" border="0" alt="" title="Smile" class="inlineimg" />',':)')
    WebPage = WebPage.replace('<img src="images/smilies/newsad.gif" border="0" alt="" title="Frown" class="inlineimg" />',':(')
    #wywalenie smieci
    WebPage = WebPage.replace('  ',' ').replace('\t\t\t','\t').replace('\t\t','\t')
    WebPage = re.sub('<font size="[0-9]">','',WebPage)
    WebPage = re.sub('<font color="[#a-zA-Z0-9]+?">','',WebPage)
    #WebPage = re.sub('<font color="#FF6600">','',WebPage)
    WebPage = re.sub('<[/]*[ibu]>','',WebPage)
    WebPage = re.sub('<[/]*strong>','',WebPage)
    WebPage = re.sub('\[[/]*SPOILER\]','',WebPage)
    WebPage = WebPage.replace('</font>','')
    WebPage = WebPage.replace('border="0" alt="" onload="NcodeImageResizer.createOn(this);"','')
    FullThread = re.findall('<!-- status icon and date -->(.+?)<!-- / status icon and date -->.+?<a class="bigusername" href="member.php(.+?)</span></a>\t<script type="text/javascript">.+?<!-- icon and title -->(.+?)<!-- / icon and title -->\t<!-- message -->(.+?)<!-- / message -->', WebPage)
    
    for Post in FullThread:
        DataPostu  = str(Post[0][Post[0].find('</a>')+4:].replace('\t','').replace('<a name="newpost"></a>',''))
        AutorPostu = str(Post[1][Post[1].find('font-weight:'):].split('>')[1])
        #PodTytulPostu = str(Post[2].encode('utf8'))
        TekstPostu = str(Post[3].replace('<br />','\n').strip())
        if TekstPostu[-6:] == '</div>':
            TekstPostu = TekstPostu[:-6]
        #obsluga cytatow
        LicznikCytatow = 0
        while (TekstPostu.count('<div class="smallfont" style="margin-bottom:2px">Cytat:</div>') > 0):
            LicznikCytatow = LicznikCytatow + 1
            TekstPostu = TekstPostu.replace('<div class="smallfont" style="margin-bottom:2px">Cytat:</div>','Cytat%i:"' % LicznikCytatow,1)
            TekstPostu = TekstPostu.replace('<table cellpadding="6" cellspacing="0" border="0" width="100%">\t<tr>\t<td class="alt2" style="border:1px inset">\t\t<div>','',1)
            TekstPostu = TekstPostu.replace('</table></div>','"\n',1)
        ######CYTATY!!!!!!!
        #>link do innego postu z cytatu
        TekstPostu = TekstPostu.replace('<img class="inlineimg" src="disturbed/buttons/viewpost.gif" border="0" alt="Zobacz post" />','')
        TekstPostu = TekstPostu.replace('<table cellpadding="6" cellspacing="0" border="0" width="100%">','<table>')
        TekstPostu = TekstPostu.replace('<div style="font-style:italic">','')
        TekstPostu = TekstPostu.replace('<td class="alt2" style="border:1px inset">','')
        TekstPostu = re.sub('<a href="showthread.php\?p=.+?" rel="nofollow"','',TekstPostu)
        #czyscimy formatowanie
        TekstPostu = re.sub('"[\t ]*[\t ]','" ',TekstPostu)
        TekstPostu = re.sub('[\t ]*[\t ]></a>\t</div>','>>\n',TekstPostu)
        TekstPostu = re.sub('</div>[\t ]*[\t ]</td>[\t ]*[\t ]</tr>[\t ]*[\t ]"',' "',TekstPostu)
        TekstPostu = re.sub('[\t]*<div id="post_message_[0-9]+?">','',TekstPostu)
        TekstPostu = re.sub('[\t]*<div style="margin:[0-9]+?px; margin-top:[0-9]+?px; ">','',TekstPostu)
        TekstPostu = TekstPostu.replace('<table>\t<tr>\t\t\t',' ')
        TekstPostu = re.sub('<a href="http://.+?[\t ]target="_blank">','',TekstPostu)
        ######KODy
        TekstPostu = TekstPostu.replace('<div style="margin:20px; margin-top:5px">\t<div class="smallfont" style="margin-bottom:2px">','@@@')
        TekstPostu = TekstPostu.replace('</pre></div>','@@@\n')
        TekstPostu = TekstPostu.replace('</div>\t<pre class="alt2" dir="ltr" style=" margin: 0px;\tpadding: 6px;\tborder: 1px inset;\twidth: 630px;\theight: 66px;\ttext-align: left;\toverflow: auto">','')
        TekstPostu = re.sub('</div>\t<pre class="alt2" dir="ltr" style=" margin: 0px;\tpadding: [0-9]+?px;\tborder: [0-9]+?px inset;\twidth: [0-9]+?px;\theight: [0-9]+?px;\ttext-align: left;\toverflow: auto">','',TekstPostu)
        #TekstPostu = TekstPostu.replace('','').replace('','').replace('','')
        PostsInThread = str(PostsInThread) + "\n########## " + DataPostu + ' , ' + AutorPostu + str(' napisał:\n')
        PostsInThread = PostsInThread + TekstPostu.strip() + '\n'
    printDBG(PostsInThread)
    return PostsInThread

def GetThreadsList(WebPage = -1 ):
    Threads = []
    if WebPage == -1:
        printDBG("GetThreadsList Pobieram WebPage\n")
        WebPage = GetDVHKforumContent()
    if WebPage == -1:
        print "GetThreadsList Brak WebPage, koniec"
        Threads.append({'threadID': 0,'threadICON': '','threadTITLE': str('Błąd logowania do DVHK!!!'), 'threadDESCR': str('Błąd logowania do DVHK!!!')})
        return Threads
    WebPage = WebPage[:WebPage.find('<td class="tfoot"')] # wywalenie stopki
    WebPage = WebPage[WebPage.find('<td class="alt1" id="td_threadstatusicon_'):] #wywalenie tego co zostalo z naglowka <td class="alt1" id="td_threadstatusicon_
    WebPage = WebPage.replace('\r','').replace('\n','').replace('<td class="alt1" id="td_threadstatusicon_','\nthreadID=') #kazdy post w jednej linii
    WebPage = WebPage.replace('  ',' ').replace('\t\t\t','\t').replace('\t\t','\t').replace('&quot;','').replace('&#10070;','') #wywalenie smieci
    WebPage = WebPage.replace('<img src="disturbed/statusicon/','threadICON=')
    WebPage = re.sub('<td class="alt2" title=".+?','',WebPage.encode('utf-8'))
    WebPage = re.sub('<div>.*<a href="showthread.php.*thread_title_[0-9]*" style="font-weight:bold">','\tthreadTITLE=',WebPage)#search,nowe posty
    WebPage = re.sub('<div>.*<a href="showthread.php.*thread_title_[0-9]*">','\tthreadTITLE=',WebPage)#lista na forum
    WebPage = re.sub('</a>[ \t]*</div>[ \t]*<div class=.*','=ENDthreadTITLE',WebPage)#koniec tytulu podfora
    WebPage = re.sub('</a>	<span class="smallfont" style="white-space:nowrap">','=ENDthreadTITLE',WebPage)#koniec tytulu podfora
    WebPage = re.sub('.gif.+?title=','\tthreadDESCR=',WebPage)
    WebPage = re.sub('<img class="inlineimg".+?','',WebPage)
    printDBG(WebPage +'\n')
    #for thread in re.findall('threadID=([0-9]+?)">.+?threadICON=(.+?) title="(.+?)">[ \t]+?<div>.+?bold">(.+?)</a>', WebPage.encode('utf-8')):
    ThreadsList = re.findall('threadID=([0-9]+?)">.+?threadICON=(.+?)\tthreadDESCR="(.+?)">[ \t]+?threadTITLE=(.+?)=ENDthreadTITLE', WebPage)
    for thread in ThreadsList:
        threadID = int(thread[0])
        threadICON = thread[1]
        threadDESCR = thread[2]
        threadTITLE =  thread[3]
        printDBG('threadID:'+ str(threadID) + '\nthreadICON:' + threadICON + '\nthreadTITLE:'+ threadTITLE + '\nthreadDESCR:' + threadDESCR + '\n')
        Threads.append({'threadID': threadID,'threadICON': threadICON,'threadTITLE': threadTITLE, 'threadDESCR': threadDESCR})
    return Threads
   
def GetForumsList(WebPage = -1):
    if WebPage == -1:
        WebPage = GetDVHKforumContent()
    if WebPage == -1:
        printDBG("Brak WebPage, koniec\n")
        return -1
    Forums = []
    if WebPage == -1:
        Forums.append({'ID': 0,'LEVEL': 0,'NAME': 'BŁĄD LOGOWANIA!!!', 'ParenID': 0})
        return Forums
    UsedIDs = []
    BlockedIDs = [97,124,112,35,158]
    level_0_ID = 0
    level_1_ID = 0
    level_2_ID = 0
    parentID = 0
    for forum in re.findall('<option value="([0-9]+?)".+?class="fjdpth([0123])".+?>(.+?)</option>', WebPage.encode('utf-8'), re.DOTALL):
        forumName = forum[2].strip()
        forumID = int(forum[0])
        forumlevel = int(forum[1])
        if forumlevel == 0:
            level_0_ID = forumID
            parentID = 0
        elif forumlevel == 1:
            level_1_ID = forumID
            parentID = level_0_ID
        elif forumlevel == 2:
            level_2_ID = forumID
            parentID = level_1_ID
        if forumName != '' and forumID not in UsedIDs and forumID not in BlockedIDs and parentID not in BlockedIDs:
            Forums.append({'ID': forumID,'LEVEL': forumlevel,'NAME': forumName, 'ParenID': parentID})
            UsedIDs.append(forumID)
    return Forums
# mniej danych do parsowania = szybciej dzialajacy skrypt
def GetDVHKforumContent(WebPage = -1):
    if WebPage == -1:
        printDBG("GetDVHKforumContent Pobieram WebPage\n")
        WebPage = GetWebPage()
    if WebPage == -1:
        printDBG("Brak WebPage, koniec\n")
        return -1
    #krok 1 - obcinamy gore strony
    Txt2Search = '<!-- / nav buttons bar -->'
    if WebPage.find(Txt2Search) > 0:
        WebPage = WebPage[WebPage.find(Txt2Search) + len(Txt2Search):]
    Txt2Search = '<!-- main -->'
    if WebPage.find(Txt2Search) > 0:
        WebPage = WebPage[WebPage.find(Txt2Search) + len(Txt2Search):]
    #krok 2 - obcinamy dol strony
    Txt2Search = '<!-- / close content container -->'
    if WebPage.find(Txt2Search) > 0:
        WebPage = WebPage[:WebPage.find(Txt2Search)]
    return WebPage

def GetWebPage(url = 'forum.dvhk.pl', vdir = '/search.php?do=getnew', uname = '', passwd = '' ):
    if uname == '' and passwd == '':
        printDBG("GetWebPage brak uname i passwd\n")
        try:
            file = open("/etc/enigma2/settings")
            for line in file:
                if line.startswith('config.plugins.iptvplayer.dvhk_login=' ) :
                    uname=line.split("=")[1].strip()
                    printDBG('Znaleziono uname:' + uname + '\n')
                if line.startswith('config.plugins.iptvplayer.dvhk_password=' ) :
                    passwd=line.split("=")[1].strip()
                    printDBG('Znaleziono passwd: XXXXXXX\n')
                if uname != '' and passwd != '':
                    break
        except:
            pass
        
    global WebPageCharSet
    if not url.startswith('http://'):
        url = 'http://' + url
    loginurl = url + '/login.php?do=login'
    if not vdir.startswith('/') and not url.endswith('/'):
        vdir = '/' + vdir
    forumurl = url + vdir
    md5 = hashlib.md5(passwd);md5 = md5.hexdigest()
    # Options for request
    opts = {
    'do': 'login',
    'vb_login_md5password': md5,
    'vb_login_md5password_utf': md5,
    's': '',
    'vb_login_username': uname, 
    'security_token': 'guest', 
    }
    data = urllib.urlencode(opts)
    
    # Request header
    global headers
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.0; en-GB; rv:1.8.1.12) Gecko/20100101 Firefox/7.0.1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-gb,en;q=0.5',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
    'Connection': 'keep-alive',
    'Referer': loginurl
    }
    
    # Cookie Handling
    jar = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
    
    # Send Request
    opener.addheader = headers
    opener.open(loginurl, data)
    # Check
    response = opener.open(forumurl)
    WebPageCharSet = response.headers.getparam('charset')
    #print kodowanie
    WebPage = response.read().decode(WebPageCharSet)
    WebPage = WebPage.replace('&quot;','"').replace('&amp;','&').replace('&lt;','<').replace('&gt;','>').replace('&nbsp;',' ')
    #poprawka smieci po kodowaniu html-a
    if 'login.php?do=logout' in WebPage:
        printDBG('GetWebPage:Zalogowany do dvhk\n')
        return WebPage
    else:
        printDBG('GetWebPage:Blad logowania do dvhk\n')
        return -1
