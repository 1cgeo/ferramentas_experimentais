# -*- coding: utf-8 -*-

from qgis import processing
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterNumber,
                       QgsGeometry, QgsField
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
                type=QgsProcessingParameterNumber.Double,
                defaultValue=50
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.P2,
                self.tr('Tolerance from point projection on line'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10
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
        p1 = self.parameterAsDouble(parameters, 'P1', context)
        p2 = self.parameterAsDouble(parameters, 'P2', context)

        drainageDict = {
            x.attribute('id'): x.geometry() for x in drainageLayer.getFeatures()
        }
        contourDict = {
            x.attribute('id'): x.geometry() for x in contourLayer.getFeatures()
        }

        # Get intersection points
        intersections = self.intersectionsPoints(context, feedback, drainageLayer, contourLayer)

        # Generate IDs for intersections
        self.generateIntersectionIds(intersections)

        # Locate point on line
        contourIntersections = self.locatePointOnLine(intersections, contourDict, 'contour', p1)

        # Verify intersection from contourIntersections and drainage
        output = self.getIntersectionOnDrainage(intersections, contourIntersections, drainageDict, p2)

        # Insert output in sink
        if output:
            sink, _ = self.parameterAsSink(parameters, self.OUTPUT, context, output[0].fields(), output[0].geometry().wkbType(), intersections.sourceCrs())
            for feat in output:
                sink.addFeature(feat)
        else:
            sink = output

        return {self.OUTPUT: sink}

    def intersectionsPoints(self, context, feedback, drainageLayer, countourLayer):
        intersectionLayer = processing.run(
            'qgis:lineintersections',
            {
                'INPUT': countourLayer,
                'INTERSECT': drainageLayer,
                'INPUT_FIELDS': ['id'],
                'INTERSECT_FIELDS': ['id'],
                'INTERSECT_FIELDS_PREFIX': 'd',
                'OUTPUT': 'memory:'
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback)['OUTPUT']
        intersectionLayer = context.takeResultLayer(intersectionLayer)
        return intersectionLayer

    def locatePointOnLine(self, pointLayer, contourDict, layerType, p1):
        interpolatedPoints = {}
        for point in pointLayer.getFeatures():
            searchId = point.attribute('id') if layerType == 'contour' else point.attribute('vid')
            locatedPoint = contourDict[searchId].lineLocatePoint(point.geometry())
            interpolated1 = contourDict[searchId].interpolate(locatedPoint + p1)
            interpolated2 = contourDict[searchId].interpolate(locatedPoint - p1)
            if interpolated1.isNull() or interpolated2.isNull():
                continue
            interpolated1 = interpolated1.asPoint()
            interpolated2 = interpolated2.asPoint()
            interpolatedPoints.update({point.attribute('vid'): (interpolated1, interpolated2)})
        return interpolatedPoints

    def getIntersectionOnDrainage(self, intersections, contourIntersections, drainageDict, p2):
        errors = []
        for p in intersections.getFeatures():
            did = p.attribute('did')
            vid = p.attribute('vid')
            if vid not in contourIntersections.keys():
                continue
            lineFromContourIntersection = QgsGeometry.fromPolylineXY(contourIntersections[vid])
            intersection = lineFromContourIntersection.intersection(drainageDict[did])
            d1 = drainageDict[did].lineLocatePoint(intersection)
            d2 = drainageDict[did].lineLocatePoint(p.geometry())
            # distance = p.geometry().distance(intersection)
            if d1-d2 < p2:
                # if distance < p2:
                errors.append(p)
        return errors

    def generateIntersectionIds(self, pointLayer):
        pointLayer.startEditing()
        pointLayer.addAttribute(QgsField(name='vid', type=QVariant.Int, typeName='int'))
        for i, feat in enumerate(pointLayer.getFeatures()):
            pointLayer.changeAttributeValue(
                fid=feat.id(), field=feat.fieldNameIndex('vid'), newValue=i)
        pointLayer.commitChanges()

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
