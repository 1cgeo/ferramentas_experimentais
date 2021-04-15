# -*- coding: utf-8 -*-

from qgis import processing
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsFeatureSink, QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProject,
                       QgsMapLayer,
                       QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsProject,
                       QgsPointXY,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterBoolean,
                       QgsProcessingRegistry,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsFeature,
                       QgsVectorLayer,
                       QgsPoint,
                       QgsGeometry,
                       QgsProcessingParameterVectorDestination,
                       QgsField,
                       QgsFields
                       )


class VerifyLayersConnection(QgsProcessingAlgorithm):

    INPUT_FRAMES = 'INPUT_FRAMES'
    LAYERS = 'LAYERS'
    TOLERANCE = 'TOLERANCE'
    IGNORE_LIST = 'IGNORE_LIST'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_FRAMES,
                self.tr('Select (two) frames'),
                layerType=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.LAYERS,
                self.tr('Layers to be verified'),
                types=[QgsProcessing.TypeVectorLine, QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.TOLERANCE,
                self.tr('Tolerance'),
                type=QgsProcessingParameterNumber.Double
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.IGNORE_LIST,
                self.tr('Fields to be ignored'),
                allowMultiple=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        pass

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return VerifyLayersConnection()

    def name(self):
        return 'Verify layers connection'

    def displayName(self):
        return self.tr('VerifyLayersConnection')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("Verifica a conexão de layers entre molduras distintas")
