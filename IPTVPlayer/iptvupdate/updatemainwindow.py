# -*- coding: utf-8 -*-
#
#  Update iptv main window
#


###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.tools.iptvtools          import printDBG, printExc, mkdirs, rmtree, FreeSpace, formatBytes, iptv_system, GetIPTVDMImgDir, GetIPTVPlayerVerstion, GetShortPythonVersion, GetTmpDir
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes          import enum
from Plugins.Extensions.IPTVPlayer.iptvupdate.iptvlist      import IPTVUpdateList
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdownloadercreator import UpdateDownloaderCreator
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh            import DMHelper
from Plugins.Extensions.IPTVPlayer.libs.pCommon             import CParsingHelper

from Plugins.Extensions.IPTVPlayer.components.articleview   import ArticleView
from Plugins.Extensions.IPTVPlayer.components.ihost         import ArticleContent
from Plugins.Extensions.IPTVPlayer.libs.pCommon             import common
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
###################################################

###################################################
# FOREIGN import
###################################################
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen
from Components.config import config
from Components.ActionMap import ActionMap
from Components.Label import Label
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

try:    import json
except: import simplejson as json

from os import path as os_path, remove as os_remove, listdir as os_listdir
###################################################


class IPTVUpdateWindow(Screen):

    skin = """
    <screen name="IPTVUpdateMainWindow" position="center,center" size="620,440" title="" >
            <widget name="sub_title"    position="10,10" zPosition="2" size="600,35"  valign="center" halign="left"   font="Regular;22" transparent="1" foregroundColor="white" />
            <widget name="list"         position="10,50" zPosition="1" size="600,380" transparent="1" scrollbarMode="showOnDemand" />
            <widget name="console"      position="40,200"   zPosition="2" size="540,80" valign="center" halign="center"   font="Regular;34" transparent="0" foregroundColor="white" backgroundColor="black"/>
    </screen>"""

    ICONS = ['iconwait1.png', 'iconwait2.png', 'iconwait3.png', 'icondone.png', 'iconerror.png', 'iconwarning.png', 'iconcancelled.png']
    ICON  = enum( WAITING = 0, PROCESSING = 1, PROCESSING_NOT_BREAK = 2, PROCESSED = 3, ERROR = 4, WARNING = 5, CANCELLED = 6 )
    
    def __init__(self, session, updateObjImpl, autoStart=True):
        printDBG("IPTVUpdateMainWindow.__init__ -------------------------------")
        Screen.__init__(self, session)
        self.autoStart = autoStart

        self.updateObjImpl = updateObjImpl
        self.updateObjImpl.setStepFinishedCallBack(self.stepFinished)

        self.setup_title = self.updateObjImpl.getSetupTitle()
        self["sub_title"] = Label(_(" "))
        self["console"] = Label(_("> Press OK to start <"))
        self["actions"] = ActionMap(["SetupActions", "ColorActions"],
            {
                "cancel": self.keyExit,
                "ok"    : self.keyOK,
            }, -2)
        self.list = []
        self["list"] = IPTVUpdateList( [GetIPTVDMImgDir(x) for x in IPTVUpdateWindow.ICONS] )
        self.currStep = 0
        self.onLayoutFinish.append(self.layoutFinished)
        self.onClose.append(self.__onClose)
        self.status =  None

    def __del__(self):
        printDBG("IPTVUpdateMainWindow.__del__ -------------------------------")

    def __onClose(self):
        printDBG("IPTVUpdateMainWindow.__onClose -----------------------------")
        self.updateObjImpl.setStepFinishedCallBack(None)
        self.updateObjImpl.terminate()
        self.onClose.remove(self.__onClose)
        self.onLayoutFinish.remove(self.layoutFinished)
        self.updateObjImpl = None
        self.list = []
        self["list"].setList([])

    def layoutFinished(self):
        self.setTitle( self.updateObjImpl.getTitle() )
        self["sub_title"].setText( self.updateObjImpl.getSubTitle() )
        self["list"].setSelectionState(enabled = False)
        self.preparUpdateStepsList()
        if self.autoStart:
            self.doStart()
        else:
            self["console"].show()
        
    def doStart(self):
        if 0 < len(self.list):
            self.currStep = 0
            self.status     = 'working'
            self.stepExecute()
            self["console"].hide()
        else:
            self["console"].setText(_("No steps to execute."))

    def reloadList(self):
        self["list"].hide()
        self["list"].setList([ (x,) for x in self.list])
        self["list"].show()
      
    def keyOK(self):
        if not self.autoStart and None == self.status:
            self.doStart()
        else:
            currItem = self["list"].getCurrent()
            if  self.status not in [None, 'working']:
                artItem = ArticleContent(title = currItem['title'], text = currItem['info'], images = [])
                self.session.open(ArticleView, artItem)

    def keyExit(self):
        if 'working' == self.status and not self.list[self.currStep].get('breakable', False):
            self.session.open(MessageBox, _("Step [%s] cannot be aborted. Please wait."), type = MessageBox.TYPE_INFO, timeout = 5 )
        else:
            self.close()

    def preparUpdateStepsList(self):
        self.list = self.updateObjImpl.getStepsList()
        for item in self.list:
            item.update( {'icon': self.ICON.WAITING} )
        self.reloadList()
        
    def stepExecute(self):
        self["list"].moveToIndex(self.currStep)
        if self.list[self.currStep].get('breakable', False):
            self.list[self.currStep].update( {'info': _("During processing, please wait."), 'icon': self.ICON.PROCESSING} )
        else:
            self.list[self.currStep].update( {'info': _("During processing, please do not interrupt."), 'icon': self.ICON.PROCESSING_NOT_BREAK} )
        self.reloadList()
        if self.updateObjImpl.isReadyToExecuteStep(self.currStep):
            self.list[self.currStep]['execFunction']()
        else:
            raise Exception("IPTVUpdateMainWindow.stepExecute seems that last step has not been finished.")
        
    def stepFinished(self, stsCode, msg):
        printDBG('IPTVUpdateMainWindow.stepFinished stsCode[%d], msg[%s]' % (stsCode, msg))
        nextStep = True
        if 0 != stsCode and self.list[self.currStep].get('repeatCount', 0) > 0:
            self.list[self.currStep]['repeatCount'] -= 1
            self.stepExecute()
            return

        if -1 == stsCode and not self.list[self.currStep]['ignoreError']:
            nextStep = False
            self.status = 'error'
            self.list[self.currStep].update( {'info': msg, 'icon': self.ICON.ERROR} )
            # cancel other steps
            currStep = self.currStep + 1
            while currStep < len(self.list):
                self.list[currStep].update( {'info': _("Aborted"), 'icon': self.ICON.CANCELLED} )
                currStep += 1
        elif 0 != stsCode:
            self.list[self.currStep].update( {'info': msg, 'icon': self.ICON.WARNING} )
        else:
            self.list[self.currStep].update( {'info': msg, 'icon': self.ICON.PROCESSED} )
        if nextStep:
            if self.currStep + 1 < len(self.list):
               self.currStep += 1 
               self.stepExecute()
            else:
                self.status = 'done'
                if  self.updateObjImpl.finalize():
                    self.close()
                    return
                else:
                    self["list"].setSelectionState(enabled = True)
        else:
            self.status = 'error'
            if  self.updateObjImpl.finalize(False, msg):
                self.close()
                return
            else:
                self["list"].setSelectionState(enabled = True)
        self.reloadList()
                
