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
            QgsProcessingParameterNumber(
                self.P1,
                self.tr('Segment size along line from intersection points'),
                type=QgsProcessingParameterNumber.Double
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.P2,
                self.tr('Tolerance from point projection on line'),
                type=QgsProcessingParameterNumber.Double
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
        p1 = self.parameterAsDouble(parameters, 'P1 ', context)
        p2 = self.parameterAsDouble(parameters, 'P2', context)

        # Get intersection points
        intersections = self.intersectionsPoints(context, feedback, drainageLayer, contourLayer)

        # Generate IDs
        self.generateIntersectionIds(context, feedback, intersections)

        # Get "buffer" from point
        drainagePointSegment, drainageSegment = self.getSegmentFromPoint(
            context, feedback, intersections, drainageLayer, p1)
        contourPointSegment, contourSegment = self.getSegmentFromPoint(
            context, feedback, intersections, contourLayer, p1)


        # Convert to single parts
        # contourSegment = self.multiPartToSingleParts(context, feedback, contourSegment)
        # drainageSegment = self.multiPartToSingleParts(context, feedback, drainageSegment)

        # Get segment created from contourSegment bounds
        countourExtentPoints = self.getLineFromExtents(context, feedback, contourSegment)

        # drainageIntersectExtentSegment = 

        # self.segmentIntersection(context, feedback, countourExtentPoints, drainageSegment)


        # Get line from contourSegment extents

        # feedback.setProgressText('')
        # self.sinkOutput(parameters, context, feedback, contourSegment)
        return {self.OUTPUT: contourSegment}

    def sinkOutput(self, parameters, context, feedback, source):
        sink, _ = self.parameterAsSink(
        parameters,
        self.OUTPUT,
        context,
        source.fields(),
        source.wkbType(),
        source.sourceCrs()
        )

        for f in source.getFeatures():
            sink.addFeature(f)

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
        return intersectionLayer

    def getSegmentFromPoint(self, context, feedback, pointLayer, vectorLayer, ):
        _segmentLayer = processing.run(
            'qgis:serviceareafromlayer',
            {
                'INPUT': vectorLayer,
                'STATEGY': 0,
                'START_POINTS': pointLayer,
                'TRAVEL_COST2': p1,
                'DEFAULT_DIRECTION' : 2,
                'DEFAULT_SPEED' : 50,
                'DIRECTION_FIELD' : '',
                'TOLERANCE' : 0,
                'VALUE_BACKWARD' : '',
                'VALUE_BOTH' : '',
                'VALUE_FORWARD' : '',
                'SPEED_FIELD' : '',
                'INCLUDE_BOUNDS' : True,
                'OUTPUT': 'memory:',
                'OUTPUT_LINES': 'memory:',
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback)
        segmentLayer = context.takeResultLayer(_segmentLayer['OUTPUT_LINES'])
        pointSegmentLayer = context.takeResultLayer(_segmentLayer['OUTPUT'])
        return pointSegmentLayer, segmentLayer

    def generateIntersectionIds(self, context, feedback, pointLayer):
        pointLayer.startEditing()
        pointLayer.addAttribute(QgsField(name='id_v', type=QVariant.Int, typeName='int'))
        for i, feat in enumerate(pointLayer.getFeatures()):
            pointLayer.changeAttributeValue(
                fid=feat.id(), field=feat.fieldNameIndex('id_v'), newValue=i)
        pointLayer.commitChanges()

    def multiPartToSingleParts(self, context, feedback, layer):
        singlePartLayer = processing.run(
            'qgis:multiparttosingleparts',
            {
                'INPUT': layer,
                'OUTPUT': 'memory:'
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback)['OUTPUT']
        singlePartLayer = context.takeResultLayer(singlePartLayer)
        return singlePartLayer

    def getLineFromExtents(self, context, feedback, vectorLayer):
        for x in vectorLayer.getFeatures():
            print(x.geometry())
        return {
            x.attribute('id_v'):(
                x.geometry().asPoint()[0],
                x.geometry().asPoint()[-1]
            ) for x in vectorLayer.getFeatures()
        }

    def segmentIntersection(self, context, feedback, points, drainage):
        for x in drainage.getFeatures():
            id_v = x.attribute('id_v')
            print(points[id_v])
            line_from_points = QgsGeometry.fromPolylineXY(points[id_v])
            print(line_from_points)
            # print(x.geometry(), x.geometry().asWkt())
            # intersection = x.geometry().intersection(line_from_points)
            # print(intersection)

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
