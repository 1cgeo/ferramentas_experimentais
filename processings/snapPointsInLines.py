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

class SnapPointsInLines(QgsProcessingAlgorithm): 

    INPUT_POINTS = 'INPUT_POINTS'
    INPUT_MIN_DIST= 'INPUT_MIN_DIST'
    INPUT_LINES = 'INPUT_LINES'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_POINTS,
                self.tr('Selecionar pontos'),
                QgsProcessing.TypeVectorPoint
            )
        )
        
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LINES,
                self.tr('Selecionar linhas'),
                QgsProcessing.TypeVectorLine
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
        pointList = self.parameterAsLayerList(parameters, self.INPUT_POINTS, context)
        lineList = self.parameterAsLayerList(parameters, self.INPUT_LINES, context)
        snapDistance = self.parameterAsDouble(parameters, self.INPUT_MIN_DIST, context)
        
        listSize = len(pointList)
        progressStep = 100/listSize if listSize else 0
        step = 0
        
        for pointLayer in pointList:
            for pointFeature in pointLayer.getFeatures():
                pointGeometry = pointFeature.geometry()
                point = pointGeometry.asMultiPoint()[0]
                request = QgsFeatureRequest().setFilterRect( pointGeometry.buffer(snapDistance, 5).boundingBox() )

                hasVertexTarget = None
                currentVertexOrSegment = None 
                currentMinDistance = None 

                for lineLayer in lineList:
                    hasVertex, vertexOrSegment, minDistance = self.foundTarget(
                        point, 
                        lineLayer.getFeatures( request ), 
                        snapDistance
                    )

                    if not vertexOrSegment:
                        continue

                    if hasVertexTarget and not hasVertex:
                        continue

                    if currentMinDistance and minDistance > currentMinDistance:
                        continue

                    hasVertexTarget = hasVertex
                    currentVertexOrSegment = vertexOrSegment 
                    currentMinDistance = minDistance 

                self.snapPoint(
                    point,
                    pointFeature,
                    pointLayer,
                    lineLayer,
                    hasVertexTarget,
                    currentVertexOrSegment
                )

            feedback.setProgress( step * progressStep )
        return {self.OUTPUT: ''}

    def foundTarget(self, point, otherFeatures, distance):
        hasVertex = False
        minVertexDistance = None
        currentVertex = None

        minSegmentDistance = None
        segment = None
        foundFeature = None
        
        otherFeatureList = list(otherFeatures)
        for otherFeature in otherFeatureList:
            vertex, vertexId, vertexDistance = self.closestVertex(point, otherFeature, distance)
            if vertex and not hasVertex:
                hasVertex = True
                minVertexDistance = vertexDistance
                currentVertex = vertex
                foundFeature = otherFeature
                continue
            if vertex and hasVertex and minVertexDistance <= vertexDistance:
                continue
            if vertex and hasVertex and minVertexDistance > vertexDistance:
                minVertexDistance = vertexDistance
                currentVertex = vertex
                foundFeature = otherFeature
                continue
            
            foundSegment, segmentDistance = self.closestSegment(point, otherFeature, distance)
            if foundSegment and not segment:
                minSegmentDistance = segmentDistance
                segment = otherFeature
                foundFeature = otherFeature
            if foundSegment and segment and minSegmentDistance > segmentDistance:
                minSegmentDistance = segmentDistance
                segment = otherFeature
                foundFeature = otherFeature
        return hasVertex, currentVertex if hasVertex else segment, minVertexDistance if hasVertex else minSegmentDistance

    def closestVertex(self, point, otherFeature, distance):
        otherLinestring = core.QgsLineString( otherFeature.geometry().vertices() )
        vertex, vertexId = core.QgsGeometryUtils.closestVertex(otherLinestring, core.QgsPoint(point.x(), point.y()))
        if vertex.isEmpty():
            return None, None
        vertexDistance = core.QgsGeometry.fromPointXY(point).distance(core.QgsGeometry.fromPointXY(QgsPointXY(vertex)))
        if vertexDistance > distance:
            return None, None, None
        return vertex, vertexId, vertexDistance

    def closestSegment(self, point, otherFeature, distance):
        segmentDistance = math.sqrt( otherFeature.geometry().closestSegmentWithContext(point)[0] )
        return segmentDistance < distance , segmentDistance

    def snapPoint(self, point, currentFeature, currentLayer, otherLayer, hasVertex, vertexOrSegment):
        if hasVertex:
            projectedPoint = vertexOrSegment
        else:
            otherGeometry = vertexOrSegment.geometry() 
            projectedPoint = core.QgsGeometryUtils.closestPoint( 
                otherGeometry.constGet(), 
                core.QgsPoint( point.x(), point.y() ) 
            )
            distance, p, after, orient = otherGeometry.closestSegmentWithContext( QgsPointXY( projectedPoint ) )
            otherGeometry.insertVertex( projectedPoint, after )
            self.updateLayerFeature( otherLayer, vertexOrSegment, otherGeometry )
        
        currentGeometry = currentFeature.geometry()
        currentGeometry.moveVertex(projectedPoint, 0)
        self.updateLayerFeature(currentLayer, currentFeature, currentGeometry)

    def updateLayerFeature(self, layer, feature, geometry):
        feature.setGeometry(geometry)
        layer.startEditing()
        layer.updateFeature(feature)

   
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return SnapPointsInLines()

    def name(self):
        return 'snappointsinlines'

    def displayName(self):
        return self.tr('Conectar pontos nas linhas')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo ...")
    
