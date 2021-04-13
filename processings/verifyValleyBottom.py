# -*- coding: utf-8 -*-

from qgis import processing
from qgis.PyQt.QtCore import QCoreApplication
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
                       QgsFeature,
                       QgsVectorLayer,
                       QgsPoint,
                       QgsGeometry,
                       QgsProcessingParameterVectorDestination,
                       QgsField,
                       QgsFields
                       )


class VerifyValleyBottom(QgsProcessingAlgorithm):

    INPUT_DRAINAGE = 'INPUT_DRAINAGE'
    INPUT_CONTOUR = 'INPUT_CONTOUR'
    P1 = 'P1'
    P2 = 'P2'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_DRAINAGE,
                self.tr('Select the drainage layer'),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_CONTOUR,
                self.tr('Select the contour layer'),
                types=[QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        drainageLayer = self.parameterAsVectorLayer(parameters, 'INPUT_DRAINAGE', context)
        contourLayer = self.parameterAsVectorLayer(parameters, 'INPUT_CONTOUR', context)

        intersections = self.intersectionsPoints(context, feedback, drainageLayer, contourLayer)

        drainageIDsIntersections = self.joinByLocation(self, context, feedback, intersections, drainageLayer)
        contourIDsIntersections = self.joinByLocation(self, context, feedback, intersections, contourLayer)

        featuresArray = self.createFeaturesArray(originalLayer)

        feedback.setProgressText('Verificando inconsistencias ')
        streamStartPoints = self.getLinesStartPoints(featuresArray)
        orderedFeatures = self.orderLines(featuresArray, streamStartPoints, 0)
        newLayer = self.orderedLayer(parameters, context, originalLayer, orderedFeatures)

        return {self.OUTPUT: newLayer}

    def joinByLocation(self, context, feedback, baseLayer, joinLayer):
        resultLayer = processing.run(
            'qgis:joinattributesbylocation',
            {
                'INPUT': baseLayer,
                'JOIN': joinLayer,
                'PREDICATE': [0],  # intersects
                'JOIN_FIELDS': ['id'],
                'PREFIX': 'join',
                'DISCARD_NONMATCHING': True,
                'OUTPUT': 'memory:'
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback)['OUTPUT']
        resultLayer = context.takeResultLayer(resultLayer)
        return resultLayer

    def intersectionsPoints(self, context, feedback, drainageLayer, countourLayer):
        intersectionLayer = processing.run(
            'qgis:lineintersections',
            {
                'INPUT': drainageLayer,
                'INTERSECT': countourLayer,
                'OUTPUT': 'memory:'
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback)['OUTPUT']
        intersectionLayer = context.takeResultLayer(intersectionLayer)
        # intersectionPoints = [x for x in intersectionLayer.getFeatures()]
        return intersectionLayer

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return VerifyValleyBottom()

    def name(self):
        return 'Verify valley bottoms'

    def displayName(self):
        return self.tr('VerifyValleyBottom')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("Verifica a correta topologia entre curvas de nível e hidrologia")
