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
                minValue=0)
            )

    def processAlgorithm(self, parameters, context, feedback):      
        layerList = self.parameterAsLayerList(parameters, self.INPUT_LAYERS, context)
        snapDistance = self.parameterAsDouble(parameters, self.INPUT_MIN_DIST, context)
        
        listSize = len(layerList)
        progressStep = 100/listSize if listSize else 0
        step = 0
        for i in range(0, layerList):   
            for currentFeature in layerList[i].getFeatures():
                currentGeometry = currentFeature.geometry()
                for currentGeometryPart in currentGeometry.constGet():
                    firstPoint = core.QgsPointXY( currentGeometryPart[0] )
                    firstRequest = self.getFeatureRequest( QgsGeometry.fromPointXY( firstPoint ) , curretLayer.crs(), snapDistance )

                    lastIdx = len(currentGeometryPart) - 1
                    lastPoint = core.QgsPointXY( currentGeometryPart[lastIdx] )
                    lastRequest = self.getFeatureRequest( QgsGeometry.fromPointXY( lastPoint ) , curretLayer.crs(), snapDistance )

                    hasVertex = False
                    minVertexDistance = None
                    vertex = None

                    minSegmentDistance = None
                    segment = None

                    for j in range(i, layerList):
                        otherFirstFeatures = layerList[j].getFeatures( firstRequest )
                        if not self.touchesOtherLine(
                                QgsGeometry.fromPointXY( firstPoint ), 
                                currentFeature,
                                otherFirstFeatures
                            ):
                            for otherFeature in otherFirstFeatures:
                                pass
                            
                        
                        otherLastFeatures = layerList[j].getFeatures( lastRequest )
                        if not self.touchesOtherLine(
                                QgsGeometry.fromPointXY( lastPoint ), 
                                currentFeature,
                                otherLastFeatures
                            ):
                            pass
                    
        return {self.OUTPUT: ''}

    def getFeatureRequest(self, geometry, crs, distance, segment=5):
        sourceTransform, destTransform = self.getGeometryTransforms(crs, 4674)
        geometry.transform( destFrameTransform )
        return QgsFeatureRequest().setFilterRect(
            geometry.buffer(distance, segment).boundingBox()
        )
    
    def getGeometryTransforms(self, sourceCrs, destCrsId):
        destCrs = core.QgsCoordinateReferenceSystem(destCrsId)
        destTransform = core.QgsCoordinateTransform(sourceCrs, destCrs, core.QgsCoordinateTransformContext())
        sourceTransform = core.QgsCoordinateTransform(destCrs, sourceCrs, core.QgsCoordinateTransformContext())
        return sourceTransform, destTransform
         
    def touchesOtherLine(self, point, currentFeature, otherFeatures):
        for otherFeature in otherFeatures:
            if otherFeature.geometry().intersects(point):
                if str(currentFeature.geometry()) == str(otherFeature.geometry()):
                    continue
                return True
        return False

    def closestVertex(self):
        sourceFrameTransform, destFrameTransform = self.getGeometryTransforms(frameLayer.crs(), 4674)
        sourceLayerTransform, destLayerTransform = self.getGeometryTransforms(layer.crs(), 4674)

        frameGeom = frameFeature.geometry()
        frameLinestring = core.QgsLineString( frameGeom.vertices() )

        vertex, vertexId = core.QgsGeometryUtils.closestVertex(frameLinestring, point)

        if core.QgsGeometry.fromPointXY(QgsPointXY(point)).distance(core.QgsGeometry.fromPointXY(QgsPointXY(vertex))) < distance:
            projectedPointLayer = vertex

    def closestSegment(self):
        return (
            frameGeom.closestSegmentWithContext(QgsPointXY(point))[0] < distance 
            and 
            allFramesGeom.closestSegmentWithContext(QgsPointXY(point))[0] < distance
        )

    def updateLayerFeature(self, layer, feature, geometry):
        feature.setGeometry(geometry)
        layer.startEditing()
        layer.updateFeature(feature)

    ###################

    def snapPoint(self, point, idxPoint, layerFeature, layer, frameFeature, frameLayer, distance):
        sourceFrameTransform, destFrameTransform = self.getGeometryTransforms(frameLayer.crs(), 4674)
        sourceLayerTransform, destLayerTransform = self.getGeometryTransforms(layer.crs(), 4674)

        frameGeom = frameFeature.geometry()
        frameLinestring = core.QgsLineString( frameGeom.vertices() )

        vertex, vertexId = core.QgsGeometryUtils.closestVertex(frameLinestring, point)

        if core.QgsGeometry.fromPointXY(QgsPointXY(point)).distance(core.QgsGeometry.fromPointXY(QgsPointXY(vertex))) < distance:
            projectedPointLayer = vertex
        else:
            frameLinestring.transform( destFrameTransform )
            point.transform( destLayerTransform )
            
            projectedPointFrame = core.QgsGeometryUtils.closestPoint( frameLinestring, point )
            projectedPointLayer = projectedPointFrame.clone()

            projectedPointFrame.transform( sourceFrameTransform )
            projectedPointLayer.transform( sourceLayerTransform )

            
            distance, p, after, orient = frameGeom.closestSegmentWithContext( QgsPointXY( projectedPointFrame ) )
            frameGeom.insertVertex( projectedPointFrame, after )
            self.updateLayerFeature(frameLayer, frameFeature, frameGeom)
        
        layerGeom = layerFeature.geometry()
        layerGeom.moveVertex(projectedPointLayer, idxPoint)
        self.updateLayerFeature(layer, layerFeature, layerGeom)
        
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
        return self.tr("O algoritmo ...")
    
