# -*- coding: utf-8 -*-

from qgis import processing
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing, QgsProject,
                       QgsFeatureSink, QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingParameterString,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterNumber,
                       QgsFeature, QgsVectorLayer,
                       QgsProcessingParameterVectorDestination,
                       QgsGeometry, QgsField,
                       QgsFields, QgsWkbTypes
                       )

class RemoveHoles(QgsProcessingAlgorithm):

    LAYERS = 'LAYERS'
    MIN_AREA = 'MIN_AREA'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.LAYERS,
                self.tr('Select layer'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MIN_AREA,
                self.tr('Minimum area'),
                QgsProcessingParameterNumber.Double
            )
        )
    
    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.LAYERS, context)
        min_area = self.parameterAsDouble(parameters, self.MIN_AREA, context)

        # Removes geometries
        cleaned = self.runDeleteHoles(context, feedback, layer, min_area)
        self.updateGeometries(layer, cleaned)
        return {}

    def runDeleteHoles(self, context, feedback, layer, tol):
        cleaned = processing.run(
            'qgis:deleteholes',
            {
                'INPUT': layer,
                'MIN_AREA': tol,
                'OUTPUT': 'memory:'
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback)['OUTPUT']
        cleaned = context.takeResultLayer(cleaned)
        return cleaned

    def updateGeometries(self, ref, cleaned):
        ref.startEditing()
        for r, c in zip(ref.getFeatures(), cleaned.getFeatures()):
            if not r.geometry().equals(c.geometry()):
                ref.changeGeometry(r.id(), c.geometry())
        ref.updateExtents()

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return RemoveHoles()

    def name(self):
        return 'Remove holes'

    def displayName(self):
        return self.tr('RemoveHoles')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("Delete holes from area layers")