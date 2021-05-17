# -*- coding: utf-8 -*-

import math
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing, QgsProject,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingParameterNumber,
                       QgsFeature, QgsGeometry,
                       QgsField, QgsPoint,
                       QgsFields, QgsWkbTypes, QgsPointXY,
                       QgsFeatureRequest, QgsGeometryUtils, 
                       )

class VerifyZAngles(QgsProcessingAlgorithm):

    INPUT_LINES = 'INPUT_LINES'
    INPUT_AREAS = 'INPUT_AREAS'
    ANGLE = 'ANGLE'
    OUTPUT = 'OUTPUT'

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
                self.ANGLE,
                self.tr('Minimum angle'),
                QgsProcessingParameterNumber.Double,
                defaultValue=300.0
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Flags')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        lines = self.parameterAsLayerList(parameters, self.INPUT_LINES, context)
        areas = self.parameterAsLayerList(parameters, self.INPUT_AREAS, context)
        angle = self.parameterAsDouble(parameters, self.ANGLE, context)

        crs = QgsProject.instance().crs()
        self.fields = QgsFields()
        self.fields.append(QgsField('source', QVariant.String))

        sink, _ = self.parameterAsSink(parameters, self.OUTPUT, context, self.fields,
            QgsWkbTypes.LineString, crs)

        twoOntwoLines = self.caseBetweenLinesFirstRun(lines, angle)
        caseBetweenLines = self.caseBetweenLinesSecondRun(twoOntwoLines, lines, angle)

        featsToAnalyse = [
            *self.caseInternLine(lines, angle),
            *self.caseInternArea(areas, angle),
            *caseBetweenLines
            ]
        sink.addFeatures(featsToAnalyse)

        return {
            self.OUTPUT: sink
            }

    def caseInternLine(self, layers, angle):
        featsToAnalyse = []
        for layer in layers:
            for feat in layer.getFeatures():
                vertices = feat.geometry().vertices()
                v1 = next(vertices) if vertices.hasNext() else None
                v2 = next(vertices) if vertices.hasNext() else None
                v3 = next(vertices) if vertices.hasNext() else None
                for v4 in vertices:
                    newFeat = self.checkIntersectionAndCreateFeature4p(v1, v2, v3, v4, angle) if all((v1,v2,v3,v4)) else None
                    if newFeat:
                        newFeat.setAttribute('source',layer.name())
                        featsToAnalyse.append(newFeat)
                    v1,v2,v3 = v2,v3,v4
        return featsToAnalyse

    def caseInternArea(self, layers, angle):
        featsToAnalyse = []
        for layer in layers:
            for feat in layer.getFeatures():
                multiPolygons = feat.geometry().asMultiPolygon()[0]
                for vertices in multiPolygons:
                    for i in range(len(vertices)-3):
                        v1, v2, v3, v4 = vertices[i:i+4]
                        newFeat = self.checkIntersectionAndCreateFeature4p(v1, v2, v3, v4, angle) if all((v1,v2,v3,v4)) else None
                        if newFeat:
                            newFeat.setAttribute('source',layer.name())
                            featsToAnalyse.append(newFeat)
                    newFeat = self.checkIntersectionAndCreateFeature4p(vertices[-3], vertices[-2],vertices[-1], vertices[1], angle)
                    if newFeat:
                        featsToAnalyse.append(newFeat)
        return featsToAnalyse

    def caseBetweenLinesFirstRun(self, layers, angle):
        featsToAnalyse = []
        for i in range(0, len(layers)):
            for feat1 in layers[i].getFeatures():
                gfeat1 = feat1.geometry()
                request = QgsFeatureRequest().setFilterRect(gfeat1.boundingBox())
                for j in range(i, len(layers)):
                    for feat2 in layers[j].getFeatures(request):
                        gfeat2 = feat2.geometry()
                        if gfeat1.intersects(gfeat2):
                            toAnalyse = self.checkIfIntersectionIsValid(gfeat1, gfeat2,angle)
                            if isinstance(toAnalyse, tuple):
                                toAnalyse = (x for x in toAnalyse if x)
                                for feat in toAnalyse:
                                    if i==j:
                                        feat.setAttribute('source',layers[i].name())
                                    else:
                                        feat.setAttribute('source',f'{layers[i].name()}/{layers[j].name()}')
                                    featsToAnalyse.append(feat)
                            elif toAnalyse:
                                if i==j:
                                    toAnalyse.setAttribute('source',layers[i].name())
                                else:
                                    toAnalyse.setAttribute('source',f'{layers[i].name()}/{layers[j].name()}')
                                featsToAnalyse.append(toAnalyse)
        return featsToAnalyse

    def caseBetweenLinesSecondRun(self, feats, layers, angle):
        featsToAnalyse = []
        for feat in feats:
            gfeat = feat.geometry()
            request = QgsFeatureRequest().setFilterRect(gfeat.boundingBox())
            for layer in layers:
                for feat2 in layer.getFeatures(request):
                    gfeat2 = feat.geometry()
                    if gfeat.intersects(gfeat2):
                            toAnalyse = self.checkIfIntersectionIsValid(gfeat, gfeat2,angle)
                            if isinstance(toAnalyse, tuple):
                                toAnalyse = (x for x in toAnalyse if x)
                                featsToAnalyse.append(feat)
                            elif toAnalyse:
                                featsToAnalyse.append(toAnalyse)
        return featsToAnalyse


    def checkIntersectionAndCreateFeature(self, v1, v2, v3, minA, maxA):
        angle = QgsGeometryUtils.angleBetweenThreePoints(v1.x(), v1.y(), v2.x(), v2.y(), v3.x(), v3.y())
        angle = math.degrees(angle)
        if angle > maxA or angle < minA:
            newFeat = QgsFeature(self.fields)
            if isinstance(v1, QgsPoint):
                newFeat.setGeometry(QgsGeometry.fromPolyline([v1,v2,v3]))
            elif isinstance(v1, QgsPointXY):
                newFeat.setGeometry(QgsGeometry.fromPolylineXY([v1,v2,v3]))
            return newFeat

    def checkIntersectionAndCreateFeature4p(self, v1, v2, v3, v4, angle):
        angle1 = QgsGeometryUtils.angleBetweenThreePoints(v1.x(), v1.y(), v2.x(), v2.y(), v3.x(), v3.y())
        angle2 = QgsGeometryUtils.angleBetweenThreePoints(v2.x(), v2.y(), v3.x(), v3.y(), v4.x(), v4.y())
        angle1 = math.degrees(angle1)
        angle2 = math.degrees(angle2)
        if angle1 > 360-angle and angle2 > 360-angle:
            newFeat = QgsFeature(self.fields)
            if isinstance(v1, QgsPoint):
                newFeat.setGeometry(QgsGeometry.fromPolyline([v1,v2,v3,v4]))
            elif isinstance(v1, QgsPointXY):
                newFeat.setGeometry(QgsGeometry.fromPolylineXY([v1,v2,v3,v4]))
            return newFeat


    def checkIfIntersectionIsValid(self, g1, g2, g3, angle):
        intersection = g1.intersection(g2)
        if intersection.wkbType() != QgsWkbTypes.Point:
            return False
        intersection = intersection.asPoint()

        _, g1VertexIdx, g1PreviousVertexIdx, g1NextVertexIdx, _ = g1.closestVertex(intersection)
        _, g2VertexIdx, g2PreviousVertexIdx, g2NextVertexIdx, _ = g2.closestVertex(intersection)

        vg1 = list(g1.vertices())
        vg2 = list(g2.vertices())

        # Intersections between beginning / end of v1 and v2
        if g1NextVertexIdx == g2PreviousVertexIdx == -1:
            feat = self.checkIntersectionAndCreateFeature(vg1[g1PreviousVertexIdx], vg1[g1VertexIdx], vg2[g2NextVertexIdx], minA, maxA)
            return feat

        elif g2NextVertexIdx == g1PreviousVertexIdx == -1:
            feat = self.checkIntersectionAndCreateFeature(vg2[g2PreviousVertexIdx], vg2[g2VertexIdx], vg1[g1NextVertexIdx], minA, maxA)
            return feat

        # Intersections between beggining / end of v1 or v2 and middle of v1/v2
        elif g1NextVertexIdx == -1 and g2PreviousVertexIdx != -1 and g2NextVertexIdx != -1:
            feat1 = self.checkIntersectionAndCreateFeature(vg1[g1PreviousVertexIdx], vg1[g1VertexIdx], vg2[g2PreviousVertexIdx], minA, maxA)
            feat2 = self.checkIntersectionAndCreateFeature(vg1[g1PreviousVertexIdx], vg1[g1VertexIdx], vg2[g2NextVertexIdx], minA, maxA)
            return feat1, feat2

        elif g1PreviousVertexIdx == -1 and g2PreviousVertexIdx != -1 and g2NextVertexIdx != -1:
            feat1 = self.checkIntersectionAndCreateFeature(vg1[g1NextVertexIdx], vg1[g1VertexIdx], vg2[g2PreviousVertexIdx], minA, maxA)
            feat2 = self.checkIntersectionAndCreateFeature(vg1[g1NextVertexIdx], vg1[g1VertexIdx], vg2[g2NextVertexIdx], minA, maxA)
            return feat1, feat2
        
        elif g2NextVertexIdx == -1 and g1PreviousVertexIdx != -1 and g1NextVertexIdx != -1:
            feat1 = self.checkIntersectionAndCreateFeature(vg2[g2PreviousVertexIdx], vg2[g2VertexIdx], vg1[g1PreviousVertexIdx], minA, maxA)
            feat2 = self.checkIntersectionAndCreateFeature(vg2[g2PreviousVertexIdx], vg2[g2VertexIdx], vg1[g1NextVertexIdx], minA, maxA)
            return feat1, feat2

        elif g2PreviousVertexIdx == -1 and g1PreviousVertexIdx != -1 and g1NextVertexIdx != -1:
            feat1 = self.checkIntersectionAndCreateFeature(vg2[g2NextVertexIdx], vg2[g2VertexIdx], vg1[g1PreviousVertexIdx], minA, maxA)
            feat2 = self.checkIntersectionAndCreateFeature(vg2[g2NextVertexIdx], vg2[g2VertexIdx], vg1[g1NextVertexIdx], minA, maxA)
            return feat1, feat2
        
        # Intersection in the middle of features
        elif all([g1PreviousVertexIdx != -1, g1NextVertexIdx!= -1, g2PreviousVertexIdx != -1, g2NextVertexIdx != -1]):
            feat1 = self.checkIntersectionAndCreateFeature(vg1[g1PreviousVertexIdx], vg1[g1VertexIdx], vg2[g2PreviousVertexIdx], minA, maxA)
            feat2 = self.checkIntersectionAndCreateFeature(vg1[g1PreviousVertexIdx], vg1[g1VertexIdx], vg2[g2NextVertexIdx], minA, maxA)
            feat3 = self.checkIntersectionAndCreateFeature(vg1[g1NextVertexIdx], vg1[g1VertexIdx], vg2[g2PreviousVertexIdx], minA, maxA)
            feat4 = self.checkIntersectionAndCreateFeature(vg1[g1NextVertexIdx], vg1[g1VertexIdx], vg2[g2NextVertexIdx], minA, maxA)
            return feat1, feat2, feat3, feat4

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return VerifyZAngles()

    def name(self):
        return 'Verify Z Angles'

    def displayName(self):
        return self.tr('Verify Z Angles')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("Verify Z Angles")
