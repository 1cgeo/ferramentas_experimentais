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
from .spatialFilter import SpatialFilter
from .defaultFields import setDefaultFields, restoreFields
from .filters import filterSelections, cleanAllFilters, filterBySelectedGeometries
from .labelTool import HydroLabelTool, HighwayLabelTool
from .copy_to_temp_layer.copyToTempLayer import copyToTempLayer
from .processings.provider import Provider

class InitPlugin:

    def __init__(self, iface):
        self.iface = iface
        self.cortaWidget = CortaTool( callback=cortaFundoVale )
        self.spatialFilterTool = SpatialFilter()
        self.hydroLabelTool = HydroLabelTool()
        self.highwayLabelTool = HighwayLabelTool()
        self.provider = None
        self.toolBar = None
        self.toolBar2 = None

    def initGui(self):
        self.toolBar = self.iface.addToolBar('Ferramentas_Experimentais')
        self.toolBar2 = self.iface.addToolBar('Ferramentas_Experimentais_2')

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

        self.actioncopyToTempLayer = self.createAction(
            "Copia Feições Para Camada Temporária", 
            "tempLayer.png", 
            copyToTempLayer, 
            "Copia Feições Selecionadas Para Camada Temporária",
            "Copia Feições Selecionadas Para Camada Temporária"
        )
        self.toolBar.addAction(self.actioncopyToTempLayer)

        self.actionaSpatialFilter = self.createAction(
            "Filtro espacial", 
            "spatialFilter.png", 
            self.spatialFilterTool.start, 
            "Filtra o espaco de aquisição",
            "Filtro espacial"
        )
        self.toolBar.addAction(self.actionaSpatialFilter)

        self.setDefaultFields = self.createAction(
            "Criar mais como esse", 
            "setDefaultFields.png", 
            setDefaultFields, 
            "Criar mais como esse",
            "Criar mais como esse"
        )
        self.toolBar.addAction(self.setDefaultFields)

        self.restoreFields = self.createAction(
            "Restaurar camada", 
            "restoreFields.png", 
            restoreFields, 
            "Restaurar camada",
            "Restaurar camada"
        )
        self.toolBar.addAction(self.restoreFields)

        self.filterSelections = self.createAction(
            "Filtra selecionados", 
            "filter.svg", 
            filterSelections, 
            "Filtra selecionados",
            "Filtra selecionados"
        )
        self.toolBar.addAction(self.filterSelections)

        self.filterBySelectedGeometries = self.createAction(
            "Filtra Todos por geometria de selecionadas", 
            "filterByGeomtries.png", 
            filterBySelectedGeometries, 
            "",
            ""
        )
        self.toolBar.addAction(self.filterBySelectedGeometries)

        self.removeSpatialFilter = self.createAction(
            "Remove filtros", 
            "removeSpatialFilter.png", 
            cleanAllFilters, 
            "",
            ""
        )
        self.toolBar.addAction(self.removeSpatialFilter)
        

        self.toolBar2.addWidget( self.hydroLabelTool )

        self.toolBar2.addWidget( self.highwayLabelTool )
        # Addprovider
        PluginAlg.initProcessing(self)

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
        self.iface.mainWindow().removeToolBar(self.toolBar)
        self.iface.mainWindow().removeToolBar(self.toolBar2)

    def createAction(self, text, icon, callback, whatisthis, tip):
        if icon:
            iconPath = self.getPluginIconPath(icon)
            action = QAction(
                QIcon(iconPath),
                text,
                self.iface.mainWindow()
            )
        else:
            action = QAction(
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