class IUpdateObjectInterface():
    def __init__(self, session):
        printDBG("IUpdateObjectInterface.__init__ -------------------------------")
    def __del__(self):
        printDBG("IUpdateObjectInterface.__del__ -------------------------------")
    def getSetupTitle(self):
        return " "
    def getTitle(self):
        return _(" ")
    def getSubTitle(self):
        return _(" ")
    def finalize(self, success=True):
        return
    def terminate(self):
        return
    def getStepsList(self):
        return []
    def isReadyToExecuteStep(currStepIdx):
        return False
    def setStepFinishedCallBack(self, stepFinishedCallbackFun):
        self.stepFinishedHandler = stepFinishedCallbackFun
    def stepFinished(self, stsCode=-1, msg=''):
        if self.stepFinishedHandler:
            self.stepFinishedHandler(stsCode, msg)
    def createPath(self, path):
        sts = True
        msg = ''
        try:
            if not os_path.isdir(path) and not os_path.islink(path):
                if not mkdirs(path):
                    msg = _("The problem with creating a directory [%s].") % path
                    sts = False
        except:
            printExc()
            msg = _("Problem with the directory [%s].") % path
            sts = False
        return sts, msg

    def checkForFreeSpace(self, dir, requairedSpace):
        sts = True
        msg = ''
        if not FreeSpace(dir, requairedSpace, 1):
            sts = False
            msg = _("There is no space in the directory [%s]\n Available[%s], required [%s].") % (dir, formatBytes(FreeSpace(dir, None, 1)), formatBytes(requairedSpace))
        return sts, msg
    
