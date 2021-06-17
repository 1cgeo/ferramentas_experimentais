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

class MergeRivers(QgsProcessingAlgorithm): 

    INPUT_LAYER_L = 'INPUT_LAYER_L'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER_L,
                self.tr('Selecionar camada de drenagem'),
                [QgsProcessing.TypeVectorLine]
            )
        )

    def processAlgorithm(self, parameters, context, feedback):      
        drainageLayer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER_L, context)

        merge = {}
        for drainageFeature in drainageLayer.getFeatures():
            if not drainageFeature['nome']:
                continue
            if not( drainageFeature['tipo'] in [1,2] ):
                continue
            mergeKey = '{0}_{1}'.format( drainageFeature['nome'].lower(), drainageFeature['tipo'])
            mergeKey = drainageFeature['nome'].lower()
            if not( mergeKey in merge):
                merge[ mergeKey ] = []
            merge[ mergeKey ].append( drainageFeature )

        for mergeKey in merge:
            self.mergeLineFeatures( merge[ mergeKey ], drainageLayer )
        return {self.OUTPUT: ''}

    def mergeLineFeatures(self, features, layer):
        layer.startEditing()
        idsToRemove = []
        featureIds = [ f.id() for f in features ]
        for featureAId in featureIds:
            if featureAId in idsToRemove:
                continue
            for featureBId in featureIds:
                if featureAId == featureBId or featureBId in idsToRemove:
                    continue
                featureA = layer.getFeature( featureAId )
                featureB = layer.getFeature( featureBId )
                if not featureA.geometry().touches( featureB.geometry() ):
                    continue
                newGeometry = featureA.geometry().combine( featureB.geometry() ).mergeLines()
                featureA.setGeometry( newGeometry )
                layer.updateFeature( featureA )
                idsToRemove.append( featureBId )
        layer.deleteFeatures( idsToRemove )

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return MergeRivers()

    def name(self):
        return 'mergerivers'

    def displayName(self):
        return self.tr('Mescla rios')

    def group(self):
        return self.tr('Edição')

    def groupId(self):
        return 'edicao'

    def shortHelpString(self):
        return self.tr("O algoritmo ...")
    
