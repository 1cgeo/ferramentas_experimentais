# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
                        QgsProcessing,
                        QgsFeatureSink,
                        QgsProcessingAlgorithm,
                        QgsProcessingParameterFeatureSink,
                        QgsCoordinateReferenceSystem,
                        QgsProcessingParameterMultipleLayers,
                        QgsFeature,
                        QgsProcessingParameterVectorLayer,
                        QgsFields,
                        QgsFeatureRequest,
                        QgsProcessingParameterNumber,
                        QgsGeometry,
                        QgsPointXY
                    )
from qgis import processing
from qgis import core, gui
from qgis.utils import iface
import math
import json
from qgis.PyQt.QtXml import QDomDocument

class OrderEditLayers(QgsProcessingAlgorithm): 

    JSON_FILE = 'JSON_FILE'
    STYLENAME_MAP = 'STYLENAME_MAP'
    STYLENAME_MINIMAP = 'STYLENAME_MINIMAP'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            core.QgsProcessingParameterFile(
                self.JSON_FILE,
                self.tr('Selecionar o arquivo de configuração:'),
                extension='json'
            )
        )
        self.addParameter(
            core.QgsProcessingParameterString(
                self.STYLENAME_MAP,
                self.tr('Digitar nome do estilo da carta')
            )
        )

        self.addParameter(
            core.QgsProcessingParameterString(
                self.STYLENAME_MINIMAP,
                self.tr('Digite o nome do estilo da carta mini')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):      
        jsonFilePath = self.parameterAsFile(parameters, self.JSON_FILE, context)
        stylenameMap = self.parameterAsFile(parameters, self.STYLENAME_MAP, context)
        stylenameMiniMap = self.parameterAsFile(parameters, self.STYLENAME_MINIMAP, context)
        
        jsonConfigData = self.getJSONConfig( jsonFilePath )

        root = core.QgsProject.instance().layerTreeRoot()
        treeLayers = root.findLayers()

        miniMapGroup = root.addGroup('carta_mini')
        self.order( jsonConfigData['carta_mini'], stylenameMiniMap, miniMapGroup, treeLayers)
        
        mapGroup = root.addGroup('carta')
        self.order( jsonConfigData['carta'], stylenameMap, mapGroup, treeLayers)

        return {self.OUTPUT: ''}

    def order(self, layerNames, styleName, groupLayer, treeLayers):
        for layerName in layerNames:
            layer = self.getLayer(layerName, treeLayers)
            if not layer:
                continue
            self.loadStyle( layer, styleName )
            groupLayer.addLayer( layer )

    def getLayer(self, layerName, treeLayers):
        for treeLayer in treeLayers:
            if not(
                    treeLayer.layer().dataProvider().uri().table() == layerName
                ):
                continue 
            return treeLayer.layer()

    def getJSONConfig(self, jsonFilePath):
        with open(jsonFilePath, 'r') as f:
            return json.load( f )

    def loadStyle(self, layer, styleName):
        for stylename, styleid in self.getLayerStyles( layer ):
            if not( stylename == styleName ):
                continue
            qml = layer.getStyleFromDatabase( styleid )
            doc = QDomDocument()
            doc.setContent( qml )
            layer.importNamedStyle( doc )
            layer.triggerRepaint()

    def getLayerStyles(self, layer):
        stylesData = layer.listStylesInDatabase()
        return zip(stylesData[2][:stylesData[0]], stylesData[1][:stylesData[0]])

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return OrderEditLayers()

    def name(self):
        return 'ordereditlayers'

    def displayName(self):
        return self.tr('Ordenar camadas de edição')

    def group(self):
        return self.tr('Edição')

    def groupId(self):
        return 'edicao'

    def shortHelpString(self):
        return self.tr("O algoritmo ...")
    
