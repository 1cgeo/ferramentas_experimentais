# -*- coding: utf-8 -*-

from qgis import processing
import math
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing, QgsProject,
                       QgsFeatureSink, QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingParameterString,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingFeatureSourceDefinition,
                       QgsProcessingParameterNumber,
                       QgsFeature, QgsVectorLayer,
                       QgsProcessingParameterVectorDestination,
                       QgsGeometry, QgsField, QgsPoint,
                       QgsFields, QgsWkbTypes,
                       QgsProcessingFeatureSourceDefinition,
                       QgsProperty, QgsFeatureRequest,
                       QgsGeometryUtils, QgsLineString
                       )

class VerifyAngles(QgsProcessingAlgorithm):

    INPUT_LINES = 'INPUT_LINES'
    INPUT_AREAS = 'INPUT_AREAS'
    MIN_ANGLE = 'MIN_ANGLE'
    MAX_ANGLE = 'MAX_ANGLE'
    OUTPUT_LINE = 'OUTPUT_LINE'
    OUTPUT_AREA = 'OUTPUT_AREA'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LINES,
                self.tr('Select line layers to be verified'),
                layerType=QgsProcessing.TypeVectorLine,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_AREAS,
                self.tr('Select area layers to be verified'),
                layerType=QgsProcessing.TypeVectorPolygon,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MIN_ANGLE,
                self.tr('Minimum angle'),
                QgsProcessingParameterNumber.Double,
                defaultValue=20.0
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_ANGLE,
                self.tr('Maximum angle'),
                QgsProcessingParameterNumber.Double,
                defaultValue=160.0
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LINE,
                self.tr('Flags for line layers')
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_AREA,
                self.tr('Flags for area layers')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        lines = self.parameterAsLayerList(parameters, self.INPUT_LINES, context)
        areas = self.parameterAsLayerList(parameters, self.INPUT_AREAS, context)
        minA = self.parameterAsDouble(parameters, self.MIN_ANGLE, context)
        maxA = self.parameterAsDouble(parameters, self.MAX_ANGLE, context)

        crs = QgsProject.instance().crs()
        fields = QgsFields()
        fields.append(QgsField('Error description', QVariant.String))

        sink_l, _ = self.parameterAsSink(parameters, self.OUTPUT_LINE, context, fields,
            QgsWkbTypes.LineString, crs)
        sink_a, _ = self.parameterAsSink(parameters, self.OUTPUT_AREA, context, fields,
            QgsWkbTypes.Polygon, crs)

        featsToAnalyse = self.checkAngleInsideLayer(lines, minA, maxA)
        sink_l.addFeatures(featsToAnalyse)

        return {
            self.OUTPUT_LINE: sink_l,
            self.OUTPUT_AREA: sink_a}

    def checkAngleInsideLayer(self, layers, minA, maxA):
        beginning = True
        featsToAnalyse = []
        for lineLayer in layers:
            for feat in lineLayer.getFeatures():
                vertices = feat.geometry().vertices()
                if beginning:
                    if vertices.hasNext():
                        v1 = next(vertices)
                    if vertices.hasNext():
                        v2 = next(vertices)
                    beginning = False
                for v3 in vertices:
                    # Jumps discontinuos lines
                    line = QgsGeometry.fromPolyline([v2,v3])
                    if not line.within(feat.geometry()):
                        beginning = True
                        continue
                    angle = QgsGeometryUtils.angleBetweenThreePoints(v1.x(), v1.y(), v2.x(), v2.y(), v3.x(), v3.y())
                    angle = math.degrees(angle)
                    if angle > maxA or angle < minA:
                        newFeat = QgsFeature()
                        newFeat.setGeometry(QgsLineString([v1,v2,v3]))
                        featsToAnalyse.append(newFeat)
                    v1, v2 = v2, v3
        return featsToAnalyse

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return VerifyAngles()

    def name(self):
        return 'Verify angles'

    def displayName(self):
        return self.tr('Verify angles')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("Verify angles")
