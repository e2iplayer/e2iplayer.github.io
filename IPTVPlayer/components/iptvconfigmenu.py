# -*- coding: utf-8 -*-
#
#  Konfigurator dla iptv 2013
#  autorzy: j00zek, samsamsam
#

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetSkinsList, GetHostsList, IsHostEnabled
from Plugins.Extensions.IPTVPlayer.iptvupdate.updatemainwindow import IPTVUpdateWindow, UpdateMainAppImpl
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, IPTVPlayerNeedInit
from Plugins.Extensions.IPTVPlayer.components.configbase import ConfigBaseWidget
from Plugins.Extensions.IPTVPlayer.components.confighost import ConfigHostsMenu
from Plugins.Extensions.IPTVPlayer.components.iptvdirbrowser import IPTVDirectorySelectorWidget
from Plugins.Extensions.IPTVPlayer.setup.iptvsetupwidget import IPTVSetupMainWidget
###################################################

###################################################
# FOREIGN import
###################################################
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard

from Components.ActionMap import ActionMap, HelpableActionMap
from Components.Label import Label
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigDirectory, ConfigYesNo, ConfigOnOff, Config, ConfigInteger, ConfigSubList, ConfigText, getConfigListEntry, configfile
from Components.ConfigList import ConfigListScreen
from Tools.BoundFunction import boundFunction
###################################################


###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer = ConfigSubsection()
config.plugins.iptvplayer.gstplayerpath = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.wgetpath      = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.rtmpdumppath  = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.f4mdumppath   = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.plarform      = ConfigSelection(default = "auto", choices = [("auto", "auto"),("mipsel", _("mipsel")),("sh4", _("sh4")),("i686", _("i686")),("unknown", _("unknown"))])

config.plugins.iptvplayer.showcover          = ConfigYesNo(default = True)
config.plugins.iptvplayer.deleteIcons        = ConfigSelection(default = "3", choices = [("0", _("after closing")),("1", _("after day")),("3", _("after three days")),("7", _("after a week"))]) 
config.plugins.iptvplayer.showinextensions   = ConfigYesNo(default = True)
config.plugins.iptvplayer.showinMainMenu     = ConfigYesNo(default = False)
config.plugins.iptvplayer.ListaGraficzna     = ConfigYesNo(default = True)
config.plugins.iptvplayer.NaszaSciezka       = ConfigDirectory(default = "/hdd/movie/") #, fixed_size = False)
config.plugins.iptvplayer.bufferingPath      = ConfigDirectory(default = config.plugins.iptvplayer.NaszaSciezka.value) #, fixed_size = False)
config.plugins.iptvplayer.buforowanie        = ConfigYesNo(default = False)
config.plugins.iptvplayer.buforowanie_m3u8   = ConfigYesNo(default = True)
config.plugins.iptvplayer.buforowanie_rtmp   = ConfigYesNo(default = False)
config.plugins.iptvplayer.requestedBuffSize  = ConfigInteger(5, (1,120))
config.plugins.iptvplayer.requestedAudioBuffSize  = ConfigInteger(256, (1,10240))

config.plugins.iptvplayer.IPTVDMRunAtStart      = ConfigYesNo(default = False)
config.plugins.iptvplayer.IPTVDMShowAfterAdd    = ConfigYesNo(default = True)
config.plugins.iptvplayer.IPTVDMMaxDownloadItem = ConfigSelection(default = "1", choices = [("1", "1"),("2", "2"),("3", "3"),("4", "4")])

config.plugins.iptvplayer.AktualizacjaWmenu = ConfigYesNo(default = True)
config.plugins.iptvplayer.sortuj = ConfigYesNo(default = True)
config.plugins.iptvplayer.devHelper = ConfigYesNo(default = False)


config.plugins.iptvplayer.NaszPlayer = ConfigSelection(default = "mini", choices = [("mini", _("internal")), ('extgstplayer', _("external gstplayer")), ("standard", _("standard"))])
    
