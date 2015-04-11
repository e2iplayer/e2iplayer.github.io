# -*- coding: utf-8 -*-
#
#  IPTVExtMoviePlayer
#
#  $Id$
#
# 

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.components.cover import Cover3
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetIPTVDMImgDir, GetBinDir, eConnectCallback
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
###################################################

###################################################
# FOREIGN import
###################################################
from enigma import eServiceReference, eConsoleAppContainer, getDesktop, eTimer
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.config import config
from Components.Label import Label
from Components.ProgressBar import ProgressBar
from Screens.MessageBox import MessageBox
from Tools.LoadPixmap import LoadPixmap
from Tools.BoundFunction import boundFunction

from datetime import timedelta
try:
    try:    import json
    except: import simplejson as json
except:
    printExc()
from os import chmod as os_chmod
import re
###################################################

class ExtPlayerCommandsDispatcher():
    def __init__(self, owner):
        self.owner = owner
        
        #SEEK_SPEED_MAP = [0.125, 0.25, 0.5, 0, 2, 4, 8, 16, 32, 64, 128]
        self.SEEK_SPEED_MAP = []
        for item in reversed(config.seek.speeds_slowmotion.value):
            self.SEEK_SPEED_MAP.append(1.0 / float(item))
        self.SEEK_SPEED_MAP.append(0)
        for item in config.seek.speeds_forward.value:
            self.SEEK_SPEED_MAP.append( item )
        self.speedIdx = self.SEEK_SPEED_MAP.index(0)
        
    def stop(self):
        self.extPlayerSendCommand('PLAYBACK_STOP')
        self.owner = None
        
    def play(self): 
        self.extPlayerSendCommand('PLAYBACK_CONTINUE')
        self.speedIdx = self.SEEK_SPEED_MAP.index(0)
    def pause(self):            
        self.extPlayerSendCommand('PLAYBACK_PAUSE')
        self.speedIdx = self.SEEK_SPEED_MAP.index(0)
    def doSeek(self, diff):       
        self.extPlayerSendCommand('PLAYBACK_SEEK_RELATIVE', '%d' %diff)
        self.speedIdx = self.SEEK_SPEED_MAP.index(0)
    def doGoToSeek(self, arg):       
        self.extPlayerSendCommand('PLAYBACK_SEEK_ABS', arg)
        self.speedIdx = self.SEEK_SPEED_MAP.index(0)
    def doSeekFwd(self, arg):    self.extPlayerSendCommand('PLAYBACK_FASTFORWARD', arg)
    def doSlowMotion(self, arg): self.extPlayerSendCommand('PLAYBACK_SLOWMOTION', arg)
    
    def doUpdateInfo(self):
        self.extPlayerSendCommand('PLAYBACK_LENGTH', '', False)
        self.extPlayerSendCommand('PLAYBACK_CURRENT_TIME', '', False)

    ##############################################
    
    def seekFwd(self):
        printDBG('seekFwd skipped')
        return
        self.speedIdx += 1
        self.tipMode()
    def seekBack(self):
        printDBG('seekBack skipped')
        return
        self.speedIdx -= 1
        self.tipMode()        
    def tipMode(self):
        printDBG("ExtPlayerCommandsDispatcher.tipMode speedIdx[%d]" % self.speedIdx)
        if self.speedIdx >= len(self.SEEK_SPEED_MAP): self.speedIdx = len(self.SEEK_SPEED_MAP) - 1
        elif self.speedIdx < 0: self.speedIdx = 0
        val = self.SEEK_SPEED_MAP[self.speedIdx]
        printDBG("ExtPlayerCommandsDispatcher.tipMode val[%r]" % val)
        if 0 == val:  self.play()
        elif 1 < val:
            if 'eplayer' == self.owner.player: val -= 1
            self.doSeekFwd(str(val))
        else: self.doSlowMotion(str(int(1.0 / val)))
    
    def extPlayerSendCommand(self, cmd, arg='', getStatus=True):
        if None != self.owner: 
            self.owner.extPlayerSendCommand(cmd, arg)
            if getStatus: 
                self.owner.extPlayerSendCommand("PLAYBACK_INFO", '')


