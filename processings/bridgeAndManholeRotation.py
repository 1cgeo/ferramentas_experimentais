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

class BridgeAndManholeRotation(QgsProcessingAlgorithm): 

    INPUT_LAYER_P = 'INPUT_LAYER_P'
    INPUT_FIELD_LAYER_P = 'INPUT_FIELD_LAYER_P'
    INPUT_HIGHWAY = 'INPUT_HIGHWAY'
    INPUT_MIN_DIST = 'INPUT_MIN_DIST'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER_P,
                self.tr('Selecionar camada de elemento viário'),
                [QgsProcessing.TypeVectorPoint]
            )
        )
        self.addParameter(
            core.QgsProcessingParameterField(
                self.INPUT_FIELD_LAYER_P,
                self.tr('Selecionar o atributo de rotação'), 
                type=core.QgsProcessingParameterField.Any, 
                parentLayerParameterName=self.INPUT_LAYER_P,
                allowMultiple=False
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.INPUT_MIN_DIST,
                self.tr('Tolerância da distância'), 
                type=QgsProcessingParameterNumber.Double, 
                minValue=0.3
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_HIGHWAY,
                self.tr('Selecionar camada de rodovia'),
                [QgsProcessing.TypeVectorLine]
            )
        )

    def processAlgorithm(self, parameters, context, feedback):      
        pointLayer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER_P, context)
        rotationField = self.parameterAsFields(parameters, self.INPUT_FIELD_LAYER_P, context)[0]
        highwayLayer = self.parameterAsVectorLayer(parameters, self.INPUT_HIGHWAY, context)
        distance = self.parameterAsDouble(parameters, self.INPUT_MIN_DIST, context)

        self.setRotationFieldOnLayer( 
            pointLayer, 
            rotationField, 
            highwayLayer, 
            distance,
            [201,202,203,204,501]
        )

        return {self.OUTPUT: ''}

    def setRotationFieldOnLayer(self, layer, rotationField, highwayLayer, distance, filterType):
        for layerFeature in layer.getFeatures():
            if not( layerFeature['tipo'] in filterType ):
                continue
            layerGeometry = layerFeature.geometry()
            request = QgsFeatureRequest().setFilterRect( layerGeometry.boundingBox() ) 
            for highwayFeature in highwayLayer.getFeatures(request):
                highwayFeatureGeometry = highwayFeature.geometry()
                if not( highwayFeatureGeometry.intersects( layerGeometry ) ):
                    continue
                clippedGeometry = highwayFeatureGeometry.clipped( layerGeometry.buffer(distance, 5).boundingBox() )
                if not( clippedGeometry.type() == core.QgsWkbTypes.LineGeometry ):
                    continue

                p1 = layerGeometry.asMultiPoint()[0]
                p2 = self.getPointWithMaxY( list( clippedGeometry.vertices() ) )

                if ( p2.y() - p1.y() ) == 0:
                    angleDegrees = 0
                else:
                    angleRadian = math.atan2( p2.x() - p1.x(), p2.y() - p1.y() ) - math.pi/2
                    if angleRadian >= math.pi:
                        angleRadian -= math.pi
                    elif angleRadian <= -math.pi:
                        angleRadian += math.pi
                    angleDegrees = round( math.degrees( angleRadian ) )
                layerFeature[ rotationField ] = angleDegrees
                self.updateLayerFeature( layer, layerFeature )

    def getPointWithMaxY(self, points):
        pointMaxY = None
        maxY = None
        for point in points:
            if maxY and maxY > point.y():
                continue
            pointMaxY = point
            maxY = point.y()
        return pointMaxY

    def updateLayerFeature(self, layer, feature):
        layer.startEditing()
        layer.updateFeature(feature)
   
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return BridgeAndManholeRotation()

    def name(self):
        return 'bridgeandmanholerotation'

    def displayName(self):
        return self.tr('Definir rotação ponte e bueiro')

    def group(self):
        return self.tr('Edição')

    def groupId(self):
        return 'edicao'

    def shortHelpString(self):
        return self.tr("O algoritmo ...")
    
