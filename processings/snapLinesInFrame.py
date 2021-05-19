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

class SnapLinesInFrame(QgsProcessingAlgorithm): 

    INPUT_LAYERS = 'INPUT_LAYER_LIST'
    INPUT_MIN_DIST= 'INPUT_MIN_DIST'
    INPUT_FRAME = 'INPUT_FRAME'
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
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_FRAME,
                self.tr('Selecionar camada correspondente à moldura'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

    def processAlgorithm(self, parameters, context, feedback):      
        layerList = self.parameterAsLayerList(parameters, self.INPUT_LAYERS, context)
        frameLayer = self.parameterAsVectorLayer(parameters, self.INPUT_FRAME, context)
        minDist = self.parameterAsDouble(parameters, self.INPUT_MIN_DIST, context)
        
        listSize = len(layerList)
        progressStep = 100/listSize if listSize else 0
        step = 0
        frameCrs = frameLayer.crs()
        #feedback.setProgressText('Junta')
        allFramesFeature = next(self.dissolveFrame(frameLayer).getFeatures())
        allFramesGeom = allFramesFeature.geometry()
        for frameFeature in frameLayer.getFeatures():
            FrameArea = frameFeature.geometry().boundingBox()
            request = QgsFeatureRequest().setFilterRect(FrameArea)
            multiPointGeom = core.QgsGeometry.fromMultiPointXY([ core.QgsPointXY( v ) for v in frameFeature.geometry().vertices() ])
            for step, layer in enumerate(layerList):   
                for layerFeature in layer.getFeatures(request):
                    featgeom = layerFeature.geometry()
                    if allFramesGeom.crosses(featgeom):
                        continue
                    for geometry in featgeom.constGet():
                        firstPoint = geometry[0]
                        lastIdx = len(geometry) - 1
                        lastPoint = geometry[lastIdx]
                        if not(multiPointGeom.intersects(core.QgsGeometry.fromPointXY(QgsPointXY(lastPoint)))) and self.isNearestPointOfFrame(lastPoint, frameFeature.geometry(), allFramesGeom, minDist):
                            self.snapPoint(lastPoint, lastIdx, layerFeature, layer, frameFeature, frameLayer, minDist)
                        if not(multiPointGeom.intersects(core.QgsGeometry.fromPointXY(QgsPointXY(firstPoint)))) and self.isNearestPointOfFrame(firstPoint, frameFeature.geometry(), allFramesGeom, minDist):
                            self.snapPoint(firstPoint, 0, layerFeature, layer, frameFeature, frameLayer, minDist)
                        
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

    def isNearestPointOfFrame(self, point, frameGeom, allFramesGeom, distance):
        return (
            frameGeom.closestSegmentWithContext(QgsPointXY(point))[0] < distance ** 2 
            and 
            allFramesGeom.closestSegmentWithContext(QgsPointXY(point))[0] < distance ** 2
        )

    def snapPoint(self, point, idxPoint, layerFeature, layer, frameFeature, frameLayer, distance):
        sourceFrameTransform, destFrameTransform = self.getGeometryTransforms(frameLayer.crs(), 4674)
        sourceLayerTransform, destLayerTransform = self.getGeometryTransforms(layer.crs(), 4674)

        frameGeom = frameFeature.geometry()
        frameLinestring = core.QgsLineString( frameGeom.vertices() )

        vertex, vertexId = core.QgsGeometryUtils.closestVertex(frameLinestring, point)
        
        if not vertex.isEmpty() and core.QgsGeometry.fromPointXY(QgsPointXY(point)).distance(core.QgsGeometry.fromPointXY(QgsPointXY(vertex))) < distance:
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

    def updateLayerFeature(self, layer, feature, geometry):
        feature.setGeometry(geometry)
        layer.startEditing()
        layer.updateFeature(feature)

    def getGeometryTransforms(self, sourceCrs, destCrsId):
        destCrs = core.QgsCoordinateReferenceSystem(destCrsId)
        destTransform = core.QgsCoordinateTransform(sourceCrs, destCrs, core.QgsCoordinateTransformContext())
        sourceTransform = core.QgsCoordinateTransform(destCrs, sourceCrs, core.QgsCoordinateTransformContext())
        return sourceTransform, destTransform
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return SnapLinesInFrame()

    def name(self):
        return 'snaplinesinframe'

    def displayName(self):
        return self.tr('Conectar pontas soltas na moldura')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo identifica se existe alguma ponta solta próxima a moldura e faz a conexão com a moldura criando um vertice em comum")
    
