# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import QCoreApplication, QVariant
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

class SnapLineInAnchor(QgsProcessingAlgorithm): 

    INPUT_LINE = 'INPUT_LINE'
    INPUT_ANCHOR = 'INPUT_ANCHOR'
    INPUT_MIN_DIST= 'INPUT_MIN_DIST'
    OUTPUT_P = 'OUTPUT_P'

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LINE,
                self.tr('Selecionar camada linha'),
                [ QgsProcessing.TypeVectorLine ]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_ANCHOR,
                self.tr('Selecionar camada linha ( âncora )'),
                [ QgsProcessing.TypeVectorLine ]
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.INPUT_MIN_DIST,
                self.tr('Insira o valor da distância'), 
                type=QgsProcessingParameterNumber.Double, 
                defaultValue=2
            )
        )

    def processAlgorithm(self, parameters, context, feedback):      
        lineLayer = self.parameterAsVectorLayer(parameters, self.INPUT_LINE, context)
        lineAnchorLayer = self.parameterAsVectorLayer(parameters, self.INPUT_ANCHOR, context)
        snapDistance = self.parameterAsDouble(parameters, self.INPUT_MIN_DIST, context)
        self.snapLineInAnchor( lineLayer, lineAnchorLayer, snapDistance)
        self.snapLineInAnchor( lineAnchorLayer, lineLayer, snapDistance)
        return {self.OUTPUT_P: ''}

    def snapLineInAnchor(self, lineLayer, lineAnchorLayer, snapDistance):
        for lineFeature in lineLayer.getFeatures():
            lineVertices = list(lineFeature.geometry().vertices())
            for linePointIdx, linePoint in enumerate(lineVertices):
                lineGeometry = lineFeature.geometry()
                request = self.getFeatureRequest( QgsGeometry.fromPointXY( QgsPointXY( linePoint ) ) , snapDistance )
                lineAnchorFeatures = lineAnchorLayer.getFeatures( request )
                for lineAnchorFeature in lineAnchorFeatures:
                    vertex, vertexId = self.closestVertex(linePoint, lineAnchorFeature, snapDistance)
                    if vertex:
                        #snap vertex
                        projectedPoint = vertex
                    elif self.closestSegment(linePoint, lineAnchorFeature, snapDistance):
                        #snap segment
                        lineAnchorGeometry = lineAnchorFeature.geometry() 
                        projectedPoint = core.QgsGeometryUtils.closestPoint( 
                            lineAnchorGeometry.constGet().clone(), 
                            core.QgsPoint(linePoint.x(), linePoint.y()) 
                        )
                        distance, p, after, orient = lineAnchorGeometry.closestSegmentWithContext( QgsPointXY( projectedPoint ) )
                        lineAnchorGeometry.insertVertex( projectedPoint, after )
                        self.updateLayerFeature(lineAnchorLayer, lineAnchorFeature, lineAnchorGeometry)
                        
                    else:
                        continue
                    lineGeometry.moveVertex( projectedPoint, linePointIdx )
                    self.updateLayerFeature(lineLayer, lineFeature, lineGeometry)

    def closestVertex(self, point, otherFeature, snapDistance):
        vertex, vertexId = core.QgsGeometryUtils.closestVertex( 
            otherFeature.geometry().constGet().clone(), 
            core.QgsPoint(point.x(), point.y())
        )
        if vertex.isEmpty():
            return None, None
        vertexDistance = core.QgsGeometry.fromPointXY( QgsPointXY(point) ).distance(core.QgsGeometry.fromPointXY(QgsPointXY(vertex)))
        if vertexDistance > snapDistance:
            return None, None
        return vertex, vertexId

    def closestSegment(self, point, otherFeature, snapDistance):
        segmentDistance = math.sqrt( otherFeature.geometry().closestSegmentWithContext(QgsPointXY( point ))[0] )
        return segmentDistance < snapDistance

    def getFeatureRequest(self, geometry, distance, segment=5):
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
        return SnapLineInAnchor()

    def name(self):
        return 'snaplineinanchor'

    def displayName(self):
        return self.tr('Conectar linha em âncora')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo ...")
    
