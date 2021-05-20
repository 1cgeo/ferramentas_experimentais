# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QCoreApplication, QVariant
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

    INPUT_LAYERS_L = 'INPUT_LAYERS_L'
    INPUT_LAYERS_A = 'INPUT_LAYERS_A'
    INPUT_FRAME = 'INPUT_FRAME'
    OUTPUT_P = 'OUTPUT_P'

    def initAlgorithm(self, config=None):
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

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_P,
                self.tr('Flag')
            )
        ) 

    def processAlgorithm(self, parameters, context, feedback):      
        points = self.parameterAsVectorLayer(parameters, self.INPUT_FRAME, context)
        lines = self.parameterAsLayerList(parameters, self.INPUT_LAYERS_L, context), 
        polygons = self.parameterAsLayerList(parameters, self.INPUT_LAYERS_A, context)
        
        CRS = QgsCoordinateReferenceSystem( iface.mapCanvas().mapSettings().destinationCrs().authid() )
        fields = core.QgsFields()
        fields.append(core.QgsField('erro', QVariant.String))
        (sink_p, sinkId_p) = self.parameterAsSink(
            parameters,
            self.OUTPUT_P,
            context,
            fields,
            core.QgsWkbTypes.MultiPoint,
            CRS
        )

        layerList = list(lines) + list(polygons)
        for pointFeature in points.getFeatures():
            pointGeometry = pointFeature.geometry()
            for layer in layerList:
                if not layer:
                    continue
                for feature in layer.getFeatures( self.getFeatureRequest(pointGeometry) ):
                    featureGeometry = feature.geometry()
                    vertices = list( featureGeometry.vertices() )
                    for idx, vertice in enumerate(vertices):
                        vertexGeom = core.QgsGeometry.fromPointXY( QgsPointXY(vertice) )
                        if not pointGeometry.intersects(  vertexGeom  ):
                            continue
                        featureGeometry.deleteVertex( idx )
                        if not featureGeometry.isValid():
                            self.addSink(vertexGeom, sink_p, fields, layer.name())
                            continue
                        self.updateLayerFeature(layer, feature, featureGeometry)
        return {self.OUTPUT_P: sinkId_p}

    def addSink(self, geom, sink, fields, nameLayer):
        newFeat = QgsFeature(fields)
        newFeat.setGeometry(geom)
        newFeat['erro'] = 'Não foi possível deleta o vértice ( {} )'.format(nameLayer)
        sink.addFeature(newFeat)

    def getFeatureRequest(self, geometry, distance=1, segment=5):
        return QgsFeatureRequest().setFilterRect(
            geometry.buffer(distance, segment).boundingBox()
        )

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
    
