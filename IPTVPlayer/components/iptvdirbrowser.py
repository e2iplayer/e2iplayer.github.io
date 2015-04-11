# -*- coding: utf-8 -*-
#
#  Directory selector
#
#  $Id$
#
# 
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.iptvlist import IPTVMainNavigatorList
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, mkdir, IsValidFileName, GetBinDir, eConnectCallback
###################################################
 
###################################################
# FOREIGN import
###################################################
from enigma import eConsoleAppContainer, getDesktop

from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.MessageBox import MessageBox
from Components.Sources.StaticText import StaticText
from Components.Label import Label
from Components.ActionMap import ActionMap
from Tools.BoundFunction import boundFunction
from os import path as os_path, chmod as os_chmod
###################################################

class CListItem:
    def __init__(self, name='', fullDir='', type='dir'):
        self.type = type
        self.name = name
        self.fullDir = fullDir

class IPTVDirBrowserList(IPTVMainNavigatorList):
    def __init__(self):
        self.ICONS_FILESNAMES = {'dir' : 'CategoryItem.png'}
        IPTVMainNavigatorList.__init__(self)

class IPTVDirectorySelectorWidget(Screen):
    screenwidth = getDesktop(0).size().width()
    if screenwidth and screenwidth == 1920:  
        skin = """
        <screen name="IPTVDirectorySelectorWidget" position="center,center" size="820,860" title="">
            <widget name="key_red"     position="10,10"  zPosition="2"  size="600,35" valign="center"  halign="left"   font="Regular;28" transparent="1" foregroundColor="red" />
            <widget name="key_blue"    position="10,10"  zPosition="2"  size="600,35" valign="center"  halign="center" font="Regular;28" transparent="1" foregroundColor="blue" />
            <widget name="key_green"   position="10,10"  zPosition="2"  size="600,35" valign="center"  halign="right"  font="Regular;28" transparent="1" foregroundColor="green" />
            <widget name="curr_dir"    position="10,50"  zPosition="2"  size="600,35" valign="center"  halign="left"   font="Regular;28" transparent="1" foregroundColor="white" />
            <widget name="list"        position="10,95"  zPosition="1"  size="800,725" transparent="1" scrollbarMode="showOnDemand" />
        </screen>"""
    else:
        skin = """
        <screen name="IPTVDirectorySelectorWidget" position="center,center" size="620,440" title="">
            <widget name="key_red"     position="10,10"  zPosition="2"  size="600,35" valign="center"  halign="left"   font="Regular;22" transparent="1" foregroundColor="red" />
            <widget name="key_blue"    position="10,10"  zPosition="2"  size="600,35" valign="center"  halign="center" font="Regular;22" transparent="1" foregroundColor="blue" />
            <widget name="key_green"   position="10,10"  zPosition="2"  size="600,35" valign="center"  halign="right"  font="Regular;22" transparent="1" foregroundColor="green" />
            <widget name="curr_dir"    position="10,50"  zPosition="2"  size="600,35" valign="center"  halign="left"   font="Regular;18" transparent="1" foregroundColor="white" />
            <widget name="list"        position="10,85"  zPosition="1"  size="580,335" transparent="1" scrollbarMode="showOnDemand" />
        </screen>"""      
    def __init__(self, session, currDir, title="Directory browser"):
        printDBG("IPTVDirectorySelectorWidget.__init__ -------------------------------")
        Screen.__init__(self, session)
        self["key_red"]    = Label(_("Cancel"))
        #self["key_yellow"] = Label(_("Odśwież"))
        self["key_blue"]   = Label(_("New dir"))
        self["key_green"]  = Label(_("Apply"))
        self["curr_dir"]   = Label(_(" "))
        self["list"]   = IPTVDirBrowserList()
        self["FilelistActions"] = ActionMap(["SetupActions", "ColorActions"],
            {
                "green" : self.requestApply,
                "red"   : self.requestCancel,
                "yellow": self.requestRefresh,
                "blue"  : self.requestNewDir,
                "ok"    : self.requestOk,
                "cancel": self.requestBack
            })
        self.title = title
        self.onLayoutFinish.append(self.layoutFinished)
        self.onClose.append(self.__onClose)
        
        self.console = eConsoleAppContainer()
        self.console_appClosed_conn   = eConnectCallback(self.console.appClosed, self.refreshFinished)
        self.console_stderrAvail_conn = eConnectCallback(self.console.stderrAvail, self.refreshNewData)
        self.underRefreshing  = False
        self.underClosing     = False
        self.deferredAction   = None
        
        self.currDir   = currDir
        self.currList  = []
        
        self.tmpData = ''
        self.tmpList = []

    def __del__(self):
        printDBG("IPTVDirectorySelectorWidget.__del__ -------------------------------")

    def __onClose(self):
        printDBG("IPTVDirectorySelectorWidget.__onClose -----------------------------")
        if None != self.console:
            self.console_appClosed_conn   = None
            self.console_stderrAvail_conn = None
            self.console_stdoutAvail_conn = None
            self.console.sendCtrlC()
            self.console = None
            
        self.onClose.remove(self.__onClose)
        self.onLayoutFinish.remove(self.layoutFinished)
        
    def _iptvDoClose(self, ret=None):
        if self.console: self.console.sendCtrlC()
        self.close(ret)
        
    def _getSelItem(self):
        currSelIndex = self["list"].getCurrentIndex()
        if len(self.currList) <= currSelIndex: return None
        return self.currList[currSelIndex]
        
    def doAction(self, action):
        if not self.underRefreshing:
            action()
        else:
            self.deferredAction = action
            self.console.sendCtrlC()
    
    def layoutFinished(self):
        printDBG("IPTVDirectorySelectorWidget.layoutFinished -------------------------------")
        self.setTitle(_(self.title))
        self.currDirChanged()

    def currDirChanged(self):
        printDBG("IPTVDirectorySelectorWidget.currDirChanged")
        self.currDir = self.getCurrentDirectory()
        self["curr_dir"].setText(_(self.currDir))
        self["list"].setList([])
        self.requestRefresh()
        
    def getCurrentDirectory(self):
        if self.currDir and os_path.isdir( self.currDir ): 
            if '/' != self.currDir[-1]: self.currDir += '/'
            return self.currDir
        else: return "/"
    
    def refreshFinished(self, code):
        printDBG("IPTVDirectorySelectorWidget.refreshFinished")
        if None != self.deferredAction:
            deferredAction = self.deferredAction
            self.deferredAction = None
            deferredAction()
        else:
            printDBG("IPTVDirectorySelectorWidget.refreshFinished fill list")
            # sort list and set
            self.currList = []
            self.tmpList.sort(key=lambda x: x.name.lower())
            self.currList = self.tmpList
            if('/' != self.currDir): self.currList.insert(0,  CListItem(name='..', fullDir='', type='dir') ) # add back item
            self["list"].setList([ (x,) for x in self.currList])
            self.tmpList = []
            self.tmpData = ''
            self.underRefreshing = False
        
    def refreshNewData(self, data):
        self.tmpData += data
        newDirs = self.tmpData.split('\n')
        if self.tmpData.endswith('\n'):
            self.tmpData = ''
        else:
            self.tmpData = newDirs[-1]
            del newDirs[-1]
        for item in newDirs:
            params = item.split('//')
            if item.startswith('.'): continue # do not list hidden items
            #printDBG(params)
            if 4 == len(params):
                #if '0' == params[2]: type = 'dir'
                #else: type = 'linkdir'
                self.tmpList.append( CListItem(name=params[0], fullDir=params[3], type='dir') )
        
    def requestApply(self):
        if self.underClosing: return
        self.doAction( boundFunction(self._iptvDoClose, self.getCurrentDirectory()) )
        
    def requestCancel(self):
        if self.underClosing: return
        self.doAction( boundFunction(self._iptvDoClose, None) )
        
    def requestRefresh(self):
        if self.underClosing: return
        if self.underRefreshing: return
        self.underRefreshing = True
        self.tmpList = []
        self.tmpData = ''
        lsdirPath = GetBinDir("lsdir")
        try: os_chmod(lsdirPath, 0777)
        except: printExc()
        cmd = '%s "%s" dl d' % (lsdirPath, self.currDir)
        printDBG("IPTVDirectorySelectorWidget.requestRefresh cmd[%s]" % cmd)
        self.console.execute( cmd )

    def requestNewDir(self):
        if self.underClosing: return
        self.doAction( self.newDir )
        
    def requestOk(self):
        if self.underClosing: return
        self.doAction( self.ok )
        
    def requestBack(self):
        if self.underClosing: return
        self.doAction( self.back )
        
    def ok(self):
        item = self._getSelItem()
        if None == item or '' == item.name: return
        fullDirName = os_path.join(self.currDir, item.name)
        if '..' == item.name: return self.back()
        if os_path.isdir( fullDirName ):
            self.currDir = fullDirName
            self.currDirChanged()

    def back(self):
        if '/' == self.currDir:
            self._iptvDoClose(None)
        else:
            self.currDir = self.currDir[:self.currDir[:-1].rfind('/')]
            self.currDirChanged()
        
    def newDir(self):
        self.session.openWithCallback(self.enterPatternCallBack, VirtualKeyBoard, title = (_("Enter name")), text = "")

    def enterPatternCallBack(self, newDirName=None):
        if None != self.currDir and newDirName != None:
            sts = False
            if IsValidFileName(newDirName):
                try: sts,msg = mkdir(os_path.join(self.currDir, newDirName))
                except: sts,msg = False, _("Exception occurs")
            else:
                msg = _("Invalid name.")
            if sts:
                self.requestRefresh()
            else:
                self.session.open(MessageBox, msg, type = MessageBox.TYPE_INFO, timeout=5)