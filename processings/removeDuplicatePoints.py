# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QCoreApplication, QVariant
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

class RemoveDuplicatePoints(QgsProcessingAlgorithm): 

    INPUT_LAYERS_L = 'INPUT_LAYERS_L'
    INPUT_LAYERS_A = 'INPUT_LAYERS_A'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS_L,
                self.tr('Selecionar camadas linha'),
                QgsProcessing.TypeVectorLine,
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS_A,
                self.tr('Selecionar camadas área'),
                QgsProcessing.TypeVectorPolygon,
                optional=True
            )
        )

    def processAlgorithm(self, parameters, context, feedback):      
        lineListLayers = self.parameterAsLayerList(parameters, self.INPUT_LAYERS_L, context)
        polygonListLayers = self.parameterAsLayerList(parameters, self.INPUT_LAYERS_A, context)
        self.removeDuplicateVertexByLayers( lineListLayers ) if lineListLayers else ''
        self.removeDuplicateVertexByLayers( polygonListLayers ) if polygonListLayers else ''
        return {self.OUTPUT: ''}

    def removeDuplicateVertexByLayers(self, layers):
        for layerOrigin in layers:
            primaryKeyIndex = layerOrigin.primaryKeyAttributes()[0]
            primaryKeyName = layerOrigin.fields().names()[ primaryKeyIndex ]
            layerCleaned = self.removeDuplicateVertex( layerOrigin )
            for featureCleaned in layerCleaned.getFeatures():
                featureOrigin  = layerOrigin.getFeature( featureCleaned[ primaryKeyName ] )
                self.updateLayerFeature( layerOrigin, featureOrigin,  featureCleaned.geometry() )

    def removeDuplicateVertex(self, layer):
        r = processing.run(
            'native:removeduplicatevertices',
            {   'TOLERANCE' : 0.000001, 
                'USE_Z_VALUE': False,
                'INPUT' : core.QgsProcessingFeatureSourceDefinition(
                    layer.source()
                ), 
                'OUTPUT' : 'TEMPORARY_OUTPUT'
            }
        )
        return r['OUTPUT']

    def updateLayerFeature(self, layer, feature, geometry):
        feature.setGeometry(geometry)
        layer.startEditing()
        layer.updateFeature(feature)
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return RemoveDuplicatePoints()

    def name(self):
        return 'removeduplicatepoints'

    def displayName(self):
        return self.tr('Remover Vértices Duplicados')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo ...")
    
