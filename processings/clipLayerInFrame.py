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

class ClipLayerInFrame(QgsProcessingAlgorithm): 

    INPUT_LINE = 'INPUT_LINE'
    INPUT_POLYGON = 'INPUT_POLYGON'
    INPUT_FRAME = 'INPUT_FRAME'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LINE,
                self.tr('Selecionar camada tipo linha'),
                QgsProcessing.TypeVectorLine,
                optional=True 
            )
        )
        
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_POLYGON,
                self.tr('Selecionar camada tipo área'),
                QgsProcessing.TypeVectorPolygon,
                optional=True 
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_FRAME,
                self.tr('Selecionar camada correspondente à moldura'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )
       
    def processAlgorithm(self, parameters, context, feedback):      
        lineLayers = self.parameterAsLayerList(parameters, self.INPUT_LINE, context)
        lineLayers = lineLayers if lineLayers else []
        polygonLayers = self.parameterAsVectorLayer(parameters, self.INPUT_POLYGON, context)
        polygonLayers = polygonLayers if polygonLayers else []
        frameLayer = self.parameterAsVectorLayer(parameters, self.INPUT_FRAME, context)
        listSize = len(lineLayers) + len(polygonLayers)
        progressStep = 100/listSize if listSize else 0
        step = 0
        dissolveFrameLayer = self.dissolveFrame(frameLayer)
        for step, layer in enumerate(lineLayers): 
            clipLayer = self.clipLayer(layer, dissolveFrameLayer)
            for feature in clipLayer.getFeatures():
                self.updateLayerFeature(layer, feature)
            feedback.setProgress( step * progressStep )
        for step, layer in enumerate(polygonLayers): 
            clipLayer = self.clipLayer(layer, dissolveFrameLayer)
            for feature in clipLayer.getFeatures():
                self.updateLayerFeature(layer, feature)
            feedback.setProgress( step * progressStep )
        return {self.OUTPUT: ''}

    def dissolveFrame(self, layer):
        r = processing.run(
            'native:dissolve',
            {   'FIELD' : [], 
                'INPUT' : core.QgsProcessingFeatureSourceDefinition(
                    layer.source()
                ), 
                'OUTPUT' : 'TEMPORARY_OUTPUT'
            }
        )
        return r['OUTPUT']

    def clipLayer(self, layer, frame):
        r = processing.run(
            'native:clip',
            {   'FIELD' : [], 
                'INPUT' : core.QgsProcessingFeatureSourceDefinition(
                    layer.source()
                ), 
                'OVERLAY' : frame,
                'OUTPUT' : 'TEMPORARY_OUTPUT'
            }
        )
        return r['OUTPUT']

    def updateLayerFeature(self, layer, feature):
        layer.startEditing()
        idIdx = layer.primaryKeyAttributes()[0]
        featureOrigin = layer.getFeature( feature[idIdx] )
        featureOrigin.setGeometry( feature.geometry() )
        layer.updateFeature( featureOrigin )
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ClipLayerInFrame()

    def name(self):
        return 'cliplayerinframe'

    def displayName(self):
        return self.tr('Corta feições na moldura')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo clipa as camadas na moldura e atualiza as feições.")
    
