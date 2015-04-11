# -*- coding: utf-8 -*-
#
#  Konfigurator dla iptv 2013
#  autorzy: j00zek, samsamsam
#


###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc
from Plugins.Extensions.IPTVPlayer.components.iptvdirbrowser import IPTVDirectorySelectorWidget
###################################################

###################################################
# FOREIGN import
###################################################
from enigma import getDesktop

from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard

from Components.ActionMap import ActionMap, HelpableActionMap
from Components.Label import Label
from Components.config import config, ConfigDirectory, ConfigText, ConfigPassword, ConfigBoolean, ConfigSelection, configfile
from Components.ConfigList import ConfigListScreen
from Tools.BoundFunction import boundFunction
###################################################


class ConfigBaseWidget(Screen, ConfigListScreen):
    screenwidth = getDesktop(0).size().width()
    if screenwidth and screenwidth == 1920:
        skin = """
            <screen name="IPTVConfigBaseWidget" position="center,center" size="920,860" title="" >
                <widget name="config"    position="10,70" size="900,780" zPosition="1" transparent="1" scrollbarMode="showOnDemand" />
                <widget name="key_red"   position="10,10" zPosition="2" size="600,35" valign="center" halign="left"   font="Regular;28" transparent="1" foregroundColor="red" />
                <widget name="key_ok"    position="10,10" zPosition="2" size="600,35" valign="center" halign="center" font="Regular;28" transparent="1" foregroundColor="white" />
                <widget name="key_green" position="10,10" zPosition="2" size="600,35" valign="center" halign="right"  font="Regular;28" transparent="1" foregroundColor="green" />
                <widget name="key_blue"    position="0,0" zPosition="2" size="600,35" valign="center" halign="right"  font="Regular;28" transparent="1" foregroundColor="green" />
                <widget name="key_yellow"  position="0,0" zPosition="2" size="600,35" valign="center" halign="right"  font="Regular;28" transparent="1" foregroundColor="green" />
            </screen>"""
    else:
        skin = """
            <screen name="IPTVConfigBaseWidget" position="center,center" size="620,440" title="" >
                <widget name="config"    position="10,50" size="600,370" zPosition="1" transparent="1" scrollbarMode="showOnDemand" />
                <widget name="key_red"   position="10,10" zPosition="2" size="600,35" valign="center" halign="left"   font="Regular;22" transparent="1" foregroundColor="red" />
                <widget name="key_ok"    position="10,10" zPosition="2" size="600,35" valign="center" halign="center" font="Regular;22" transparent="1" foregroundColor="white" />
                <widget name="key_green" position="10,10" zPosition="2" size="600,35" valign="center" halign="right"  font="Regular;22" transparent="1" foregroundColor="green" />
                
                <widget name="key_blue"    position="0,0" zPosition="2" size="600,35" valign="center" halign="right"  font="Regular;22" transparent="1" foregroundColor="green" />
                <widget name="key_yellow"  position="0,0" zPosition="2" size="600,35" valign="center" halign="right"  font="Regular;22" transparent="1" foregroundColor="green" />
            </screen>"""      
    def __init__(self, session):
        printDBG("ConfigBaseWidget.__init__ -------------------------------")
        Screen.__init__(self, session)
        
        self.onChangedEntry = [ ]
        self.list = [ ]
        ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changedEntry)
        self.setup_title = "IPTV Player - ustawienia"

        self["key_green"] = Label(_("Save"))
        self["key_ok"] = Label(_(" "))
        self["key_red"] = Label(_("Cancel"))
        
        self["key_blue"] = Label()
        self["key_yellow"] = Label()
        self["key_blue"].hide()
        self["key_yellow"].hide()
        
        self["actions"] = ActionMap(["SetupActions", "ColorActions", "WizardActions", "ListboxActions", "IPTVPlayerListActions"],
            {
                "cancel": self.keyExit,
                "green" : self.keySave,
                "ok"    : self.keyOK,
                "red"   : self.keyCancel,
                "yellow": self.keyYellow,
                "blue"  : self.keyBlue,
                "menu"  : self.keyMenu,
                
                "up"      : self.keyUp,
                "down"    : self.keyDown,
                "moveUp"  : self.keyUp,
                "moveDown": self.keyDown,
                "moveTop" : self.keyHome,
                "moveEnd" : self.keyEnd,
                "home"    : self.keyHome,
                "end"     : self.keyEnd,
                "pageUp"  : self.keyPageUp,
                "pageDown": self.keyPageDown
            }, -2)

        self.onLayoutFinish.append(self.layoutFinished)
        self.onClose.append(self.__onClose)
        self.isOkEnabled = False
        self.hiddenOptionsSecretCode = ""

    def __del__(self):
        printDBG("ConfigBaseWidget.__del__ -------------------------------")

    def __onClose(self):
        printDBG("ConfigBaseWidget.__onClose -----------------------------")
        self.onClose.remove(self.__onClose)
        self.onLayoutFinish.remove(self.layoutFinished)
        if self.onSelectionChanged in self["config"].onSelectionChanged:
            self["config"].onSelectionChanged.remove(self.onSelectionChanged)

    def layoutFinished(self):
        self.setTitle("IPTV Player - ustawienia")
        if not self.onSelectionChanged in self["config"].onSelectionChanged:
            self["config"].onSelectionChanged.append(self.onSelectionChanged)
        self.runSetup()

    def onSelectionChanged(self):
        self.isOkEnabled = self.isOkActive()              
        self.isSelectable = self.isSelectableActive()
        self.setOKLabel()
        
    def isHiddenOptionsUnlocked(self):
        if "ybybyybb" == self.hiddenOptionsSecretCode:
            return True
        else:
            return False

    def setOKLabel(self):
        if self.isSelectable:
            labelText = "<  %s  >"
        else:
            labelText = "   %s   "
        if self.isOkEnabled:
            labelText = labelText % "OK"
        else:
            labelText = labelText % "  "
        self["key_ok"].setText(_(labelText))
        
    def isOkActive(self):
        if self["config"].getCurrent() is not None:
            currItem = self["config"].getCurrent()[1]
            if isinstance(currItem, ConfigText) or isinstance(currItem, ConfigPassword):
                return True
        return False
        
    def isSelectableActive(self):
        if self["config"].getCurrent() is not None:
            currItem = self["config"].getCurrent()[1]
            if currItem and isinstance(currItem, ConfigSelection) or isinstance(currItem, ConfigBoolean):
                return True
        return False

    def runSetup(self):
        self["config"].list = self.list
        self["config"].setList(self.list)
        
    def isChanged(self):
        bChanged = False
        for x in self["config"].list:
            if x[1].isChanged():
                bChanged = True
                break
        printDBG("ConfigMenu.isChanged bChanged[%r]" % bChanged)
        return bChanged
        
    def askForSave(self, callbackYesFun, callBackNoFun):
        self.session.openWithCallback(boundFunction(self.saveOrCancelChanges, callbackYesFun, callBackNoFun), MessageBox, text = _("Save changes?"), type = MessageBox.TYPE_YESNO)
        return
        
    def saveOrCancelChanges(self, callbackFun=None, failCallBackFun=None, answer=None):
        if answer:
            self.save()
            if callbackFun: callbackFun()
        else:
            self.cancel()
            if failCallBackFun: failCallBackFun()

    def keySave(self):
        self.save()
        self.close()
        
    def saveOrCancel(self, operation="save"):
        for x in self["config"].list:
            if "save" == operation:
                x[1].save()
            else:
                x[1].cancel()  
        if "save" == operation:
            configfile.save()
    
    def save(self):
        self.saveOrCancel("save")
            
    def cancel(self):
        self.saveOrCancel("cancel")
        self.runSetup()
        
    def saveAndClose(self):
        self.save()
        self.close()
        
    def cancelAndClose(self):
        self.cancel()
        self.close()
      
    def keyOK(self):
        if not self.isOkEnabled: 
            return

        curIndex = self["config"].getCurrentIndex()
        currItem = self["config"].list[curIndex][1]
        if isinstance(currItem, ConfigDirectory):
            def SetDirPathCallBack(curIndex, newPath):
                if None != newPath: self["config"].list[curIndex][1].value = newPath
            self.session.openWithCallback(boundFunction(SetDirPathCallBack, curIndex), IPTVDirectorySelectorWidget, currDir=currItem.value, title="Wybierz katalog")
            return
        elif isinstance(currItem, ConfigText):
            def VirtualKeyBoardCallBack(curIndex, newTxt):
                if isinstance(newTxt, basestring): self["config"].list[curIndex][1].value = newTxt
            self.session.openWithCallback(boundFunction(VirtualKeyBoardCallBack, curIndex), VirtualKeyBoard, title=(_("Wprowadź wartość")), text=currItem.value)
            return

        ConfigListScreen.keyOK(self)

    def keyExit(self):
        if self.isChanged():
            self.askForSave(self.saveAndClose, self.cancelAndClose)
        else:
            self.close()
        
    def keyCancel(self):
        self.cancelAndClose()
        
    def keyYellow(self):
        self.hiddenOptionsSecretCode += "y"
        self.runSetup()

    def keyBlue(self):
        self.hiddenOptionsSecretCode += "b"
        self.runSetup()
        
    def keyMenu(self):
        pass
        
    def keyUp(self):
        if self["config"].instance is not None:
            self["config"].instance.moveSelection(self["config"].instance.moveUp)
        
    def keyDown(self):
        if self["config"].instance is not None:
            self["config"].instance.moveSelection(self["config"].instance.moveDown)
            
    def keyPageUp(self):
        pass
    
    def keyPageDown(self):
        pass
        
    def keyHome(self):
        pass
    
    def keyEnd(self):
        pass
    
    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        
    def keyRight(self):
        ConfigListScreen.keyRight(self)

    def getSubOptionsList(self):
        tab = []
        return tab
        
    def changeSubOptions(self):
        if self["config"].getCurrent()[1] in self.getSubOptionsList():
            self.runSetup()       

    def changedEntry(self):
        self.changeSubOptions()
        for x in self.onChangedEntry: x() 

