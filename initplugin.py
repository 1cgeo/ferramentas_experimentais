# -*- coding: utf-8 -*-

import os
import sys
import inspect

from qgis.core import(QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProject,
                       QgsMapLayer,
                       QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsProject,
                       QgsPointXY,
                       QgsAbstractFeatureSource,
                       QgsExpression,
                       QgsVectorLayer,
                       QgsField,
                       QgsExpressionContext,
                       QgsExpressionContextScope,
                       QgsAuxiliaryStorage,
                       QgsPropertyDefinition,
                       QgsFeature,
                       Qgis,
                       QgsWkbTypes,
                       QgsApplication,
                       QgsGeometry
                       )
from PyQt5.QtWidgets import * 
from PyQt5 import QtCore, QtGui 
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 
from qgis.utils import iface
from .processings.plugin_alg import PluginAlg
from .calcula_azimute.calcazimute import AzimButton
from .copia_wkt.copiarwkt import WktButton
from .copia_cola_geometria.copia_cola_geom import CCGButton
from .processings.provider import Provider
from Ferramentas_Experimentais import resources
from processing.core.ProcessingConfig import ProcessingConfig, Setting

class InitPlugin:

    def __init__(self, iface):
        self.iface = iface
        self.provider = None
    def initGui(self):
        #Carregar icones
        #   Calcula Azimute
        self.actionazm = QAction(QIcon(":/plugins/Ferramentas_Experimentais/icons/azim.png"), "Calcula Azimute", self.iface.mainWindow())
        self.actionazm.setWhatsThis("Calcula o angulo, no sentido horário, entre o norte e a direção da feicao(ombb)")
        self.actionazm.setStatusTip("Calcula azimute")
        self.actionazm.triggered.connect(AzimButton.calazim)
        self.iface.addToolBarIcon(self.actionazm)
        #   Copiar Wkt
        self.actionwkt = QAction(QIcon(":/plugins/Ferramentas_Experimentais/icons/copywkt.png"), "CopiaWkt", self.iface.mainWindow())
        self.actionwkt.setWhatsThis(u"Copia as coordenadas das feições selecionadas em WKT")
        self.actionwkt.setStatusTip("Copiar em WKT")
        self.actionwkt.triggered.connect(WktButton.copywkt)
        self.iface.addToolBarIcon(self.actionwkt)
        #   Copiar Colar Geometria
        self.actioncopy = QAction(QIcon(":/plugins/Ferramentas_Experimentais/icons/copygeom.png"), u"Copiar Geometria", self.iface.mainWindow())
        self.actionpaste = QAction(QIcon(":/plugins/Ferramentas_Experimentais/icons/pastegeom.png"), u"Colar Geometria", self.iface.mainWindow())
        
        self.popupMenu = QMenu( self.iface.mainWindow() )
        self.popupMenu.addAction( self.actioncopy )
        self.popupMenu.addAction( self.actionpaste )

        self.actioncopy.triggered.connect( CCGButton.copygeom)
        self.actionpaste.triggered.connect(CCGButton.pastegeom)
        self.toolButton = QToolButton()
        self.toolButton.setMenu( self.popupMenu )
        self.toolButton.setDefaultAction( self.actioncopy )
        self.toolButton.setPopupMode( QToolButton.MenuButtonPopup )
        self.tbaction=self.iface.addToolBarWidget( self.toolButton )
        #Addprovider
        PluginAlg.initProcessing(self)
    def initSignals(self):
        pass
    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
        self.iface.removeToolBarIcon(self.actionazm)
        self.iface.removeToolBarIcon(self.actionwkt)
        self.iface.removeToolBarIcon( self.tbaction )
