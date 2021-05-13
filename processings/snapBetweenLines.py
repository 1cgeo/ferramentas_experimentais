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

class SnapBetweenLines(QgsProcessingAlgorithm): 

    INPUT_LAYERS = 'INPUT_LAYER_LIST'
    INPUT_MIN_DIST= 'INPUT_MIN_DIST'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS,
                self.tr('Selecionar camadas'),
                QgsProcessing.TypeVectorLine
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.INPUT_MIN_DIST,
                self.tr('Insira o valor da distância'), 
                type=QgsProcessingParameterNumber.Double, 
                defaultValue=2)
            )

    def processAlgorithm(self, parameters, context, feedback):      
        layerList = self.parameterAsLayerList(parameters, self.INPUT_LAYERS, context)
        snapDistance = self.parameterAsDouble(parameters, self.INPUT_MIN_DIST, context)
        
        listSize = len(layerList)
        progressStep = 100/listSize if listSize else 0
        step = 0
        for i in range(0, listSize):   
            currentLayer = layerList[i]
            for currentFeature in currentLayer.getFeatures():
                currentGeometry = currentFeature.geometry()
                for currentGeometryPart in currentGeometry.constGet():
                    firstPoint = core.QgsPointXY( currentGeometryPart[0] )

                    lastIdx = len(currentGeometryPart) - 1
                    lastPoint = core.QgsPointXY( currentGeometryPart[lastIdx] )

                    targets = []
                    #Testa se o ponto inicial ou final é ponta solta
                    for idx, currentPoint in enumerate([firstPoint, lastPoint]):
                        found = False
                        for j in range(i, listSize):
                            request = self.getFeatureRequest( QgsGeometry.fromPointXY( currentPoint ) , currentLayer.crs(), snapDistance )
                            otherLayer = layerList[j]
                            otherFeatures = otherLayer.getFeatures( request )
                            otherFeatureList = list(otherFeatures)
                            if not self.touchesOtherLine(
                                    QgsGeometry.fromPointXY( currentPoint ), 
                                    currentFeature,
                                    otherFeatureList,
                                    sameLayer
                                ):
                                found = True
                                break
                        if found:
                            continue
                        targets.append({ 
                            'currentPoint': currentPoint,
                            'pointIndex': 0 if idx == 0 else lastIdx,
                            'hasSameLayerTarget': False,
                            'hasVertexTarget': None,
                            'vertexOrSegmentTarget': None,
                            'minDistanceTarget': None,
                            'layerTarget': None
                        })
                   
                    for j in range(i, listSize):
                        sameLayer = i == j
                        for idx, target in enumerate(targets):
                            
                            if targets[idx]['hasSameLayerTarget'] and not sameLayer:
                                continue

                            request = self.getFeatureRequest( QgsGeometry.fromPointXY( targets[idx]['currentPoint'] ) , currentLayer.crs(), snapDistance )
                            otherLayer = layerList[j]
                            otherFeatures = otherLayer.getFeatures( request )
                            hasVertex, vertexOrSegment, minDistance = self.foundTarget(
                                targets[idx]['currentPoint'], 
                                currentFeature, 
                                otherFeatures, 
                                sameLayer, 
                                snapDistance
                            )
                            if not vertexOrSegment:
                                continue

                            if targets[idx]['hasVertexTarget'] and not hasVertex:
                                continue

                            if targets[idx]['minDistanceTarget'] and minDistance < targets[idx]['minDistanceTarget']:
                                targets[idx]['hasVertexTarget'] = hasVertex
                                targets[idx]['vertexOrSegmentTarget'] = vertexOrSegment
                                targets[idx]['minDistanceTarget'] = minDistance
                                targets[idx]['layerTarget'] = otherLayer
                                targets[idx]['hasSameLayerTarget'] = sameLayer
                                continue

                            targets[idx]['hasVertexTarget'] = hasVertex
                            targets[idx]['vertexOrSegmentTarget'] = vertexOrSegment
                            targets[idx]['minDistanceTarget'] = minDistance
                            targets[idx]['layerTarget'] = otherLayer
                            targets[idx]['hasSameLayerTarget'] = sameLayer
                    for idx, target in enumerate(targets):
                        if not targets[idx]['layerTarget']:
                            continue
                        self.snapPoint(
                            targets[idx]['currentPoint'], 
                            targets[idx]['pointIndex'], 
                            currentFeature, 
                            currentLayer, 
                            targets[idx]['layerTarget'], 
                            targets[idx]['hasVertexTarget'], 
                            targets[idx]['vertexOrSegmentTarget']
                        )
            feedback.setProgress( i * progressStep )

        return {self.OUTPUT: ''}

    def getFeatureRequest(self, geometry, crs, distance, segment=5):
        return QgsFeatureRequest().setFilterRect(
            geometry.buffer(distance, segment).boundingBox()
        )

    def foundTarget(self, point, currentFeature, otherFeatures, sameLayer, distance):
        hasVertex = False
        minVertexDistance = None
        currentVertex = None

        minSegmentDistance = None
        segment = None

        otherFeatureList = list(otherFeatures)
        for otherFeature in otherFeatureList:
            if sameLayer and currentFeature.id() == otherFeature.id():
                continue
            vertex, vertexId, vertexDistance = self.closestVertex(point, otherFeature, distance)
            if vertex and not hasVertex:
                hasVertex = True
                minVertexDistance = vertexDistance
                currentVertex = vertex
                continue
            if vertex and hasVertex and minVertexDistance <= vertexDistance:
                continue
            if vertex and hasVertex and minVertexDistance > vertexDistance:
                minVertexDistance = vertexDistance
                currentVertex = vertex
                continue
            
            foundSegment, segmentDistance = self.closestSegment(point, otherFeature, distance)
            if foundSegment and not segment:
                minSegmentDistance = segmentDistance
                segment = otherFeature
            if foundSegment and segment and minSegmentDistance > segmentDistance:
                minSegmentDistance = segmentDistance
                segment = otherFeature
        return hasVertex, currentVertex if hasVertex else segment, minVertexDistance if hasVertex else minSegmentDistance

    def touchesOtherLine(self, point, currentFeature, otherFeatures, sameLayer):
        for otherFeature in otherFeatures:
            if (
                    otherFeature.geometry().intersects(point) 
                    and 
                    not sameLayer
                ):
                return True
        return False

    def closestVertex(self, point, otherFeature, distance):
        otherLinestring = core.QgsLineString( otherFeature.geometry().vertices() )
        vertex, vertexId = core.QgsGeometryUtils.closestVertex(otherLinestring, core.QgsPoint(point.x(), point.y()))
        vertexDistance = core.QgsGeometry.fromPointXY(point).distance(core.QgsGeometry.fromPointXY(QgsPointXY(vertex)))
        if vertexDistance > distance:
            return None, None, None
        return vertex, vertexId, vertexDistance

    def closestSegment(self, point, otherFeature, distance):
        segmentDistance = otherFeature.geometry().closestSegmentWithContext(point)[0]
        return segmentDistance < distance, segmentDistance

    def snapPoint(self, point, idxPoint, currentFeature, currentLayer, otherLayer, hasVertex, vertexOrSegment):
        if hasVertex:
            projectedPoint = vertexOrSegment
        else:
            otherGeometry = vertexOrSegment.geometry() 
            linestring = core.QgsLineString( otherGeometry.vertices() )
            projectedPoint = core.QgsGeometryUtils.closestPoint( linestring, core.QgsPoint(point.x(), point.y()) )

            distance, p, after, orient = otherGeometry.closestSegmentWithContext( QgsPointXY( projectedPoint ) )
            otherGeometry.insertVertex( projectedPoint, after )
            self.updateLayerFeature(otherLayer, vertexOrSegment, otherGeometry)
        
        currentGeometry = currentFeature.geometry()
        currentGeometry.moveVertex(projectedPoint, idxPoint)
        self.updateLayerFeature(currentLayer, currentFeature, currentGeometry)

    def updateLayerFeature(self, layer, feature, geometry):
        feature.setGeometry(geometry)
        layer.startEditing()
        layer.updateFeature(feature)
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return SnapBetweenLines()

    def name(self):
        return 'snapbetweenlines'

    def displayName(self):
        return self.tr('Conectar pontas soltas entre linhas')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo realiza o snap topológico entre linhas")
    
