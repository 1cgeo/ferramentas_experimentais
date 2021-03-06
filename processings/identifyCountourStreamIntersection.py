# -*- coding: utf-8 -*-

import os
import processing

import concurrent.futures

from qgis.core import (QgsFeature, QgsFeatureRequest, QgsFeatureSink, QgsField,
                       QgsFields, QgsProcessing, QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterVectorLayer, QgsSpatialIndex, QgsGeometry)
from qgis.PyQt.QtCore import QCoreApplication, QVariant


class IdentifyCountourStreamIntersection(QgsProcessingAlgorithm):

    INPUT_STREAM = 'INPUT_STREAM'
    INPUT_CONTOUR_LINES = 'INPUT_CONTOUR_LINES'
    OUTPUT = 'OUTPUT'
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_STREAM',
                self.tr('Selecione a camada contendo os trechos de drenagem'),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_COUNTOUR_LINES',
                self.tr('Selecione a camada contendo as curvas de nível'),
                types=[QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Flag Interseções Curva de Nível e Drenagem')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        streamLayerInput = self.parameterAsVectorLayer( parameters,'INPUT_STREAM', context )
        
        outputLinesSet, outputPointsSet = set(), set()
        countourLayer = self.parameterAsVectorLayer( parameters,'INPUT_COUNTOUR_LINES', context )

        feedback.setProgressText('Verificando inconsistencias ')
        
        multiStepFeedback = QgsProcessingMultiStepFeedback(7, feedback)
        multiStepFeedback.setCurrentStep(0)
        multiStepFeedback.pushInfo("Construindo estruturas auxiliares.")

        auxStreamLayerInput = self.runAddCount(streamLayerInput, feedback=multiStepFeedback)
        multiStepFeedback.setCurrentStep(1)
        self.runCreateSpatialIndex(auxStreamLayerInput, feedback=multiStepFeedback)
        
        multiStepFeedback.setCurrentStep(2)
        auxCountourLayer = self.runAddCount(countourLayer, feedback=multiStepFeedback)
        multiStepFeedback.setCurrentStep(3)
        self.runCreateSpatialIndex(auxCountourLayer, feedback=multiStepFeedback)
        multiStepFeedback.setCurrentStep(4)
        idDict = {feat['AUTO']: feat for feat in auxCountourLayer.getFeatures()}
        
        multiStepFeedback.setCurrentStep(5)
        multiStepFeedback.pushInfo("Realizando join espacial")
        spatialJoinOutput = self.runSpatialJoin(auxStreamLayerInput, auxCountourLayer, feedback=multiStepFeedback)
        
        multiStepFeedback.setCurrentStep(6)
        multiStepFeedback.pushInfo("Procurando problemas.")
        
        self.findProblems(multiStepFeedback, outputPointsSet, outputLinesSet, spatialJoinOutput, idDict)
                
        AllOK = True
        if outputPointsSet != set() :
            newLayer = self.outLayer(parameters, context, outputPointsSet, streamLayerInput, 1)
            AllOK = False
        if outputLinesSet != set():
            newLayer = self.outLayer(parameters, context, outputLinesSet, streamLayerInput, 2)
            AllOK = False
        if AllOK: 
            newLayer = 'nenhuma inconsistência verificada'
        return {self.OUTPUT: newLayer}

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

    def findProblems(self, feedback, outputPointsSet, outputLinesSet, inputLyr, idDict):
        total = 100.0 / inputLyr.featureCount() if inputLyr.featureCount() else 0
        def buildOutputs(riverFeat, feedback):
            if feedback.isCanceled():
                return
            riverGeom = riverFeat.geometry()
            if riverFeat['AUTO_2'] not in idDict:
                return
            countourGeom = idDict[riverFeat['AUTO_2']].geometry()
            intersection = countourGeom.intersection(riverGeom)
            if intersection.isEmpty() or intersection.wkbType() == 1:
                return
            if intersection.wkbType() == 4:
                outputPointsSet.add(intersection)
            if intersection.wkbType() in [2, 5]:
                outputLinesSet.add(intersection)
        
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

    def outLayer(self, parameters, context, geometry, streamLayer, geomtype):
        newFields = QgsFields()
        newFields.append(QgsField('id', QVariant.Int))

        (sink, newLayer) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            newFields,
            geomtype,
            streamLayer.sourceCrs()
        )
        idcounter = 1
        for geom in geometry:
            newFeat = QgsFeature()
            newFeat.setGeometry(geom)
            newFeat.setFields(newFields)
            newFeat['id'] = idcounter
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
            idcounter +=1
        return newLayer
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return IdentifyCountourStreamIntersection()

    def name(self):
        return 'identifycountourstreamintersection'

    def displayName(self):
        return self.tr('Identifica Múltiplas Interseções Entre Curva de Nível e Drenagem')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("Retorna interseções, diferentes de um único ponto, entre curvas de nível e drenagem")
    