config.plugins.iptvplayer.defaultSH4MoviePlayer         = ConfigSelection(default = "mini", choices = [("mini", _("internal")),("standard", _("standard")), ('exteplayer', _("external eplayer3")), ('extgstplayer', _("external gstplayer"))]) 
config.plugins.iptvplayer.alternativeSH4MoviePlayer     = ConfigSelection(default = "mini", choices = [("mini", _("internal")),("standard", _("standard")), ('exteplayer', _("external eplayer3")), ('extgstplayer', _("external gstplayer"))]) 

config.plugins.iptvplayer.defaultMIPSELMoviePlayer      = ConfigSelection(default = "mini", choices = [("mini", _("internal")),("standard", _("standard")), ('extgstplayer', _("external gstplayer"))])
config.plugins.iptvplayer.alternativeMIPSELMoviePlayer  = ConfigSelection(default = "mini", choices = [("mini", _("internal")),("standard", _("standard")), ('extgstplayer', _("external gstplayer"))])

config.plugins.iptvplayer.defaultI686MoviePlayer        = ConfigSelection(default = "mini", choices = [("mini", _("internal")),("standard", _("standard")), ('extgstplayer', _("external gstplayer"))])
config.plugins.iptvplayer.alternativeI686MoviePlayer    = ConfigSelection(default = "mini", choices = [("mini", _("internal")),("standard", _("standard")), ('extgstplayer', _("external gstplayer"))])

config.plugins.iptvplayer.SciezkaCache = ConfigDirectory(default = "/hdd/IPTVCache/") #, fixed_size = False)
config.plugins.iptvplayer.NaszaTMP = ConfigDirectory(default = "/tmp/") #, fixed_size = False)
config.plugins.iptvplayer.ZablokujWMV = ConfigYesNo(default = True)

config.plugins.iptvplayer.hd3d_login    = ConfigText(default="", fixed_size = False)
config.plugins.iptvplayer.hd3d_password = ConfigText(default="", fixed_size = False)

config.plugins.iptvplayer.debugprint = ConfigSelection(default = "", choices = [("", _("no")),("console", _("yes, to console")),("debugfile", _("yes, to file /hdd/iptv.dbg"))]) 

#icons
config.plugins.iptvplayer.IconsSize = ConfigSelection(default = "135", choices = [("135", "135x135"),("120", "120x120"),("100", "100x100")]) 
config.plugins.iptvplayer.numOfRow = ConfigSelection(default = "0", choices = [("1", "1"),("2", "2"),("3", "3"),("4", "4"),("0", "auto")])
config.plugins.iptvplayer.numOfCol = ConfigSelection(default = "0", choices = [("1", "1"),("2", "2"),("3", "3"),("4", "4"),("5", "5"),("6", "6"),("7", "7"),("8", "8"),("0", "auto")])

config.plugins.iptvplayer.skin = ConfigSelection(default = "Default", choices = GetSkinsList())

#Pin code
from iptvpin import IPTVPinWidget
config.plugins.iptvplayer.fakePin = ConfigSelection(default = "fake", choices = [("fake", "****")])
config.plugins.iptvplayer.pin = ConfigText(default = "0000", fixed_size = False)
config.plugins.iptvplayer.configProtectedByPin = ConfigYesNo(default = False)
config.plugins.iptvplayer.pluginProtectedByPin = ConfigYesNo(default = False)

config.plugins.iptvplayer.httpssslcertvalidation = ConfigYesNo(default = True)

#PROXY
config.plugins.iptvplayer.proxyurl = ConfigText(default = "http://PROXY_IP:PORT", fixed_size = False)
config.plugins.iptvplayer.german_proxyurl = ConfigText(default = "http://PROXY_IP:PORT", fixed_size = False)


