# -*- coding: utf-8 -*-

import os
import processing

import concurrent.futures

from qgis.core import (QgsFeature, QgsFeatureRequest, QgsFeatureSink, QgsField,
                       QgsFields, QgsProcessing, QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterMultipleLayers,
                       QgsCoordinateReferenceSystem, QgsWkbTypes,
                       QgsProcessingParameterVectorLayer, QgsSpatialIndex, QgsGeometry)
from qgis.PyQt.QtCore import QCoreApplication, QVariant

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

    def runSpatialJoin(self, streamLayerInput, countourLayer, feedback):
        output = processing.run(
            'native:joinattributesbylocation',
            {
                'INPUT': streamLayerInput,
                'JOIN': countourLayer,
                'PREDICATE': [0],
                'JOIN_FIELDS': [],
                'METHOD': 0,
                'DISCARD_NONMATCHING': True,
                'PREFIX': '',
                'OUTPUT': 'TEMPORARY_OUTPUT' 
            },
            feedback=feedback
        )
        return output['OUTPUT']

    def runAddCount(self, inputLyr, feedback):
        output = processing.run(
            "native:addautoincrementalfield",
            {
                'INPUT':inputLyr,
                'FIELD_NAME':'AUTO',
                'START':0,
                'GROUP_FIELDS':[],
                'SORT_EXPRESSION':'',
                'SORT_ASCENDING':False,
                'SORT_NULLS_FIRST':False,
                'OUTPUT':'TEMPORARY_OUTPUT'
            },
            feedback=feedback
        )
        return output['OUTPUT']

    def runCreateSpatialIndex(self, inputLyr, feedback):
        processing.run(
            "native:createspatialindex",
            {'INPUT':inputLyr},
            feedback=feedback
        )

    def findOverlaps(self, feedback, output, inputLyr, idDict, i, j, geomType):
        total = 100.0 / inputLyr.featureCount() if inputLyr.featureCount() else 0
        def buildOutputs(feat1, feedback):
            if feedback.isCanceled():
                return
            feat1Geom = feat1.geometry()
            if feat1['AUTO_2'] not in idDict:
                return
            feat2Geom = idDict[feat1['AUTO_2']].geometry()
            if (i!=j or (i==j and feat1['AUTO_2'] > feat1['AUTO'])) and feat1geom.intersects(feat2geom):
                intersections = feat1geom.intersection(feat2geom)
                if intersections.type() == geomType:
                    if intersections.isMultipart():
                        output.extend(intersections.asGeometryCollection())
                    else:
                        output.append(intersections)
        
        buildOutputsLambda = lambda x: buildOutputs(x, feedback)
        
        pool = concurrent.futures.ThreadPoolExecutor(os.cpu_count())
        futures = set()
        current_idx = 0
        
        for feat in inputLyr.getFeatures():
            if feedback is not None and feedback.isCanceled():
                break
            futures.add(pool.submit(buildOutputsLambda, feat))
        
        for x in concurrent.futures.as_completed(futures):
            if feedback is not None and feedback.isCanceled():
                break
            feedback.setProgress(current_idx * total)
            current_idx += 1


    def pairLayersForVerification(self, feedback, layerList, overlaps, geomType):
        auxLayerList = []
        idDictList = []
        for i in range(0, len(layerList)):
            auxLayer = self.runAddCount(layerList[i], feedback=feedback)
            self.runCreateSpatialIndex(auxLayer, feedback=feedback)
            auxLayerList.append(auxLayer)
            idDict = {feat['AUTO']: feat for feat in auxLayer.getFeatures()}
            idDictList.append(idDict)

        for i in range(0, len(auxLayerList)):
            for j in range(i, len(auxLayerList)):
                spatialJoinOutput = self.runSpatialJoin(auxLayerList[i], auxLayerList[j], feedback=feedback)
                self.findOverlaps(feedback, overlaps, spatialJoinOutput, idDictList[j], i , j, geomType)



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
        multiStepFeedback = QgsProcessingMultiStepFeedback(2, feedback)
        multiStepFeedback.setCurrentStep(0)
        multiStepFeedback.pushInfo("Verificando linhas.")
        if len(layerListlinha) > 0:
            overlaps_l = []
            self.pairLayersForVerification(multiStepFeedback, layerListlinha, overlaps_l, QgsWkbTypes.LineGeometry)
            self.addSink(overlaps_l, sink_l, fields)


        multiStepFeedback.setCurrentStep(1)
        multiStepFeedback.pushInfo("Verificando áreas.")

        if len(layerListpol) > 0:
            overlaps_a = []
            self.pairLayersForVerification(multiStepFeedback, layerListpol, overlaps_a, QgsWkbTypes.PolygonGeometry)
            self.addSink(overlaps_a, sink_a, fields)

        return {self.OUTPUT_L: sinkId_l, self.OUTPUT_A: sinkId_a}


    def addSink(self, geometries, sink, fields):
        for geom in geometries:
            newFeat = QgsFeature(fields)
            newFeat.setGeometry(geom)
            newFeat['erro'] = 'Overlap incorreto'
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
        
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
    
