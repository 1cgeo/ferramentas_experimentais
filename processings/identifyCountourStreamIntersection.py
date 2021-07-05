# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterVectorLayer,
                       QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsFeatureRequest
                       )

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
        total = 100.0 / streamLayerInput.featureCount() if streamLayerInput.featureCount() else 0

        feedback.setProgressText('Verificando inconsistencias ')
        
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

        for current, river in enumerate(streamLayerInput.getFeatures()):
            if feedback is not None and feedback.isCanceled():
                break
            riverGeom = river.geometry()
            AreaOfInterest = riverGeom.boundingBox()
            request = QgsFeatureRequest().setFilterRect(AreaOfInterest)
            buildOutputsLambda = lambda x: buildOutputs(x, riverGeom, feedback)
            list(map(buildOutputsLambda, countourLayer.getFeatures(request)))
            if feedback is not None:
                feedback.setProgress(int(current * total))
                
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
    