# Update
config.plugins.iptvplayer.autoCheckForUpdate = ConfigYesNo(default = True)
config.plugins.iptvplayer.updateLastCheckedVersion = ConfigText(default = "00.00.00.00", fixed_size = False)
config.plugins.iptvplayer.fakeUpdate               = ConfigSelection(default = "fake", choices = [("fake", "  ")])
config.plugins.iptvplayer.downgradePossible        = ConfigYesNo(default = False)
config.plugins.iptvplayer.possibleUpdateType       = ConfigSelection(default = "precompiled", choices = [("sourcecode", _("with source code")),("precompiled", _("precompiled")), ("all", _("all types"))]) 

# Hosts lists
config.plugins.iptvplayer.fakeHostsList = ConfigSelection(default = "fake", choices = [("fake", "  ")])
# hidden options
config.plugins.iptvplayer.hiddenAllVersionInUpdate = ConfigYesNo(default = False)

config.plugins.iptvplayer.extplayer_infobar_timeout = ConfigSelection(default = "5", choices = [
        ("1", "1 " + _("second")), ("2", "2 " + _("seconds")), ("3", "3 " + _("seconds")),
        ("4", "4 " + _("seconds")), ("5", "5 " + _("seconds")), ("6", "6 " + _("seconds")), ("7", "7 " + _("seconds")),
        ("8", "8 " + _("seconds")), ("9", "9 " + _("seconds")), ("10", "10 " + _("seconds"))])


###################################################

########################################################
# Generate list of hosts options for Enabling/Disabling
########################################################
class ConfigIPTVHostOnOff(ConfigOnOff):
    def __init__(self, default = False):
        ConfigOnOff.__init__(self, default = default)

gListOfHostsNames = GetHostsList()
for hostName in gListOfHostsNames:
    try:
        printDBG("Set default options for host '%s'" % hostName)
        # as default all hosts are enabled
        exec('config.plugins.iptvplayer.host' + hostName + ' = ConfigIPTVHostOnOff(default = True)')
    except:
        printExc(hostName)

###################################################

