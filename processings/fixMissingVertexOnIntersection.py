# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
                        QgsProcessing,
                        QgsFeatureSink,
                        QgsProcessingAlgorithm,
                        QgsProcessingParameterFeatureSink,
                        QgsCoordinateReferenceSystem,
                        QgsProcessingParameterMultipleLayers,
                        QgsFeature,
                        QgsProcessingParameterVectorLayer,
                        QgsFields,
                        QgsFeatureRequest,
                        QgsProcessingParameterNumber,
                        QgsGeometry,
                        QgsPointXY,
                        QgsPoint
                    )
from qgis import processing
from qgis.utils import iface

class FixMissingVertexOnIntersection(QgsProcessingAlgorithm): 

    INPUT_LAYERS = 'INPUT_LAYER_LIST'
    INPUT_MIN_DIST= 'INPUT_MIN_DIST'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS,
                self.tr('Selecionar camadas'),
                QgsProcessing.TypeVectorLine
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.INPUT_MIN_DIST,
                self.tr('Insira o valor da distância'), 
                type=QgsProcessingParameterNumber.Double, 
                defaultValue = 1.0,
                minValue=0)
        )

    def processAlgorithm(self, parameters, context, feedback):      
        layerList = self.parameterAsLayerList(parameters, self.INPUT_LAYERS, context)
        minDist = self.parameterAsDouble(parameters, self.INPUT_MIN_DIST, context)

        for i in range(0, len(layerList)):
            for feat1 in layerList[i].getFeatures():
                feat1geom = feat1.geometry()
                request = QgsFeatureRequest().setFilterRect(feat1geom.boundingBox())
                for j in range(i, len(layerList)):
                    for feat2 in layerList[j].getFeatures(request):
                        feat2geom = feat2.geometry()
                        if feat1geom.intersects(feat2geom) and (i!=j or (i==j and feat1.id() > feat2.id())):
                            intersections = feat1geom.intersection(feat2geom)
                            for intersection in intersections.vertices():
                                intersection = self.closestCommonVertex(intersection,feat1geom,feat2geom, minDist)
                                if not self.checkVertex(intersection, feat1geom):
                                    newgeom1 = self.addVertex(intersection, feat1geom)
                                    self.updateLayerFeature(layerList[i], feat1, newgeom1)
                                if not self.checkVertex(intersection, feat2geom):
                                    newgeom2 = self.addVertex(intersection, feat2geom)
                                    self.updateLayerFeature(layerList[j], feat2, newgeom2)
        
        return {}


    def closestCommonVertex(self, intersection, geom1, geom2, dist):
        closest1 = geom1.closestVertex(QgsPointXY(intersection))
        closest2 = geom2.closestVertex(QgsPointXY(intersection))
        dist1 = QgsGeometry.fromPointXY(QgsPointXY(intersection)).distance(QgsGeometry.fromPointXY(closest1[0]))
        dist2 = QgsGeometry.fromPointXY(QgsPointXY(intersection)).distance(QgsGeometry.fromPointXY(closest2[0]))
        if dist1 < dist and  dist1 < dist2 :
            return QgsPoint(closest1[0])
        if dist2 < dist and  dist2 <= dist1 :
            return QgsPoint(closest2[0])

        return intersection

    def checkVertex(self, intersection, geom):
        closest = geom.closestVertex(QgsPointXY(intersection))
        return QgsGeometry.fromPointXY(closest[0]).intersects(QgsGeometry.fromPointXY(QgsPointXY(intersection)))

    def addVertex(self, point, geom):
        distance, p, after, orient = geom.closestSegmentWithContext( QgsPointXY( point ) )
        geom.insertVertex( point, after )
        return geom

    def updateLayerFeature(self, layer, feature, geometry):
        feature.setGeometry(geometry)
        layer.startEditing()
        layer.updateFeature(feature)

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return FixMissingVertexOnIntersection()

    def name(self):
        return 'fixmissingvertexonintersection'

    def displayName(self):
        return self.tr('Corrige vértice faltando na interseção')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo corrige os casos de feições linha se intersectando sem vértice em comum")
    
