# -*- coding: utf-8 -*-
#
#  IplaPlayer based on SHOUTcast
#
#  $Id$
#
# 

from time import sleep as time_sleep
from os import remove as os_remove, path as os_path
from urllib import quote as urllib_quote

####################################################
#                   E2 components
####################################################
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ScrollLabel import ScrollLabel
from Components.config import config, configfile
from Components.Sources.StaticText import StaticText
from Tools.BoundFunction import boundFunction
from Tools.LoadPixmap import LoadPixmap
from enigma import getDesktop, eTimer

####################################################
#                   IPTV components
####################################################
from Plugins.Extensions.IPTVPlayer.components.iptvfavouriteswidgets import IPTVFavouritesAddItemWidget, IPTVFavouritesMainWidget
 
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdownloadercreator import IsUrlDownloadable
from Plugins.Extensions.IPTVPlayer.libs.urlparser import urlparser
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import FreeSpace as iptvtools_FreeSpace, \
                                                          mkdirs as iptvtools_mkdirs, GetIPTVPlayerVerstion, GetVersionNum, \
                                                          printDBG, printExc, iptv_system, GetHostsList, \
                                                          eConnectCallback, GetSkinsDir, GetIconDir, GetPluginDir,\
                                                          SortHostsList, GetHostsOrderList, CSearchHistoryHelper, IsExecutable, \
                                                          CMoviePlayerPerHost, GetFavouritesDir
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvbuffui import IPTVPlayerBufferingWidget
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdmapi import IPTVDMApi, DMItem
from Plugins.Extensions.IPTVPlayer.iptvupdate.updatemainwindow import IPTVUpdateWindow, UpdateMainAppImpl

from Plugins.Extensions.IPTVPlayer.components.iptvconfigmenu import ConfigMenu
from Plugins.Extensions.IPTVPlayer.components.confighost import ConfigHostMenu
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, IPTVPlayerNeedInit
from Plugins.Extensions.IPTVPlayer.setup.iptvsetupwidget import IPTVSetupMainWidget
from Plugins.Extensions.IPTVPlayer.components.iptvplayer import IPTVStandardMoviePlayer, IPTVMiniMoviePlayer
from Plugins.Extensions.IPTVPlayer.components.iptvextmovieplayer import IPTVExtMoviePlayer
from Plugins.Extensions.IPTVPlayer.components.iptvpictureplayer import IPTVPicturePlayerWidget
from Plugins.Extensions.IPTVPlayer.components.iptvlist import IPTVMainNavigatorList
from Plugins.Extensions.IPTVPlayer.components.articleview import ArticleView
from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CDisplayListItem, RetHost, CUrlItem, ArticleContent, CFavItem
from Plugins.Extensions.IPTVPlayer.components.iconmenager import IconMenager
from Plugins.Extensions.IPTVPlayer.components.cover import Cover, Cover3
import Plugins.Extensions.IPTVPlayer.components.asynccall as asynccall

######################################################
gDownloadManager = None

