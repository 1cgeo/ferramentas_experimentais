# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.Qt import QVariant
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
                        QgsField,
                        QgsFeatureRequest,
                        QgsProcessingParameterNumber,
                        QgsGeometry,
                        QgsPointXY,
                        QgsPoint,
                        QgsWkbTypes
                    )
from qgis import processing
from qgis.utils import iface

class IdentifyOverlaps(QgsProcessingAlgorithm): 

    INPUT_LAYERS_L = 'INPUT_LAYERS_L'
    INPUT_LAYERS_A = 'INPUT_LAYERS_A'
    OUTPUT_L = 'OUTPUT_L'
    OUTPUT_A = 'OUTPUT_A'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS_L,
                self.tr('Selecionar camadas linha'),
                QgsProcessing.TypeVectorLine,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS_A,
                self.tr('Selecionar camadas polígono'),
                QgsProcessing.TypeVectorPolygon,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_L,
                self.tr('Flag overlap de linhas')
            )
        ) 
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_A,
                self.tr('Flag overlap de polígonos')
            )
        ) 

    def processAlgorithm(self, parameters, context, feedback):      
        layerListlinha = self.parameterAsLayerList(parameters, self.INPUT_LAYERS_L, context)
        layerListpol = self.parameterAsLayerList(parameters, self.INPUT_LAYERS_A, context)

        CRSstr = iface.mapCanvas().mapSettings().destinationCrs().authid()
        CRS = QgsCoordinateReferenceSystem(CRSstr)

        fields = QgsFields()
        fields.append(QgsField('erro', QVariant.String))


        (sink_l, sinkId_l) = self.parameterAsSink(
            parameters,
            self.OUTPUT_L,
            context,
            fields,
            5,
            CRS
        )

        (sink_a, sinkId_a) = self.parameterAsSink(
            parameters,
            self.OUTPUT_A,
            context,
            fields,
            6,
            CRS
        )

        if len(layerListlinha) > 0:
            overlaps_l = []
            for i in range(0, len(layerListlinha)):
                for feat1 in layerListlinha[i].getFeatures():
                    feat1geom = feat1.geometry()
                    request = QgsFeatureRequest().setFilterRect(feat1geom.boundingBox())
                    for j in range(i, len(layerListlinha)):
                        for feat2 in layerListlinha[j].getFeatures(request):
                            feat2geom = feat2.geometry()
                            if feat1geom.intersects(feat2geom) and (i!=j or (i==j and feat1.id() > feat2.id())):
                                intersections = feat1geom.intersection(feat2geom)
                                if intersections.type() == QgsWkbTypes.LineGeometry:
                                    if intersections.isMultipart():
                                        overlaps_l.extend(intersections.asGeometryCollection())
                                    else:
                                        overlaps_l.append(intersections)

            self.addSink(overlaps_l, sink_l, fields)

        if len(layerListpol) > 0:
            overlaps_a = []
            for i in range(0, len(layerListpol)):
                for feat1 in layerListpol[i].getFeatures():
                    feat1geom = feat1.geometry()
                    request = QgsFeatureRequest().setFilterRect(feat1geom.boundingBox())
                    for j in range(i, len(layerListpol)):
                        for feat2 in layerListpol[j].getFeatures(request):
                            feat2geom = feat2.geometry()
                            if feat1geom.intersects(feat2geom) and (i!=j or (i==j and feat1.id() > feat2.id())):
                                intersections = feat1geom.intersection(feat2geom)
                                if intersections.type() == QgsWkbTypes.PolygonGeometry:
                                    if intersections.isMultipart():
                                        overlaps_a.extend(intersections.asGeometryCollection())
                                    else:
                                        overlaps_a.append(intersections)

            self.addSink(overlaps_a, sink_a, fields)

        return {self.OUTPUT_L: sinkId_l, self.OUTPUT_A: sinkId_a}


    def addSink(self, geometries, sink, fields):
        for geom in geometries:
            newFeat = QgsFeature(fields)
            newFeat.setGeometry(geom)
            newFeat['erro'] = 'Overlap incorreto'
            sink.addFeature(newFeat)
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return IdentifyOverlaps()

    def name(self):
        return 'identifyOverlaps'

    def displayName(self):
        return self.tr('Identifica overlaps')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo identifica overlaps entre feições da mesma geometria")
    
