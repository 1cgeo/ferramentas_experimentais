# -*- coding: utf-8 -*-
from qgis.core import QgsApplication
from .provider import Provider
from PyQt5.QtWidgets import * 
from PyQt5 import QtCore, QtGui 
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 
from processing.core.ProcessingConfig import ProcessingConfig
from qgis.utils import iface

class PluginAlg(object):

    def __init__(self):
        self.provider = None

    def initProcessing(self):
        self.provider = Provider()
        ProcessingConfig.settingIcons["Ferramentas Experimentais"] = QIcon(':/plugins/Ferramentas_Experimentais/lab.png')
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
