# -*- coding: utf-8 -*-
#
#  IPTVMultipleInputBox
#
#  $Id$
#
#

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetIconDir
from Plugins.Extensions.IPTVPlayer.components.cover import Cover3
###################################################

###################################################
# FOREIGN import
###################################################
from enigma import eRCInput, getPrevAsciiCode
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import NumberActionMap
from Components.Label import Label
from Components.Input import Input
from Tools.BoundFunction import boundFunction
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.LoadPixmap import LoadPixmap
from enigma import gRGB
###################################################

class IPTVMultipleInputBox(Screen):
    DEF_INPUT_PARAMS = {'validator':None, 'title':'', 'useable_chars':None, 'label_font':'Regular;23', 'label_size':(550,25), 'input_font':'Regular;20', 'input_size':(550,25), 'input':dict(text="", maxSize = False, visible_width = False, type = Input.TEXT)}
    DEF_PARAMS = {'title':_("Input"), 'list':[]}
    def __init__(self, session, params={}):
        
        # Skin generator
        maxWidth = 0
        pX = 40
        pY = 60
        dY = 10
        skinItems = ''
        self.list = params['list']
        for idx in range(len(self.list)):
            item = self.list[idx]
            self["text_%d"%idx] = Label(item.get('title', ''))
            self["input_%d"%idx] = Input(**item['input'])
            self["border_%d"%idx] = Label("")
            if item.get('useable_chars', None) is not None:
                self["input_%d"%idx].setUseableChars(item['useable_chars'])
            skinItems +=  '<widget name="text_%d" position="%d,%d" size="%d,%d" font="%s" zPosition="2" />' % (idx, 10, pY, item['label_size'][0], item['label_size'][1], item['label_font'])
            pY += dY + item['label_size'][1]
            if item['label_size'][0] > maxWidth: maxWidth = item['label_size'][0]
            skinItems +=  '<widget name="input_%d" position="%d,%d" size="%d,%d" font="%s" zPosition="2" />' % (idx, pX, pY, item['input_size'][0], item['input_size'][1], item['input_font'])
            skinItems +=  '<widget name="border_%d" position="%d,%d" size="%d,%d" font="%s" zPosition="1" transparent="0" backgroundColor="#331F93B9" />' % (idx, pX-5, pY-5, item['input_size'][0]+10, item['input_size'][1]+10, item['input_font'])
            if 0 == idx: 
                self['marker'] = Cover3()
                skinItems +=  '<widget name="marker" zPosition="2" position="10,%d" size="16,16" transparent="1" alphatest="blend" />' % (pY + (item['input_size'][1]-16) / 2)
            skinItems +=  '<widget name="marker_%d" zPosition="1" position="10,%d" size="16,16" transparent="1" alphatest="blend" />' % (idx, pY + (item['input_size'][1]-16) / 2)
            self['marker_%d'%idx] = Cover3()
            pY += dY*2 + item['input_size'][1]
            if item['input_size'][0] > maxWidth: maxWidth = item['input_size'][0]
            
        maxWidth += pX*2
        self.skin = """
        <screen name="IPTVMultipleInputBox" position="center,center" size="%d,%d" title="%s">
            <widget name="key_red"   position="10,10" zPosition="2" size="%d,35" valign="center" halign="left"   font="Regular;22" transparent="1" foregroundColor="red" />
            <widget name="key_ok"    position="10,10" zPosition="2" size="%d,35" valign="center" halign="center" font="Regular;22" transparent="1" foregroundColor="white" />
            <widget name="key_green" position="10,10" zPosition="2" size="%d,35" valign="center" halign="right"  font="Regular;22" transparent="1" foregroundColor="green" />
            %s
        </screen>
        """ % (maxWidth, pY, params.get('title', _("Input")), maxWidth-20, maxWidth-20, maxWidth-20, skinItems)
        
        self["key_green"] = Label(_("Save"))
        self["key_ok"]    = Label(_("OK"))
        self["key_red"]   = Label(_("Cancel"))
    
        Screen.__init__(self, session)
        self.onShown.append(self.onStart)
        
        self["actions"] = NumberActionMap(["ColorActions", "WizardActions", "InputBoxActions", "InputAsciiActions", "KeyboardInputActions"], 
        {
            "gotAsciiCode": self.gotAsciiCode,
            "green" : self.keySave,
            "ok"    : self.keyOK,
            "red"   : self.keyCancel,
            "back"  : self.keyCancel,
            "left"  : self.keyLeft,
            "right" : self.keyRight,
            "up"    : self.keyUp,
            "down"  : self.keyUp,
            "right" : self.keyRight,
            "home"  : self.keyHome,
            "end"   : self.keyEnd,
            "deleteForward" : self.keyDelete,
            "deleteBackward": self.keyBackspace,
            "tab": self.keyTab,
            "toggleOverwrite": self.keyInsert,
            "1": self.keyNumberGlobal,
            "2": self.keyNumberGlobal,
            "3": self.keyNumberGlobal,
            "4": self.keyNumberGlobal,
            "5": self.keyNumberGlobal,
            "6": self.keyNumberGlobal,
            "7": self.keyNumberGlobal,
            "8": self.keyNumberGlobal,
            "9": self.keyNumberGlobal,
            "0": self.keyNumberGlobal
        }, -1)
        
        self.idx   = 0
        self.activeInput = "input_0"
        self.setKeyboardMode()
        self.markerPixmap = [LoadPixmap(GetIconDir('radio_button_on.png')), LoadPixmap(GetIconDir('radio_button_off.png'))]
        
        self.started = False
        
    def onStart(self):
        self.onShown.remove(self.onStart)
        self.loadMarkers()
        self.setMarker()
        self.started = True
        
    def loadMarkers(self):
        try:
            if "marker" in self:
                self["marker"].setPixmap(self.markerPixmap[0])
                for idx in range(len(self.list)):
                    self['marker_%d'%idx].setPixmap(self.markerPixmap[1])
        except: printExc()
        
    def keyUp(self):
        if not self.started: return
        prevIdx = self.idx
        self.idx -= 1
        if self.idx < 0: self.idx = len(self.list) - 1
        self.activeInput = "input_%d" % self.idx
        self.setKeyboardMode()
        self.setMarker(prevIdx)

    def keyDown(self):
        if not self.started: return
        prevIdx = self.idx
        self.idx += 1
        if self.idx >= len(self.list): self.idx = 0
        self.activeInput = "input_%d" % self.idx
        self.setKeyboardMode() 
        self.setMarker(prevIdx)
        
    def setMarker(self, prevIdx=None):
        if "marker" in self:
            x, y = self["marker_%d"%self.idx].getPosition()
            self["marker"].setPosition(x, y)
        try:
            if None != prevIdx: 
                self["border_%d"%prevIdx].hide()
            else:
                for idx in range(len(self.list)):
                    self["border_%d"%idx].hide()
            self["border_%d"%self.idx].show()
        except: printExc()

        
    def setKeyboardMode(self):
        rcinput = eRCInput.getInstance()
        if self[self.activeInput].type == Input.TEXT:
            rcinput.setKeyboardMode(rcinput.kmAscii)
        else:
            rcinput.setKeyboardMode(rcinput.kmNone)

    def gotAsciiCode(self):
        self[self.activeInput].handleAscii(getPrevAsciiCode())

    def keyLeft(self):
        self[self.activeInput].left()

    def keyRight(self):
        self[self.activeInput].right()

    def keyNumberGlobal(self, number):
        self[self.activeInput].number(number)

    def keyDelete(self):
        self[self.activeInput].delete()

    def keySave(self):
        rcinput = eRCInput.getInstance()
        rcinput.setKeyboardMode(rcinput.kmNone)
        
        retList = []
        for idx in range(len(self.list)):
            if None != self.list[idx]['validator']:
                sts,msg = self.list[idx]['validator'](self["input_%d"%idx].getText())
                if not sts: 
                    self.session.open(MessageBox, msg, type=MessageBox.TYPE_ERROR)
                    self.idx = idx
                    self.activeInput = "input_%d"%idx
                    self.setMarker()
                    return
            retList.append(self["input_%d"%idx].getText())
        self.close(retList)
        
    def keyOK(self):
        def VirtualKeyBoardCallBack(newTxt):
            if isinstance(newTxt, basestring): self[self.activeInput].setText( newTxt )
        self.session.openWithCallback(VirtualKeyBoardCallBack, VirtualKeyBoard, title=self["text_%d"%self.idx].getText(), text=self[self.activeInput].getText())

    def keyCancel(self):
        rcinput = eRCInput.getInstance()
        rcinput.setKeyboardMode(rcinput.kmNone)
        self.close(None)

    def keyHome(self):
        self[self.activeInput].home()

    def keyEnd(self):
        self[self.activeInput].end()

    def keyBackspace(self):
        self[self.activeInput].deleteBackward()

    def keyTab(self):
        self[self.activeInput].tab()

    def keyInsert(self):
        self[self.activeInput].toggleOverwrite()
