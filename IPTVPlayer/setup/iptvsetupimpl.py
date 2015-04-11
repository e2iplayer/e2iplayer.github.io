# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.tools.iptvtools           import printDBG, printExc, GetBinDir, GetTmpDir
from Plugins.Extensions.IPTVPlayer.setup.iptvsetuphelper     import CBinaryStepHelper, CCmdValidator, SetupDownloaderCmdCreator
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
###################################################

###################################################
# FOREIGN import
###################################################
from Screens.MessageBox  import MessageBox
from Components.config   import config, configfile
from Tools.BoundFunction import boundFunction
from Tools.Directories   import resolveFilename, SCOPE_PLUGINS
from os                  import path as os_path, chmod as os_chmod, remove as os_remove, listdir as os_listdir
import re
###################################################

class IPTVSetupImpl:
    def __init__(self, finished, chooseQuestion, showMessage, setInfo):
        printDBG("IPTVSetupImpl.__init__ -------------------------------")
        
        # callbacks
        self._finished    = finished
        self._chooseQuestion = chooseQuestion
        self._showMessage = showMessage
        self._setInfo     = setInfo
        self.workingObj   = None
        self.stepHelper   = None
        self.termination  = False
        
        self.tmpDir = GetTmpDir()
        self.resourceServers = ["http://iptvplayer.pl/resources/", "http://iptvplayer.vline.pl/resources/"]
        
        self.gstreamerVersion = ""
        self.openSSLVersion = ""
        self.supportedPlatforms = ["sh4", "mipsel", "i686"]
        self.platform = "unknown"
        
        # wget members
        self.wgetVersion = 15 # 1.15 
        self.wgetpaths = ["wget", "/usr/bin/wget", "/usr/bin/fullwget", GetBinDir("wget", "")]
        self._wgetInstallChoiseList = [(_('Install into the "%s".') % ("/usr/bin/fullwget " + _("recommended")), "/usr/bin/fullwget"),
                                       (_('Install into the "%s".') % "IPTVPlayer/bin/wget", GetBinDir("wget", "")),
                                       (_('Install into the "%s".') % "/usr/bin/wget", "/usr/bin/wget"),
                                       (_("Do not install (not recommended)"), "")]
        # rtmpdump members
        self.rtmpdumpVersion = "Compiled by samsamsam@o2.pl 2015-01-11"
        self.rtmpdumppaths = ["/usr/bin/rtmpdump", "rtmpdump"]
        
        # f4mdump member
        self.f4mdumpVersion = "F4MDump v0.32"
        self.f4mdumppaths = ["/usr/bin/f4mdump", GetBinDir("f4mdump", "")]
        self._f4mdumpInstallChoiseList = [(_('Install into the "%s".') % ("/usr/bin/f4mdump (%s)" % _("recommended")), "/usr/bin/f4mdump"),
                                          (_('Install into the "%s".') % "IPTVPlayer/bin/f4mdump", GetBinDir("f4mdump", "")),
                                          (_("Do not install (not recommended)"), "")]
        self._f4mdumpInstallChoiseList2 = [(_('Install into the "%s".') % ("/usr/bin/f4mdump static libstdc++ (%s)" % _("recommended")), "/usr/bin/f4mdump"),
                                          (_('Install into the "%s".') % "IPTVPlayer/bin/f4mdump _static_libstdc++", GetBinDir("f4mdump", "")),
                                          (_("Do not install (not recommended)"), "")]
                                          
        # gstplayer
        self.gstplayerVersion = 12
        self.gstplayerpaths = ["/usr/bin/gstplayer", GetBinDir("gstplayer", "")]
        self._gstplayerInstallChoiseList = [(_('Install into the "%s".') % ("/usr/bin/gstplayer (%s)" % _("recommended")), "/usr/bin/gstplayer"),
                                          (_('Install into the "%s".') % "IPTVPlayer/bin/gstplayer", GetBinDir("gstplayer", "")),
                                          (_("Do not install (not recommended)"), "")]
                                          
        # flumpegdemux
        self.flumpegdemuxVersion = "0.10.85" #{'i686':199720, 'mipsel':275752, 'sh4':151664}
        self.flumpegdemuxpaths = ["/usr/lib/gstreamer-0.10/libgstflumpegdemux.so"]
        
        self.binaryInstalledSuccessfully = False
        self.tries = 0
        
    def __del__(self):
        printDBG("IPTVSetupImpl.__del__ -------------------------------")
        
    def terminate(self):
        printDBG("IPTVSetupImpl.terminate -------------------------------")
        self.termination  = True
        self._finished    = None
        self._chooseQuestion = None
        self._showMessage = None
        self._setInfo     = None 
        if self.workingObj: self.workingObj.terminate()
        
    def finish(self, sts=None, ret=None):
        printDBG("IPTVSetupImpl.finish")
        if self._finished: self._finished()
        
    def chooseQuestion(self, title, list, callback):
        printDBG("IPTVSetupImpl.chooseQuestion")
        if self._chooseQuestion: self._chooseQuestion(title, list, callback)
        
    def showMessage(self, message, type, callback):
        printDBG("IPTVSetupImpl.showMessage")
        if self._showMessage: self._showMessage(message, type, callback)
        
    def setInfo(self, title, message):
        printDBG("IPTVSetupImpl.setInfo")
        if self._setInfo: self._setInfo(title, message)
        
    def setInfoFromStepHelper(self, key):
        if None != self.stepHelper:
            self.setInfo(_(self.stepHelper.getMessage(key,0)), _(self.stepHelper.getMessage(key,1)))
       
    def start(self):
        printDBG("IPTVSetupImpl.showMessage")
        self.platformDetect()

    ###################################################
    # STEP: PLATFORM DETECTION
    ###################################################
    def platformDetect(self):
        printDBG("IPTVSetupImpl.platformDetect")
        self.setInfo(_("Detection of the platform."), _("Plugin can be run on one of the following platforms: sh4, mipsel, i686."))
        cmdTabs = []
        for platform in self.supportedPlatforms:
            platformtesterPath = resolveFilename(SCOPE_PLUGINS, "Extensions/IPTVPlayer/bin/%s/platformtester" % platform)
            try: os_chmod(platformtesterPath, 0777)
            except: printExc()
            cmdTabs.append(platformtesterPath + "  2>&1 ")
        def _platformValidator(code, data):
            printDBG("IPTVSetupImpl._platformValidator")
            if "Test platform OK" in data: return True,False
            else: return False,True
        self.workingObj = CCmdValidator(self.platformDetectFinished, _platformValidator, cmdTabs)
        self.workingObj.start()
        
    def platformDetectFinished(self, stsTab, dataTab):
        printDBG("IPTVSetupImpl.platformDetectFinished")
        def _saveConfig(platform):
            self.platform = platform
            config.plugins.iptvplayer.plarform.value = self.platform
            printDBG("IPTVSetupImpl.platformDetectFinished platform[%s]" % self.platform)
            config.plugins.iptvplayer.plarform.save()
            configfile.save()
        
        if len(stsTab) > 0 and True == stsTab[-1]:
            _saveConfig( self.supportedPlatforms[len(stsTab)-1] )
            # NEXT STEP
            #self.showMessage(_("Your platform is [%s]") % self.platform, MessageBox.TYPE_INFO, self.setOpenSSLVersion)
            self.setOpenSSLVersion()
        else:
            _saveConfig( "unknown" )
            self.showMessage(_("Fatal Error!\nPlugin is not supported with your platform."), MessageBox.TYPE_ERROR, boundFunction(self.finish, False) )
            
    ###################################################
    # STEP: OpenSSL DETECTION
    ###################################################
    def setOpenSSLVersion(self, ret=None):
        printDBG('Check opennSSL version')
        self.setInfo(_("Detection of the OpenSSL version."), _("OpenSSL lib is needed by wget and rtmpdump utilities."))
        for ver in ['.0.9.8', '.1.0.0']:
            libsslExist = False
            libryptoExist = False
            for path in ['/usr/lib/', '/lib/', '/usr/local/lib/', '/local/lib/', '/lib/i386-linux-gnu/']:
                try:
                    filePath = path + 'libssl.so' + ver
                    if os_path.isfile(filePath) and not os_path.islink(filePath):
                        libsslExist = True
                    filePath = path + 'libcrypto.so' + ver
                    if os_path.isfile(filePath) and not os_path.islink(filePath):
                        libryptoExist = True
                    if libsslExist and libryptoExist:
                        break
                except:
                    printExc()
                    continue
            if libsslExist and libryptoExist:
                break
        if libsslExist and libryptoExist:
            self.openSSLVersion = ver
            #self.showMessage(_("Your OpenSSL version is [%s]") % self.openSSLVersion, MessageBox.TYPE_INFO, self.wgetDetect)
            self.getGstreamerVer()
        else:
            self.openSSLVersion = ""
            self.showMessage(_("Fatal Error!\nOpenssl could not be found. Please install it and retry."), MessageBox.TYPE_ERROR, boundFunction(self.finish, False) )
            
    ###################################################
    # STEP: GSTREAMER VERSION
    ###################################################
    def getGstreamerVer(self):
        printDBG("IPTVSetupImpl.getGstreamerVer")
        self.setInfo(_("Detection of the gstreamer version."), None)
        def _verValidator(code, data):
            if 'GStreamer Core Library version 0.10' in data: return True,False
            else: return False,True
        self.workingObj = CCmdValidator(self.getGstreamerVerFinished, _verValidator, ['gst-launch --gst-version'])
        self.workingObj.start()
        
    def getGstreamerVerFinished(self, stsTab, dataTab):
        printDBG("IPTVSetupImpl.getGstreamerVerFinished")
        if len(stsTab) > 0 and True == stsTab[-1]: self.gstreamerVersion = "0.10"
        else: self.gstreamerVersion = ""
        self.wgetStep()
            
    ###################################################
    # STEP: WGET
    ###################################################
    def wgetStep(self, ret=None):
        printDBG("IPTVSetupImpl.wgetStep")
        def _detectValidator(code, data):
            if 'BusyBox' not in data and '+https' in data: 
                try: ver = int(re.search("GNU Wget 1\.([0-9]+?)[^0-9]", data).group(1))
                except: ver = 0
                if ver >= self.wgetVersion: return True,False
            return False,True
        def _deprecatedHandler(paths, stsTab, dataTab):
            sts, retPath = False, ""
            for idx in range(len(dataTab)):
                if 'BusyBox' not in dataTab[idx] and '+https' in dataTab[idx]: sts, retPath = True, paths[idx]
            return sts, retPath
        
        self.stepHelper = CBinaryStepHelper("wget", self.platform, self.openSSLVersion, config.plugins.iptvplayer.wgetpath)
        self.stepHelper.updateMessage('detection', _('The "%s" utility is used by the IPTVPlayer to buffering and downloading [%s] links.' % ('wget', 'http, https, f4m, uds, hls')), 1)
        self.stepHelper.setInstallChoiseList( self._wgetInstallChoiseList )
        self.stepHelper.setPaths( self.wgetpaths )
        self.stepHelper.setDetectCmdBuilder( lambda path: path + " -V 2>&1 " )
        self.stepHelper.setDetectValidator( _detectValidator )
        self.stepHelper.setDeprecatedHandler( _deprecatedHandler )
        self.stepHelper.setFinishHandler( self.wgetStepFinished )
        self.binaryDetect()

    def wgetStepFinished(self, sts, ret=None):
        printDBG("IPTVSetupImpl.wgetStepFinished sts[%r]" % sts)
        self.rtmpdumpStep()
        
    ###################################################
    # STEP: RTMPDUMP
    ###################################################
    def rtmpdumpStep(self, ret=None):
        printDBG("IPTVSetupImpl.rtmpdumpStep")
        def _detectValidator(code, data):
            if self.rtmpdumpVersion in data: return True,False
            else: return False,True
        def _deprecatedHandler(paths, stsTab, dataTab):
            sts, retPath = False, ""
            for idx in range(len(dataTab)):
                if 'RTMPDump v2.4' in dataTab[idx]: sts, retPath = True, paths[idx]
            return sts, retPath
        def _downloadCmdBuilder(binName, platform, openSSLVersion, server, tmpPath):
            url = server + ('rtmpdump_%s_libssl.so%s.tar.gz' % (platform, openSSLVersion))
            tmpFile = tmpPath + 'rtmpdump.tar.gz' 
            cmd = SetupDownloaderCmdCreator(url, tmpFile) + ' > /dev/null 2>&1'
            return cmd
        def _installCmdBuilder(binName, binaryInstallPath, tmpPath):
            sourceArchive = tmpPath + 'rtmpdump.tar.gz'         
            cmd = 'tar -xzf "%s" -C / 2>&1' % sourceArchive
            return cmd
            
        self.stepHelper = CBinaryStepHelper("rtmpdump", self.platform, self.openSSLVersion, config.plugins.iptvplayer.rtmpdumppath)
        self.stepHelper.updateMessage('detection', _('The "%s" utility is used by the IPTVPlayer to buffering and downloading [%s] links.' % ('rtmpdump', 'rtmp, rtmpt, rtmpe, rtmpte, rtmps')), 1)
        self.stepHelper.setInstallChoiseList( [('rtmpdump', '/usr/bin/rtmpdump')] )
        self.stepHelper.setPaths( self.rtmpdumppaths )
        self.stepHelper.setDetectCmdBuilder( lambda path: path + " -V 2>&1 " )
        self.stepHelper.setDetectValidator( _detectValidator )
        self.stepHelper.setDeprecatedHandler( _deprecatedHandler )
        self.stepHelper.setDownloadCmdBuilder( _downloadCmdBuilder )
        self.stepHelper.setInstallCmdBuilder( _installCmdBuilder )
        self.stepHelper.setFinishHandler( self.rtmpdumpStepFinished )
        self.binaryDetect()

    def rtmpdumpStepFinished(self, sts, ret=None):
        printDBG("IPTVSetupImpl.rtmpdumpStepFinished sts[%r]" % sts)
        self.f4mdumpStep()
        
    ###################################################
    # STEP: F4MDUMP
    ###################################################
    def f4mdumpStep(self, ret=None):
        printDBG("IPTVSetupImpl.f4mdumpStep")
        self.binaryInstalledSuccessfully = False
        def _detectValidator(code, data):
            if self.binaryInstalledSuccessfully: self.stepHelper.setInstallChoiseList( self._f4mdumpInstallChoiseList2 )
            else: self.stepHelper.setInstallChoiseList( self._f4mdumpInstallChoiseList )
            if self.f4mdumpVersion in data: return True,False
            else: return False,True
        def _deprecatedHandler(paths, stsTab, dataTab):
            sts, retPath = False, ""
            for idx in range(len(dataTab)):
                if 'samsamsam@o2.pl' in dataTab[idx]: sts, retPath = True, paths[idx]
            return sts, retPath
        def _downloadCmdBuilder(binName, platform, openSSLVersion, server, tmpPath):
            if self.binaryInstalledSuccessfully:
                url = server + 'bin/' + platform + ('/%s_openssl' % binName) + openSSLVersion + '_static_libstdc++'
                self.binaryInstalledSuccessfully = False
            else: url = server + 'bin/' + platform + ('/%s_openssl' % binName) + openSSLVersion
                
            tmpFile = tmpPath + binName
            cmd = SetupDownloaderCmdCreator(url, tmpFile) + ' > /dev/null 2>&1'
            return cmd
            
        self.stepHelper = CBinaryStepHelper("f4mdump", self.platform, self.openSSLVersion, config.plugins.iptvplayer.f4mdumppath)
        self.stepHelper.updateMessage('detection', _('The "%s" utility is used by the IPTVPlayer to buffering and downloading [%s] links.' % ('f4mdump', 'f4m, uds')), 1)
        self.stepHelper.setInstallChoiseList( self._f4mdumpInstallChoiseList )
        self.stepHelper.setPaths( self.f4mdumppaths )
        self.stepHelper.setDetectCmdBuilder( lambda path: path + " 2>&1 " )
        self.stepHelper.setDetectValidator( _detectValidator )
        self.stepHelper.setDownloadCmdBuilder( _downloadCmdBuilder )
        self.stepHelper.setDeprecatedHandler( _deprecatedHandler )
        self.stepHelper.setFinishHandler( self.f4mdumpStepFinished )
        self.binaryDetect()

    def f4mdumpStepFinished(self, sts, ret=None):
        printDBG("IPTVSetupImpl.f4mdumpStepFinished sts[%r]" % sts)
        if "" != self.gstreamerVersion: self.gstplayerStep()
        else: self.finish()
        
    ###################################################
    # STEP: GSTPLAYER
    ###################################################
    def gstplayerStep(self, ret=None):
        printDBG("IPTVSetupImpl.gstplayerStep")
        def _detectValidator(code, data):
            if '{"GSTPLAYER_EXTENDED":{"version":' in data: 
                try: ver = int(re.search('"version":([0-9]+?)[^0-9]', data).group(1))
                except: ver = 0
                if ver >= self.gstplayerVersion: return True,False
            return False,True
        def _deprecatedHandler(paths, stsTab, dataTab):
            sts, retPath = False, ""
            for idx in range(len(dataTab)):
                if '{"GSTPLAYER_EXTENDED":{"version":' in dataTab[idx]: sts, retPath = True, paths[idx]
            return sts, retPath
        def _downloadCmdBuilder(binName, platform, openSSLVersion, server, tmpPath):
            url = server + 'bin/' + platform + ('/%s_gstreamer' % binName) + "0.10"
            tmpFile = tmpPath + binName
            cmd = SetupDownloaderCmdCreator(url, tmpFile) + ' > /dev/null 2>&1'
            return cmd
        self.stepHelper = CBinaryStepHelper("gstplayer", self.platform, self.openSSLVersion, config.plugins.iptvplayer.gstplayerpath)
        self.stepHelper.updateMessage('detection', _('The "%s" utility is used by the IPTVPlayer as external movie player.') % ('gstplayer'), 1)
        self.stepHelper.setInstallChoiseList( self._gstplayerInstallChoiseList )
        self.stepHelper.setPaths( self.gstplayerpaths )
        self.stepHelper.setDetectCmdBuilder( lambda path: path + " 2>&1 " )
        self.stepHelper.setDetectValidator( _detectValidator )
        self.stepHelper.setDownloadCmdBuilder( _downloadCmdBuilder )
        self.stepHelper.setDeprecatedHandler( _deprecatedHandler )
        self.stepHelper.setFinishHandler( self.gstplayerStepFinished )
        self.binaryDetect()

    def gstplayerStepFinished(self, sts, ret=None):
        printDBG("IPTVSetupImpl.gstplayerStepFinished sts[%r]" % sts)
        if sts: self.flumpegdemuxStep()
        else: self.finish()
        
    ###################################################
    # STEP: FLUENDO MPEGDEMUX
    ###################################################
    def flumpegdemuxStep(self, ret=None):
        printDBG("IPTVSetupImpl.flumpegdemuxStep")
        def _detectValidator(code, data):
            if 0 == code: return True,False
            return False,True
        def _deprecatedHandler(paths, stsTab, dataTab):
            sts, retPath = False, ""
            try: currentSize = os_path.getsize(self.flumpegdemuxpaths[0])
            except: currentSize = -1
            if -1 < currentSize: sts, retPath = True, paths[0]
            return sts, retPath
        def _downloadCmdBuilder(binName, platform, openSSLVersion, server, tmpPath):
            url = server + 'bin/' + platform + ('/%s_gstreamer' % binName) + "0.10"
            tmpFile = tmpPath + binName
            cmd = SetupDownloaderCmdCreator(url, tmpFile) + ' > /dev/null 2>&1'
            return cmd
        self.stepHelper = CBinaryStepHelper("libgstflumpegdemux.so", self.platform, self.openSSLVersion, None)
        msg1 = "Fluendo mpegdemux for GSTREAMER 0.10"
        msg2 = "\nFor more info please visit http://fluendo.com/"
        msg3 = _('It improves playing of streams hls/m3u8.\n')
        self.stepHelper.updateMessage('detection', msg1, 0)
        self.stepHelper.updateMessage('detection', msg2, 1)
        self.stepHelper.updateMessage('not_detected_2', msg1 + _(' has not been detected. \nDo you want to install it? ') + msg3 + msg2, 1)
        self.stepHelper.updateMessage('deprecated_2', msg1 + _(' is deprecated. \nDo you want to install new one? ') + msg3 + msg2, 1)
        
        self.stepHelper.setInstallChoiseList( [('gst-fluendo-mpegdemux', self.flumpegdemuxpaths[0])] )
        self.stepHelper.setPaths( self.flumpegdemuxpaths )
        self.stepHelper.setDetectCmdBuilder( lambda path: ('grep "%s" "%s" 2>&1 ' % (self.flumpegdemuxVersion, path)) )
        self.stepHelper.setDetectValidator( _detectValidator )
        self.stepHelper.setDownloadCmdBuilder( _downloadCmdBuilder )
        self.stepHelper.setDeprecatedHandler( _deprecatedHandler )
        self.stepHelper.setFinishHandler( self.flumpegdemuxStepFinished )
        self.binaryDetect()

    def flumpegdemuxStepFinished(self, sts, ret=None):
        printDBG("IPTVSetupImpl.flumpegdemuxStepFinished sts[%r]" % sts)
        self.finish()

    ###################################################
    ###################################################
    ###################################################
        
    ###################################################
    # STEP: SEARCHING FOR binary
    ###################################################
    def binaryDetect(self, ret=None):
        printDBG("IPTVSetupImpl.binaryDetect")
        self.setInfoFromStepHelper('detection')
        self.workingObj = CCmdValidator(self.binaryDetectFinished, self.stepHelper.getDetectValidator(), self.stepHelper.getDetectCmds())
        self.workingObj.start()
        
    def binaryDetectFinished(self, stsTab, dataTab):
        printDBG("IPTVSetupImpl.binaryDetectFinished")
        
        if len(stsTab) > 0 and True == stsTab[-1]:
            path = self.stepHelper.getPaths()[len(stsTab)-1]
            self.stepHelper.getSaveConfigOptionHandler()( self.stepHelper.getConfigOption(), path )
            # NEXT STEP
            if self.stepHelper.isDebugMessagesAllowed():
                self.showMessage(_("[%s] will be used by IPTVPlayer.") % path, MessageBox.TYPE_INFO, self.finish)
            else:
                self.stepHelper.getFinishHandler()(True)
        else:
            path = ""
            sts = False
            if 0 < len(dataTab) and None != self.stepHelper.getDeprecatedHandler():
                sts,path = self.stepHelper.getDeprecatedHandler()(self.stepHelper.getPaths(), stsTab, dataTab)
            self.stepHelper.getSaveConfigOptionHandler()( self.stepHelper.getConfigOption(), path )
            installChoiseList = self.stepHelper.getInstallChoiseList()
            if 1 < len(installChoiseList):
                if not sts: message = self.stepHelper.getMessage('not_detected_1', 1)
                else: message = message = self.stepHelper.getMessage('deprecated_1', 1)
                self.chooseQuestion(message, installChoiseList, self.binaryDownload_1)
            elif 1 == len(installChoiseList):
                if not sts: message = self.stepHelper.getMessage('not_detected_2', 1)
                else: message = message = self.stepHelper.getMessage('deprecated_2', 1)
                self.showMessage(message, MessageBox.TYPE_YESNO, self.binaryDownload_2)
            else:
                self.stepHelper.getFinishHandler()(False)
    ###################################################
    # STEP: binary DOWNLOAD
    ###################################################
    def binaryDownload(self):
        self.setInfoFromStepHelper('download')
        cmdTabs = []
        for server in self.resourceServers:
            cmd = self.stepHelper.getDownloadCmdBuilder()(self.stepHelper.getName(), self.platform, self.openSSLVersion, server, self.tmpDir)
            cmdTabs.append(cmd)
        self.workingObj = CCmdValidator(self.binaryDownloadFinished, self.stepHelper.getDownloadValidator(), cmdTabs)
        self.workingObj.start()
    
    def binaryDownload_1(self, ret=None):
        printDBG("IPTVSetupImpl.binaryDownload_1")
        if ret: self._binaryInstallPath = ret[1]
        else: self._binaryInstallPath = ""
        if "" != self._binaryInstallPath: self.binaryDownload()
        else: self.stepHelper.getFinishHandler()(False)
        
    def binaryDownload_2(self, ret=None):
        printDBG("IPTVSetupImpl.binaryDownload_2")
        if ret:
            self._binaryInstallPath = self.stepHelper.getInstallChoiseList()[0][1]
            self.binaryDownload()
        else:
            self._binaryInstallPath = ""
            self.stepHelper.getFinishHandler()(False)
        
    def binaryDownloadFinished(self, stsTab, dataTab):
        printDBG("IPTVSetupImpl.binaryDownloadFinished")
        if len(stsTab) > 0 and True == stsTab[-1]:
            # NEXT STEP
            self.binaryInstall()
        else: self.showMessage(self.stepHelper.getMessage('dwn_failed', 1), MessageBox.TYPE_YESNO, self.binaryDownloadRetry)
            
    def binaryDownloadRetry(self, ret=None):
        printDBG("IPTVSetupImpl.binaryDownloadRetry")
        if ret: self.binaryDetect()
        else: self.stepHelper.getFinishHandler()(False)
            
    ###################################################
    # STEP: binary Install
    ###################################################
    def binaryInstall(self, ret=None):
        printDBG("IPTVSetupImpl.binaryInstall")
        self.setInfoFromStepHelper('install')
        cmd = self.stepHelper.getInstallCmdBuilder()(self.stepHelper.getName(), self._binaryInstallPath, self.tmpDir)
        self.workingObj = CCmdValidator(self.binaryInstallFinished, self.stepHelper.getInstallValidator(), [cmd])
        self.workingObj.start()
        
    def binaryInstallFinished(self, stsTab, dataTab):
        printDBG("IPTVSetupImpl.binaryInstallFinished")
        if len(stsTab) > 0 and True == stsTab[-1]:
            self.binaryInstalledSuccessfully = True
            # NEXT STEP
            self.binaryDetect() # run detect step once again to make sure that installed binary will be detected
        else: self.showMessage(_("Installation binary failed. Retry?"), MessageBox.TYPE_YESNO, self.binaryInstallRetry)
        
    def binaryInstallRetry(self, ret=None):
        printDBG("IPTVSetupImpl.binaryInstallRetry")
        if ret: self.binaryInstall()
        else: self.stepHelper.getFinishHandler()(False)