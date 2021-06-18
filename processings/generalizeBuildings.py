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

class GeneralizeBuildings(QgsProcessingAlgorithm): 

    INPUT_BUILDING_P = 'INPUT_BUILDING_P'
    INPUT_BUILDING_VISIBLE_FIELD = 'INPUT_BUILDING_VISIBLE_FIELD'
    INPUT_DEPOSIT_P = 'INPUT_DEPOSIT_P'
    INPUT_DEPOSIT_VISIBLE_FIELD = 'INPUT_DEPOSIT_VISIBLE_FIELD'
    INPUT_MINERAL_EXTRACTION_A = 'INPUT_MINERAL_EXTRACTION_A'
    INPUT_BUILDING_AREA_A = 'INPUT_BUILDING_AREA_A'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_BUILDING_P,
                self.tr('Selecionar camada de edificação'),
                [QgsProcessing.TypeVectorPoint]
            )
        )

        self.addParameter(
            core.QgsProcessingParameterField(
                self.INPUT_BUILDING_VISIBLE_FIELD,
                self.tr('Selecionar o atributo de "visibilidade" da camada de edificação'), 
                type=core.QgsProcessingParameterField.Any, 
                parentLayerParameterName=self.INPUT_BUILDING_P,
                allowMultiple=False
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_DEPOSIT_P,
                self.tr('Selecionar camada de depósito'),
                [QgsProcessing.TypeVectorPoint]
            )
        )

        self.addParameter(
            core.QgsProcessingParameterField(
                self.INPUT_DEPOSIT_VISIBLE_FIELD,
                self.tr('Selecionar o atributo de "visibilidade" da camada de depósito'), 
                type=core.QgsProcessingParameterField.Any, 
                parentLayerParameterName=self.INPUT_DEPOSIT_P,
                allowMultiple=False
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_MINERAL_EXTRACTION_A,
                self.tr('Selecionar camada de extração mineral'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_BUILDING_AREA_A,
                self.tr('Selecionar camada de área edificada'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

    def processAlgorithm(self, parameters, context, feedback):      
        buildingLayer = self.parameterAsVectorLayer(parameters, self.INPUT_BUILDING_P, context)
        buildingVisibleField = self.parameterAsFields(parameters, self.INPUT_BUILDING_VISIBLE_FIELD, context)[0]
        depositLayer = self.parameterAsVectorLayer(parameters, self.INPUT_DEPOSIT_P, context)
        depositVisibleField = self.parameterAsFields(parameters, self.INPUT_DEPOSIT_VISIBLE_FIELD, context)[0]
        mineralExtractionLayer = self.parameterAsVectorLayer(parameters, self.INPUT_MINERAL_EXTRACTION_A, context)
        buildingArea = self.parameterAsVectorLayer(parameters, self.INPUT_BUILDING_AREA_A, context)

        for mineralExtractionFeature in mineralExtractionLayer.getFeatures():
            mineralExtractionGeometry = mineralExtractionFeature.geometry()
            request = QgsFeatureRequest().setFilterRect( mineralExtractionGeometry.boundingBox() )
            for visibleField, layer in [ (buildingVisibleField, buildingLayer), (depositVisibleField, depositLayer) ]:
                features = list( layer.getFeatures( request ) )
                for feature in features:
                    if not feature.geometry().intersects( mineralExtractionGeometry ):
                        continue
                    feature[ visibleField ] = False
                    self.updateLayerFeature( layer, feature )

        for buildingAreaFeature in buildingArea.getFeatures():
            buildingAreaGeometry = buildingAreaFeature.geometry()
            request = QgsFeatureRequest().setFilterRect( buildingAreaGeometry.boundingBox() )
            for visibleField, layer in [ (buildingVisibleField, buildingLayer) ]:
                features = list( layer.getFeatures( request ) )
                for feature in features:
                    if not( feature['tipo'] == 0 and feature.geometry().intersects( buildingAreaGeometry ) ):
                        continue
                    feature[ visibleField ] = False
                    self.updateLayerFeature( layer, feature )
        
        return {self.OUTPUT: ''}

    def updateLayerFeature(self, layer, feature):
        layer.startEditing()
        layer.updateFeature(feature)
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return GeneralizeBuildings()

    def name(self):
        return 'generalizebuildings'

    def displayName(self):
        return self.tr('Generalizar edificações')

    def group(self):
        return self.tr('Edição')

    def groupId(self):
        return 'edicao'

    def shortHelpString(self):
        return self.tr("O algoritmo ...")
    
