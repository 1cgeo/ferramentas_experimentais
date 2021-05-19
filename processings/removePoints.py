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

class RemovePoints(QgsProcessingAlgorithm): 

    INPUT_LAYERS_P = 'INPUT_LAYERS_P'
    INPUT_LAYERS_L = 'INPUT_LAYERS_L'
    INPUT_LAYERS_A = 'INPUT_LAYERS_A'
    INPUT_FRAME = 'INPUT_FRAME'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS_P,
                self.tr('Selecionar camadas ponto'),
                QgsProcessing.TypeVectorPoint,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS_L,
                self.tr('Selecionar camadas linha'),
                QgsProcessing.TypeVectorLine,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS_A,
                self.tr('Selecionar camadas área'),
                QgsProcessing.TypeVectorPolygon,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_FRAME,
                self.tr('Selecionar camada de pontos'),
                [QgsProcessing.TypeVectorPoint]
            )
        )

    def processAlgorithm(self, parameters, context, feedback):      
        layerPoints = self.parameterAsLayerList(parameters, self.INPUT_LAYERS_P, context)
        layerLines = self.parameterAsLayerList(parameters, self.INPUT_LAYERS_L, context)
        layerPolygons = self.parameterAsLayerList(parameters, self.INPUT_LAYERS_A, context)
        points = self.parameterAsVectorLayer(parameters, self.INPUT_FRAME, context)
        for pointFeature in points.getFeatures():
            for layerList in [ layerPoints, layerLines, layerPolygons]:
                self.deleteAllVerticesInLayers( pointFeature.geometry(), layerList )
        return {self.OUTPUT: ''}

    def deleteAllVerticesInLayers(self, pointGeometry, layers):
        for layer in layers:
            for feature in layer.getFeatures():
                featureGeometry = feature.geometry()
                vertices = list( featureGeometry.vertices() )
                for vertice in vertices:
                    if not pointGeometry.intersects( core.QgsGeometry.fromPointXY( QgsPointXY(vertice) )   ):
                        continue
                    _, vertexAt = featureGeometry.closestVertexWithContext( QgsPointXY( vertice ) )
                    featureGeometry.deleteVertex( vertexAt )
                    self.updateLayerFeature(layer, feature, featureGeometry)

    def updateLayerFeature(self, layer, feature, geometry):
        feature.setGeometry(geometry)
        layer.startEditing()
        layer.updateFeature(feature)
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return RemovePoints()

    def name(self):
        return 'removepoints'

    def displayName(self):
        return self.tr('Remover Pontos')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo remove todos o pontos das camadas, que coincide com a camada de ponto de entrada.")
    
