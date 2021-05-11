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
                defaultValue=340.0
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

        sinkL, _ = self.parameterAsSink(parameters, self.OUTPUT_LINE, context, fields,
            QgsWkbTypes.LineString, crs)
        sinkA, _ = self.parameterAsSink(parameters, self.OUTPUT_AREA, context, fields,
            QgsWkbTypes.LineString, crs)

        featsToAnalyseL = self.checkAngleInsideLayerL(lines, minA, maxA)
        featsToAnalyseA = self.checkAngleInsideLayerA(areas, minA, maxA)
        sinkL.addFeatures(featsToAnalyseL)
        sinkA.addFeatures(featsToAnalyseA)

        return {
            self.OUTPUT_LINE: sinkL,
            self.OUTPUT_AREA: sinkA}

    def checkAngleInsideLayerL(self, layers, minA, maxA):
        beginning = True
        featsToAnalyse = []
        for layer in layers:
            for feat in layer.getFeatures():
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
                        # beginning = True
                        v1 = v3
                        if vertices.hasNext():
                            v2 = next(vertices)
                        if vertices.hasNext():
                            v3 = next(vertices)
                    # Checks angle
                    angle = QgsGeometryUtils.angleBetweenThreePoints(v1.x(), v1.y(), v2.x(), v2.y(), v3.x(), v3.y())
                    angle = math.degrees(angle)
                    if angle > maxA or angle < minA:
                        newFeat = QgsFeature()
                        newFeat.setGeometry(QgsLineString([v1,v2,v3]))
                        featsToAnalyse.append(newFeat)
                    v1, v2 = v2, v3
        return featsToAnalyse

    def checkAngleInsideLayerA(self, layers, minA, maxA):
        beginning = True
        featsToAnalyse = []
        for layer in layers:
            for feat in layer.getFeatures():
                vertices = feat.geometry().vertices()
                geom = feat.geometry()
                if beginning:
                    if vertices.hasNext():
                        v1 = next(vertices)
                        vf = v1.clone()
                    if vertices.hasNext():
                        v2 = next(vertices)
                        vi = v2.clone()
                    beginning = False
                for v3 in vertices:
                    # Jumps discontinuos lines
                    # Can use all(v.within...)
                    v2g, v3g, vig = QgsGeometry.fromWkt(v2.asWkt()), QgsGeometry.fromWkt(v3.asWkt()), QgsGeometry.fromWkt(vi.asWkt())
                    print(all([geom.intersects(v2g), geom.intersects(v3g), geom.intersects(vig)]), vertices.hasNext() )
                    if not vertices.hasNext() and all([geom.intersects(v2g), geom.intersects(v3g), geom.intersects(vig)]):
                        angle = QgsGeometryUtils.angleBetweenThreePoints(v2.x(), v2.y(), v3.x(), v3.y(), vi.x(), vi.y())
                        if angle > maxA or angle < minA:
                            newFeat = QgsFeature()
                            newFeat.setGeometry(QgsLineString([v2,v3,vi]))
                            featsToAnalyse.append(newFeat)
                    line = QgsGeometry.fromPolyline([v2,v3])
                    if not line.within(feat.geometry()):
                        # beginning = True
                        v1 = v3
                        if vertices.hasNext():
                            v2 = next(vertices)
                        if vertices.hasNext():
                            v3 = next(vertices)
                    # Checks angle
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