class IPTVPlayerWidget(Screen):
    IPTV_VERSION = GetIPTVPlayerVerstion()
    screenwidth = getDesktop(0).size().width()
    if screenwidth and screenwidth == 1920:
        skin =  """
                    <screen name="IPTVPlayerWidget" position="center,center" size="1590,825" title="IPTV Player HD wersja %s">
                            <ePixmap position="5,9" zPosition="4" size="30,30" pixmap="%s" transparent="1" alphatest="on" />
                            <ePixmap position="180,9" zPosition="4" size="30,30" pixmap="%s" transparent="1" alphatest="on" />
                            <ePixmap position="385,9" zPosition="4" size="30,30" pixmap="%s" transparent="1" alphatest="on" />
                            <ePixmap position="700,9" zPosition="4" size="30,30" pixmap="%s" transparent="1" alphatest="on" />
                            <widget render="Label" source="key_red" position="45,9" size="140,32" zPosition="5" valign="center" halign="left" backgroundColor="black" font="Regular;32" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
                            <widget render="Label" source="key_yellow" position="220,9" size="180,32" zPosition="5" valign="center" halign="left" backgroundColor="black" font="Regular;32" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
                            <widget render="Label" source="key_green" position="425,9" size="300,32" zPosition="5" valign="center" halign="left" backgroundColor="black" font="Regular;32" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
                            <widget render="Label" source="key_blue" position="740,9" size="140,32" zPosition="5" valign="center" halign="left" backgroundColor="black" font="Regular;32" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
                            <widget name="headertext" position="15,55" zPosition="1" size="1080,30" font="Regular;30" transparent="1" backgroundColor="#00000000" />
                            <widget name="statustext" position="15,148" zPosition="1" size="985,90" font="Regular;30" halign="center" valign="center" transparent="1" backgroundColor="#00000000" />
                            <widget name="list" position="5,115" zPosition="2" size="860,690" scrollbarMode="showOnDemand" transparent="1" backgroundColor="#00000000" />
                            <widget name="console" position="1020,310" zPosition="1" size="500,630" font="Regular;26" transparent="1" backgroundColor="#00000000" />
                            <widget name="cover" zPosition="2" position="1020,80" size="244,280" alphatest="blend" />     
                            <widget name="playerlogo" zPosition="4" position="1264,3" size="240,80" alphatest="blend" />
                            <widget name="sequencer" position="0,0" zPosition="6" size="1090,625" font="Regular;160" halign="center" valign="center" transparent="1" backgroundColor="#00000000" />
                            <widget name="spinner"   zPosition="2" position="463,200" size="16,16" transparent="1" alphatest="blend" />
                            <widget name="spinner_1" zPosition="1" position="463,200" size="16,16" transparent="1" alphatest="blend" />
                            <widget name="spinner_2" zPosition="1" position="479,200" size="16,16" transparent="1" alphatest="blend" />
                            <widget name="spinner_3" zPosition="1" position="495,200" size="16,16" transparent="1" alphatest="blend" />
                            <widget name="spinner_4" zPosition="1" position="511,200" size="16,16" transparent="1" alphatest="blend" />
                    </screen>
                """ %( IPTV_VERSION, GetIconDir('red.png'), GetIconDir('yellow.png'), GetIconDir('green.png'), GetIconDir('blue.png'))
    else:
        skin =  """
                    <screen name="IPTVPlayerWidget" position="center,center" size="1090,525" title="IPTV Player wersja %s">
                            <ePixmap position="5,9" zPosition="4" size="30,30" pixmap="%s" transparent="1" alphatest="on" />
                            <ePixmap position="180,9" zPosition="4" size="30,30" pixmap="%s" transparent="1" alphatest="on" />
                            <ePixmap position="385,9" zPosition="4" size="30,30" pixmap="%s" transparent="1" alphatest="on" />
                            <ePixmap position="700,9" zPosition="4" size="30,30" pixmap="%s" transparent="1" alphatest="on" />
                            <widget render="Label" source="key_red" position="45,9" size="140,27" zPosition="5" valign="center" halign="left" backgroundColor="black" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
                            <widget render="Label" source="key_yellow" position="220,9" size="180,27" zPosition="5" valign="center" halign="left" backgroundColor="black" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
                            <widget render="Label" source="key_green" position="425,9" size="300,27" zPosition="5" valign="center" halign="left" backgroundColor="black" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
                            <widget render="Label" source="key_blue" position="740,9" size="140,27" zPosition="5" valign="center" halign="left" backgroundColor="black" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
                            <widget name="headertext" position="5,47" zPosition="1" size="1080,23" font="Regular;20" transparent="1" backgroundColor="#00000000" />
                            <widget name="statustext" position="5,140" zPosition="1" size="985,90" font="Regular;20" halign="center" valign="center" transparent="1" backgroundColor="#00000000" />
                            <widget name="list" position="5,100" zPosition="2" size="1080,280" scrollbarMode="showOnDemand" transparent="1" backgroundColor="#00000000" />
                            <widget name="console" position="165,430" zPosition="1" size="935,140" font="Regular;20" transparent="1" backgroundColor="#00000000" />
                            <widget name="cover" zPosition="2" position="5,400" size="122,140" alphatest="blend" />     
                            <widget name="playerlogo" zPosition="4" position="964,3" size="120,40" alphatest="blend" />
                            <ePixmap zPosition="4" position="5,395" size="1080,5" pixmap="%s" transparent="1" />
                            <widget name="sequencer" position="0,0" zPosition="6" size="1090,525" font="Regular;160" halign="center" valign="center" transparent="1" backgroundColor="#00000000" />
                            
                            <widget name="spinner"   zPosition="2" position="463,200" size="16,16" transparent="1" alphatest="blend" />
                            <widget name="spinner_1" zPosition="1" position="463,200" size="16,16" transparent="1" alphatest="blend" />
                            <widget name="spinner_2" zPosition="1" position="479,200" size="16,16" transparent="1" alphatest="blend" />
                            <widget name="spinner_3" zPosition="1" position="495,200" size="16,16" transparent="1" alphatest="blend" />
                            <widget name="spinner_4" zPosition="1" position="511,200" size="16,16" transparent="1" alphatest="blend" />
                    </screen>
                """ %( IPTV_VERSION, GetIconDir('red.png'), GetIconDir('yellow.png'), GetIconDir('green.png'), GetIconDir('blue.png'), GetIconDir('line.png'))      
    def __init__(self, session):
        printDBG("IPTVPlayerWidget.__init__ desktop IPTV_VERSION[%s]\n" % (IPTVPlayerWidget.IPTV_VERSION) )
        self.session = session
        path = GetSkinsDir(config.plugins.iptvplayer.skin.value) + "/playlist.xml" 
        try:    
            with open(path, "r") as f:
               self.skin = f.read()
               f.close()
        except: printExc("Skin read error: " + path)
                
        Screen.__init__(self, session)
        self.recorderMode = False #j00zek

        self.currentService = self.session.nav.getCurrentlyPlayingServiceReference()
        #self.session.nav.stopService()

        self["key_red"]    = StaticText(_("Exit"))
        self["key_green"]  = StaticText(_("Player > Recorder"))
        self["key_yellow"] = StaticText(_("Refresh"))
        self["key_blue"]   = StaticText(_("More"))

        self["list"] = IPTVMainNavigatorList()
        self["list"].connectSelChanged(self.onSelectionChanged)
        self["statustext"] = Label("Loading...")
        self["actions"] = ActionMap(["IPTVPlayerListActions", "WizardActions", "DirectionActions", "ColorActions", "NumberActions"],
        {
            "red"     :   self.red_pressed,
            "green"   :   self.green_pressed,
            "yellow"  :   self.yellow_pressed,
            "blue"    :   self.blue_pressed,
            "ok"      :   self.ok_pressed,
            "back"    :   self.back_pressed,
            "info"    :   self.info_pressed,
            "8"       :   self.startAutoPlaySequencer,
#            "0"       :   self.ok_pressedUseAlternativePlayer,
            "0"       :   self.ok_pressed0,
            "1"       :   self.ok_pressed1,
            "2"       :   self.ok_pressed2,
            "3"       :   self.ok_pressed3,
            "play"    :   self.startAutoPlaySequencer
        }, -1)

        self["headertext"] = Label()
        self["console"] = Label()
        self["sequencer"] = Label()
        
        self["cover"] = Cover()
        self["cover"].hide()
        self["playerlogo"] = Cover()
        
        try:
            for idx in range(5):
                spinnerName = "spinner"
                if idx: spinnerName += '_%d' % idx 
                self[spinnerName] = Cover3()
        except: printExc()
        
        # Check for plugin update
        self.lastPluginVersion  = ''
        self.checkUpdateConsole = None 
        self.checkUpdateTimer = eTimer()
        self.checkUpdateTimer_conn = eConnectCallback(self.checkUpdateTimer.timeout, self.__requestCheckUpdate)
        self.checkUpdateTimer_interval = 1000 * 60 * 60 * 2 # 2h
        self.__requestCheckUpdate()

        self.spinnerPixmap = [LoadPixmap(GetIconDir('radio_button_on.png')), LoadPixmap(GetIconDir('radio_button_off.png'))]
        self.useAlternativePlayer = False
        
        self.showMessageNoFreeSpaceForIcon = False
        self.iconMenager = None
        if config.plugins.iptvplayer.showcover.value:
            if not os_path.exists(config.plugins.iptvplayer.SciezkaCache.value):
                iptvtools_mkdirs(config.plugins.iptvplayer.SciezkaCache.value)

            if iptvtools_FreeSpace(config.plugins.iptvplayer.SciezkaCache.value,10):
                self.iconMenager = IconMenager(True)
            else:
                self.showMessageNoFreeSpaceForIcon = True
                self.iconMenager = IconMenager(False)
            self.iconMenager.setUpdateCallBack( self.checkIconCallBack )
        self.showHostsErrorMessage = True
        
        self.onClose.append(self.__onClose)
        #self.onLayoutFinish.append(self.onStart)
        self.onShow.append(self.onStart)
        
        #Defs
        self.searchPattern = CSearchHistoryHelper.loadLastPattern()[1]
        self.searchType = None
        self.workThread = None
        self.host       = None
        self.hostName     = ''
        self.hostFavTypes = []
        
        self.nextSelIndex = 0
        self.currSelIndex = 0
        
        self.prevSelList = []
        self.categoryList = []
      
        self.currList = []
        self.currItem = CDisplayListItem()

        self.visible = True
        self.bufferSize = config.plugins.iptvplayer.requestedBuffSize.value * 1024 * 1024
        
    
        #################################################################
        #                      Inits for Proxy Queue
        #################################################################
       
        # register function in main Queue
        if None == asynccall.gMainFunctionsQueue:
            asynccall.gMainFunctionsQueue = asynccall.CFunctionProxyQueue(self.session)
        asynccall.gMainFunctionsQueue.clearQueue()
        asynccall.gMainFunctionsQueue.setProcFun(self.doProcessProxyQueueItem)

        #main Queue
        self.mainTimer = eTimer()
        self.mainTimer_conn = eConnectCallback(self.mainTimer.timeout, self.processProxyQueue)
        # every 100ms Proxy Queue will be checked  
        self.mainTimer_interval = 100
        self.mainTimer.start(self.mainTimer_interval, True)
        
        # delayed decode cover timer
        self.decodeCoverTimer = eTimer()
        self.decodeCoverTimer_conn = eConnectCallback(self.decodeCoverTimer.timeout, self.doStartCoverDecode) 
        self.decodeCoverTimer_interval = 100
        
        # spinner timer
        self.spinnerTimer = eTimer()
        self.spinnerTimer_conn = eConnectCallback(self.spinnerTimer.timeout, self.updateSpinner) 
        self.spinnerTimer_interval = 200
        self.spinnerEnabled = False
        
        #################################################################
        
        #################################################################
        #                      Inits for IPTV Download Manager
        #################################################################
        global gDownloadManager
        if None == gDownloadManager:
            printDBG('============Initialize Download Menager============')
            gDownloadManager = IPTVDMApi(2, int(config.plugins.iptvplayer.IPTVDMMaxDownloadItem.value))
            if config.plugins.iptvplayer.IPTVDMRunAtStart.value:
                gDownloadManager.runWorkThread() 
        #################################################################


        #################################################################
        #                   Auto playing sequencer
        #################################################################
        self.autoPlaySeqStarted = False
        self.autoPlaySeqTimer = eTimer()
        self.autoPlaySeqTimer_conn = eConnectCallback(self.autoPlaySeqTimer.timeout, self.autoPlaySeqTimerCallBack)
        self.autoPlaySeqTimerValue = 0
        #################################################################
        
        self.activePlayer = None
    #end def __init__(self, session):
        
    def __del__(self):
        printDBG("IPTVPlayerWidget.__del__ --------------------------")

    def __onClose(self):
        self.session.nav.playService(self.currentService)
        self["list"].disconnectSelChanged(self.onSelectionChanged)
        #self["list"] = None
        #self["actions"] = None
        if None != self.checkUpdateConsole: self.checkUpdateConsole.terminate()
        if None != self.iconMenager:
            self.iconMenager.setUpdateCallBack(None)
            self.iconMenager.clearDQueue()
            self.iconMenager = None
        self.checkUpdateTimer_conn = None
        self.checkUpdateTimer = None
        self.mainTimer_conn = None
        self.mainTimer = None
        self.decodeCoverTimer_conn = None
        self.decodeCoverTimer = None
        self.spinnerTimer_conn = None
        self.spinnerTimer = None
           
        try:
            self.stopAutoPlaySequencer()
            self.autoPlaySeqTimer_conn = None         
            self.autoPlaySeqTimer = None
        except:
            printExc()

        try:
            asynccall.gMainFunctionsQueue.setProcFun(None)
            asynccall.gMainFunctionsQueue.clearQueue()
            iptv_system('echo 1 > /proc/sys/vm/drop_caches')
        except:
            printExc()
        self.activePlayer = None
            
    def loadSpinner(self):
        try:
            if "spinner" in self:
                self["spinner"].setPixmap(self.spinnerPixmap[0])
                for idx in range(4):
                    spinnerName = 'spinner_%d' % (idx + 1)
                    self[spinnerName].setPixmap(self.spinnerPixmap[1])
        except: printExc()
        
    def showSpinner(self):
        if None != self.spinnerTimer:
            self._setSpinnerVisibility(True)
            self.spinnerTimer.start(self.spinnerTimer_interval, True)
    
    def hideSpinner(self):
        self._setSpinnerVisibility(False)
    
    def _setSpinnerVisibility(self, visible=True):
        self.spinnerEnabled = visible
        try:
            if "spinner" in self:
                for idx in range(5):
                    spinnerName = "spinner"
                    if idx: spinnerName += '_%d' % idx
                    self[spinnerName].visible = visible
        except: printExc()
        
    def updateSpinner(self):
        try:
            if self.spinnerEnabled and None != self.workThread:
                if self.workThread.isAlive():
                    if "spinner" in self:
                        x, y = self["spinner"].getPosition()
                        x   += self["spinner"].getWidth()
                        if x > self["spinner_4"].getPosition()[0]:
                            x = self["spinner_1"].getPosition()[0]
                        self["spinner"].setPosition(x, y)
                    if None != self.spinnerTimer:
                        self.spinnerTimer.start(self.spinnerTimer_interval, True)
                        return
                elif not self.workThread.isFinished():
                    message = _('It seems that the host "%s" has crashed. Do you want to report this problem?') % self.hostName
                    message += _('\nMake sure you are using the latest version of the plugin.')
                    self.session.openWithCallback(self.reportHostCrash, MessageBox, text=message, type=MessageBox.TYPE_YESNO)
            self.hideSpinner()
        except: printExc()
        
    def reportHostCrash(self, ret):
        try:
            if ret:
                try: 
                    exceptStack = self.workThread.getExceptStack()
                    reporter = GetPluginDir('iptvdm/reporthostcrash.py')
                    msg = urllib_quote('%s|%s|%s|%s' % ('HOST_CRASH', IPTVPlayerWidget.IPTV_VERSION, self.hostName, self.getCategoryPath()))
                    self.crashConsole = iptv_system('python "%s" "http://iptvplayer.vline.pl/reporthostcrash.php?msg=%s" "%s" 2&>1 > /dev/null' % (reporter, msg, exceptStack))
                    printDBG(msg)
                except:
                    printExc()
            self.workThread = None
            self.prevSelList = []
            self.back_pressed()
        except: printExc()

    def processProxyQueue(self):
        if None != self.mainTimer:
            asynccall.gMainFunctionsQueue.processQueue()
            self.mainTimer.start(self.mainTimer_interval, True)
        return
        
    def doProcessProxyQueueItem(self, item):
        try:
            if None == item.retValue[0] or self.workThread == item.retValue[0]:
                if isinstance(item.retValue[1], asynccall.CPQParamsWrapper): getattr(self, method)(*item.retValue[1])
                else: getattr(self, item.clientFunName)(item.retValue[1])
            else:
                printDBG('>>>>>>>>>>>>>>> doProcessProxyQueueItem callback from old workThread[%r][%s]' % (self.workThread, item.retValue))
        except: printExc()
            
    def getArticleContentCallback(self, thread, ret):
        asynccall.gMainFunctionsQueue.addToQueue("showArticleContent", [thread, ret])
        
    def selectHostVideoLinksCallback(self, thread, ret):
        asynccall.gMainFunctionsQueue.addToQueue("selectMainVideoLinks", [thread, ret])
        
    def getResolvedURLCallback(self, thread, ret):
        asynccall.gMainFunctionsQueue.addToQueue("selectResolvedVideoLinks", [thread, ret])
        
    def callbackGetList(self, addParam, thread, ret):
        asynccall.gMainFunctionsQueue.addToQueue("reloadList", [thread, {'add_param':addParam, 'ret':ret}])
        
    # method called from IconMenager when a new icon has been dowlnoaded
    def checkIconCallBack(self, ret):
        asynccall.gMainFunctionsQueue.addToQueue("displayIcon", [None, ret])
        
    def isInWorkThread(self):
        return None != self.workThread and (not self.workThread.isFinished() or self.workThread.isAlive())
 
    def red_pressed(self):
        self.stopAutoPlaySequencer()
        self.close()
        return

    def green_pressed(self):
        self.stopAutoPlaySequencer()
        if self.recorderMode and IsExecutable( DMHelper.GET_WGET_PATH() ):
            self.recorderMode = False
            printDBG( "IPTV - tryb Odtwarzacza" )
            self["key_green"].setText(_("Player > Recorder"))
        elif not IsExecutable( DMHelper.GET_WGET_PATH() ):
            self.recorderMode = False
            self["key_green"].setText(_("Player > Recorder"))
        else:
            self.recorderMode = True
            printDBG( "IPTV - tryb Rekordera" )
            self["key_green"].setText(_("Recorder > Player"))
        return

    def yellow_pressed(self):
        self.stopAutoPlaySequencer()
        self.getRefreshedCurrList()
        return
     
    def blue_pressed(self):       
        self.stopAutoPlaySequencer()
        options = []
        
        if -1 < self.canByAddedToFavourites()[0]: 
            options.append((_("Add item to favourites"), "ADD_FAV"))
            options.append((_("Edit favourites"), "EDIT_FAV"))
        elif 'favourites' == self.hostName: options.append((_("Edit favourites"), "EDIT_FAV"))
        
        if None != self.activePlayer.get('player', None): title = _('Change active movie player')
        else: title = _('Set active movie player')
        options.append((title, "SetActiveMoviePlayer"))
        try:
            host = __import__('Plugins.Extensions.IPTVPlayer.hosts.host' + self.hostName, globals(), locals(), ['GetConfigList'], -1)
            if( len( host.GetConfigList() ) > 0 ):
                options.append((_("Configure host"), "HostConfig"))
        except: printExc()
        options.append((_("Info"), "info"))
        options.append((_("IPTV download manager"), "IPTVDM"))
        self.session.openWithCallback(self.blue_pressed_next, ChoiceBox, title = _("Select option"), list = options)

    def pause_pressed(self):
        printDBG('pause_pressed')
        self.stopAutoPlaySequencer()
        
    def startAutoPlaySequencer(self):
        if not self.autoPlaySeqStarted:
            self.autoPlaySeqStarted = True
            self.autoPlaySequencerNext(False)
        
    def stopAutoPlaySequencer(self):
        if self.autoPlaySeqStarted:
            #try: raise
            #except: printExc()
            self.autoPlaySeqTimer.stop()
            self["sequencer"].setText("")
            self.autoPlaySeqStarted = False
            return True
        return False

    def autoPlaySequencerNext(self, goToNext=True):
        if not self.autoPlaySeqStarted:
            printDBG("ERROR in autoPlaySequencerNext - sequencer stopped")
            return
        
        idx = self.getSelIndex()
        if -1 != idx:
            # find next playable item
            if goToNext:  idx += 1
            while idx < len(self.currList):
                if self.currList[idx].type in [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO, CDisplayListItem.TYPE_MORE]:
                    break
                else:
                    idx += 1
            if idx < len(self.currList):
                self["list"].moveToIndex(idx)
                self.sequencerPressOK()
                return
        self.stopAutoPlaySequencer()
    
    def sequencerPressOK(self):
        self.autoPlaySeqTimerValue = 3
        self["sequencer"].setText(str(self.autoPlaySeqTimerValue))
        self.autoPlaySeqTimer.start(1000)
            
    def autoPlaySeqTimerCallBack(self):
        self.autoPlaySeqTimerValue -= 1
        if self.autoPlaySeqTimerValue > 0:
            self["sequencer"].setText(str(self.autoPlaySeqTimerValue))
        else:
            self["sequencer"].setText("")
            self.autoPlaySeqTimer.stop()
            self.ok_pressed('sequencer')
        
    def checkAutoPlaySequencer(self):
        if self.autoPlaySeqStarted:
            self.autoPlaySequencerNext()
            return True
        return False

    def blue_pressed_next(self, ret):
        TextMSG = ''
        if ret:
            if ret[1] == "info": #informacje o wtyczce
                TextMSG = _("Autors: samsamsam, zdzislaw22, mamrot, MarcinO, skalita, huball, matzg, tomashj291")
                self.session.open(MessageBox, TextMSG, type = MessageBox.TYPE_INFO, timeout = 10 )
            elif ret[1] == "IPTVDM":
                self.runIPTVDM()
            elif ret[1] == "HostConfig":
                self.runConfigHostIfAllowed()
            elif ret[1] == "SetActiveMoviePlayer":
                options = []
                if None != self.activePlayer.get('player', None): options.append((_("Auto selection based on the settings"), {}))
                player = self.getMoviePlayer(True, False)
                printDBG("SetActiveMoviePlayer [%r]" % dir(player))
                options.append((_("[%s] with buffering") % player.getText(), {'buffering':True, 'player':player}))
                player = self.getMoviePlayer(True, True)
                options.append((_("[%s] with buffering") % player.getText(), {'buffering':True, 'player':player}))
                player = self.getMoviePlayer()
                options.append((_("[%s] without buffering") % player.getText(), {'buffering':False, 'player':player}))
                self.session.openWithCallback(self.setActiveMoviePlayer, ChoiceBox, title = _("Select movie player"), list = options)
            elif ret[1] == 'ADD_FAV':
                currSelIndex = self.canByAddedToFavourites()[0]
                self.requestListFromHost('ForFavItem', currSelIndex, '')
            elif ret[1] == 'EDIT_FAV':
                self.session.openWithCallback(self.editFavouritesCallback, IPTVFavouritesMainWidget)
    
    def editFavouritesCallback(self, ret=False):
        if ret and 'favourites' == self.hostName: # we must reload host
            self.loadHost()
    
    def setActiveMoviePlayer(self, ret):
        if ret: self.activePlayer.set(ret[1])

    def runIPTVDM(self, callback=None):
        global gDownloadManager
        if None != gDownloadManager:
            from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdmui import IPTVDMWidget
            if None == callback: self.session.open(IPTVDMWidget, gDownloadManager)
            else: self.session.openWithCallback(callback, IPTVDMWidget, gDownloadManager)
        elif None != callback: callback()
        return
        
    def displayIcon(self, ret=None, doDecodeCover=False):
        # check if displays icon is enabled in options
        if not config.plugins.iptvplayer.showcover.value or None == self.iconMenager :
            return
        
        selItem = self.getSelItem()
        # when ret is != None the method is called from IconMenager 
        # and in this variable the url for icon which was downloaded 
        # is returned
        # if icon for other than selected item has been downloaded 
        # the displayed icon will not be changed
        if ret != None and selItem != None and ret != selItem.iconimage:
            return
    
        # Display icon
        if selItem and '' != selItem.iconimage and self.iconMenager:
            # check if we have this icon and get the path to this icon on disk
            iconPath = self.iconMenager.getIconPathFromAAueue(selItem.iconimage)
            printDBG('displayIcon -> getIconPathFromAAueue: ' + selItem.iconimage)
            if '' != iconPath and not self["cover"].checkDecodeNeeded(iconPath):
                self["cover"].show()
                return
            else:
                if doDecodeCover:
                    self["cover"].decodeCover(iconPath, self.updateCover, "cover")
                else:
                    self.decodeCoverTimer.start(self.decodeCoverTimer_interval, True)
        self["cover"].hide()
        
    def doStartCoverDecode(self):
        if self.decodeCoverTimer:
            self.displayIcon(None, doDecodeCover=True)
            
    def updateCover(self, retDict):
        # retDict - return dictionary  {Ident, Pixmap, FileName, Changed}
        printDBG('updateCover')
        if retDict:
            printDBG("updateCover retDict for Ident: %s " % retDict["Ident"])
            updateIcon = False
            if 'cover' == retDict["Ident"]:
                #check if we have icon for right item on list
                selItem = self.getSelItem()
                if selItem and '' != selItem.iconimage:
                    # check if we have this icon and get the path to this icon on disk
                    iconPath = self.iconMenager.getIconPathFromAAueue(selItem.iconimage)
                    
                    if iconPath == retDict["FileName"]:
                        # now we are sure that we have right icon
                        updateIcon = True
                        self.decodeCoverTimer_interval = 100
                    else: self.decodeCoverTimer_interval = 1000
            else: 
                updateIcon = True
            if updateIcon:
                if None != retDict["Pixmap"]:
                    self[retDict["Ident"]].updatePixmap(retDict["Pixmap"], retDict["FileName"])
                    self[retDict["Ident"]].show()
                else:
                    self[retDict["Ident"]].hide()
        else:
            printDBG("updateCover retDict empty")
    #end updateCover(self, retDict):
                
    def changeBottomPanel(self):
        self.displayIcon()
        selItem = self.getSelItem()
        if selItem and selItem.description != '':
            data = selItem.description
            sData = data.replace('\n','')
            self["console"].setText(sData)
        else:
            self["console"].setText('')
    
    def onSelectionChanged(self):
        self.changeBottomPanel()

    def back_pressed(self):
        if self.stopAutoPlaySequencer() and self.autoPlaySeqTimerValue: return
        try:
            if self.isInWorkThread():
                if self.workThread.kill():
                    self.workThread = None
                    self["statustext"].setText("Operation aborted!")
                return
        except: return    
        if self.visible:
                       
            if len(self.prevSelList) > 0:
                self.nextSelIndex = self.prevSelList.pop()
                self.categoryList.pop()
                printDBG( "back_pressed prev sel index %s" % self.nextSelIndex )
                self.requestListFromHost('Previous')
            else:
                #There is no prev categories, so exit
                #self.close()
                self.askUpdateAvailable(self.selectHost)
        else:
            self.showWindow()
    #end back_pressed(self):
    
    def info_pressed(self):
        printDBG('info_pressed')
        if self.visible and not self.isInWorkThread():
            try: 
                item = self.getSelItem()
            except:
                printExc()
                item = None
            if None != item:
                self.stopAutoPlaySequencer()
                self.currSelIndex = currSelIndex = self["list"].getCurrentIndex()
                self.requestListFromHost('ForArticleContent', currSelIndex)
    #end info_pressed(self):
    
