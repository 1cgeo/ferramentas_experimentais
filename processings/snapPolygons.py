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

class SnapPolygons(QgsProcessingAlgorithm): 

    INPUT_LAYERS_L = 'INPUT_LAYERS_L'
    INPUT_LAYERS_A = 'INPUT_LAYERS_A'
    INPUT_MIN_DIST= 'INPUT_MIN_DIST'
    OUTPUT_P = 'OUTPUT_P'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS_L,
                self.tr('Selecionar camadas linhas:'),
                QgsProcessing.TypeVectorLine
            )
        )
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS_A,
                self.tr('Selecionar camadas áreas:'),
                QgsProcessing.TypeVectorPolygon
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
        layerList_l = self.parameterAsLayerList(parameters, self.INPUT_LAYERS_L, context)
        layerList_a = self.parameterAsLayerList(parameters, self.INPUT_LAYERS_A, context)
        snapDistance = self.parameterAsDouble(parameters, self.INPUT_MIN_DIST, context)

        self.snapPolygons(layerList_a, snapDistance) 
        self.snapLineInPolygons(layerList_l, layerList_a, snapDistance)
        self.snapPolygonInLines(layerList_a, layerList_l, snapDistance)
        
        return {self.OUTPUT_P: ''}

    def snapPolygons(self, polygons, snapDistance):
        for i in range(0, len(polygons)):   
            currentLayer = polygons[i]
            featureIds = [ feat.id() for feat in currentLayer.getFeatures() ]
            for featureId in featureIds:
                currentFeature = currentLayer.getFeature(featureId)
                currentGeometry = currentFeature.geometry()
                currentVertices = list(currentGeometry.vertices())
                for currentPoint in currentVertices:
                    for j in range(i, len(polygons)):
                        request = self.getFeatureRequest( QgsGeometry.fromPointXY( QgsPointXY( currentPoint ) ) , currentLayer.crs(), snapDistance )
                        otherLayer = polygons[j]
                        otherFeatures = otherLayer.getFeatures( request )
                        for otherFeature in otherFeatures:
                            if i == j and currentFeature.id() == otherFeature.id():
                                continue
                            vertexList = self.closestVertexList(currentPoint, otherFeature, snapDistance)
                            otherGeometry = otherFeature.geometry()
                            if vertexList:
                                #snap vertex
                                multiPointGeom = core.QgsGeometry.fromMultiPointXY([ core.QgsPointXY( v ) for v in currentVertices ])
                                change = True
                                for v in vertexList:
                                    if multiPointGeom.intersects( core.QgsGeometry.fromPointXY( QgsPointXY( v ) ) ):
                                        continue
                                    _, vertexAt = otherGeometry.closestVertexWithContext( QgsPointXY( v ) )
                                    if change:
                                        otherGeometry.moveVertex(core.QgsPoint(currentPoint.x(), currentPoint.y()), vertexAt)
                                        change = False
                                        continue
                                    otherGeometry.deleteVertex( vertexAt )
                                self.updateLayerFeature(otherLayer, otherFeature, otherGeometry)
                                continue
                            if not self.closestSegment(currentPoint, otherFeature, snapDistance):
                                continue
                            #snap segment
                            linestring = core.QgsLineString( otherGeometry.vertices() )
                            projectedPoint = core.QgsGeometryUtils.closestPoint( linestring, core.QgsPoint(currentPoint.x(), currentPoint.y()) )
                            distance, p, after, orient = otherGeometry.closestSegmentWithContext( QgsPointXY( projectedPoint ) )
                            otherGeometry.insertVertex( currentPoint, after )
                            self.updateLayerFeature(otherLayer, otherFeature, otherGeometry)

    def snapPolygonInLines(self, polygons, lines, snapDistance):
        for polygonLayer in polygons:   
            for polygonFeature in polygonLayer.getFeatures():
                polygonGeometry = polygonFeature.geometry()
                polygonVertices = list(polygonGeometry.vertices())
                for polygonPoint in polygonVertices:
                    for lineLayer in lines:
                        request = self.getFeatureRequest( QgsGeometry.fromPointXY( QgsPointXY( polygonPoint) ) , polygonLayer.crs(), snapDistance )
                        lineFeatures = lineLayer.getFeatures( request )
                        for lineFeature in lineFeatures:
                            lastPolygonGeometry = polygonLayer.getFeature( polygonFeature.id() ).geometry()
                            lastPolygonVertices = list(lastPolygonGeometry.vertices()) 
                            multiPointPolygonGeom = core.QgsGeometry.fromMultiPointXY([ 
                                core.QgsPointXY( v ) for v in lastPolygonVertices
                            ])
                            vertex, vertexId = self.closestVertex(polygonPoint, lineFeature, snapDistance)
                            if vertex:
                                #snap vertex
                                linePoint = lineFeature.geometry().vertexAt( lineFeature.geometry().vertexNrFromVertexId( vertexId ) )
                                _, vertexAt = lastPolygonGeometry.closestVertexWithContext( QgsPointXY( polygonPoint ) )
                                polygonGeometry.moveVertex(linePoint, vertexAt)
                                self.updateLayerFeature(polygonLayer, polygonFeature, polygonGeometry)
                                continue
                            if not self.closestSegment(linePoint, polygonFeature, snapDistance):
                                continue
                            #snap segment
                            lineGeometry = lineFeature.geometry() 
                            linestring = core.QgsLineString( lineGeometry.vertices() )
                            projectedPoint = core.QgsGeometryUtils.closestPoint( linestring, core.QgsPoint(polygonPoint.x(), polygonPoint.y()) )
                            distance, p, after, orient = lineGeometry.closestSegmentWithContext( QgsPointXY( projectedPoint ) )
                            lineGeometry.insertVertex( projectedPoint, after )
                            self.updateLayerFeature(lineLayer, lineFeature, lineGeometry)
                            _, vertexAt = polygonGeometry.closestVertexWithContext( QgsPointXY( polygonPoint ) )
                            polygonGeometry.moveVertex(projectedPoint, vertexAt)
                            self.updateLayerFeature(polygonLayer, polygonFeature, polygonGeometry)

    def snapLineInPolygons(self, lines, polygons, snapDistance):
        for lineLayer in lines:   
            for lineFeature in lineLayer.getFeatures():
                lineGeometry = lineFeature.geometry()
                multiPointGeom = core.QgsGeometry.fromMultiPointXY([ core.QgsPointXY( v ) for v in lineGeometry.vertices() ])
                lineVertices = lineGeometry.vertices()
                for linePoint in lineVertices:
                    for polygonLayer in polygons:
                        request = self.getFeatureRequest( QgsGeometry.fromPointXY( QgsPointXY( linePoint ) ) , lineLayer.crs(), snapDistance )
                        polygonFeatures = polygonLayer.getFeatures( request )
                        for polygonFeature in polygonFeatures:
                            vertex, vertexId = self.closestVertex(linePoint, polygonFeature, snapDistance)
                            if vertex and not multiPointGeom.intersects( core.QgsGeometry.fromPointXY( QgsPointXY( vertex ) ) ):
                                #snap vertex
                                polygonGeometry = polygonFeature.geometry()
                                polygonGeometry.moveVertex(linePoint, polygonGeometry.vertexNrFromVertexId( vertexId ) )
                                self.updateLayerFeature(polygonLayer, polygonFeature, polygonGeometry)
                                continue
                            if vertex and core.QgsGeometry.fromPointXY( QgsPointXY( linePoint ) ).intersects( core.QgsGeometry.fromPointXY( QgsPointXY( vertex ) ) ):
                                continue
                            if not self.closestSegment(linePoint, polygonFeature, snapDistance):
                                continue
                            #snap segment
                            polygonGeometry = polygonFeature.geometry() 
                            linestring = core.QgsLineString( polygonGeometry.vertices() )
                            projectedPoint = core.QgsGeometryUtils.closestPoint( linestring, core.QgsPoint(linePoint.x(), linePoint.y()) )
                            distance, p, after, orient = polygonGeometry.closestSegmentWithContext( QgsPointXY( projectedPoint ) )
                            polygonGeometry.insertVertex( linePoint, after )
                            self.updateLayerFeature(polygonLayer, polygonFeature, polygonGeometry)

    def closestVertex(self, point, otherFeature, snapDistance):
        otherLinestring = core.QgsLineString( otherFeature.geometry().vertices() )
        vertex, vertexId = core.QgsGeometryUtils.closestVertex(otherLinestring, core.QgsPoint(point.x(), point.y()))
        if vertex.isEmpty():
            return None, None
        vertexDistance = core.QgsGeometry.fromPointXY( QgsPointXY(point) ).distance(core.QgsGeometry.fromPointXY(QgsPointXY(vertex)))
        if vertexDistance > snapDistance:
            return None, None
        return vertex, vertexId

    def closestVertexList(self, point, otherFeature, snapDistance):
        vertices = []
        [ vertices.append(v) for v in otherFeature.geometry().vertices() if not v in vertices]
        otherLinestring = core.QgsLineString( vertices )
        vertexList = []
        while True:
            vertex, vertexId = core.QgsGeometryUtils.closestVertex(otherLinestring, core.QgsPoint(point.x(), point.y()))
            if vertex.isEmpty():
                break
            vertexDistance = core.QgsGeometry.fromPointXY(QgsPointXY( point )).distance(core.QgsGeometry.fromPointXY(QgsPointXY(vertex)))
            if vertexDistance > snapDistance:
                break
            vertexList.append(vertex)
            otherLinestring.deleteVertex(vertexId)
        return vertexList

    def closestSegment(self, point, otherFeature, snapDistance):
        segmentDistance = math.sqrt( otherFeature.geometry().closestSegmentWithContext(QgsPointXY( point ))[0] )
        return segmentDistance < snapDistance

    def getFeatureRequest(self, geometry, crs, distance, segment=5):
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
        return SnapPolygons()

    def name(self):
        return 'snappolygons'

    def displayName(self):
        return self.tr('Conectar áreas e linhas')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo realiza o snap topológico entre áreas, áreas com linhas e linhas com áreas.")
    