class IPTVExtMoviePlayer(Screen):
    # 
    skin = """
    <screen name="IPTVExtMoviePlayer"    position="center,center" size="%d,%d" flags="wfNoBorder" backgroundColor="#FFFFFFFF" >
            <widget name="playbackInfoBaner"  position="0,30"          size="650,77"  zPosition="2" pixmap="%s" transparent="1" alphatest="blend" />
            <widget name="progressBar"        position="94,54"         size="544,7"   zPosition="4" pixmap="%s" transparent="1" borderWidth="1" borderColor="#888888" />
            <widget name="bufferingBar"       position="94,54"         size="544,7"   zPosition="3" pixmap="%s" borderWidth="1" borderColor="#888888" />
            <widget name="statusIcon"         position="20,45"         size="40,40"   zPosition="4"             transparent="1" alphatest="blend" />
            
            <widget name="goToSeekPointer"    position="94,0"          size="150,60"  zPosition="8" pixmap="%s" transparent="1" alphatest="blend" />
            <widget name="goToSeekLabel"      position="94,0"          size="150,40"  zPosition="9" transparent="1" foregroundColor="white"     backgroundColor="#251f1f1f" font="Regular;24" halign="center" valign="center"/>
            <widget name="infoBarTitle"       position="82,30"         size="568,23"  zPosition="3" transparent="1" foregroundColor="white"     backgroundColor="#251f1f1f" font="Regular;18" halign="center" valign="center"/>
            <widget name="currTimeLabel"      position="94,62"         size="100,30"  zPosition="3" transparent="1" foregroundColor="#66ccff"   backgroundColor="#251f1f1f" font="Regular;24" halign="left"   valign="top"/>
            <widget name="lengthTimeLabel"    position="317,62"        size="100,30"  zPosition="3" transparent="1" foregroundColor="#999999"   backgroundColor="#251f1f1f" font="Regular;24" halign="center" valign="top"/>
            <widget name="remainedLabel"      position="538,62"        size="100,30"  zPosition="3" transparent="1" foregroundColor="#66ccff"   backgroundColor="#251f1f1f" font="Regular;24" halign="right"  valign="top"/>    
    </screen>""" % ( getDesktop(0).size().width(), 
                     getDesktop(0).size().height(),
                     GetIPTVDMImgDir("playback_banner.png"),
                     GetIPTVDMImgDir("playback_progress.png"),
                     GetIPTVDMImgDir("playback_buff_progress.png"),
                     GetIPTVDMImgDir('playback_pointer.png') )
    
    def __init__(self, session, filesrcLocation, FileName, lastPosition=None, player='eplayer', additionalParams={}):
        # 'gstplayer'
        Screen.__init__(self, session)
        self.skinName = "IPTVExtMoviePlayer"
        self.player = player
        if 'gstplayer' == self.player: 
            self.playerName = _("external gstplayer")
            self.gstAdditionalParams = {}
            self.gstAdditionalParams['download-buffer-path'] = additionalParams.get('download-buffer-path', '') # File template to store temporary files in, should contain directory and XXXXXX
            self.gstAdditionalParams['ring-buffer-max-size'] = additionalParams.get('ring-buffer-max-size', 0) # in MB
            self.gstAdditionalParams['buffer-duration']      = additionalParams.get('buffer-duration', -1) # in s
            self.gstAdditionalParams['buffer-size']          = additionalParams.get('buffer-size', 0) # in KB
        else: self.playerName = _("external eplayer3")

        self.session.nav.playService(None) # current service must be None to give free access to DVB Audio and Video Sinks
        self.fileSRC      = filesrcLocation
        self.title        = FileName
        if lastPosition:
            self.lastPosition = lastPosition
        else:
            self.lastPosition = 0 
        self.downloader = additionalParams.get('downloader', None)
        
        printDBG('IPTVExtMoviePlayer.__init__ lastPosition[%r]' % self.lastPosition)
        
        self.extPlayerCmddDispatcher = ExtPlayerCommandsDispatcher(self)
        
        self["actions"] = ActionMap(['IPTVAlternateVideoPlayer', 'MoviePlayerActions', 'MediaPlayerActions', 'MediaPlayerSeekActions', 'WizardActions'],
            {
                "leavePlayer"  : self.key_stop,
                'play'         : self.key_play,
                'pause'        : self.key_pause,
                'exit'         : self.key_exit,
                'back'         : self.key_exit,
                'info'         : self.key_info,
                'seekdef:1'    : self.key_seek1,
                'seekdef:3'    : self.key_seek3,
                'seekdef:4'    : self.key_seek4,
                'seekdef:6'    : self.key_seek6,
                'seekdef:7'    : self.key_seek7,
                'seekdef:9'    : self.key_seek9,
                'seekFwd'      : self.key_seekFwd,
                'seekBack'     : self.key_seekBack,
                'left_press'   : self.key_left_press,
                'left_repeat'  : self.key_left_repeat,
                'rigth_press'  : self.key_rigth_press,
                'rigth_repeat' : self.key_rigth_repeat,
                'ok'           : self.key_ok,
            }, -1)
        
        self.onClose.append(self.__onClose)
        #self.onShow.append(self.__onShow)
        self.onLayoutFinish.append(self.onStart)
        
        self.console = None
        
        self.isClosing = False
        self.responseData = ""
        
        # playback info
        # GUI
        self.updateInfoTimer = eTimer()
        self.updateInfoTimer_conn = eConnectCallback(self.updateInfoTimer.timeout, self.updateInfo)
        
        # playback info bar gui elements
        self['playbackInfoBaner'] = Cover3()
        self['statusIcon']        = Cover3()
        self['progressBar']       = ProgressBar()
        self['bufferingBar']      = ProgressBar()
        self['goToSeekPointer']   = Cover3() 
        self['infoBarTitle']      = Label(self.title)
        self['goToSeekLabel']     = Label("0:00:00")
        self['currTimeLabel']     = Label("0:00:00")
        self['remainedLabel']     = Label("-0:00:00")
        self['lengthTimeLabel']   = Label("0:00:00")
        
        # goto seek  timer
        self.playback = {}
        self.playback['GoToSeekTimer'] = eTimer()
        self.playback['GoToSeekTimer_conn'] = eConnectCallback(self.playback['GoToSeekTimer'].timeout, self.doGoToSeek)
        
        self.playback.update( {'CurrentTime':    0,
                               'Length':         0,
                               'LengthFromPlayerReceived': False,
                               'GoToSeekTime':   0,
                               'StartGoToSeekTime': 0,
                               'GoToSeeking':    False,
                               'IsLive':         False,
                               'Status':         None
                              } )
        # load pixmaps for statusIcon
        self.playback['statusIcons'] = {'Play':None, 'Pause':None, 'FastForward':None, 'SlowMotion':None}
        try:
            self.playback['statusIcons']['Play']        = LoadPixmap( GetIPTVDMImgDir("playback_a_play.png") )
            self.playback['statusIcons']['Pause']       = LoadPixmap( GetIPTVDMImgDir("playback_a_pause.png") )
            self.playback['statusIcons']['FastForward'] = LoadPixmap( GetIPTVDMImgDir("playback_a_ff.png") )
            self.playback['statusIcons']['SlowMotion']  = self.playback['statusIcons']['FastForward']
        except:
            printExc()
        
        # show hide info bar functionality
        self.goToSeekRepeatCount = 0
        self.goToSeekStep = 0
        self.playbackInfoBar = {'visible':False, 'blocked':False, 'guiElemNames':['playbackInfoBaner', 'progressBar', 'bufferingBar', 'goToSeekPointer', 'goToSeekLabel', 'infoBarTitle', 'currTimeLabel', 'remainedLabel', 'lengthTimeLabel', 'statusIcon'] }
        self.playbackInfoBar['timer'] = eTimer()
        self.playbackInfoBar['timer_conn'] = eConnectCallback(self.playbackInfoBar['timer'].timeout, self.hidePlaybackInfoBar)
        
        self.isStarted = False
        self.hidePlaybackInfoBar()
        
        self.waitEOSAbortedFix = {'EOSaborted_received': False, 'poll_received': False, 'timer': None}
        self.waitEOSAbortedFix['timer'] = eTimer()
        self.waitEOSAbortedFix['timer_conn'] = eConnectCallback(self.waitEOSAbortedFix['timer'].timeout, self.waitEOSAbortedFixTimeoutCallback)
        
        self.waitCloseFix = {'waiting':False}
        self.waitCloseFix['timer'] = eTimer()
        self.waitCloseFix['timer_conn'] = eConnectCallback(self.waitCloseFix['timer'].timeout, self.waitCloseTimeoutCallback)
        
        self.isCloseRequestedByUser = False
        self.playerBinaryInfo = {'version':None, 'data':''}
        self.messageQueue = []
        self.underMessage = False
        
        try: self.autoHideTime = 1000 * int(config.plugins.iptvplayer.extplayer_infobar_timeout.value)
        except: self.autoHideTime = 1000
        
    def updateInfo(self):
        self.extPlayerCmddDispatcher.doUpdateInfo()
        if None != self.downloader:
            remoteFileSize = self.downloader.getRemoteFileSize()
            if 0 < remoteFileSize:
                localFileSize = self.downloader.getLocalFileSize(True) 
                if 0 < localFileSize:
                    self['bufferingBar'].value = (localFileSize * 100000) / remoteFileSize
                    
    def showMessage(self, message, type, callback=None):
        printDBG("IPTVExtMoviePlayer.showMessage")
        if self.isClosing and type != None: return
        messageItem = {'msg':message, 'type':type, 'callback':callback}
        self.messageQueue.append(messageItem)
        self.processMessageQueue()
        
    def processMessageQueue(self):
        if self.underMessage or 0 == len(self.messageQueue): return
        self.underMessage = True
        while len(self.messageQueue):
            messageItem = self.messageQueue.pop(0)
            message, type, callback = messageItem['msg'], messageItem['type'], messageItem['callback']
            if None == type and None != callback: 
                callback()
            else:
                if self.isClosing and None != callback: continue # skip message with callback
                else: self.session.openWithCallback(boundFunction(self.messageClosedCallback, callback), MessageBox, text=message, type=type)
            return
        
    def messageClosedCallback(self, callback, arg=None):
        self.underMessage = False
        if None != callback: callback()
        else: self.processMessageQueue()
            
    def waitEOSAbortedFixTimeoutCallback(self):
        if self.waitEOSAbortedFix['EOSaborted_received']:
            self.extPlayerCmddDispatcher.stop()
        
    def playbackUpdateInfo(self, stsObj):
        for key, val in stsObj.iteritems():
            if 'Length' == key: 
                if 0 > val:
                    printDBG('IPTVExtMoviePlayer.playbackUpdateInfo Length[%d] - live stream?' % val )
                    val = 0
                    self.playback['IsLive'] = True
                else:
                    self.playback['IsLive'] = False
                if 0 < val:
                    # restore last position
                    if 10 < self.lastPosition and self.lastPosition < self.playback['Length']:
                        self.showPlaybackInfoBar()
                        self.extPlayerCmddDispatcher.doGoToSeek(str(self.lastPosition-5))
                        self.lastPosition = 0
                    tmpLength = self.playback['CurrentTime']
                    if val > self.playback['CurrentTime']: tmpLength = val
                    if 0 < tmpLength:
                        self.playback['Length'] = tmpLength
                        self['progressBar'].range = (0, tmpLength)
                        self['lengthTimeLabel'].setText( str(timedelta(seconds=tmpLength)) )
                    self.playback['LengthFromPlayerReceived'] = True
            elif 'CurrentTime' == key:
                if self.playback['Length'] < val:
                    self.playback['Length'] = val
                    self['progressBar'].range = (0, val)
                    self['lengthTimeLabel'].setText( str(timedelta(seconds=val)) )
                self['progressBar'].value = val
                self.playback['CurrentTime'] = stsObj['CurrentTime']
                if 0 < self.playback['CurrentTime']: self.playback['StartGoToSeekTime'] = self.playback['CurrentTime']
                self['currTimeLabel'].setText( str(timedelta(seconds=self.playback['CurrentTime'])) )
                self['remainedLabel'].setText( '-' + str(timedelta(seconds=self.playback['Length']-self.playback['CurrentTime'])) )
            elif 'Status' == key:
                curSts = self.playback['Status']
                if self.playback['Status'] != val[0]:
                    if 'Play' == val[0]:
                        self.showPlaybackInfoBar()
                    elif val[0] in ['Pause', 'FastForward', 'SlowMotion']:
                        self.showPlaybackInfoBar(blocked=True)
                    self.playback['Status'] = val[0]
                    self['statusIcon'].setPixmap( self.playback['statusIcons'].get(val[0], None) )
            else:
                self.playback[key] = val
                
    def doGoToSeek(self):
        self.playback['GoToSeekTimer'].stop()
        if self.playback['GoToSeeking']:
            self.showPlaybackInfoBar()
            self.playback['StartGoToSeekTime'] = self.playback['GoToSeekTime']
            self.extPlayerCmddDispatcher.doGoToSeek(str(self.playback['GoToSeekTime']))
            self.playback['GoToSeeking'] = False
            self['goToSeekPointer'].hide()
            self["goToSeekLabel"].hide()

    def doGoToSeekPointerMove(self, seek):
        printDBG('IPTVExtMoviePlayer.doGoToSeekPointerMove seek[%r], LengthFromPlayerReceived[%r], GoToSeeking[%r]' % (seek, self.playback['LengthFromPlayerReceived'], self.playback['GoToSeeking']))
        self.playback['GoToSeekTimer'].stop()
        if not self.playback['LengthFromPlayerReceived']: return
        if not self.playback['GoToSeeking']:
            self.playback['GoToSeeking']  = True
            self.playback['GoToSeekTime'] = self.playback['StartGoToSeekTime']
            self.showPlaybackInfoBar([], True)
            self['goToSeekPointer'].show()
            self["goToSeekLabel"].show()
        
        # update data
        self.playback['GoToSeekTime'] += seek
        if self.playback['GoToSeekTime'] < 0: self.playback['GoToSeekTime'] = 0
        if self.playback['GoToSeekTime'] > self.playback['Length']: self.playback['GoToSeekTime'] = self.playback['Length']
        self["goToSeekLabel"].setText( str(timedelta(seconds=self.playback['GoToSeekTime'])) )
        
        # update position
        # convert time to width
        relativeX = self["progressBar"].instance.size().width() * self.playback['GoToSeekTime'] / self.playback['Length']
        x = self['progressBar'].position[0] - self["goToSeekPointer"].getWidth()/2 + relativeX

        self['goToSeekPointer'].setPosition(x, self['goToSeekPointer'].position[1])
        self["goToSeekLabel"].setPosition(x, self['goToSeekLabel'].position[1])
        
        # trigger delayed seek
        self.playback['GoToSeekTimer'].start(1000) 

    # handling of RCU keys
    def key_stop(self):
        self.isCloseRequestedByUser = True
        self.extPlayerCmddDispatcher.stop()
    def key_play(self):         self.extPlayerCmddDispatcher.play()
    def key_pause(self):        self.extPlayerCmddDispatcher.pause()
    def key_exit(self):         self.doExit()
    def key_info(self):         self.doInfo()
    def key_seek1(self):        self.extPlayerCmddDispatcher.doSeek(config.seek.selfdefined_13.value * -1)
    def key_seek3(self):        self.extPlayerCmddDispatcher.doSeek(config.seek.selfdefined_13.value) 
    def key_seek4(self):        self.extPlayerCmddDispatcher.doSeek(config.seek.selfdefined_46.value * -1)
    def key_seek6(self):        self.extPlayerCmddDispatcher.doSeek(config.seek.selfdefined_46.value)
    def key_seek7(self):        self.extPlayerCmddDispatcher.doSeek(config.seek.selfdefined_79.value * -1)
    def key_seek9(self):        self.extPlayerCmddDispatcher.doSeek(config.seek.selfdefined_79.value)  
    def key_seekFwd(self):      self.extPlayerCmddDispatcher.seekFwd()   
    def key_seekBack(self):     self.extPlayerCmddDispatcher.seekBack()   
    def key_left_press(self):   self.goToSeekKey(-1, 'press')
    def key_left_repeat(self):  self.goToSeekKey(-1, 'repeat')
    def key_rigth_press(self):  self.goToSeekKey(1, 'press')
    def key_rigth_repeat(self): self.goToSeekKey(1, 'repeat')
    def key_ok(self):
        if 'Pause' == self.playback['Status']: self.extPlayerCmddDispatcher.play()
        else: self.extPlayerCmddDispatcher.pause()
        
    def goToSeekKey(self, direction, state='press'):
        if 'press' == state: 
            self.goToSeekStep = 5
            self.goToSeekRepeatCount = 1
        elif 3 <= self.goToSeekRepeatCount:
            self.goToSeekRepeatCount = 1
            self.goToSeekStep *= 2
        else:
            self.goToSeekRepeatCount += 1
        
        # not allow faster than (0.1 * playback length)
        if self.goToSeekStep > (self.playback['Length'] / 10):
            self.goToSeekStep = self.playback['Length'] / 10
        if 0 >= self.goToSeekStep:
            self.goToSeekStep = 1
        
        self.doGoToSeekPointerMove(self.goToSeekStep * direction)
        
    def doExit(self):
        if self.playbackInfoBar['visible']:
            self.playbackInfoBar['blocked'] = False
            self.hidePlaybackInfoBar()
        elif not self.isClosing:
            self.extPlayerCmddDispatcher.stop()
            
    def doInfo(self):
        if not self.playbackInfoBar['visible']:
            if self.isStarted and not self.isClosing:
                self.playbackInfoBar['blocked'] = True
                self.showPlaybackInfoBar()
        else: self.doExit()
    
    def eplayer3Finished(self, code):
        printDBG("IPTVExtMoviePlayer.eplayer3Finished code[%r]" % code)
        if self.isClosing: return
         
        msg = _("It seems that the video player \"%s\" does not work properly.\n\nSTS: %s\nERROR CODE: %r")
        if None == self.playerBinaryInfo['version']:
            msg = msg % (self.playerName, self.playerBinaryInfo['data'], code)
            self.showMessage(msg, MessageBox.TYPE_ERROR, self.onLeavePlayer)
        elif 'gstplayer' == self.player and 246 == code:
            msg = msg % (self.playerName, _("ERROR: pipeline could not be constructed: no element \"playbin2\" \nPlease check if gstreamer plugins are available in your system."), code)
            self.showMessage(msg, MessageBox.TYPE_ERROR, self.onLeavePlayer)
        else: self.onLeavePlayer()
        
    def waitCloseTimeoutCallback(self):
        printDBG("IPTVExtMoviePlayer.waitCloseTimeoutCallback")
        if None != self.console:
            printDBG("Force close movie player by sending CtrlC")
            self.console.sendCtrlC()
        self.onLeavePlayer()
        
    def eplayer3DataAvailable2(self, data):
        if None == data or self.isClosing:
            return
            
        if 'got buffer empty from driver!' in data:
            self.extPlayerCmddDispatcher.stop()

        # work around to catch EOF event after seeking, pause .etc
        if 'wait EOS aborted!!' in data:
            self.waitEOSAbortedFix['EOSaborted_received'] = True
            self.waitEOSAbortedFix['timer'].start(2000, True) # singleshot

        if self.waitEOSAbortedFix['EOSaborted_received'] and 'poll' in data:
            self.waitEOSAbortedFix['timer'].stop()
            self.waitEOSAbortedFix['timer'].start(2000, True)

    def eplayer3DataAvailable(self, data):
        if None == data or self.isClosing:
            return
        if None == self.playerBinaryInfo['version']: self.playerBinaryInfo['data'] += data
        data = self.responseData + data
        if '\n' != data[-1]: truncated = True
        else:                truncated = False
        data = data.split('\n')
        if truncated: 
            self.responseData = data[-1]
            del data[-1]
        for item in data:
            printDBG(item)
            if item.startswith('{'): 
                try:
                    obj = json.loads(item.strip())
                    printDBG("Status object [%r]" % obj)
                    key = obj.keys()[0]
                    obj = obj[key]
                except: 
                    printExc()
                    continue
                    
                if "PLAYBACK_PLAY" == key:
                    self.onStartPlayer()
                    if 'gstplayer' != self.player: self.updateInfoTimer.start(1000)
                elif "PLAYBACK_STOP" == key:
                    self.onLeavePlayer()
                elif "PLAYBACK_LENGTH" == key and 0 == obj['sts']:
                    self.playbackUpdateInfo({'Length':int(obj['length'])})
                elif "PLAYBACK_CURRENT_TIME" == key and 0 == obj['sts']:
                    self.playbackUpdateInfo({'CurrentTime':int(obj['sec'])})
                elif "PLAYBACK_INFO" == key:
                    if obj['isPaused']:
                        self.playbackUpdateInfo({'Status': ['Pause', '0']})
                        if 'gstplayer' == self.player: self.updateInfoTimer.stop()
                    else:
                        if 'gstplayer' == self.player: self.updateInfoTimer.start(1000)
                        if obj['isForwarding']:
                            self.playbackUpdateInfo({'Status': ['FastForward', str(obj['Speed'])]})
                        elif 0 < obj['SlowMotion']:
                            self.playbackUpdateInfo({'Status': ['SlowMotion', '1/%d' % obj['SlowMotion']]})
                        elif obj['isPlaying']: # and 1 == obj['Speed']:
                            self.playbackUpdateInfo({'Status': ['Play', '1']})
                        else:
                            printDBG('eplayer3DataAvailable PLAYBACK_INFO not handled')
                elif "GSTPLAYER_EXTENDED" == key: self.playerBinaryInfo['version'] = obj['version']
                elif "EPLAYER3_EXTENDED" == key: self.playerBinaryInfo['version'] = obj['version']
                elif "GST_ERROR" == key: self.showMessage('%s\ncode:%s' % (obj['msg'].encode('utf-8'), obj['code']), MessageBox.TYPE_ERROR, None)
                elif "GST_MISSING_PLUGIN" == key: self.showMessage(obj['msg'].encode('utf-8'), MessageBox.TYPE_INFO, None)

                        
                # {u'PLAYBACK_INFO': 
                # {u'isSeeking': False, 
                # u'BackWard': 0.0, 
                # u'isForwarding': False, 
                # u'mayWriteToFramebuffer': True, 
                # u'AVSync': 1, 
                # u'isTeletext': False, 
                # u'isAudio': True, 
                # u'isCreationPhase': False, 
                # u'abortRequested': False, 
                # u'isVideo': True, 
                # u'isPaused': False, 
                # u'SlowMotion': 0, 
                # u'isPlaying': True, 
                # u'Speed': 1, 
                # u'isSubtitle': False, 
                # u'isDvbSubtitle': False}}

    def __onClose(self):
        self.isClosing = True
        if None != self.console:
            self.console_appClosed_conn   = None
            self.console_stderrAvail_conn = None
            self.console_stdoutAvail_conn = None
            self.console.sendCtrlC()
            self.console = None
        self.downloader = None
        self.playbackInfoBar['timer'].stop()
        self.playbackInfoBar['timer_conn'] = None
        self.waitEOSAbortedFix['timer_conn'] = None
        self.waitCloseFix['timer_conn'] = None
        
        self.updateInfoTimer_conn = None
        self.playback['GoToSeekTimer_conn'] = None
        self.onClose.remove(self.__onClose)
        self.messageQueue = []
        
    def onStartPlayer(self):
        self.isStarted = True
        self.showPlaybackInfoBar()

    def onLeavePlayer(self):
        printDBG("IPTVExtMoviePlayer.onLeavePlayer")
        if self.waitCloseFix['waiting'] and None != self.waitCloseFix['timer']: self.waitCloseFix['timer'].stop()
        self.updateInfoTimer.stop()
        self.playbackInfoBar['blocked'] = False
        self.hidePlaybackInfoBar()
        
        # onLeavePlayer can be called by two reason:
        #   - no data in buffer - should return sts = 1
        #   - triggered by user - should return sts = 0
        if self.isCloseRequestedByUser: 
            sts = 0
        else:
            sts = 1
            
        self.isClosing = True
        self.showMessage(None, None, boundFunction(self.close, sts, self.playback.get('CurrentTime', 0)))

    def onStart(self):
        self.onLayoutFinish.remove(self.onStart)
        self['progressBar'].value = 0
        self['bufferingBar'].range = (0, 100000)
        self['bufferingBar'].value = 0
        self.initGuiComponentsPos()
        if 'gstplayer' == self.player:
            gstplayerPath = config.plugins.iptvplayer.gstplayerpath.value
            #'export GST_DEBUG="*:6" &&' + 
            cmd = gstplayerPath  + ' "%s"' % self.fileSRC
            if "://" in self.fileSRC: 
                cmd += ' "%s" "%s"  "%s"  "%s" ' % (self.gstAdditionalParams['download-buffer-path'], self.gstAdditionalParams['ring-buffer-max-size'], self.gstAdditionalParams['buffer-duration'], self.gstAdditionalParams['buffer-size'])
                tmp = strwithmeta(self.fileSRC)
                url,httpParams = DMHelper.getDownloaderParamFromUrl(tmp)
                for key in httpParams: cmd += (' "%s=%s" ' % (key, httpParams[key]) )
                if 'http_proxy' in tmp.meta:
                    tmp = tmp.meta['http_proxy']
                    if '://' in tmp:
                        if '@' in tmp:
                            tmp = re.search('([^:]+?://)([^:]+?):([^@]+?)@(.+?)$', tmp)
                            if tmp: cmd += (' "proxy=%s" "proxy-id=%s" "proxy-pw=%s" ' % (tmp.group(1)+tmp.group(4), tmp.group(2), tmp.group(3)) )
                        else: cmd += (' "proxy=%s" ' % tmp)
        else:
            cmd = 'exteplayer3 "%s"' % self.fileSRC + " > /dev/null"
        
        self.console = eConsoleAppContainer()
        self.console_appClosed_conn = eConnectCallback(self.console.appClosed, self.eplayer3Finished)
        self.console_stderrAvail_conn = eConnectCallback(self.console.stderrAvail, self.eplayer3DataAvailable)
        #if 'gstplayer' == self.player: 
        #    self.console_stdoutAvail_conn = eConnectCallback(self.console.stdoutAvail, self.eplayer3DataAvailable2 ) # work around to catch EOF event after seeking, pause .etc
        printDBG("onStart cmd[%s]" % cmd)
        self.console.execute( cmd )
        self['statusIcon'].setPixmap( self.playback['statusIcons']['Play'] ) # sulge for test
            
    def initGuiComponentsPos(self):

        # calculate offset
        offset_x = (getDesktop(0).size().width() - self['playbackInfoBaner'].instance.size().width()) / 2
        offset_y = (getDesktop(0).size().height() - self['playbackInfoBaner'].instance.size().height()) - 50 # 10px - cropping guard
        if offset_x < 0: offset_x = 0
        if offset_y < 0: offset_y = 0

        for elem in self.playbackInfoBar['guiElemNames']:
            self[elem].setPosition(self[elem].position[0]+offset_x, self[elem].position[1]+offset_y)

    def showPlaybackInfoBar(self, excludeElems=['goToSeekPointer', 'goToSeekLabel'], blocked=None):
        self.playbackInfoBar['timer'].stop()
        
        for elem in self.playbackInfoBar['guiElemNames']:
            if elem not in excludeElems:
                self[elem].show()
        
        if None == blocked or self.playbackInfoBar['blocked']:
            blocked = self.playbackInfoBar['blocked']

        self.playbackInfoBar['visible'] = True

        if not blocked:
            self.playbackInfoBar['timer'].start(self.autoHideTime, True) # singleshot

    def hidePlaybackInfoBar(self, excludeElems=[], force=False):
        self.playbackInfoBar['timer'].stop()

        if self.playbackInfoBar['blocked'] and not force:
            return

        for elem in self.playbackInfoBar['guiElemNames']:
            if elem not in excludeElems:
                self[elem].hide()
            
        self.playbackInfoBar['visible'] = False
        
    def __onShow(self):
        pass
        #Screen.hide(self) # we do not need window at now maybe in future
        
    def extPlayerSendCommand(self, command, arg1=''):
        printDBG("IPTVExtMoviePlayer.extPlayerSendCommand command[%s] arg1[%s]" % (command, arg1))
        if None == self.console: 
            printExc("IPTVExtMoviePlayer.extPlayerSendCommand console not available")
            return
            
        if   'PLAYBACK_LENGTH'       == command: 
            self.console.write( "l\n" )
        elif 'PLAYBACK_CURRENT_TIME' == command: 
            self.console.write( "j\n" )
        elif 'PLAYBACK_INFO'         == command: 
            self.console.write( "i\n" )
        else:
            # All below commands require that 'PLAY ' status, 
            # so we first send command to resume playback
            self.console.write( "c\n" )

            if   'PLAYBACK_CONTINUE'      == command:
                # this is done to flush data
                # without thos workaround for some materials 
                # there is a lack of liquidity playback after resume             
                if 'eplayer' == self.player: 
                    #self.console.write( "k-2\n" ) # this causing problem for non-seekable streams
                    self.console.write( "c\n" )
            elif 'PLAYBACK_PAUSE'         == command: 
                self.console.write( "p\n" )
            elif 'PLAYBACK_SEEK_RELATIVE' == command: 
                self.console.write( "kc%s\n" % (arg1) ) 
            elif 'PLAYBACK_SEEK_ABS'      == command: 
                self.console.write( "gf%s\n" % (arg1) )
            elif 'PLAYBACK_FASTFORWARD'   == command:
                self.console.write( "f%s\n" % arg1 )
            elif 'PLAYBACK_FASTBACKWARD'  == command: 
                self.console.write( "b%s\n" % arg1 )
            elif 'PLAYBACK_SLOWMOTION'    == command: 
                self.console.write( "m%s\n" % arg1 )
            elif 'PLAYBACK_STOP'          == command: 
                if not self.waitCloseFix['waiting']:
                    self.waitCloseFix['waiting'] = True
                    self.waitCloseFix['timer'].start(10000, True) # singleshot
                self.console.write( "q\n" )
            else:
                printDBG("IPTVExtMoviePlayer.extPlayerSendCommand unknown command[%s]" % command)