# -*- coding: utf-8 -*-
import os
from PyQt5.QtWidgets import QAction, QMenu
from PyQt5.QtGui import QIcon
from qgis.core import QgsApplication

from .processings.plugin_alg import PluginAlg
from .calcula_azimute.calcazimute import calazim
from .copia_wkt.copiarwkt import copywkt
from .copia_cola_geom.copia_cola_geom import startCopyButton, startPasteButton
from .corta_fundo_vale.corta_fundo_vale import cortaFundoVale
from .corta_fundo_vale.widgets.corta_tool import CortaTool

from .processings.provider import Provider
from . import resources

class InitPlugin:

    def __init__(self, iface):
        self.iface = iface
        self.cortaWidget = CortaTool( callback=cortaFundoVale )
        self.provider = None
        self.toolBar = None

    def initGui(self):
        self.toolBar = self.iface.addToolBar('Ferramentas_Experimentais')
        
        self.toolBar.addWidget(self.cortaWidget)

        self.actionazm = self.createAction(
            "Calcula Azimute", 
            "azim.png", 
            calazim, 
            "Calcula o angulo, no sentido horário, entre o norte e a direção da feicao(ombb)",
            "Calcula azimute"
        )
        self.toolBar.addAction(self.actionazm)

        self.actionwkt = self.createAction(
            "Copia WKT", 
            "copywkt.png", 
            copywkt, 
            "Copia as coordenadas das feições selecionadas em WKT",
            "Copiar em WKT"
        )
        self.toolBar.addAction(self.actionwkt)

        self.actioncolageom = self.createAction(
            "Copiar Geometria", 
            "copygeom.png", 
            startCopyButton, 
            "Copia a geometria",
            "Copia geometria"
        )
        self.toolBar.addAction(self.actioncolageom)

        self.actioncopiageom = self.createAction(
            "Colar Geometria", 
            "pastegeom.png", 
            startPasteButton, 
            "Cola a geometria",
            "Cola a geometria"
        )
        self.toolBar.addAction(self.actioncopiageom)
        
        # Addprovider
        PluginAlg.initProcessing(self)

    def initSignals(self):
        pass

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
        self.iface.mainWindow().removeToolBar(self.toolBar)


    def createAction(self, text, icon, callback, whatisthis, tip):
        iconPath = self.getPluginIconPath(icon)
        action = QAction(
            QIcon(iconPath),
            text,
            self.iface.mainWindow()
        )
        action.triggered.connect(callback)
        action.setWhatsThis(whatisthis)
        action.setStatusTip(tip)
        return action

    def getPluginIconPath(self, name):
        return os.path.join(
            os.path.abspath(os.path.join(
                os.path.dirname(__file__)
            )),
            'icons',
            name
        )