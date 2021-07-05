# -*- coding: utf-8 -*-

import processing

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
    
    def buildSpatialIndexAndIdDict(self, inputLyr, feedback=None):
        """
        creates a spatial index for the centroid layer
        """
        spatialIdx = QgsSpatialIndex()
        idDict = {}
        size = 100.0 / inputLyr.featureCount() if inputLyr.featureCount() else 0
        buildLambda = lambda x: self.buildSpatialIndexAndIdDictEntry(
            x[0], x[1], spatialIdx, idDict, size, feedback)
        list(
            map(buildLambda, enumerate(inputLyr.getFeatures()))
        )
        return spatialIdx, idDict

    def buildSpatialIndexAndIdDictEntry(self, current, feat, spatialIdx, idDict, size, feedback):
        if feedback is not None and feedback.isCanceled():
            return
        spatialIdx.addFeature(feat)
        idDict[feat.id()] = feat
        if feedback is not None:
            feedback.setProgress(size * current)
        

    def processAlgorithm(self, parameters, context, feedback):

        streamLayerInput = self.parameterAsVectorLayer( parameters,'INPUT_STREAM', context )
        
        outputLinesSet, outputPointsSet = set(), set()
        countourLayer = self.parameterAsVectorLayer( parameters,'INPUT_COUNTOUR_LINES', context )

        feedback.setProgressText('Verificando inconsistencias ')
        
        multiStepFeedback = QgsProcessingMultiStepFeedback(3, feedback)
        multiStepFeedback.setCurrentStep(0)
        multiStepFeedback.pushInfo("Construindo estruturas auxiliares.")
        idDict = {feat['id']: feat for feat in countourLayer.getFeatures()}
        
        multiStepFeedback.setCurrentStep(1)
        multiStepFeedback.pushInfo("Realizando join espacial")
        spatialJoinOutput = self.runSpatialJoin(streamLayerInput, countourLayer, feedback=multiStepFeedback)
        
        multiStepFeedback.setCurrentStep(2)
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
                'DISCARD_NONMATCHING': False,
                'PREFIX': '',
                'OUTPUT': 'TEMPORARY_OUTPUT' 
            },
            feedback=feedback
        )
        return output['OUTPUT']

    def findProblems(self, feedback, outputPointsSet, outputLinesSet, inputLyr, idDict):
        total = 100.0 / inputLyr.featureCount() if inputLyr.featureCount() else 0
        def buildOutputs(countour, riverGeom, feedback):
            if feedback.isCanceled():
                return
            countourGeom = countour.geometry()
            if not countourGeom.intersects(riverGeom):
                return
            intersection = countourGeom.intersection(riverGeom)
            if intersection.isEmpty() or intersection.wkbType() == 1:
                return
            if intersection.wkbType() == 4:
                outputPointsSet.add(intersection)
            if intersection.wkbType() in [2, 5]:
                outputLinesSet.add(intersection)

        for current, feat in enumerate(inputLyr.getFeatures()):
            if feedback is not None and feedback.isCanceled():
                break
            geom = feat.geometry()
            if feat['id_2'] not in idDict:
                feedback.setProgress(int(current * total))
                continue
            candidateContour = idDict[feat['id_2']]
            buildOutputs(candidateContour, geom, feedback)
            if feedback is not None:
                feedback.setProgress(int(current * total))



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
    
