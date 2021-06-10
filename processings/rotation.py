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

class Rotation(QgsProcessingAlgorithm): 

    INPUT_POINTS = 'INPUT_POINTS'
    INPUT_MIN_DIST= 'INPUT_MIN_DIST'
    INPUT_LINES = 'INPUT_LINES'
    INPUT_FIELDS = 'INPUT_FIELDS'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_POINTS,
                self.tr('Selecionar camada ponto'),
                [QgsProcessing.TypeVectorPoint]
            )
        )
        self.addParameter(
            core.QgsProcessingParameterField(
                self.INPUT_FIELDS,
                self.tr('Selecionar o atributo de rotação da camada'), 
                type=core.QgsProcessingParameterField.Any, 
                parentLayerParameterName=self.INPUT_POINTS,
                allowMultiple=True
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.INPUT_MIN_DIST,
                self.tr('Tolerância da distância'), 
                type=QgsProcessingParameterNumber.Double, 
                minValue=0
            )
        )

        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LINES,
                self.tr('Selecionar linhas'),
                QgsProcessing.TypeVectorLine
            )
        )

    def processAlgorithm(self, parameters, context, feedback):      
        pointLayer = self.parameterAsVectorLayer(parameters, self.INPUT_POINTS, context)
        rotationField = self.parameterAsFields(parameters, self.INPUT_FIELDS, context)[0]
        distance = self.parameterAsDouble(parameters, self.INPUT_MIN_DIST, context)
        lineList = self.parameterAsLayerList(parameters, self.INPUT_LINES, context)
      
        for pointFeature in pointLayer.getFeatures():
            pointGeometry = pointFeature.geometry()
            point = pointGeometry.asMultiPoint()[0]
            request = self.getFeatureRequestByPoint( pointGeometry,  distance)            
            for step, lineLayer in enumerate(lineList):   

                nearestLineGeometry = None
                shortestDistance = None

                for lineFeature in lineLayer.getFeatures(request):
                    lineGeometry = lineFeature.geometry()
                    distanceFound = pointGeometry.distance( lineGeometry )
                    if not shortestDistance:
                        nearestLineGeometry = lineGeometry
                        shortestDistance = distanceFound  
                    elif distanceFound < shortestDistance:
                        nearestLineGeometry = lineGeometry
                        shortestDistance = distanceFound
                    
                if not nearestLineGeometry:
                    continue   
                    
                projectedPoint = core.QgsGeometryUtils.closestPoint( 
                    nearestLineGeometry.constGet(), 
                    core.QgsPoint( point.x(), point.y()) 
                )
                angleRadian = math.atan2( projectedPoint.y() - point.y(), projectedPoint.x() - point.x() )
                if angleRadian < 0:
                    angleRadian += 2 * math.pi
                angleDegrees = 360 - round( math.degrees( angleRadian ) )
                pointFeature[ rotationField ] = angleDegrees
                self.updateLayerFeature( pointLayer, pointFeature)
        
        return {self.OUTPUT: ''}

    def getFeatureRequestByPoint(self, geometry, distance, segment=5):
        return QgsFeatureRequest().setFilterRect(
            geometry.buffer(distance, segment).boundingBox()
        )
   
    def updateLayerFeature(self, layer, feature):
        layer.startEditing()
        layer.updateFeature(feature)
   
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Rotation()

    def name(self):
        return 'rotation'

    def displayName(self):
        return self.tr('Definir rotação')

    def group(self):
        return self.tr('Edição')

    def groupId(self):
        return 'edicao'

    def shortHelpString(self):
        return self.tr("O algoritmo ...")
    
