# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget import IPTVPlayerWidget
from Plugins.Extensions.IPTVPlayer.components.iptvconfigmenu import ConfigMenu
from Plugins.Extensions.IPTVPlayer.components.iptvpin import IPTVPinWidget
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, IPTVPlayerNeedInit
from Plugins.Extensions.IPTVPlayer.setup.iptvsetupwidget import IPTVSetupMainWidget
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import IsExecutable
###################################################

###################################################
# FOREIGN import
###################################################
from enigma import getDesktop

from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Tools.BoundFunction import boundFunction
from Components.config import config
###################################################

####################################################
# Wywołanie wtyczki w roznych miejscach
####################################################
def Plugins(**kwargs):
    screenwidth = getDesktop(0).size().width()
    if screenwidth and screenwidth == 1920: iconFile = "icons/iptvlogohd.png"
    else: iconFile = "icons/iptvlogo.png"
    desc = _("Watch video materials from IPTV services")
    list = [PluginDescriptor(name="IPTV Player", description=desc, where = [PluginDescriptor.WHERE_PLUGINMENU], icon=iconFile, fnc=main)] # always show in plugin menu
    list.append(PluginDescriptor(name="IPTV Player", description=desc, where = PluginDescriptor.WHERE_MENU, fnc=startIPTVfromMenu))
    if config.plugins.iptvplayer.showinextensions.value:
        list.append (PluginDescriptor(name="IPTV Player", description=desc, where = [PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main))
    return list

####################################################
# Konfiguracja wtyczki
####################################################

#from __init__ import _

def startIPTVfromMenu(menuid, **kwargs):
    if menuid == "system":
        return [(_("Configure IPTV Player"), mainSetup, "iptv_config", None)]
    elif menuid == "mainmenu" and config.plugins.iptvplayer.showinMainMenu.value == True:
        return [("IPTV Player", main, "iptv_main", None)]
    else:
        return []
    
def mainSetup(session,**kwargs):
    if config.plugins.iptvplayer.configProtectedByPin.value:
        session.openWithCallback(boundFunction(pinCallback, session, runSetup), IPTVPinWidget, title=_("Enter pin")) 
    else:
        runSetup(session)
    
def runSetup(session):
    session.open(ConfigMenu) 
    
def main(session,**kwargs):
    if config.plugins.iptvplayer.pluginProtectedByPin.value:
        session.openWithCallback(boundFunction(pinCallback, session, runMain), IPTVPinWidget, title =_("Enter pin")) 
    else:
        runMain(session)
        
def runMain(session):
    wgetpath     = IsExecutable(config.plugins.iptvplayer.wgetpath.value)
    rtmpdumppath = IsExecutable(config.plugins.iptvplayer.rtmpdumppath.value)
    f4mdumppath  = IsExecutable(config.plugins.iptvplayer.f4mdumppath.value)
    #print "//////////////////////////////////////////////////////////////////////////////////////"
    #print config.plugins.iptvplayer.wgetpath.value
    #print config.plugins.iptvplayer.rtmpdumppath.value
    #print config.plugins.iptvplayer.f4mdumppath.value
    platform     = config.plugins.iptvplayer.plarform.value
    if platform in ["auto", "unknown"] or not wgetpath or not rtmpdumppath or not f4mdumppath:
        session.openWithCallback(boundFunction(doRunMain, session), IPTVSetupMainWidget)
    elif IPTVPlayerNeedInit():
        session.openWithCallback(boundFunction(doRunMain, session), IPTVSetupMainWidget, True)
    else:
        doRunMain(session)
        
def doRunMain(session):
    session.open(IPTVPlayerWidget)
        
def pinCallback(session, callbackFun, pin=None):
    if None == pin: return
    if pin != config.plugins.iptvplayer.pin.value:
        session.open(MessageBox, _("Pin incorrect!"), type = MessageBox.TYPE_INFO, timeout = 5)
        return
    callbackFun(session)
    
    