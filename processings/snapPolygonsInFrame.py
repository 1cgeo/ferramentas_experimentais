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

class SnapPolygonsInFrame(QgsProcessingAlgorithm): 

    INPUT_LAYERS = 'INPUT_LAYER_LIST'
    INPUT_MIN_DIST= 'INPUT_MIN_DIST'
    INPUT_FRAME = 'INPUT_FRAME'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS,
                self.tr('Selecionar camadas'),
                QgsProcessing.TypeVectorPolygon
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.INPUT_MIN_DIST,
                self.tr('Insira o valor da distância'), 
                type=QgsProcessingParameterNumber.Double, 
                minValue=2)
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
        snapDistance = self.parameterAsDouble(parameters, self.INPUT_MIN_DIST, context)
        
        listSize = len(layerList)
        progressStep = 100/listSize if listSize else 0
        step = 0
        
        for frameFeature in frameLayer.getFeatures():
            FrameArea = frameFeature.geometry().boundingBox()
            request = QgsFeatureRequest().setFilterRect(FrameArea)
            multiPointGeom = core.QgsGeometry.fromMultiPointXY([ core.QgsPointXY( v ) for v in frameFeature.geometry().vertices() ])
            for step, layer in enumerate(layerList):   
                for layerFeature in layer.getFeatures(request):
                    layerGeometry = layerFeature.geometry()
                    layerVertices = list(layerGeometry.vertices())
                    for vertexAt, vertex in enumerate(layerVertices):
                        if (
                            not( multiPointGeom.intersects(core.QgsGeometry.fromPointXY(QgsPointXY(vertex))) ) 
                            and 
                            self.isNearestPointOfFrame( vertex, frameFeature.geometry(), snapDistance )
                        ):
                            self.snapPoint(vertex, vertexAt, layerFeature, layer, frameFeature, frameLayer, snapDistance)
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

    def isNearestPointOfFrame(self, point, frameGeom, snapDistance):
        return (
            frameGeom.closestSegmentWithContext(QgsPointXY(point))[0] < snapDistance ** 2
        )

    def snapPoint(self, point, vertexAt, layerFeature, layer, frameFeature, frameLayer, snapDistance):
        sourceFrameTransform, destFrameTransform = self.getGeometryTransforms(frameLayer.crs(), 4674)
        sourceLayerTransform, destLayerTransform = self.getGeometryTransforms(layer.crs(), 4674)

        layerGeom = layerFeature.geometry()

        frameGeom = frameFeature.geometry()
        frameLinestring = core.QgsLineString( frameGeom.vertices() )

        vertex, vertexId = core.QgsGeometryUtils.closestVertex(frameLinestring, point)
        
        if not vertex.isEmpty() and core.QgsGeometry.fromPointXY(QgsPointXY(point)).distance(core.QgsGeometry.fromPointXY(QgsPointXY(vertex))) < snapDistance:
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
        
        layerGeom.moveVertex(projectedPointLayer, vertexAt)
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
        return SnapPolygonsInFrame()

    def name(self):
        return 'snappolygonsinframe'

    def displayName(self):
        return self.tr('Conectar áreas na moldura')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo identifica se existe alguma ponta solta próxima a moldura e faz a conexão com a moldura criando um vertice em comum")
    
