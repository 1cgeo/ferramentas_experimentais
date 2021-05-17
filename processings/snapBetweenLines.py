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

class SnapBetweenLines(QgsProcessingAlgorithm): 

    INPUT_LAYERS = 'INPUT_LAYER_LIST'
    INPUT_MIN_DIST= 'INPUT_MIN_DIST'
    OUTPUT_P = 'OUTPUT_P'

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

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_P,
                self.tr('Flag overlap de linhas')
            )
        ) 

    def processAlgorithm(self, parameters, context, feedback):      
        layerList = self.parameterAsLayerList(parameters, self.INPUT_LAYERS, context)
        snapDistance = self.parameterAsDouble(parameters, self.INPUT_MIN_DIST, context)

        CRSstr = iface.mapCanvas().mapSettings().destinationCrs().authid()
        CRS = QgsCoordinateReferenceSystem(CRSstr)
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
                    points = [firstPoint, lastPoint]
                    
                    targets = []
                    #Testa se o ponto inicial ou final é ponta solta
                    for idx, currentPoint in enumerate(points):
                        found = True
                        for j in range(i, listSize):
                            sameLayer = i == j
                            request = self.getFeatureRequest( QgsGeometry.fromPointXY( currentPoint ) , currentLayer.crs(), snapDistance )
                            otherLayer = layerList[j]
                            otherFeatures = otherLayer.getFeatures( request )
                            otherFeatureList = list(otherFeatures)
                            if self.touchesOtherLine(
                                    QgsGeometry.fromPointXY( currentPoint ), 
                                    currentFeature,
                                    otherFeatureList,
                                    sameLayer
                                ):
                                found = False
                                break
                        if not found:
                            continue
                        targets.append({ 
                            'currentPoint': currentPoint,
                            'pointIndex': 0 if idx == 0 else lastIdx,
                            'hasSameLayerTarget': False,
                            'hasVertexTarget': None,
                            'vertexOrSegmentTarget': None,
                            'minDistanceTarget': None,
                            'layerTarget': None,
                            'featureTarget': None
                        })
                   
                    for j in range(i, listSize):
                        sameLayer = i == j
                        for idx, target in enumerate(targets):
                            
                            if targets[idx]['hasSameLayerTarget'] and not sameLayer:
                                continue

                            request = self.getFeatureRequest( QgsGeometry.fromPointXY( targets[idx]['currentPoint'] ) , currentLayer.crs(), snapDistance )
                            otherLayer = layerList[j]
                            otherFeatures = otherLayer.getFeatures( request )
                            hasVertex, vertexOrSegment, minDistance, foundFeature = self.foundTarget(
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
                                targets[idx]['featureTarget'] = foundFeature
                                continue

                            targets[idx]['hasVertexTarget'] = hasVertex
                            targets[idx]['vertexOrSegmentTarget'] = vertexOrSegment
                            targets[idx]['minDistanceTarget'] = minDistance
                            targets[idx]['layerTarget'] = otherLayer
                            targets[idx]['hasSameLayerTarget'] = sameLayer
                            targets[idx]['featureTarget'] = foundFeature
                    for idx, target in enumerate(targets):
                        if not targets[idx]['layerTarget']:
                            continue
                        if currentFeature.geometry().crosses( targets[idx]['featureTarget'].geometry() ):
                            flags_p = self.trim(
                                targets[idx]['currentPoint'], 
                                targets[idx]['pointIndex'], 
                                currentFeature, 
                                currentLayer, 
                                targets[idx]['featureTarget'],
                                targets[idx]['layerTarget'], 
                                targets[idx]['hasVertexTarget'], 
                                targets[idx]['vertexOrSegmentTarget'],
                                snapDistance
                            )
                            self.addSink(flags_p, sink_p, fields) if flags_p else ''
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

        return {self.OUTPUT_P: sinkId_p}

    def addSink(self, geom, sink, fields):
        newFeat = QgsFeature(fields)
        newFeat.setGeometry(geom)
        newFeat['erro'] = 'Ponta solta incorreto'
        sink.addFeature(newFeat)

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
        foundFeature = None
        
        otherFeatureList = list(otherFeatures)
        for otherFeature in otherFeatureList:
            if sameLayer and currentFeature.id() == otherFeature.id():
                continue
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
        return hasVertex, currentVertex if hasVertex else segment, minVertexDistance if hasVertex else minSegmentDistance, foundFeature

    def touchesOtherLine(self, point, currentFeature, otherFeatures, sameLayer):
        for otherFeature in otherFeatures:
            if (
                    otherFeature.geometry().intersects(point) 
                    and 
                    ( not sameLayer or ( sameLayer and currentFeature.id() != otherFeature.id() ) )
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
        segmentDistance = math.sqrt( otherFeature.geometry().closestSegmentWithContext(point)[0] )
        return segmentDistance < distance , segmentDistance

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

    def trim(self, point, idxPoint, currentFeature, currentLayer, otherFeature, otherLayer, hasVertex, vertexOrSegment, snapDistance):
        freePoint = QgsGeometry.fromPointXY( core.QgsPointXY( currentFeature.geometry().vertexAt(idxPoint) ) )
        intersections = currentFeature.geometry().intersection( otherFeature.geometry() )
        if intersections.type() != core.QgsWkbTypes.PointGeometry:
            return
        if intersections.isMultipart():
            points = intersections.asGeometryCollection()
        else:
            points = [ intersections ]
        
        selectedPoint = None
        minDistance = None
        for point in points:
            if point.distance( freePoint ) > snapDistance:
                continue
            if not minDistance:
                minDistance = point.distance( freePoint )
                selectedPoint = point
                continue
            if minDistance <= point.distance( freePoint ):
                continue
            minDistance = point.distance( freePoint )
            selectedPoint = point 

        if not selectedPoint:
            return freePoint

        vertex, vertexIdx, _, _, _ = currentFeature.geometry().closestVertex( selectedPoint.asPoint() )
        geom = currentFeature.geometry()
        if idxPoint == 0:
            for idx in reversed(range(0, vertexIdx)):
                geom.deleteVertex(idx)
        else:
            print(currentFeature["pk"], vertexIdx, idxPoint)
            for idx in reversed(range(vertexIdx+1, idxPoint+1)):
                geom.deleteVertex(idx)
        
        self.updateLayerFeature(currentLayer, currentFeature, geom)

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
    
