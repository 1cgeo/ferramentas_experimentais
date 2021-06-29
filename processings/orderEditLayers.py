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
                        QgsPointXY,
                        QgsProcessingParameterEnum
                    )
from qgis import processing
from qgis import core, gui
from qgis.utils import iface
import math
import json
from qgis.PyQt.QtXml import QDomDocument

class OrderEditLayers(QgsProcessingAlgorithm): 

    JSON_FILE = 'JSON_FILE'
    STYLENAME = 'STYLENAME'
    MODE = 'MODE'
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
                self.STYLENAME,
                self.tr('Digitar nome do estilo')
            )
        )

        self.modes = [
            self.tr('carta'),
            self.tr('carta_mini'),
        ]

        self.addParameter(
            QgsProcessingParameterEnum(
                self.MODE,
                self.tr('Modo'),
                options=self.modes,
                defaultValue=0
            )
        )

    def processAlgorithm(self, parameters, context, feedback): 
        jsonFilePath = self.parameterAsFile(parameters, self.JSON_FILE, context)
        stylename = self.parameterAsFile(parameters, self.STYLENAME, context)
        mode = self.parameterAsEnum(
            parameters,
            self.MODE,
            context
        )
        jsonConfigData = self.getJSONConfig( jsonFilePath )
        iface.mapCanvas().freeze(True)
        groupName = self.modes[ mode ]
        self.order( [ i['tabela'] for i in jsonConfigData[ groupName ] ], stylename, context)   
        iface.mapCanvas().freeze(False) 
        return {self.OUTPUT: ''}

    def order(self, layerNames, styleName, context):
        project = core.QgsProject.instance()
        layers = project.mapLayers().values()
        order = []
        for layer in layers:
            layerName = layer.dataProvider().uri().table()
            
            if not( layerName in layerNames ):
                project.removeMapLayer( layer.id() )
                continue
            loaded = self.loadStyle( layer, styleName )
            if not loaded:
                project.removeMapLayer( layer.id() )
                continue    
            order.insert( 
                layerNames.index( layerName ), 
                layer
            )
        project.layerTreeRoot().setHasCustomLayerOrder(True)
        project.layerTreeRoot().setCustomLayerOrder( order )

    def getJSONConfig(self, jsonFilePath):
        with open(jsonFilePath, 'r') as f:
            return json.load( f )

    def loadStyle(self, layer, styleName):
        loaded = False
        for stylename, styleid in self.getLayerStyles( layer ):
            if not( stylename == styleName ):
                continue
            qml = layer.getStyleFromDatabase( styleid )[0]
            doc = QDomDocument()
            doc.setContent( qml )
            layer.importNamedStyle( doc )
            #layer.triggerRepaint()
            loaded =  True
        return loaded

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
    
