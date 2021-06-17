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

class HighestQuotaOnTheFrame(QgsProcessingAlgorithm): 

    INPUT_QUOTA_LAYER = 'INPUT_LAYER_P'
    INPUT_QUOTA_FIELD = 'INPUT_QUOTA_FIELD'
    INPUT_HIGHEST_QUOTA_FIELD = 'INPUT_HIGHEST_QUOTA_FIELD'
    INPUT_FRAME = 'INPUT_FRAME'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_QUOTA_LAYER,
                self.tr('Selecionar camada de ponto cotado'),
                [QgsProcessing.TypeVectorPoint]
            )
        )

        self.addParameter(
            core.QgsProcessingParameterField(
                self.INPUT_QUOTA_FIELD,
                self.tr('Selecionar o atributo de "cota"'), 
                type=core.QgsProcessingParameterField.Any, 
                parentLayerParameterName=self.INPUT_QUOTA_LAYER,
                allowMultiple=False
            )
        )

        self.addParameter(
            core.QgsProcessingParameterField(
                self.INPUT_HIGHEST_QUOTA_FIELD,
                self.tr('Selecionar o atributo de "cota mais alta"'), 
                type=core.QgsProcessingParameterField.Any, 
                parentLayerParameterName=self.INPUT_QUOTA_LAYER,
                allowMultiple=False
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_FRAME,
                self.tr('Selecionar camada de moldura'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )


    def processAlgorithm(self, parameters, context, feedback):      
        quotaLayer = self.parameterAsVectorLayer(parameters, self.INPUT_QUOTA_LAYER, context)
        quotaField = self.parameterAsFields(parameters, self.INPUT_QUOTA_FIELD, context)[0]
        higuestQuotaField = self.parameterAsFields(parameters, self.INPUT_HIGHEST_QUOTA_FIELD, context)[0]
        frameLayer = self.parameterAsVectorLayer(parameters, self.INPUT_FRAME, context)

        for frameFeature in frameLayer.getFeatures():
            frameGeometry = frameFeature.geometry()
            request = QgsFeatureRequest().setFilterRect( frameGeometry.boundingBox() ) 
            maxQuotaFeature = None
            features = list( quotaLayer.getFeatures( request ) )
            for quotaFeature in features:
                if not( frameGeometry.intersects( quotaFeature.geometry() ) ):
                    continue
                if maxQuotaFeature and maxQuotaFeature[ quotaField ] > quotaFeature[ quotaField ]:
                    quotaFeature[ higuestQuotaField ] = False
                    self.updateLayerFeature( quotaLayer, quotaFeature)
                    continue
                if maxQuotaFeature:
                    maxQuotaFeature[ higuestQuotaField ] = False
                    self.updateLayerFeature( quotaLayer, maxQuotaFeature)
                maxQuotaFeature = quotaFeature
                maxQuotaFeature[ higuestQuotaField ] = True
                self.updateLayerFeature( quotaLayer, maxQuotaFeature)
                
        
        return {self.OUTPUT: ''}

    def updateLayerFeature(self, layer, feature):
        layer.startEditing()
        layer.updateFeature(feature)
   
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return HighestQuotaOnTheFrame()

    def name(self):
        return 'highestquotaqntheframe'

    def displayName(self):
        return self.tr('Definir cota mais alta por moldura')

    def group(self):
        return self.tr('Edição')

    def groupId(self):
        return 'edicao'

    def shortHelpString(self):
        return self.tr("O algoritmo ...")
    