class UpdateMainAppImpl(IUpdateObjectInterface):
    SERVERS_LIST_URLS = ["http://iptvplayer.pl/download/update/serwerslist.json", "http://iptvplayer.vline.pl/download/update/serwerslist.json"]
    VERSION_PATTERN   = 'IPTV_VERSION="([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)"'
    
    def __init__(self, session):
        printDBG("UpdateMainAppImpl.__init__ -------------------------------")
        self.session = session
        IUpdateObjectInterface.__init__(self, session)
        self.cm = common()

        self.setup_title = _("IPTVPlayer - update")
        self.tmpDir = GetTmpDir('iptv_update')
        self.ExtensionPath = resolveFilename(SCOPE_PLUGINS, 'Extensions/')
        self.ExtensionTmpPath = None
        
        self.terminating = False
        self.status      = 'none'
        self.downloader  = None
        self.cmd         = None
        self.serversList = []
        self.currServIdx = 0
        
        self.sourceArchive      = None
        self.destinationArchive = None
        self.serverIdx          = 0
        
    def checkVersionFile(self, newVerPath):
        code = 0
        msg  = 'Wersja poprawna.'
        
        newVerFile = os_path.join(newVerPath, 'version.py')
        if os_path.isfile(newVerFile):
            verPattern = self.VERSION_PATTERN
        else:
            newVerFile = os_path.join(newVerPath, 'version.pyo')
            verPattern = '([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)'

        try:
            # get new version
            with open (newVerFile, "r") as verFile: data = verFile.read()
            newVerNum = CParsingHelper.getSearchGroups(data, verPattern)[0]
            if newVerNum != self.serversList[self.currServIdx]['version']:
                code = -1
                msg  = _("Wrong version. \n downloaded version [%s] is different from the requested [%s].") % (newVerNum, self.serversList[self.currServIdx]['version'])
        except:
            printExc()
            code = -1
            msg  = _("File [%s] reading failed.") % newVerFile
        return code, msg
        
    def doRestart(self, *args):
        try:
            msgtxt = _("Please remember that you use this plugin at your own risk.")
            self.session.open(MessageBox, _("E2 GUI restart after IPTVPlayer update to version[%s].\n\n") % self.serversList[self.currServIdx]['version'] + msgtxt, type = MessageBox.TYPE_INFO, timeout = 5 )
            from enigma import quitMainloop
            quitMainloop(3)
        except:
            printExc()
            self.session.open(MessageBox, _("Restart GUI failed. \nPlease restart STB manually."), type = MessageBox.TYPE_INFO, timeout=5 )

    #########################################################
    # INREFACE IMPLEMENTATION METHODS
    #########################################################
    def getSetupTitle(self):
        return _("IPTVPlayer - update")
        
    def getTitle(self):
        return _("IPTVPlayer - update")
        
    def getSubTitle(self):
        return _("Currently you have version [%s].") % GetIPTVPlayerVerstion()
        
    def finalize(self, success=True, errorMsg=""):
        if success:
            self.session.openWithCallback(self.doRestart, MessageBox, _("Update completed successfully. For the moment, the system will reboot."), type = MessageBox.TYPE_INFO, timeout=10 )
            return False
        else:
            message = errorMsg 
            # Failed message:
            message += "\n\n" + _("Update failed.\nCheck the status by selecting interesting and pressing OK.") 
            self.session.open(MessageBox, message, type = MessageBox.TYPE_ERROR, timeout = -1)
            return False

    def terminate(self):
        self.terminating = True
        if self.downloader:
            self.downloader.terminate()
            self.downloader = None
        if self.cmd:
            self.cmd.kill()
        self.clearTmpData()
    
    def getStepsList(self):
        list = []
        def __getStepDesc(title, execFunction, breakable=True, ignoreError=False, repeatCount=0):
            return  { 'title': title, 'execFunction': execFunction, 'breakable': breakable, 'ignoreError': ignoreError, 'info': _("Pending"), 'progressFun': None, 'repeatCount': repeatCount }
        list.append( __getStepDesc(title = _("Obtaining server list."),          execFunction = self.stepGetServerLists ) )
        list.append( __getStepDesc(title = _("Downloading an update packet."),   execFunction = self.stepGetArchive ) )
        list.append( __getStepDesc(title = _("Extracting an update packet."),    execFunction = self.stepUnpackArchive ) )
        list.append( __getStepDesc(title = _("Executing user scripts."),         execFunction = self.stepExecuteUserScripts ) )
        list.append( __getStepDesc(title = _("Checking version."),               execFunction = self.stepCheckFiles ) )
        list.append( __getStepDesc(title = _("Confirmation of installation."),   execFunction = self.stepConfirmInstalation) )
        list.append( __getStepDesc(title = _("Removing the old version."),       execFunction = self.stepRemoveOldVersion, breakable=False, ignoreError=True, repeatCount=2) )
        list.append( __getStepDesc(title = _("Installing new version."),         execFunction = self.stepInstallNewVersion,   breakable=False, ignoreError=False, repeatCount=3) )
        return list
        
    def isReadyToExecuteStep(self, currStepIdx):
        if not self.downloader and not self.cmd:
            return True
        else:
            return False

    #########################################################
    # STEPS IMPLEMENTATION METHODS
    #########################################################
    def stepGetServerLists(self):
        printDBG('UpdateMainAppImpl.stepGetServerLists')
        self.clearTmpData()
        sts, msg = self.createPath(self.tmpDir)
        if not sts:
            self.stepFinished(-1, msg)
            return
        serverUrl = UpdateMainAppImpl.SERVERS_LIST_URLS[self.serverIdx]
        self.downloader = UpdateDownloaderCreator(serverUrl)
        self.downloader.subscribersFor_Finish.append( boundFunction(self.downloadFinished, self.__serversListDownloadFinished, None))
        self.downloader.start(serverUrl, os_path.join(self.tmpDir, 'serwerslist.json'))
        
    def stepGetArchive(self):
        self.downloader = UpdateDownloaderCreator(self.serversList[self.currServIdx]['url'])
        self.downloader.subscribersFor_Finish.append( boundFunction(self.downloadFinished, self.__archiveDownloadFinished, None))
        self.sourceArchive = os_path.join(self.tmpDir, 'iptvplayer_archive.tar.gz')
        self.downloader.start(self.serversList[self.currServIdx]['url']+("?ver=%s&type=%s" % (self.serversList[self.currServIdx]['version'], self.serversList[self.currServIdx]['pyver'])), self.sourceArchive)
        
    def stepUnpackArchive(self):
        self.destinationArchive  = os_path.join(self.tmpDir , 'iptv_archive')
        self.ExtensionTmpPath    = os_path.join(self.destinationArchive, self.serversList[self.currServIdx]['subdir'])
        printDBG('UpdateMainAppImpl.stepUnpackArchive: sourceArchive[%s] -> destinationArchive[%s] -> ExtensionTmpPath[%s]' % (self.sourceArchive, self.destinationArchive, self.ExtensionTmpPath) )
        sts, msg = self.createPath(self.destinationArchive)
        if not sts:
            self.stepFinished(-1, msg)
            return

        cmd = 'tar -xzf "%s" -C "%s" 2>&1' % (self.sourceArchive, self.destinationArchive)
        self.cmd = iptv_system( cmd, self.__unpackCmdFinished )
        
    def stepCheckFiles(self):
        code, msg = self.checkVersionFile( os_path.join(self.ExtensionTmpPath, 'IPTVPlayer') )
        self.stepFinished(code, msg)
        
    def stepExecuteUserScripts(self, init=True, code=0, msg=''):
        # get users scripts
        if init:
            self.customUserCmdList = self.__getUserCmdsList()
            if 0 <len(self.customUserCmdList):
                self.customUserMsg = ''
            else:
                self.customUserMsg = _("No user scripts.")

        self.customUserMsg += msg
        if 0 != code:
            self.stepFinished(-1, _("Problem with user script execution [%s].") + self.customUserMsg)
        elif 0 < len(self.customUserCmdList):
            cmd = self.customUserCmdList.pop()
            self.cmd = iptv_system( cmd, self.__userCmdFinished )
        else:
            self.stepFinished(0, _("Completed.\n") + self.customUserMsg)
        
    def stepConfirmInstalation(self, confirmed=None):
        if None == confirmed:
            self.session.openWithCallback(self.stepConfirmInstalation, MessageBox, _("Version [%s] is ready for installation. After installation, restart of the system will be done.\nDo you want to continue?") % self.serversList[self.currServIdx]['version'], type = MessageBox.TYPE_YESNO, timeout = -1)
        else:
            if confirmed:
                self.stepFinished(0, _("Installation has been confirmed."))
            else:
                self.stepFinished(-1, _("Installation has been aborted."))
        
    def stepRemoveOldVersion(self):
        # if not config.plugins.iptvplayer.cleanup.value:
            # code = 1
            # self.stepFinished(1, "Pominięty.\nCzyszczenie w czasie aktualizacji jest wyłączone w ustawieniach pluginu.")
        # else:
        cmd = 'rm -rf "%s"/*' % ( os_path.join(self.ExtensionPath, 'IPTVPlayer') )
        printDBG('UpdateMainAppImpl.stepRemoveOldVersion cmd[%s]' % cmd)
        self.cmd = iptv_system( cmd, self.__removeOldVersionCmdFinished )

    def stepInstallNewVersion(self):
        cmd = 'cp -rf "%s"/* "%s"/ 2>&1' % (os_path.join(self.ExtensionTmpPath, 'IPTVPlayer'), os_path.join(self.ExtensionPath, 'IPTVPlayer'))
        printDBG('UpdateMainAppImpl.stepInstallNewVersion cmd[%s]' % cmd)
        self.cmd = iptv_system( cmd, self.__installNewVersionCmdFinished )

    def downloadFinished(self, callBackFun, arg, status):
        printDBG('UpdateMainAppImpl.downloadFinished file[%s], status[%s]' % (file, status))
        self.downloader.subscribersFor_Finish = []
        if self.terminating:
            printDBG('UpdateMainAppImpl.downloadFinished closing')
            return
        callBackFun(arg, status)
        
    def clearTmpData(self):
        try:
            rmtree(self.tmpDir)
        except:
            printExc()
    
    ##############################################################################
    # SERWERS LISTS STEP'S PRIVATES METHODS
    ############################################################################## 
    def __addLastVersion(self, servers):
        mainUrl = "https://gitorious.org/iptvplayer-for-e2/iptvplayer-for-e2"
        sts, response = self.cm.getPage(mainUrl, {'return_data':False})
        if sts:
            finalurl = response.geturl()
            printDBG("UpdateMainAppImpl.__addLastVersion finalurl[%s]" % finalurl)
            response.close()
            crcSum = finalurl.split('/')[-1].replace(':', '')
            if 40 == len(crcSum):
                sts, data = self.cm.getPage(finalurl + "IPTVPlayer/version.py")
                if sts:
                    newVerNum = CParsingHelper.getSearchGroups(data, '&quot;([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)&quot;')[0]
                    sourceUrl = mainUrl + "/archive/%s.tar.gz" % crcSum
                    server = {'name':'gitorious.org', 'version':newVerNum, 'url':sourceUrl, 'subdir':'iptvplayer-for-e2-iptvplayer-for-e2/', 'pyver':'X.X', 'packagetype':'sourcecode'}
                    printDBG("UpdateMainAppImpl.__addLastVersion server: [%s]" % str(server))
                    servers.append(server)
            else:
                printDBG("Wrong crcSum[%s]" % crcSum)
                

    def __serversListDownloadFinished(self, arg, status):
        def ServerComparator(x, y):
            try:    val1 = int(x['version'].replace('.', ''))
            except: val1 = 0
            try:    val2 = int(y['version'].replace('.', ''))
            except: val2 = 0
            #printDBG("ServerComparator val1[%d], val2[%d]" % (val1, val2))
            return cmp(val1, val2)
        try:
            currVerNum = int(GetIPTVPlayerVerstion().replace('.', ''))
        except:
            printDBG('Version of the current instalation [%s]' % GetIPTVPlayerVerstion())
            currVerNum = 0
        pythonVer = GetShortPythonVersion()

        url      = self.downloader.getUrl()
        filePath = self.downloader.getFullFileName()
        self.downloader = None
        if DMHelper.STS.DOWNLOADED != status:
            self.serverIdx += 1
            if self.serverIdx <  len(UpdateMainAppImpl.SERVERS_LIST_URLS): self.stepGetServerLists()
            else:
                urls = ""
                for idx in range(self.serverIdx):
                    urls += "%s, " % (UpdateMainAppImpl.SERVERS_LIST_URLS[idx])
                if 1 < len(urls): urls = urls[:-2]
                self.stepFinished(-1, _("Problem with downloading the server list from [%s].") % urls)
        else:
            # process servers list
            serversList = []
            try:
                with open(filePath) as fileHandle:    
                    jsonData = json.load(fileHandle, 'utf-8')
                #printDBG("__serversListDownloadFinished jsonData [%r]" % jsonData)
                for server in jsonData['servers']:
                    serverOK = True
                    extServer = {}
                    for key in ['name', 'version', 'url', 'subdir', 'pyver', 'packagetype']:
                        if key not in server.iterkeys():
                            serverOK = False
                            break
                        else:
                            extServer[key] = server[key].encode('utf8')
                            
                    #printDBG("")
                    if not serverOK: continue
                    newServer = dict(extServer)
                    serversList.append(newServer)
            except:
                printExc()
                self.stepFinished(-1, _("Problem with downloading the server list."))
                return
            if config.plugins.iptvplayer.hiddenAllVersionInUpdate.value:
                self.__addLastVersion(serversList) # get last version from gitorious.org only for developers

            self.serversList = serversList
            if 0 < len(serversList):
                options = []
                self.serversList.sort(cmp=ServerComparator, reverse=True)
                for idx in range(len(serversList)):
                    server = serversList[idx]
                    if not config.plugins.iptvplayer.hiddenAllVersionInUpdate.value:
                        try: newVerNum = int(server['version'].replace('.', ''))
                        except: continue
                        #printDBG("newVerNum[%s], currVerNum[%s]" % (newVerNum, currVerNum))
                        if newVerNum < currVerNum and not config.plugins.iptvplayer.downgradePossible.value:
                            continue
                        if newVerNum == currVerNum:
                            continue
                        if 'X.X' != server['pyver'] and pythonVer != server['pyver']:
                            continue
                        if config.plugins.iptvplayer.possibleUpdateType.value not in [server['packagetype'], 'all']: #"sourcecode", "precompiled"
                            continue

                    name = "| %s | python %s | %s | %s |" % (server['version'], server['pyver'], server['packagetype'], server['name'])
                    #printDBG("server list: " + name)
                    options.append((name, idx))
                if 1 == len(options) and not config.plugins.iptvplayer.downgradePossible.value:
                    self.__selServerCallBack(options[0])
                elif 0 < len(options):
                    self.session.openWithCallback(self.__selServerCallBack, ChoiceBox, title=_("Select update server"), list = options)
                else:
                    self.stepFinished(-1, _("There is no update for the current configuration."))
            else:
                self.stepFinished(-1, _("Update not available."))
        
    def __selServerCallBack(self, retArg):
        if retArg and len(retArg) == 2:
            self.currServIdx = retArg[1]
            # if GetIPTVPlayerVerstion() == self.serversList[self.currServIdx]['version']:
                # self.stepFinished(-1, 'Wybrano wersję [%s]. Wybrana wersja jest wersją aktualną' % retArg[0])
            # else:
            self.stepFinished(0, _("Selected version [%s].") % retArg[0])
        else:
            self.stepFinished(-1, _("Update server not selected."))
    
    ##############################################################################
    # GET ARCHIVE STEP'S PRIVATES METHODS
    ############################################################################## 
    def __archiveDownloadFinished(self, arg, status):
        url            = self.downloader.getUrl()
        filePath       = self.downloader.getFullFileName()
        remoteFileSize = self.downloader.getRemoteFileSize()
        localFileSize  = self.downloader.getLocalFileSize(True)
        self.downloader = None
        printDBG('UpdateMainAppImpl.__archiveDownloadFinished url[%s], filePath[%s], remoteFileSize[%d], localFileSize[%d] ' % (url, filePath, remoteFileSize, localFileSize))
        if DMHelper.STS.DOWNLOADED != status and remoteFileSize > localFileSize:
            sts, msg = self.checkForFreeSpace(self.tmpDir, remoteFileSize - localFileSize)
            if sts:
                msg = _("Problem with downloading the packet:\n[%s].") % url
            self.stepFinished(-1, msg)
        else:
            self.stepFinished(0, _("Update packet was downloaded successfully."))
        return
        
    ##############################################################################
    # UNPACK ARCHIVE STEP'S PRIVATES METHODS
    ##############################################################################
    def __unpackCmdFinished(self, status, outData):
        code = -1
        msg  = ""
        self.cmd = None
        if 0 != status:
            code = -1
            msg  = _("Problem with extracting the archive. Return code [%d]\n%s.") % (status, outData)
        else:
            try:
                os_remove
            except:
                printExc()
            code = 0
            msg  = _("Unpacking the archive completed successfully.")
        self.stepFinished(code, msg)
        
    ##############################################################################
    # ExecuteUserScripts STEP'S PRIVATES METHODS
    ##############################################################################
    def __getUserCmdsList(self):
        printDBG('UpdateMainAppImpl.__getScriptsList begin')
        cmdList = [] 
        try:
            pathWithUserScripts =  os_path.join(self.ExtensionPath, 'IPTVPlayer/iptvupdate/custom/')
            fileList = os_listdir( pathWithUserScripts )
            for wholeFileName in fileList:
                # separate file name and file extension
                fileName, fileExt = os_path.splitext(wholeFileName)
                filePath = os_path.join(pathWithUserScripts, wholeFileName) 
                if os_path.isfile(filePath):
                    if fileExt in ['.pyo', '.pyc', '.py']:
                        interpreterBinName = 'python'
                    elif '.sh' == fileExt:
                        interpreterBinName = 'sh'
                    else:
                        continue 
                    cmdList.append('%s "%s" "%s" "%s" 2>&1 ' % (interpreterBinName, filePath, os_path.join(self.ExtensionPath, 'IPTVPlayer/'), os_path.join(self.ExtensionTmpPath, 'IPTVPlayer/')) )
            cmdList.sort()
        except:
            printExc()
        printDBG('UpdateMainAppImpl.__getScriptsList [%r]' % cmdList)
        return cmdList
     
    def __userCmdFinished(self, status, outData):
        self.cmd = None
        if 0 != status:
            code = -1
        else:
            code = 0
        msg  = '------------\nstatus[%d]\n[%s]\n------------\n' % (status, outData)
        self.stepExecuteUserScripts(init=False, code=code, msg=msg)
        
    ##############################################################################
    # Instalation new version STEP'S PRIVATES METHODS
    ##############################################################################
    def __removeOldVersionCmdFinished(self, status, outData):
        self.cmd = None
        if 0 != status:
            code = -1
            msg = _("Problem with the removal of the previous version.\nStatus[%d], outData[%s].") % (status, outData)
        else:
            code = 0
            msg = _("Completed.")
        self.stepFinished(code, msg)
        
    def __installNewVersionCmdFinished(self, status, outData):
        self.cmd = None
        if 0 != status:
            msg = _("Problem with installing the new version.\nStatus[%d], outData[%s]") % (status, outData)
            self.stepFinished(-1, msg)
        else:
            self.cmd = iptv_system( 'rm -rf ' + self.tmpDir + " && sync" , self.__doSyncCallBack )
        return
        
    def __doSyncCallBack(self, status, outData):
        self.cmd = None
        code, msg = self.checkVersionFile( os_path.join(self.ExtensionPath, 'IPTVPlayer') )
        self.stepFinished(code, msg)