#    def ok_pressedUseAlternativePlayer(self):
#        self.ok_pressed(useAlternativePlayer=True)

    def ok_pressed0(self):
        self.activePlayer.set({}) 
        self.ok_pressed(useAlternativePlayer=False)

    def ok_pressed1(self):
        player = self.getMoviePlayer(True, False)
        self.activePlayer.set({'buffering':True, 'player':player}) 
        self.ok_pressed(useAlternativePlayer=True)

    def ok_pressed2(self):
        player = self.getMoviePlayer(True, True)
        self.activePlayer.set({'buffering':True, 'player':player}) 
        self.ok_pressed(useAlternativePlayer=True)

    def ok_pressed3(self):
        player = self.getMoviePlayer()
        self.activePlayer.set({'buffering':False, 'player':player}) 
        self.ok_pressed(useAlternativePlayer=False)
    
    def ok_pressed(self, eventFrom='remote', useAlternativePlayer=False):
        self.useAlternativePlayer = useAlternativePlayer
        if 'sequencer' != eventFrom:
            self.stopAutoPlaySequencer()
        if self.visible:
            sel = None
            try:
                sel = self["list"].l.getCurrentSelection()[0]
            except:
                printExc
                self.getRefreshedCurrList()
                return
            if sel is None:
                printDBG( "ok_pressed sel is None" )
                self.stopAutoPlaySequencer()
                self.getInitialList()
                return
            elif len(self.currList) <= 0:
                printDBG( "ok_pressed list is empty" )
                self.stopAutoPlaySequencer()
                self.getRefreshedCurrList()
                return
            else:
                printDBG( "ok_pressed selected item: %s" % (sel.name) )
                
                item = self.getSelItem()  
                self.currItem = item
                
                #Get current selection
                currSelIndex = self["list"].getCurrentIndex()
                #remember only prev categories
                if item.type in [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO, CDisplayListItem.TYPE_PICTURE]:
                    if CDisplayListItem.TYPE_AUDIO == item.type: 
                        self.bufferSize = config.plugins.iptvplayer.requestedAudioBuffSize.value * 1024
                    else: self.bufferSize = config.plugins.iptvplayer.requestedBuffSize.value * 1024 * 1024
                    # check if separete host request is needed to get links to VIDEO
                    if item.urlSeparateRequest == 1:
                        printDBG( "ok_pressed selected TYPE_VIDEO.urlSeparateRequest" )
                        self.requestListFromHost('ForVideoLinks', currSelIndex)
                    else:
                        printDBG( "ok_pressed selected TYPE_VIDEO.selectLinkForCurrVideo" )
                        self.selectLinkForCurrVideo()
                elif item.type == CDisplayListItem.TYPE_CATEGORY:
                    printDBG( "ok_pressed selected TYPE_CATEGORY" )
                    self.stopAutoPlaySequencer()
                    self.currSelIndex = currSelIndex
                    self.requestListFromHost('ForItem', currSelIndex, '')
                elif item.type == CDisplayListItem.TYPE_MORE:
                    printDBG( "ok_pressed selected TYPE_MORE" )
                    self.currSelIndex = currSelIndex
                    self.requestListFromHost('ForMore', currSelIndex, '')
                elif item.type == CDisplayListItem.TYPE_ARTICLE:
                    printDBG( "ok_pressed selected TYPE_ARTICLE" )
                    self.info_pressed()
                else:
                    printDBG( "ok_pressed selected TYPE_SEARCH" )
                    self.stopAutoPlaySequencer()
                    self.currSelIndex = currSelIndex
                    self.startSearchProcedure(item.possibleTypesOfSearch)
        else:
            self.showWindow()
    #end ok_pressed(self):
    
    def leaveArticleView(self):
        printDBG("leaveArticleView")
        pass
    
    def showArticleContent(self, ret):
        printDBG("showArticleContent")
        self["statustext"].setText("")            
        self["list"].show()

        artItem = None
        if ret.status != RetHost.OK or 0 == len(ret.value):
            item = self.currList[self.currSelIndex]
            if len(item.description):
                artItem = ArticleContent(title = item.name, text = item.description, images = [{'title':'Fot.', 'url':item.iconimage}])
        else:
            artItem = ret.value[0]
        if None != artItem:
            self.session.openWithCallback(self.leaveArticleView, ArticleView, artItem)
    
    def selectMainVideoLinks(self, ret):
        printDBG( "selectMainVideoLinks" )
        self["statustext"].setText("")
        self["list"].show()
        
        # ToDo: check ret.status if not OK do something :P
        if ret.status != RetHost.OK:
            printDBG( "++++++++++++++++++++++ selectHostVideoLinksCallback ret.status = %s" % ret.status )
        else:
            # update links in List
            currSelIndex = self.getSelIndex()
            if -1 == currSelIndex: return
            self.currList[currSelIndex].urlItems = ret.value
        self.selectLinkForCurrVideo()
    #end selectMainVideoLinks(self, ret):
    
    def selectResolvedVideoLinks(self, ret):
        printDBG( "selectResolvedVideoLinks" )
        self["statustext"].setText("")
        self["list"].show()
        linkList = []
        if ret.status == RetHost.OK and isinstance(ret.value, list):
            for item in ret.value:
                if isinstance(item, CUrlItem): 
                    item.urlNeedsResolve = 0 # protection from recursion 
                    linkList.append(item)
                elif isinstance(item, basestring): linkList.append(CUrlItem(item, item, 0))
                else: printExc("selectResolvedVideoLinks: wrong resolved url type!")
        else: printExc()
        self.selectLinkForCurrVideo(linkList)
 
    def getSelIndex(self):
        currSelIndex = self["list"].getCurrentIndex()
        if len(self.currList) > currSelIndex:
            return currSelIndex
        return -1

    def getSelItem(self):
        currSelIndex = self["list"].getCurrentIndex()
        if len(self.currList) <= currSelIndex:
            printDBG( "ERROR: getSelItem there is no item with index: %d, listOfItems.len: %d" % (currSelIndex, len(self.currList)) )
            return None
        return self.currList[currSelIndex]
        
    def getSelectedItem(self):
        sel = None
        try:
            sel = self["list"].l.getCurrentSelection()[0]
        except:return None
        return sel
        
    def onStart(self):
        self.onShow.remove(self.onStart)
        #self.onLayoutFinish.remove(self.onStart)
        self.loadSpinner()
        self.hideSpinner()
        self.askUpdateAvailable(self.selectHost)
    
    def __requestCheckUpdate(self):
        lastVerUrl = 'http://iptvplayer.pl/download/update/lastversion.php'
        if config.plugins.iptvplayer.autoCheckForUpdate.value:
            self.checkUpdateTimer.start(self.checkUpdateTimer_interval, True)
            if IsExecutable( DMHelper.GET_WGET_PATH() ):
                cmd = '%s "%s" -O - 2> /dev/null ' % (DMHelper.GET_WGET_PATH(), lastVerUrl)
                if None != self.checkUpdateConsole: self.checkUpdateConsole.terminate()
                printDBG("__requestCheckUpdate cmd[%r]" % cmd)
                self.checkUpdateConsole = iptv_system( cmd, self.__checkUpdateCmdFinished )
                
    def __checkUpdateCmdFinished(self, status, lastversion):
        printDBG("__checkUpdateCmdFinished  status[%r] lastversion[%r]" % (status, lastversion))
        if 0 == status and 50000000 < GetVersionNum(lastversion):
            self.lastPluginVersion = lastversion
        
    def askUpdateAvailable(self, NoUpdateCallback):
        if  config.plugins.iptvplayer.autoCheckForUpdate.value \
            and  0 < GetVersionNum( self.lastPluginVersion ) \
            and GetVersionNum( self.lastPluginVersion ) > GetVersionNum( GetIPTVPlayerVerstion() ) \
            and self.lastPluginVersion != config.plugins.iptvplayer.updateLastCheckedVersion.value:
            
            message = _('There is a new version available do you want to update? \nYour version [%s], latest version on server [%s]') % (GetIPTVPlayerVerstion(), self.lastPluginVersion)
            config.plugins.iptvplayer.updateLastCheckedVersion.value = self.lastPluginVersion
            config.plugins.iptvplayer.updateLastCheckedVersion.save()
            configfile.save()
            self.session.openWithCallback(boundFunction(self.answerUpdateAvailable, NoUpdateCallback), MessageBox, text=message, type=MessageBox.TYPE_YESNO)
            return
        NoUpdateCallback()
        
    def answerUpdateAvailable(self, NoUpdateCallback, ret):
        try:
            if ret: self.session.openWithCallback(self.displayListOfHosts, IPTVUpdateWindow, UpdateMainAppImpl(self.session), True)
            else: NoUpdateCallback()
        except: printExc()
        
    def selectHost(self):
        self.host = None
        self.hostName = ''
        self.nextSelIndex = 0
        self.prevSelList = []
        self.categoryList = []
        self.currList = []
        self.currItem = CDisplayListItem()

        self.displayHostsList = [] 
        sortedList = SortHostsList( GetHostsList() )
        brokenHostList = []
        for hostName in sortedList:
            hostEnabled  = False
            try:
                exec('if config.plugins.iptvplayer.host' + hostName + '.value: hostEnabled = True')
            except:
                hostEnabled = False
            if True == hostEnabled:
                if not config.plugins.iptvplayer.devHelper.value:
                    try:
                        _temp = __import__('Plugins.Extensions.IPTVPlayer.hosts.host' + hostName, globals(), locals(), ['gettytul'], -1)
                        title = _temp.gettytul()
                    except:
                        printExc('get host name exception for host "%s"' % hostName)
                        brokenHostList.append('host'+hostName)
                        continue # do not use default name if import name will failed
                else:
                    _temp = __import__('Plugins.Extensions.IPTVPlayer.hosts.host' + hostName, globals(), locals(), ['gettytul'], -1)
                    title = _temp.gettytul()
                self.displayHostsList.append((title, hostName))
        # if there is no order hosts list use old behavior
        if 0 == len(GetHostsOrderList()):
            self.displayHostsList.sort()
        self.displayHostsList.append((_("Configuration"), "config"))
        
        # prepare info message when some host or update cannot be used
        errorMessage = ""
        if len(brokenHostList) > 0:
            errorMessage = _("Following host are broken or additional python modules are needed.") + '\n' + '\n'.join(brokenHostList)
     
        if config.plugins.iptvplayer.AktualizacjaWmenu.value == True:
            self.displayHostsList.append((_("Update"), "update"))
                
        try:     import json 
        except:
            try: import simplejson
            except: errorMessage = errorMessage + "\n" + _("JSON module not available!")
        
        if "" != errorMessage and True == self.showHostsErrorMessage:
            self.showHostsErrorMessage = False
            self.session.openWithCallback(self.displayListOfHosts, MessageBox, errorMessage, type = MessageBox.TYPE_INFO, timeout = 10 )
        else:
            self.displayListOfHosts()
        return

    def displayListOfHosts(self, arg = None):
        if config.plugins.iptvplayer.ListaGraficzna.value == False:
            self.session.openWithCallback(self.selectHostCallback, ChoiceBox, title=_("Select service"), list = self.displayHostsList)
        else:
            from playerselector import PlayerSelectorWidget
            self.session.openWithCallback(self.selectHostCallback, PlayerSelectorWidget, list = self.displayHostsList)
        return
    
    def selectHostCallback(self, ret):
        checkUpdate = True
        try: 
            if 0 < len(ret) and ret[1] == "update": checkUpdate = False
        except: pass
        if checkUpdate: self.askUpdateAvailable(boundFunction(self.selectHostCallback2, ret))
        else: self.selectHostCallback2(ret)

    def selectHostCallback2(self, ret):
        hasIcon = False
        nextFunction = None
        protectedByPin = False 
        if ret:
            if ret[1] == "config":
                nextFunction = self.runConfig
                protectedByPin = config.plugins.iptvplayer.configProtectedByPin.value
            elif ret[1] == "noupdate":
                self.close()
                return
            elif ret[1] == "update":
                self.session.openWithCallback(self.displayListOfHosts, IPTVUpdateWindow, UpdateMainAppImpl(self.session))
                return
            elif ret[1] == "IPTVDM":
                self.runIPTVDM(self.selectHost)
                return
            else: # host selected
                self.hostName = ret[1] 
                self.loadHost()
                
            if self.showMessageNoFreeSpaceForIcon and hasIcon:
                self.showMessageNoFreeSpaceForIcon = False
                self.session.open(MessageBox, (_("There is no free space on the drive [%s].") % config.plugins.iptvplayer.SciezkaCache.value) + "\n" + _("New icons will not be available."), type = MessageBox.TYPE_INFO, timeout=10)
        else:
            self.close()
            return
            
        if nextFunction:
            if True == protectedByPin:
                from iptvpin import IPTVPinWidget
                self.session.openWithCallback(boundFunction(self.checkPin, nextFunction, self.selectHost), IPTVPinWidget, title=_("Enter pin"))
            else:
                nextFunction()

    def runConfig(self):
        self.session.openWithCallback(self.configCallback, ConfigMenu)
        
    def runConfigHostIfAllowed(self):
        if config.plugins.iptvplayer.configProtectedByPin.value:
            from iptvpin import IPTVPinWidget
            self.session.openWithCallback(boundFunction(self.checkPin, self.runConfigHost, None), IPTVPinWidget, title=_("Enter pin"))
        else:
            self.runConfigHost()

    def runConfigHost(self):
        self.session.openWithCallback(self.runConfigHostCallBack, ConfigHostMenu, hostName = self.hostName)
        
    def runConfigHostCallBack(self, confgiChanged=False):
        if confgiChanged: self.loadHost()

    def checkPin(self, callbackFun, failCallBackFun, pin=None):
        if pin != None:
            if pin == config.plugins.iptvplayer.pin.value:
                callbackFun();
            else:
                self.session.openWithCallback(self.close, MessageBox, _("Pin incorrect!"), type = MessageBox.TYPE_INFO, timeout = 5 )
        else:
            if failCallBackFun:
                failCallBackFun()

    def loadHost(self):
        self.hostFavTypes = []
        if not config.plugins.iptvplayer.devHelper.value:
            try:
                _temp = __import__('Plugins.Extensions.IPTVPlayer.hosts.host' + self.hostName, globals(), locals(), ['IPTVHost'], -1)
                self.host = _temp.IPTVHost()
                if not isinstance(self.host, IHost):
                    printDBG("Host [%r] does not inherit from IHost" % self.hostName)
                    self.close()
                    return
            except:
                printExc( 'Cannot import class IPTVHost for host [%r]' %  self.hostName)
                self.close()
                return
        else:
            _temp = __import__('Plugins.Extensions.IPTVPlayer.hosts.host' + self.hostName, globals(), locals(), ['IPTVHost'], -1)
            self.host = _temp.IPTVHost()
            
        try: protectedByPin = self.host.isProtectedByPinCode()
        except: protected = False # should never happen
        
        if protectedByPin:
            from iptvpin import IPTVPinWidget
            self.session.openWithCallback(boundFunction(self.checkPin, self.loadHostData, self.selectHost), IPTVPinWidget, title=_("Enter pin"))
        else: self.loadHostData();

    def loadHostData(self):
        if None != self.activePlayer: self.activePlayer.save()
        self.activePlayer = CMoviePlayerPerHost(self.hostName)

        # change logo for player
        self["playerlogo"].hide()
        try:
            hRet= self.host.getLogoPath()
            if hRet.status == RetHost.OK and  len(hRet.value):
                logoPath = hRet.value[0]
                    
                if logoPath != '':
                    printDBG('Logo Path: ' + logoPath)
                    self["playerlogo"].decodeCover(logoPath, \
                                                   self.updateCover, \
                                                   "playerlogo")
        except: printExc()
        
        # get types of items which can be added as favourites
        self.hostFavTypes = []
        try:
            hRet = self.host.getSupportedFavoritesTypes()
            if hRet.status == RetHost.OK: self.hostFavTypes = hRet.value
        except: printExc('The current host crashed')
        
        # request initial list from host        
        self.getInitialList()
    #end selectHostCallback(self, ret):

    def selectLinkForCurrVideo(self, customUrlItems=None):
        if not self.visible:
            self["statustext"].setText("")
            self.showWindow()
        
        item = self.getSelItem()
        if item.type not in [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO, CDisplayListItem.TYPE_PICTURE]:
            printDBG("Incorrect icon type[%s]" % item.type)
            return
        
        if None == customUrlItems: links = item.urlItems
        else: links = customUrlItems
        
        options = []
        for link in links:
            printDBG("selectLinkForCurrVideo: |%s| |%s|" % (link.name, link.url))
            if type(u'') == type(link.name):
                link.name = link.name.encode('utf-8', 'ignore')
            if type(u'') == type(link.url):
                link.url = link.url.encode('utf-8', 'ignore')
            options.append((link.name, link.url, link.urlNeedsResolve))
        
        #There is no free links for current video
        numOfLinks = len(links)
        if 0 == numOfLinks:
            if not self.checkAutoPlaySequencer(): 
                self.session.open(MessageBox, _("No valid links available."), type=MessageBox.TYPE_INFO, timeout=10 )
            return
        elif 1 == numOfLinks or self.autoPlaySeqStarted:
            #call manualy selectLinksCallback - start VIDEO without links selection
            arg = []
            arg.append(" ") #name of item - not displayed so empty
            arg.append(links[0].url) #url to VIDEO
            arg.append(links[0].urlNeedsResolve) # if 1 this links should be resolved
            self.selectLinksCallback(arg)
            return

        #options.sort(reverse=True)
        self.session.openWithCallback(self.selectLinksCallback, ChoiceBox, title=_("Select link"), list = options)

        
    def selectLinksCallback(self, retArg):
        # retArg[0] - name
        # retArg[1] - url src
        # retArg[2] - urlNeedsResolve
        if retArg and 3 == len(retArg):
            #check if we have URL
            if isinstance(retArg[1], basestring):
                videoUrl = retArg[1]
                if len(videoUrl) > 3:
                    #check if we need to resolve this URL
                    if str(retArg[2]) == '1':
                        #call resolve link from host
                        self.requestListFromHost('ResolveURL', -1, videoUrl)
                    else:
                        list = []
                        list.append(videoUrl)
                        self.playVideo(RetHost(status = RetHost.OK, value = list))
                    return
            self.playVideo(RetHost(status = RetHost.ERROR, value = []))
    # end selectLinksCallback(self, retArg):
        
    def checkBuffering(self, url):
        # check flag forcing of the using/not using buffering
        if 'iptv_buffering' in url.meta:
            if "required" == url.meta['iptv_buffering']:
                # iptv_buffering was set as required, this is done probably due to 
                # extra http headers needs, at now extgstplayer can handle this headers,
                # so we skip forcing buffering for such links. at now this is temporary 
                # solution we need to add separate filed iptv_extraheaders_need!
                if url.startswith("http") and "extgstplayer" == config.plugins.iptvplayer.NaszPlayer.value: pass # skip forcing buffering
                else: return True
            elif "forbidden" == url.meta['iptv_buffering']:
                return False
        if "|" in url:
            return True
        
        # check based on protocol
        protocol = url.meta.get('iptv_proto', '')
        protocol = url.meta.get('iptv_proto', '')
        if protocol in ['f4m', 'uds']:
            return True # supported only in buffering mode
        elif protocol in ['http', 'https']:
            return config.plugins.iptvplayer.buforowanie.value
        elif 'rtmp' == protocol:
            return config.plugins.iptvplayer.buforowanie_rtmp.value
        elif 'm3u8' == protocol:
            return config.plugins.iptvplayer.buforowanie_m3u8.value
        
    def isUrlBlocked(self, url):
        protocol = url.meta.get('iptv_proto', '')
        if ".wmv" == self.getFileExt(url) and config.plugins.iptvplayer.ZablokujWMV.value :
            return True, _("Format 'wmv' blocked in configuration.")
        elif '' == protocol:
            return True, _("Unknown protocol [%s]") % url
        return False, ''
        
    def getFileExt(self, url):
        format = url.meta.get('iptv_format', '')
        if '' != format: return '.' + format
        protocol = url.meta.get('iptv_proto', '')
        if url.endswith(".wmv"): fileExtension   = '.wmv'
        elif url.endswith(".mp4"): fileExtension = '.mp4'
        elif url.endswith(".flv"): fileExtension = '.flv'
        elif protocol in ['mms', 'mmsh', 'rtsp']: fileExtension = '.wmv'
        elif protocol in ['f4m', 'uds', 'rtmp']: fileExtension = '.flv'
        else: fileExtension = '.mp4' # default fileExtension
        return fileExtension
        
    def getMoviePlayer(self, buffering=False, useAlternativePlayer=False):
        printDBG("getMoviePlayer")
        # select movie player
        if buffering:
            if 'sh4' == config.plugins.iptvplayer.plarform.value:
                if useAlternativePlayer: player = config.plugins.iptvplayer.alternativeSH4MoviePlayer
                else: player = config.plugins.iptvplayer.defaultSH4MoviePlayer
            elif 'mipsel' == config.plugins.iptvplayer.plarform.value:
                if useAlternativePlayer: player = config.plugins.iptvplayer.alternativeMIPSELMoviePlayer
                else: player = config.plugins.iptvplayer.defaultMIPSELMoviePlayer
            elif 'i686' == config.plugins.iptvplayer.plarform.value:
                if useAlternativePlayer: player = config.plugins.iptvplayer.alternativeI686MoviePlayer
                else: player = config.plugins.iptvplayer.defaultI686MoviePlayer
            else: player = config.plugins.iptvplayer.NaszPlayer
        else: player = config.plugins.iptvplayer.NaszPlayer
        return player

    def playVideo(self, ret):
        printDBG( "playVideo" )
        url = ''
        if RetHost.OK == ret.status:
            if len(ret.value) > 0:
                url = ret.value[0]
        
        self["statustext"].setText("")            
        self["list"].show()
        
        if url != '' and CDisplayListItem.TYPE_PICTURE == self.currItem.type:
            self.session.open(IPTVPicturePlayerWidget, url, config.plugins.iptvplayer.bufferingPath.value, self.currItem.name)
        elif url != '' and self.currItem.type in [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO]:
            printDBG( "playVideo url[%s]" % url)
            url = urlparser.decorateUrl(url)
            titleOfMovie = self.currItem.name.replace('/','-').replace(':','-').replace('*','-').replace('?','-').replace('"','-').replace('<','-').replace('>','-').replace('|','-')
            fileExtension = self.getFileExt(url)            
                        
            blocked, reaseon = self.isUrlBlocked(url)
            if blocked:
                self.session.open(MessageBox, reaseon, type = MessageBox.TYPE_INFO, timeout = 10)
                return

            isBufferingMode = self.activePlayer.get('buffering', self.checkBuffering(url))
            if not self.recorderMode:
                pathForRecordings = config.plugins.iptvplayer.bufferingPath.value
            else:
                pathForRecordings = config.plugins.iptvplayer.NaszaSciezka.value
            fullFilePath = pathForRecordings + '/' + titleOfMovie + fileExtension
             
            if (self.recorderMode or isBufferingMode) and not iptvtools_FreeSpace(pathForRecordings, 500):
                self.stopAutoPlaySequencer()
                self.session.open(MessageBox, _("There is no free space on the drive [%s].") % pathForRecordings, type=MessageBox.TYPE_INFO, timeout=10)
            elif self.recorderMode:
                global gDownloadManager
                if None != gDownloadManager:
                    if IsUrlDownloadable(url):
                        ret = gDownloadManager.addToDQueue( DMItem(url, fullFilePath) )
                    else:
                        ret = False
                        self.session.open(MessageBox, _("File can not be downloaded. Protocol [%s] is unsupported") % url.meta.get('iptv_proto', ''), type=MessageBox.TYPE_INFO, timeout=10)
                    if ret:
                        if not self.checkAutoPlaySequencer():
                            if config.plugins.iptvplayer.IPTVDMShowAfterAdd.value:
                                self.runIPTVDM()
                            else:
                                self.session.open(MessageBox, _("File [%s] was added to downloading queue.") % titleOfMovie, type=MessageBox.TYPE_INFO, timeout=10)
                    else:
                        self.stopAutoPlaySequencer()
                else:
                    self.stopAutoPlaySequencer()
            elif isBufferingMode:
                self.session.nav.stopService()
                player = self.activePlayer.get('player', self.getMoviePlayer(True, self.useAlternativePlayer))
                self.session.openWithCallback(self.leaveMoviePlayer, IPTVPlayerBufferingWidget, url, pathForRecordings, titleOfMovie, player.value, self.bufferSize)
            else:
                self.session.nav.stopService()
                player = self.activePlayer.get('player', config.plugins.iptvplayer.NaszPlayer)
                if "mini" == player.value:
                    self.session.openWithCallback(self.leaveMoviePlayer, IPTVMiniMoviePlayer, url, self.currItem.name)
                elif "standard" == player.value:
                    self.session.openWithCallback(self.leaveMoviePlayer, IPTVStandardMoviePlayer, url, self.currItem.name)
                else:
                    gstAdditionalParams = {}
                    gstAdditionalParams['download-buffer-path'] = ''
                    gstAdditionalParams['ring-buffer-max-size'] = 0
                    if 'sh4' == config.plugins.iptvplayer.plarform.value: # use default value, due to small amount of RAM
                        #use the default value, due to small amount of RAM
                        #in the future it will be configurable
                        gstAdditionalParams['buffer-duration'] = -1
                        gstAdditionalParams['buffer-size']     = 0
                    else:
                        gstAdditionalParams['buffer-duration'] = 18000 # 300min
                        gstAdditionalParams['buffer-size']     = 10240 # 10MB
                    self.session.openWithCallback(self.leaveMoviePlayer, IPTVExtMoviePlayer, url, self.currItem.name, None, 'gstplayer', gstAdditionalParams)
        else:
            #There was problem in resolving direct link for video
            if not self.checkAutoPlaySequencer():
                self.session.open(MessageBox, _("No valid links available."), type=MessageBox.TYPE_INFO, timeout=10)
    #end playVideo(self, ret):
        
    def leaveMoviePlayer(self, answer = None, lastPosition = None, *args, **kwargs):
        self.session.nav.playService(self.currentService)
        self.checkAutoPlaySequencer()
    
    def requestListFromHost(self, type, currSelIndex = -1, videoUrl = ''):
        
        if not self.isInWorkThread():
            self["list"].hide()
            
            if type not in ['ForVideoLinks', 'ResolveURL', 'ForArticleContent', 'ForFavItem']:
                #hide bottom panel
                self["cover"].hide()
                self["console"].setText('')
                
            if type == 'ForItem' or type == 'ForSearch':
                self.prevSelList.append(self.currSelIndex)
                if type == 'ForSearch':
                    self.categoryList.append('Search results')
                else:
                    self.categoryList.append(self.currItem.name) 
                #new list, so select first index
                self.nextSelIndex = 0
            
            selItem = None
            if currSelIndex > -1 and len(self.currList) > currSelIndex:
                selItem = self.currList[currSelIndex]
            
            dots = ""#_("...............")
            IDS_DOWNLOADING = _("Downloading") + dots
            IDS_LOADING     = _("Loading") + dots
            IDS_REFRESHING  = _("Refreshing") + dots
            try:
                if type == 'Refresh':
                    self["statustext"].setText(IDS_REFRESHING)
                    self.workThread = asynccall.AsyncMethod(self.host.getCurrentList, boundFunction(self.callbackGetList, {'refresh':1, 'selIndex':currSelIndex}), True)(1)
                elif type == 'ForMore':
                    self["statustext"].setText(IDS_DOWNLOADING)
                    self.workThread = asynccall.AsyncMethod(self.host.getMoreForItem, boundFunction(self.callbackGetList, {'refresh':2, 'selIndex':currSelIndex}), True)(currSelIndex)
                elif type == 'Initial':
                    self["statustext"].setText(IDS_DOWNLOADING)
                    self.workThread = asynccall.AsyncMethod(self.host.getInitList, boundFunction(self.callbackGetList, {}), True)()
                elif type == 'Previous':
                    self["statustext"].setText(IDS_DOWNLOADING)
                    self.workThread = asynccall.AsyncMethod(self.host.getPrevList, boundFunction(self.callbackGetList, {}), True)()
                elif type == 'ForItem':
                    self["statustext"].setText(IDS_DOWNLOADING)
                    self.workThread = asynccall.AsyncMethod(self.host.getListForItem, boundFunction(self.callbackGetList, {}), True)(currSelIndex, 0, selItem)
                elif type == 'ForVideoLinks':
                    self["statustext"].setText(IDS_LOADING)
                    self.workThread = asynccall.AsyncMethod(self.host.getLinksForVideo, self.selectHostVideoLinksCallback, True)(currSelIndex, selItem)
                elif type == 'ResolveURL':
                    self["statustext"].setText(IDS_LOADING)
                    self.workThread = asynccall.AsyncMethod(self.host.getResolvedURL, self.getResolvedURLCallback, True)(videoUrl)
                elif type == 'ForSearch':
                    self["statustext"].setText(IDS_LOADING)
                    self.workThread = asynccall.AsyncMethod(self.host.getSearchResults, boundFunction(self.callbackGetList, {}), True)(self.searchPattern, self.searchType)
                elif type == 'ForArticleContent':
                    self["statustext"].setText(IDS_DOWNLOADING)
                    self.workThread = asynccall.AsyncMethod(self.host.getArticleContent, self.getArticleContentCallback, True)(currSelIndex)
                elif type == 'ForFavItem':
                    self["statustext"].setText(IDS_LOADING)
                    self.workThread = asynccall.AsyncMethod(self.host.getFavouriteItem, self.getFavouriteItemCallback, True)(currSelIndex)
                else:
                    printDBG( 'requestListFromHost unknown list type: ' + type )
                self.showSpinner()
            except:
                printExc('The current host crashed')
    #end requestListFromHost(self, type, currSelIndex = -1, videoUrl = ''):
        
    def startSearchProcedure(self, searchTypes):
        sts, prevPattern = CSearchHistoryHelper.loadLastPattern()
        if sts: self.searchPattern = prevPattern
        if searchTypes:
            self.session.openWithCallback(self.selectSearchTypeCallback, ChoiceBox, title=_("Search type"), list = searchTypes)
        else:
            self.searchType = None
            self.session.openWithCallback(self.enterPatternCallBack, VirtualKeyBoard, title=(_("Your search entry")), text = self.searchPattern)
    
    def selectSearchTypeCallback(self, ret = None):
        if ret:
            self.searchType = ret[1]
            self.session.openWithCallback(self.enterPatternCallBack, VirtualKeyBoard, title=(_("Your search entry")), text = self.searchPattern)
        else:
            pass
            # zrezygnowal z wyszukiwania

    def enterPatternCallBack(self, callback = None):
        if callback is not None and len(callback):  
            self.searchPattern = callback
            CSearchHistoryHelper.saveLastPattern(self.searchPattern)
            self.requestListFromHost('ForSearch')
        else:
            pass
            # zrezygnowal z wyszukiwania

    def configCallback(self):
        if IPTVPlayerNeedInit():
            self.session.openWithCallback(self.selectHost, IPTVSetupMainWidget, True)
        else:
            self.askUpdateAvailable(self.selectHost)

    def reloadList(self, params):
        printDBG( "reloadList" )
        refresh  = params['add_param'].get('refresh', 0)
        selIndex = params['add_param'].get('selIndex', 0)
        ret      = params['ret']
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> IPTVPlayerWidget.reloadList refresh[%s], selIndex[%s]" % (refresh, selIndex))
        if 0 < refresh and 0 < selIndex:
            self.nextSelIndex = selIndex
        # ToDo: check ret.status if not OK do something :P
        if ret.status != RetHost.OK:
            printDBG( "++++++++++++++++++++++ reloadList ret.status = %s" % ret.status )
            self.stopAutoPlaySequencer()

        self.currList = ret.value
        self["list"].setList([ (x,) for x in self.currList])
        
        ####################################################
        #                   iconMenager
        ####################################################
        iconList = []
        # fill icon List for icon manager 
        # if an user whant to see icons
        if config.plugins.iptvplayer.showcover.value and self.iconMenager:
            for it in self.currList:
                if it.iconimage != '':
                    iconList.append(it.iconimage)
        
        if len(iconList):
            # List has been changed so clear old Queue
            self.iconMenager.clearDQueue()
            # a new list of icons should be downloaded
            self.iconMenager.addToDQueue(iconList)
        #####################################################
        
        self["headertext"].setText(self.getCategoryPath())
        if len(self.currList) <= 0:
            disMessage = _("No item to display. \nPress OK to refresh.\n")
            if ret.message and ret.message != '':
                disMessage += ret.message
            self["statustext"].setText(disMessage)
            self["list"].hide()
        else:
            #restor previus selection
            if len(self.currList) > self.nextSelIndex:
                self["list"].moveToIndex(self.nextSelIndex)
            #else:
            #selection will not be change so manualy call
            self.changeBottomPanel()
            
            self["statustext"].setText("")            
            self["list"].show()
        if 2 == refresh:
            self.autoPlaySequencerNext(False)
    #end reloadList(self, ret):
    
    def getCategoryPath(self):
        def _getCat(cat, num):
            if '' == cat: return ''
            cat = ' > ' + cat
            if 1 < num: cat += (' (x%d)' % num)
            return cat

        str = self.hostName
        prevCat = ''
        prevNum = 0
        for cat in self.categoryList:
            if prevCat != cat:
                str += _getCat(prevCat, prevNum) 
                prevCat = cat
                prevNum = 1
            else: prevNum += 1
        str += _getCat(prevCat, prevNum) 
        return str

    def getRefreshedCurrList(self):
        currSelIndex = self["list"].getCurrentIndex()
        self.requestListFromHost('Refresh', currSelIndex)

    def getInitialList(self):
        self.nexSelIndex = 0
        self.prevSelList = []
        self.categoryList = []
        self.currList = []
        self.currItem = CDisplayListItem()
        self["headertext"].setText(self.getCategoryPath())
        self.requestListFromHost('Initial')

    def hideWindow(self):
        self.visible = False
        self.hide()

    def showWindow(self):
        self.visible = True
        self.show()

    def createSummary(self):
        return IPTVPlayerLCDScreen
        
    def canByAddedToFavourites(self):
        try: favouritesHostActive = config.plugins.iptvplayer.hostfavourites.value
        except: favouritesHostActive = False
        cItem = None
        index = -1
        # we need to check if fav is available
        if favouritesHostActive and len(self.hostFavTypes) and self.visible and \
           None != self.getSelectedItem() and \
           self.getSelItem().type in self.hostFavTypes:
            cItem = self.getSelItem()
            index = self.getSelIndex()
        return index, cItem
        
    def getFavouriteItemCallback(self, thread, ret):
        asynccall.gMainFunctionsQueue.addToQueue("handleFavouriteItemCallback", [thread, ret])
        
    def handleFavouriteItemCallback(self, ret):
        printDBG("IPTVPlayerWidget.handleFavouriteItemCallback")
        self["statustext"].setText("")
        self["list"].show()
        linkList = []
        if ret.status == RetHost.OK and \
           isinstance(ret.value, list) and \
            1 == len(ret.value) and isinstance(ret.value[0], CFavItem):
            favItem = ret.value[0]
            if CFavItem.RESOLVER_SELF == favItem.resolver: favItem.resolver = self.hostName
            self.session.open(IPTVFavouritesAddItemWidget, favItem)
        else: self.session.open(MessageBox, _("No valid links available."), type=MessageBox.TYPE_INFO, timeout=10 )
    
#class IPTVPlayerWidget

class IPTVPlayerLCDScreen(Screen):
    skin = """
    <screen position="0,0" size="132,64" title="IPTVPlayer">
        <widget name="text1" position="4,0" size="132,14" font="Regular;12" halign="center" valign="center"/>
         <widget name="text2" position="4,14" size="132,49" font="Regular;10" halign="center" valign="center"/>
    </screen>"""

    def __init__(self, session, parent):
        Screen.__init__(self, session)
        self["text1"] =  Label("IPTVPlayer")
        self["text2"] = Label("")

    def setText(self, text):
        self["text2"].setText(text[0:39])

