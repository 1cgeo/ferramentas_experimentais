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

class SnapPointsInLinesIntersection(QgsProcessingAlgorithm): 

    INPUT_POINT = 'INPUT_POINT'
    INPUT_MIN_DIST= 'INPUT_MIN_DIST'
    INPUT_LINE_1 = 'INPUT_LINE_1'
    INPUT_LINE_2 = 'INPUT_LINE_2'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_POINT,
                self.tr('Selecionar ponto'),
                [QgsProcessing.TypeVectorPoint]
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LINE_1,
                self.tr('Selecionar primeira linha'),
                [QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LINE_2,
                self.tr('Selecionar segunda linha'),
                [QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.INPUT_MIN_DIST,
                self.tr('Insira o valor da distância'), 
                type=QgsProcessingParameterNumber.Double, 
                minValue=0)
            )

    def processAlgorithm(self, parameters, context, feedback):      
        pointLayer = self.parameterAsVectorLayer(parameters, self.INPUT_POINT, context)
        lineLayer1 = self.parameterAsVectorLayer(parameters, self.INPUT_LINE_1, context)
        lineLayer2 = self.parameterAsVectorLayer(parameters, self.INPUT_LINE_2, context)
        snapDistance = self.parameterAsDouble(parameters, self.INPUT_MIN_DIST, context)
        
        listSize = pointLayer.featureCount()
        progressStep = 100/listSize if listSize else 0
        step = 0
        
        for pointFeature in pointLayer.getFeatures():
            pointGeometry = pointFeature.geometry()
            point = pointGeometry.asMultiPoint()[0]
            request = QgsFeatureRequest().setFilterRect( pointGeometry.buffer(snapDistance, 5).boundingBox() )

            lineFeatures1 = lineLayer1.getFeatures( request )
            lineFeatures2 = lineLayer2.getFeatures( request )

            currentLineFeature1 = None
            currentLineFeature2 = None
            currentMinDistance = None
            currentIntersectionPoint = None

            for lineFeature1 in lineFeatures1:
                for lineFeature2 in lineFeatures2:
                    intersectionPoints = []
                    intersections = lineFeature1.geometry().intersection( lineFeature2.geometry() )
                    if intersections.type() == core.QgsWkbTypes.PointGeometry:
                        if intersections.isMultipart():
                            intersectionPoints.extend( intersections.asGeometryCollection() )
                        else:
                            intersectionPoints.append( intersections )
                    for intersectionPoint in intersectionPoints:
                        minDistance = pointGeometry.distance( intersectionPoint )
                        if minDistance > snapDistance:
                            continue
                        if currentMinDistance and minDistance > currentMinDistance:
                            continue
                        currentLineFeature1 = lineFeature1
                        currentLineFeature2 = lineFeature2
                        currentMinDistance = minDistance
                        currentIntersectionPoint = intersectionPoint

            if not currentIntersectionPoint:
                continue

            for layer, feature in [ (lineLayer1, currentLineFeature1), (lineLayer2, currentLineFeature2) ]:
                if not self.hasPointOnFeature( intersectionPoint, feature ):
                    self.insertPointOnFeature( layer,  feature, intersectionPoint)

            self.updateLayerFeature(pointLayer, pointFeature, intersectionPoint)

        feedback.setProgress( step * progressStep )
        return {self.OUTPUT: ''}

    
    def hasPointOnFeature(self, pointGeometry, feature):
        point = pointGeometry.asPoint()
        vertex, vertexId = core.QgsGeometryUtils.closestVertex(
            feature.geometry().constGet(), 
            core.QgsPoint( point.x(), point.y() )
        )
        if vertex.isEmpty():
            return False
        return core.QgsGeometry.fromPointXY( QgsPointXY( vertex ) ).equals( pointGeometry )

    def insertPointOnFeature(self, layer, feature, point):
        otherGeometry = feature.geometry() 
        projectedPoint = core.QgsGeometryUtils.closestPoint( 
            otherGeometry.constGet(), 
            core.QgsPoint( point.asPoint().x(), point.asPoint().y() ) 
        )
        distance, p, after, orient = otherGeometry.closestSegmentWithContext( QgsPointXY( projectedPoint ) )
        otherGeometry.insertVertex( projectedPoint, after )
        self.updateLayerFeature( layer, feature, otherGeometry )

    def updateLayerFeature(self, layer, feature, geometry):
        feature.setGeometry(geometry)
        layer.startEditing()
        layer.updateFeature(feature)

   
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return SnapPointsInLinesIntersection()

    def name(self):
        return 'snappointsinlinesintersection'

    def displayName(self):
        return self.tr('Conectar pontos nas intersecções de linhas')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo ...")
    
