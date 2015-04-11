# -*- coding: utf-8 -*-
#
#  IPTV download manager List UI
#
#  $Id$
#
# 
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, formatBytes
from Plugins.Extensions.IPTVPlayer.components.iptvlist import IPTVListComponentBase
###################################################

###################################################
# FOREIGN import
###################################################
from enigma import eListboxPythonMultiContent, eListbox, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_VALIGN_CENTER
from Tools.LoadPixmap import LoadPixmap
###################################################

class IPTVUpdateList(IPTVListComponentBase):

    def __init__(self, iconsPaths):
        IPTVListComponentBase.__init__(self)
    
        self.l.setFont(2, gFont("Regular", 20))
        self.l.setFont(1, gFont("Regular", 26))
        self.l.setFont(0, gFont("Regular", 16))
        self.l.setItemHeight(70)
        self.iconsPaths    = iconsPaths
        self.iconsPixList  = [ None for x in self.iconsPaths ]
        self.releaseIcons()

    def onCreate(self):
        for idx in range(len(self.iconsPaths)):
            try:
                self.iconsPixList[idx] = LoadPixmap(cached=False, path=self.iconsPaths[idx])
            except:
                printExc()
        
    def onDestroy(self):
        self.releaseIcons()
        
    def buildEntry(self, item):
        width = self.l.getItemSize().width()
        res = [ None ]
        res.append((eListboxPythonMultiContent.TYPE_TEXT, 70, 3, width-70, 25, 2, RT_HALIGN_LEFT|RT_VALIGN_CENTER, item.get('title', '')))
        res.append((eListboxPythonMultiContent.TYPE_TEXT, 70, 25, width-70, 35, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, item.get('info', '')))
        idx = item.get('icon', None)
        if None != idx and idx < len(self.iconsPixList):
            iconPix = self.iconsPixList[idx]
        else:
            iconPix = None
        res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, 3, 1, 64, 64, iconPix))
        return res
        
    def releaseIcons(self):
        for idx in range(len(self.iconsPixList)):
            self.iconsPixList[idx] = None
            