class ConfigMenu(ConfigBaseWidget):

    def __init__(self, session):
        printDBG("ConfigMenu.__init__ -------------------------------")
        self.list = [ ]
        ConfigBaseWidget.__init__(self, session)
        # remember old
        self.showcoverOld = config.plugins.iptvplayer.showcover.value
        self.SciezkaCacheOld = config.plugins.iptvplayer.SciezkaCache.value
        self.platformOld = config.plugins.iptvplayer.plarform.value

    def __del__(self):
        printDBG("ConfigMenu.__del__ -------------------------------")
        
    def __onClose(self):
        printDBG("ConfigMenu.__onClose -----------------------------")
        ConfigBaseWidget.__onClose(self)

    def layoutFinished(self):
        ConfigBaseWidget.layoutFinished(self)
        self.setTitle("IPTV Player - ustawienia")
        
    @staticmethod
    def fillConfigList(list, hiddenOptions=False):
        if hiddenOptions:
            list.append( getConfigListEntry(_("Last checked version"), config.plugins.iptvplayer.updateLastCheckedVersion) )
            list.append( getConfigListEntry(_("Show all version in the update menu"), config.plugins.iptvplayer.hiddenAllVersionInUpdate) )
            list.append(getConfigListEntry(_("Disable host protection (error == GS)"), config.plugins.iptvplayer.devHelper))
            
            list.append(getConfigListEntry("gstplayerpath", config.plugins.iptvplayer.gstplayerpath))
            list.append(getConfigListEntry("wgetpath", config.plugins.iptvplayer.wgetpath))
            list.append(getConfigListEntry("rtmpdumppath", config.plugins.iptvplayer.rtmpdumppath))
            list.append(getConfigListEntry("f4mdumppath", config.plugins.iptvplayer.f4mdumppath))
        
        list.append( getConfigListEntry(_("Auto check for plugin update"), config.plugins.iptvplayer.autoCheckForUpdate) )
        list.append( getConfigListEntry(_("Update"), config.plugins.iptvplayer.fakeUpdate) )
        list.append( getConfigListEntry(_("Platform"), config.plugins.iptvplayer.plarform) )
        list.append( getConfigListEntry(_("Services configuration"), config.plugins.iptvplayer.fakeHostsList) )
        list.append( getConfigListEntry(_("Pin protection for plugin"), config.plugins.iptvplayer.pluginProtectedByPin))
        list.append( getConfigListEntry(_("Pin protection for configuration"), config.plugins.iptvplayer.configProtectedByPin) )
        if config.plugins.iptvplayer.pluginProtectedByPin.value or config.plugins.iptvplayer.configProtectedByPin.value:
            list.append( getConfigListEntry(_("Set pin code"), config.plugins.iptvplayer.fakePin) )
        
        list.append(getConfigListEntry(_("Skin"), config.plugins.iptvplayer.skin))
        list.append(getConfigListEntry(_("Display thumbnails"), config.plugins.iptvplayer.showcover))
        if config.plugins.iptvplayer.showcover.value:
            list.append(getConfigListEntry(_("    Remove thumbnails"), config.plugins.iptvplayer.deleteIcons))
        #list.append(getConfigListEntry("Sortować listy?", config.plugins.iptvplayer.sortuj))            
        list.append(getConfigListEntry(_("Graphic services selector"), config.plugins.iptvplayer.ListaGraficzna))
        if config.plugins.iptvplayer.ListaGraficzna.value == True:
            list.append(getConfigListEntry(_("    Service icon size"), config.plugins.iptvplayer.IconsSize))
            list.append(getConfigListEntry(_("    Number of rows"), config.plugins.iptvplayer.numOfRow))
            list.append(getConfigListEntry(_("    Number of columns"), config.plugins.iptvplayer.numOfCol))
        
        list.append(getConfigListEntry(_("https - validate SSL certificates"), config.plugins.iptvplayer.httpssslcertvalidation))
        list.append(getConfigListEntry(_("Polish proxy server url"), config.plugins.iptvplayer.proxyurl))
        list.append(getConfigListEntry(_("German proxy server url"), config.plugins.iptvplayer.german_proxyurl))
        
        list.append(getConfigListEntry(_("Folder for cache data"), config.plugins.iptvplayer.SciezkaCache))
        list.append(getConfigListEntry(_("Folder for temporary data"), config.plugins.iptvplayer.NaszaTMP))
        
        # BUFFERING
        list.append(getConfigListEntry(_("[HTTP] buffering"), config.plugins.iptvplayer.buforowanie))
        list.append(getConfigListEntry(_("[HLS/M3U8] buffering"), config.plugins.iptvplayer.buforowanie_m3u8))
        list.append(getConfigListEntry(_("[RTMP] buffering (rtmpdump required)"), config.plugins.iptvplayer.buforowanie_rtmp)) 
        
        if config.plugins.iptvplayer.buforowanie.value or config.plugins.iptvplayer.buforowanie_m3u8.value or config.plugins.iptvplayer.buforowanie_rtmp.value:
            list.append(getConfigListEntry(_("    Video buffer size [MB]"), config.plugins.iptvplayer.requestedBuffSize))
            list.append(getConfigListEntry(_("    Audio buffer size [KB]"), config.plugins.iptvplayer.requestedAudioBuffSize))
            list.append(getConfigListEntry(_("Buffer path"), config.plugins.iptvplayer.bufferingPath))
            
        list.append(getConfigListEntry(_("Records path"), config.plugins.iptvplayer.NaszaSciezka))           
        list.append(getConfigListEntry(_("Start download manager per default"), config.plugins.iptvplayer.IPTVDMRunAtStart))
        list.append(getConfigListEntry(_("Show download manager after adding new item"), config.plugins.iptvplayer.IPTVDMShowAfterAdd))
        list.append(getConfigListEntry(_("Number of downloaded files simultaneously"), config.plugins.iptvplayer.IPTVDMMaxDownloadItem))
        
        list.append(getConfigListEntry("HD3D " + _("login"), config.plugins.iptvplayer.hd3d_login))
        list.append(getConfigListEntry("HD3D " + _("password"), config.plugins.iptvplayer.hd3d_password))
        
        players = []
        if  config.plugins.iptvplayer.buforowanie.value or config.plugins.iptvplayer.buforowanie_m3u8.value or config.plugins.iptvplayer.buforowanie_rtmp.value:
            if 'sh4' == config.plugins.iptvplayer.plarform.value:
                list.append(getConfigListEntry(_("First move player in buffering mode"), config.plugins.iptvplayer.defaultSH4MoviePlayer))
                list.append(getConfigListEntry(_("Second move player in buffering mode"), config.plugins.iptvplayer.alternativeSH4MoviePlayer))
                list.append(getConfigListEntry(_("Movie player without buffering mode"), config.plugins.iptvplayer.NaszPlayer))
                players = [config.plugins.iptvplayer.defaultSH4MoviePlayer.value, config.plugins.iptvplayer.alternativeSH4MoviePlayer.value]
            elif 'mipsel' == config.plugins.iptvplayer.plarform.value:
                list.append(getConfigListEntry(_("First move player in buffering mode"), config.plugins.iptvplayer.defaultMIPSELMoviePlayer))
                list.append(getConfigListEntry(_("Second move player in buffering mode"), config.plugins.iptvplayer.alternativeMIPSELMoviePlayer))
                list.append(getConfigListEntry(_("Movie player without buffering mode"), config.plugins.iptvplayer.NaszPlayer))
                players = [config.plugins.iptvplayer.defaultMIPSELMoviePlayer.value, config.plugins.iptvplayer.alternativeMIPSELMoviePlayer.value]
            elif 'i686' == config.plugins.iptvplayer.plarform.value:
                list.append(getConfigListEntry(_("First move player in buffering mode"), config.plugins.iptvplayer.defaultI686MoviePlayer))
                list.append(getConfigListEntry(_("Second move player in buffering mode"), config.plugins.iptvplayer.alternativeI686MoviePlayer))
                list.append(getConfigListEntry(_("Movie player without buffering mode"), config.plugins.iptvplayer.NaszPlayer))
                players = [config.plugins.iptvplayer.defaultI686MoviePlayer.value, config.plugins.iptvplayer.alternativeI686MoviePlayer.value]
            else: list.append(getConfigListEntry(_("Movie player"), config.plugins.iptvplayer.NaszPlayer))
        else:
            list.append(getConfigListEntry(_("Movie player"), config.plugins.iptvplayer.NaszPlayer))
        players.append( config.plugins.iptvplayer.NaszPlayer.value )
        if 'exteplayer' in players or 'extgstplayer' in players:
            list.append(getConfigListEntry(_("External player infobar timeout"), config.plugins.iptvplayer.extplayer_infobar_timeout))

        list.append(getConfigListEntry(_("Block wmv files"), config.plugins.iptvplayer.ZablokujWMV))

        list.append(getConfigListEntry(_("Show IPTVPlayer in extension list"), config.plugins.iptvplayer.showinextensions))
        list.append(getConfigListEntry(_("Show IPTVPlayer in main menu"), config.plugins.iptvplayer.showinMainMenu))
        list.append(getConfigListEntry(_("Show update icon in service selection menu"), config.plugins.iptvplayer.AktualizacjaWmenu))
        list.append(getConfigListEntry(_("Debug logs"), config.plugins.iptvplayer.debugprint))
        list.append(getConfigListEntry(_("Allow downgrade"), config.plugins.iptvplayer.downgradePossible))
        list.append(getConfigListEntry(_("Update packet type"), config.plugins.iptvplayer.possibleUpdateType))

    def runSetup(self):
        self.list = []
        ConfigMenu.fillConfigList(self.list, self.isHiddenOptionsUnlocked())
        ConfigBaseWidget.runSetup(self)
        
    def onSelectionChanged(self):
        currItem = self["config"].getCurrent()[1]
        if currItem in [config.plugins.iptvplayer.fakePin, config.plugins.iptvplayer.fakeUpdate, config.plugins.iptvplayer.fakeHostsList]:
            self.isOkEnabled  = True
            self.isSelectable = False 
            self.setOKLabel()
        else:
            ConfigBaseWidget.onSelectionChanged(self)

    def keyUpdate(self):
        printDBG("ConfigMenu.keyUpdate")
        if self.isChanged():
            self.askForSave(self.doUpdate, self.doUpdate)
        else:
            self.doUpdate()

    def doUpdate(self):
        printDBG("ConfigMenu.doUpdate")
        self.session.open(IPTVUpdateWindow, UpdateMainAppImpl(self.session))
        

    def save(self):
        ConfigBaseWidget.save(self)
        if self.showcoverOld != config.plugins.iptvplayer.showcover.value or \
           self.SciezkaCacheOld != config.plugins.iptvplayer.SciezkaCache.value:
           pass
           # plugin must be restarted if we wont to this options take effect
        if self.platformOld != config.plugins.iptvplayer.plarform.value:
            IPTVPlayerNeedInit(True)

    def keyOK(self):
        curIndex = self["config"].getCurrentIndex()
        currItem = self["config"].list[curIndex][1]
        if isinstance(currItem, ConfigDirectory):
            def SetDirPathCallBack(curIndex, newPath):
                if None != newPath: self["config"].list[curIndex][1].value = newPath
            self.session.openWithCallback(boundFunction(SetDirPathCallBack, curIndex), IPTVDirectorySelectorWidget, currDir=currItem.value, title="Wybierz katalog")
        elif config.plugins.iptvplayer.fakePin == currItem:
            self.changePin(start = True)
        elif config.plugins.iptvplayer.fakeUpdate == currItem:
            self.keyUpdate()
        elif config.plugins.iptvplayer.fakeHostsList == currItem:
            self.hostsList()
        else:
            ConfigBaseWidget.keyOK(self)

    def getSubOptionsList(self):
        tab = [config.plugins.iptvplayer.buforowanie,
              config.plugins.iptvplayer.buforowanie_m3u8,
              config.plugins.iptvplayer.buforowanie_rtmp,
              config.plugins.iptvplayer.showcover,
              config.plugins.iptvplayer.ListaGraficzna,
              config.plugins.iptvplayer.pluginProtectedByPin,
              config.plugins.iptvplayer.configProtectedByPin,
              config.plugins.iptvplayer.plarform,
              ]
        return tab

    def changePin(self, pin = None, start = False):
        # 'PUT_OLD_PIN', 'PUT_NEW_PIN', 'CONFIRM_NEW_PIN'
        if True == start:
            self.changingPinState = 'PUT_OLD_PIN'
            self.session.openWithCallback(self.changePin, IPTVPinWidget, title=_("Enter old pin"))
        else:
            if pin == None: return
            if 'PUT_OLD_PIN' == self.changingPinState:
                if pin == config.plugins.iptvplayer.pin.value:
                    self.changingPinState = 'PUT_NEW_PIN'
                    self.session.openWithCallback(self.changePin, IPTVPinWidget, title=_("Enter new pin"))
                else:
                    self.session.open(MessageBox, _("Pin incorrect!"), type=MessageBox.TYPE_INFO, timeout=5)
            elif 'PUT_NEW_PIN' == self.changingPinState:
                self.newPin = pin
                self.changingPinState = 'CONFIRM_NEW_PIN'
                self.session.openWithCallback(self.changePin, IPTVPinWidget, title=_("Confirm new pin"))
            elif 'CONFIRM_NEW_PIN' == self.changingPinState:
                if self.newPin == pin:
                    config.plugins.iptvplayer.pin.value = pin
                    config.plugins.iptvplayer.pin.save()
                    configfile.save()
                    self.session.open(MessageBox, _("Pin has been changed."), type=MessageBox.TYPE_INFO, timeout=5)
                else:
                    self.session.open(MessageBox, _("Confirmation error."), type=MessageBox.TYPE_INFO, timeout=5)
                    
    def hostsList(self):
        global gListOfHostsNames
        self.session.open(ConfigHostsMenu, gListOfHostsNames)

