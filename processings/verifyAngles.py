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
                defaultValue=20.0
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
        minA = self.parameterAsDouble(parameters, self.ANGLE, context)
        maxA = 360 - minA

        crs = QgsProject.instance().crs()
        self.fields = QgsFields()
        self.fields.append(QgsField('source', QVariant.String))

        sink, _ = self.parameterAsSink(parameters, self.OUTPUT, context, self.fields,
            QgsWkbTypes.Point, crs)

        featsToAnalyse = [
            *self.caseInternLine(lines, minA, maxA),
            *self.caseInternArea(areas, minA, maxA),
            *self.caseBetweenLines(lines, minA, maxA)
            ]
        sink.addFeatures(featsToAnalyse)

        return {
            self.OUTPUT: sink
            }

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
                        newFeat.setAttribute('source',layer.name())
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
                            newFeat.setAttribute('source',layer.name())
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
                        if i!=j or (i==j and feat1.id() != feat2.id()):
                            gfeat2 = feat2.geometry()
                            if gfeat1.intersects(gfeat2):
                                toAnalyse = self.checkIfIntersectionIsValid(gfeat1, gfeat2, minA, maxA)
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

    def checkIntersectionAndCreateFeature(self, v1, v2, v3, minA, maxA):
        angle = QgsGeometryUtils.angleBetweenThreePoints(v1.x(), v1.y(), v2.x(), v2.y(), v3.x(), v3.y())
        angle = math.degrees(angle)
        if angle > maxA or angle < minA:
            newFeat = QgsFeature(self.fields)
            if isinstance(v1, QgsPoint):
                newFeat.setGeometry(v2)
            elif isinstance(v1, QgsPointXY):
                newFeat.setGeometry(v2)
            return newFeat

    def checkIfIntersectionIsValid(self, g1, g2, minA, maxA):
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
        return VerifyAngles()

    def name(self):
        return 'Verify Angles'

    def displayName(self):
        return self.tr('Verify Angles')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("Verify Angles")
