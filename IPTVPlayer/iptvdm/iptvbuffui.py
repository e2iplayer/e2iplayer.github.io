# -*- coding: utf-8 -*-
#
#  IPTV download manager UI
#
#  $Id$
#
#
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.cover import SimpleAnimatedCover
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, formatBytes, touch, eConnectCallback
from Plugins.Extensions.IPTVPlayer.components.iptvplayer import IPTVStandardMoviePlayer, IPTVMiniMoviePlayer
from Plugins.Extensions.IPTVPlayer.components.iptvextmovieplayer import IPTVExtMoviePlayer
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdownloadercreator import DownloaderCreator
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
###################################################

###################################################
# FOREIGN import
###################################################
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from enigma import getDesktop
from enigma import eTimer
from Components.config import config
from Components.ActionMap import ActionMap
from Components.Label import Label
#from Components.Sources.StaticText import StaticText
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS
from os import remove as os_remove
###################################################

class IPTVPlayerBufferingWidget(Screen):
    GST_FLV_DEMUX_IS_DEMUXING_INFINITE_FILE = "/tmp/gst_flv_demux_is_demuxing_infinite_file"
    NUM_OF_ICON_FRAMES = 8
    #######################
    #       SIZES
    #######################
    # screen size
    # we do not want borders, so make the screen lager than a desktop
    sz_w = getDesktop(0).size().width() 
    sz_h = getDesktop(0).size().height()
    # icon
    i_w = 128
    i_h = 128
    # percentage
    p_w = 120
    p_h = 120
    # console
    c_w = sz_w
    c_h = 80
    #######################
    #     POSITIONS
    #######################  
    start_y = (sz_h - (i_h + c_h)) / 2 
    # icon
    i_x = (sz_w - i_w) / 2
    i_y = start_y
    # percentage
    p_x = (sz_w - p_w) / 2
    p_y = start_y + (i_h - p_h) / 2
    # console
    c_x = 0
    c_y = i_y + i_h
    
    printDBG("[IPTVPlayerBufferingWidget] desktop size %dx%d" % (sz_w, sz_h) )
    skin = """
        <screen name="IPTVPlayerBufferingWidget"  position="center,center" size="%d,%d" title="IPTV Player Buffering...">
         <widget name="percentage" size="%d,%d"   position="%d,%d"  zPosition="5" valign="center" halign="center"  font="Regular;21" backgroundColor="black" transparent="1" /> #foregroundColor="white" shadowColor="black" shadowOffset="-1,-1"
         <widget name="console"    size="%d,%d"   position="%d,%d"  zPosition="5" valign="center" halign="center"  font="Regular;21" backgroundColor="black" transparent="1" />
         <widget name="icon"       size="%d,%d"   position="%d,%d"  zPosition="4" transparent="1" alphatest="blend" />
        </screen>""" %( sz_w, sz_h,         # screen
                        p_w, p_h, p_x, p_y, # percentage
                        c_w, c_h, c_x, c_y, # console
                        i_w, i_h, i_x, i_y  # icon
                      )
   
    def __init__(self, session, url, pathForRecordings, movieTitle, activMoviePlayer, requestedBuffSize):
        self.session = session
        Screen.__init__(self, session)
        self.onStartCalled = False
        
        self.recordingPath = pathForRecordings
        self.filePath      = pathForRecordings + '/.iptv_buffering.flv'
        self.url           = url
        self.movieTitle    = movieTitle
        
        self.currentService   = self.session.nav.getCurrentlyPlayingServiceReference()
        self.activMoviePlayer = activMoviePlayer
        
        self.onClose.append(self.__onClose)
        #self.onLayoutFinish.append(self.doStart)
        self.onShow.append(self.onWindowShow)
        #self.onHide.append(self.onWindowHide)
        
        self["actions"] = ActionMap(["WizardActions", "MoviePlayerActions"],
        {
            "ok":          self.ok_pressed,
            "back":        self.back_pressed,
            "leavePlayer": self.back_pressed,
        }, -1)     

        self["console"] = Label()
        self["percentage"] = Label()
             
        self["icon"] = SimpleAnimatedCover()
        # prepare icon frames path
        frames = []
        for idx in range(1,self.NUM_OF_ICON_FRAMES+1): frames.append( resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/icons/buffering/buffering_%d.png' % idx) )
        self["icon"].loadFrames(frames) 
        
        self.inMoviePlayer = False
        self.canRunMoviePlayer = False # used in function updateDisplay, so must be first initialized
        #main Timer
        self.mainTimer = eTimer()
        self.mainTimerEnabled = False
        self.mainTimer_conn = eConnectCallback(self.mainTimer.timeout, self.updateDisplay)
        self.mainTimerInterval = 1000 # by default 1s
        
        self.requestedBuffSize = requestedBuffSize
        
        
    #end def __init__(self, session):
 
    def onStart(self):
        '''
            this method is called once like __init__ but in __init__ we cannot display MessageBox
        '''
        self.lastPosition  = None
        self.lastSize = 0
        # create downloader
        self.downloader = DownloaderCreator(self.url)
        self._cleanedUp()
        if self.downloader:
            self.downloader.isWorkingCorrectly(self._startDownloader)
        else:
            self.session.openWithCallback(self.close, MessageBox, _("Pobieranie nie może zostać rozpoczęte.\n Podany adres ('%r') jest niepoprawny.") % self.url, type = MessageBox.TYPE_ERROR, timeout = 10)

    def _isFlvInfiniteFile(self, url):
        try:
            url = strwithmeta(url)
            if (url.startswith('rtmp') or url.split('?')[0].endswith('.f4m')) and url.meta.get('iptv_livestream', True): return True
        except: printExc()
        return False
        
    def _startDownloader(self, sts, reason):
        if sts:
            url,downloaderParams = DMHelper.getDownloaderParamFromUrl(self.url)
            if self._isFlvInfiniteFile(self.url):
                ret = touch(self.GST_FLV_DEMUX_IS_DEMUXING_INFINITE_FILE) # TODO: check returns value, and display message in case of False
            self.downloader.start(url, self.filePath, downloaderParams)
            self.setMainTimerSts(True)
            self.canRunMoviePlayer = True
        else:
            self.session.openWithCallback(self.close, MessageBox, _("Pobieranie nie może zostać rozpoczęte.\n Downloader %s nie działa prawidłowo.\nStatus[%s]") % (self.downloader.getName(), reason.strip()), type = MessageBox.TYPE_ERROR, timeout = 10 )

    def _isInLiveMode(self):
        if isinstance(self.url, strwithmeta):
            if 'iptv_livestream' in self.url.meta:
                return self.url.meta['iptv_livestream']
        # if we do not have information if it is live try to figure out from other sources
        if self.downloader:
            tmp = self.downloader.isLiveStream()
            if None != tmp:
                return tmp
        if self.url.startswith('rtmp'):
            return True
        
    def onEnd(self):
        self.setMainTimerSts(False)
        if self.downloader:
            self.downloader.terminate()
            self.downloader = None
        self._cleanedUp()

    def leaveMoviePlayer(self, ret=None, lastPosition=None, *args, **kwargs):
        printDBG("leaveMoviePlayer ret[%r], lastPosition[%r]" % (ret, lastPosition))
        # There is need to set None for current service
        # otherwise there is a problem with resuming play
        self.session.nav.playService(None)
        self.lastPosition = lastPosition
        self.canRunMoviePlayer = False
        self.inMoviePlayer = False
        
        #  ret == 1 - no data in buffer
        #  ret == 0 - triggered by user
        if 1 == ret:
            if DMHelper.STS.DOWNLOADING == self.downloader.getStatus():
                self.lastSize = self.downloader.getLocalFileSize(True)
                printDBG("IPTVPlayerBufferingWidget.leaveMoviePlayer: movie player consume all data from buffer - still downloading")
                self.confirmExitCallBack() # continue
            else:
                printDBG("IPTVPlayerBufferingWidget.leaveMoviePlayer: movie player consume all data from buffer - downloading finished")
                if DMHelper.STS.DOWNLOADED != self.downloader.getStatus(): 
                    self.session.openWithCallback(self.close, MessageBox, text=_("Nastąpił błąd pobierania."), type = MessageBox.TYPE_ERROR, timeout=5)
                else:
                    self.close()
        elif 0 == ret or None == ret:
            # ask if we should close
            self.lastSize = self.downloader.getLocalFileSize(True)
            self.session.openWithCallback(self.confirmExitCallBack, MessageBox, text=_("Zakończyć odtwarzanie?"), type=MessageBox.TYPE_YESNO)

    def confirmExitCallBack(self, ret=None):
        if ret and ret == True:
            self.close()
        else:
            if not self._isInLiveMode():
                self.canRunMoviePlayer = True
                self.setMainTimerSts(True)
            else:
                # for live streams we will remove old buffer and start downloader once again
                self.onEnd()
                self.onStart()

    def back_pressed(self):
        self.close()
        return

    def ok_pressed(self):
        if self.canRunMoviePlayer and self.downloader.getLocalFileSize() > 0:
            self.runMovePlayer()

    def runMovePlayer(self):
        # this shoudl not happen but to make sure
        if not self.canRunMoviePlayer:
            printDBG('called runMovePlayer with canRunMoviePlayer set to False')
            return
        
        self.inMoviePlayer = True
        buffSize = self.downloader.getLocalFileSize() - self.lastSize 
        printDBG("Run MoviePlayer with buffer size [%s]" % formatBytes(float(buffSize)) )
        self.setMainTimerSts(False)
        
        exteplayerBlocked =  strwithmeta(self.url).meta.get('iptv_block_exteplayer', False)
        printDBG("runMovePlayer >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> exteplayerBlocked[%s]" % exteplayerBlocked)
        
        player = self.activMoviePlayer
        printDBG('IPTVPlayerBufferingWidget.runMovePlayer [%r]' % player)
        if "mini" == player:
            self.session.openWithCallback(self.leaveMoviePlayer, IPTVMiniMoviePlayer, self.filePath, self.movieTitle, self.lastPosition, 4)
        elif "exteplayer" == player:
            if not exteplayerBlocked: self.session.openWithCallback(self.leaveMoviePlayer, IPTVExtMoviePlayer, self.filePath, self.movieTitle, self.lastPosition, 'eplayer', {'downloader':self.downloader})
            else: self.session.openWithCallback(self.leaveMoviePlayer, IPTVExtMoviePlayer, self.filePath, self.movieTitle, self.lastPosition, 'gstplayer', {'downloader':self.downloader})
        elif "extgstplayer" == player: self.session.openWithCallback(self.leaveMoviePlayer, IPTVExtMoviePlayer, self.filePath, self.movieTitle, self.lastPosition, 'gstplayer', {'downloader':self.downloader})
        else: self.session.openWithCallback(self.leaveMoviePlayer, IPTVStandardMoviePlayer, self.filePath, self.movieTitle)
            
    def setMainTimerSts(self, start):
        try:
            if start:
                if not self.mainTimerEnabled:
                    self.mainTimer.start(self.mainTimerInterval)
                    self.mainTimerEnabled = True
                    self.updateDisplay()
            else:
                if self.mainTimerEnabled:
                    self.mainTimer.stop()
                    self.mainTimerEnabled = False
        except: printDBG("setMainTimerSts status[%r] EXCEPTION" % start)
            
    def updateDisplay(self):
        printDBG("updateDisplay")
        if self.inMoviePlayer:
            printDBG("updateDisplay aborted - we are in moviePlayer")
            return

        if not self.mainTimerEnabled:
            printDBG("updateDisplay aborted - timer stoped")
            return

        self.downloader.updateStatistic()
        tmpBuffSize = self.downloader.getLocalFileSize() - self.lastSize + 1 # simple when getLocalFileSize() returns -1
        # remote size
        rFileSize = self.downloader.getRemoteFileSize()       
        if -1 == rFileSize: rFileSize = '??'
        else: rFileSize = formatBytes(float(rFileSize))
        # local size
        lFileSize = self.downloader.getLocalFileSize()
        if -1 == lFileSize: lFileSize = '??'
        else: lFileSize = formatBytes(float(lFileSize))
        # download speed
        dSpeed = self.downloader.getDownloadSpeed()
        if -1 == dSpeed: dSpeed = ''
        else: dSpeed = formatBytes(float(dSpeed))

        speed     = self.downloader.getDownloadSpeed()
        tmpStr    = ''
        if 0 < self.downloader.getLocalFileSize():
            if 0 <= self.downloader.getRemoteFileSize():
                tmpStr = "\n%s/%s" % (lFileSize, rFileSize)
            else:
                tmpStr = "\n%s" % (lFileSize)
            if 0 <= dSpeed:
               tmpStr += "\n%s/s" % (dSpeed)
        else:
            tmpStr += '\n\n'
        
        self["console"].setText(self.movieTitle + tmpStr)
        if tmpBuffSize > self.requestedBuffSize: percentage = 100
        else: percentage = (100 * tmpBuffSize) / self.requestedBuffSize
        self["percentage"].setText(str(percentage))
        self["icon"].nextFrame()
        
        # check if we start move player
        if self.canRunMoviePlayer:
            if tmpBuffSize >= self.requestedBuffSize or (self.downloader.getStatus() == DMHelper.STS.DOWNLOADED and 0 < self.downloader.getLocalFileSize()):
                self.runMovePlayer()
                return
        
        # check if it is downloading 
        if self.downloader.getStatus() not in [DMHelper.STS.DOWNLOADING, DMHelper.STS.WAITING]:
            self.session.openWithCallback(self.close, MessageBox, "Nastąpił błąd pobierania. \nStatus[%s], tmpBuffSize[%r], canRunMoviePlayer[%r]" % (self.downloader.getStatus(), tmpBuffSize, self.canRunMoviePlayer), type = MessageBox.TYPE_ERROR, timeout = 10 )
            self.canRunMoviePlayer = False
            # stop timer before message
            self.setMainTimerSts(False)

        return
    
    def __del__(self):
        printDBG('IPTVPlayerBufferingWidget.__del__ --------------------------------------')
        
    def __onClose(self):
        printDBG('IPTVPlayerBufferingWidget.__onClose ------------------------------------')
        self.onEnd()
        self.session.nav.playService(self.currentService)
        try:
            self.mainTimer_conn = None
            self.mainTimer = None
        except:   printExc()

        self.onClose.remove(self.__onClose)
        #self.onLayoutFinish.remove(self.doStart)
        self.onShow.remove(self.onWindowShow)
        #self.onHide.remove(self.onWindowHide)
        
    def _cleanedUp(self):
        if fileExists(self.filePath):
            try: os_remove(self.filePath)
            except: printDBG('Problem with removing old buffering file')
        if fileExists(self.GST_FLV_DEMUX_IS_DEMUXING_INFINITE_FILE):
            try: os_remove(self.GST_FLV_DEMUX_IS_DEMUXING_INFINITE_FILE)
            except: printDBG('Problem with removing gstreamer flag file [%s]' % self.GST_FLV_DEMUX_IS_DEMUXING_INFINITE_FILE)
    '''
    def doStart(self):
        if not self.onStartCalled:
            self.onStartCalled = True
            self.onStart()
    
    
    def onWindowHide(self): 
        self.visible = False
    '''

    def onWindowShow(self):
        if not self.onStartCalled:
            self.onStartCalled = True
            self.onStart()

#class IPTVPlayerWidget