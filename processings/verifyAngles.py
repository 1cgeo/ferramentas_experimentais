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
                       QgsFields, QgsWkbTypes, QgsPointXY,
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

        # featsToAnalyseL = self.checkAngleInsideLayerL(lines, minA, maxA)
        # featsToAnalyseA = self.checkAngleInsideLayerA(areas, minA, maxA)
        featsToAnalyseL = [
            *self.caseInternLine(lines, minA, maxA),
            *self.caseInternArea(areas, minA, maxA)
            # *self.caseBetweenLines(lines, minA, maxA)
            ]
        sinkL.addFeatures(featsToAnalyseL)
        # sinkA.addFeatures(featsToAnalyseA)

        return {
            self.OUTPUT_LINE: sinkL,
            self.OUTPUT_AREA: sinkA}

    # def checkAngleInsideLayerL(self, layers, minA, maxA):
    #     rotated = False
    #     featsToAnalyse = []
    #     for layer in layers:
    #         for feat in layer.getFeatures():
    #             if 'oldFeat' not in locals():
    #                 oldFeat = QgsFeature(feat)
    #             vertices = feat.geometry().vertices()
    #             # Gets v1 and v2 in the first iteration
    #             if all(('v1' not in locals(), 'v2' not in locals())):
    #                 v1 = next(vertices) if vertices.hasNext() else None
    #                 v2 = next(vertices) if vertices.hasNext() else None
    #             # Calls next() when it was rotated on last vertex, otherwise two last points would be the same
    #             if rotated:
    #                 next(vertices)
    #             for v3 in vertices:
    #                 # Checks connection between lines
    #                 oldLine = QgsGeometry.fromPolyline([v1,v2])
    #                 newLine = QgsGeometry.fromPolyline([v2,v3])
    #                 # 1st case: oldline inside oldfeat, but line disconnected
    #                 # 2nd case: oldLine not inside oldFeat nor feat (oldLine disconnected)
    #                 # In any of those scenarios, there will be a rotation
    #                 if all([not newLine.within(feat.geometry()), oldLine.within(oldFeat.geometry())]) or all([not oldLine.within(feat.geometry()),not oldLine.within(oldFeat.geometry())]): # and line.within(feat.geometry()):
    #                     v1, v2 = v2, v3
    #                     rotated = True if not vertices.hasNext() else False
    #                     continue
    #                 # Checks angle
    #                 angle = QgsGeometryUtils.angleBetweenThreePoints(v1.x(), v1.y(), v2.x(), v2.y(), v3.x(), v3.y())
    #                 angle = math.degrees(angle)
    #                 if angle > maxA or angle < minA:
    #                     newFeat = QgsFeature()
    #                     newFeat.setGeometry(QgsLineString([v1,v2,v3]))
    #                     featsToAnalyse.append(newFeat)
    #                 v1, v2 = v2, v3
    #             oldFeat = QgsFeature(feat)
    #     return featsToAnalyse

    # def checkAngleInsideLayerA(self, layers, minA, maxA):
    #     featsToAnalyse = []
    #     for layer in layers:
    #         for feat in layer.getFeatures():
    #             vertices = feat.geometry().vertices()
    #             geom = feat.geometry()
    #             if vertices.hasNext():
    #                 v1 = next(vertices)
    #             if vertices.hasNext():
    #                 v2 = next(vertices)
    #                 _v = v2.clone()
    #             for v3 in vertices:
    #                 v1g, v2g, v3g,  = QgsGeometry.fromWkt(v1.asWkt()), QgsGeometry.fromWkt(v2.asWkt()), QgsGeometry.fromWkt(v3.asWkt())
    #                 if all([geom.intersects(v2g), geom.intersects(v3g), geom.intersects(v1g)]):
    #                     angle = QgsGeometryUtils.angleBetweenThreePoints(v1.x(), v1.y(), v2.x(), v2.y(), v3.x(), v3.y())
    #                     angle = math.degrees(angle)
    #                     if angle > maxA or angle < minA:
    #                         newFeat = QgsFeature()
    #                         newFeat.setGeometry(QgsLineString([v1,v2,v3]))
    #                         featsToAnalyse.append(newFeat)
    #                     if not vertices.hasNext():
    #                         angle = QgsGeometryUtils.angleBetweenThreePoints(v2.x(), v2.y(), v3.x(), v3.y(), _v.x(), _v.y())
    #                         if angle > maxA or angle < minA:
    #                             newFeat = QgsFeature()
    #                             newFeat.setGeometry(QgsLineString([v2,v3,_v]))
    #                             featsToAnalyse.append(newFeat)
    #                 v1, v2 = v2, v3
    #     return featsToAnalyse

    def caseInternLine(self, layers, minA, maxA):
        featsToAnalyse = []
        for layer in layers:
            for feat in layer.getFeatures():
                vertices = feat.geometry().vertices()
                v1 = next(vertices) if vertices.hasNext() else None
                v2 = next(vertices) if vertices.hasNext() else None
                for v3 in vertices:
                    newFeat = self.checkIntersectionAndCreateFeature(v1, v2, v3, minA, maxA) if all((v1,v2,v3)) else None
                    if newFeat:
                        featsToAnalyse.append(newFeat)
                    v1,v2 = v2,v3
        return featsToAnalyse

    def caseInternArea(self, layers, minA, maxA):
        featsToAnalyse = []
        for layer in layers:
            for feat in layer.getFeatures():
                multiPolygons = feat.geometry().asMultiPolygon()[0]
                for vertices in multiPolygons:
                    for i in range(len(vertices) - 2):
                        v1, v2, v3 = vertices[i:i+3]
                        newFeat = self.checkIntersectionAndCreateFeature(v1, v2, v3, minA, maxA) if all((v1,v2,v3)) else None
                        if newFeat:
                            featsToAnalyse.append(newFeat)
                    newFeat = self.checkIntersectionAndCreateFeature(vertices[-2],vertices[-1], vertices[1], minA, maxA )
                    if newFeat:
                        featsToAnalyse.append(newFeat)
        return featsToAnalyse

    def caseBetweenLines(self, layers, minA, maxA):
        featsToAnalyse = []
        for i in range(0, len(layers)):
            for feat1 in layers[i].getFeatures():
                gfeat1 = feat1.geometry()
                request = QgsFeatureRequest().setFilterRect(gfeat1.boundingBox())
                for j in range(i, len(layers)):
                    for feat2 in layers[j].getFeatures(request):
                        gfeat2 = feat2.geometry()
                        if gfeat1.intersects(gfeat2):
                            toAnalyse = self.checkIfIntersectionIsValid(gfeat1, gfeat2, minA, maxA)
                            if toAnalyse:
                                featsToAnalyse.append(toAnalyse)
        return featsToAnalyse

    def checkIntersectionAndCreateFeature(self, v1, v2, v3, minA, maxA):
        angle = QgsGeometryUtils.angleBetweenThreePoints(v1.x(), v1.y(), v2.x(), v2.y(), v3.x(), v3.y())
        angle = math.degrees(angle)
        if angle > maxA or angle < minA:
            newFeat = QgsFeature()
            if isinstance(v1, QgsPoint):
                newFeat.setGeometry(QgsGeometry.fromPolyline([v1,v2,v3]))
            if isinstance(v1, QgsPointXY):
                newFeat.setGeometry(QgsGeometry.fromPolylineXY([v1,v2,v3]))
            print('passed!')
            print(v1,v2,v3)
            return newFeat
    
    def checkIfIntersectionIsValid(self, g1, g2, minA, maxA):
        intersection = g1.intersection(g2)
        intersection = intersection.asPoint()
        vg1 = list(g1.vertices())
        vg2 = list(g2.vertices())
        # Se não há sobreposição
        if not vg1[0].compare(vg2[0]):
            if vg1[-1].compare(vg2[0]):
                feat = self.checkIntersectionAndCreateFeature(vg1[-2], vg1[-1], vg2[1], minA, maxA)
            elif vg1[0].compare(vg2[-1]):
                feat = self.checkIntersectionAndCreateFeature(vg2[-2], vg2[-1], vg1[1], minA, maxA)
        return feat

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
