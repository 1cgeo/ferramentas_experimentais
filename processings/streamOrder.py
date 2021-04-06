# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProject,
                       QgsMapLayer,
                       QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsProject,
                       QgsPointXY,
                       QgsProcessingParameterCrs,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterBoolean,
                       QgsProcessingRegistry,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterField,
                       QgsFeature,
                       QgsVectorLayer,
                       QgsPoint,
                       QgsGeometry,
                       QgsProcessingParameterVectorDestination,
                       QgsField,
                       QgsFields,
                       NULL
                       )
from qgis import processing
from qgis.analysis import QgsNativeAlgorithms

class StreamOrder(QgsProcessingAlgorithm):

    INPUT_STREAM = 'INPUT_STREAM'
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
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Camada de Saída')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        originalLayer = self.parameterAsVectorLayer( parameters,'INPUT_STREAM', context )
        featuresArray = self.createFeaturesArray(originalLayer)
        
        feedback.setProgressText('Verificando inconsistencias ')
        streamStartPoints = self.getLinesStartPoints(featuresArray)
        orderedFeatures = self.orderLines(featuresArray, streamStartPoints, 0)
        newLayer = self.orderedLayer(parameters, context, originalLayer, orderedFeatures)

        return {self.OUTPUT: newLayer}

    def createFeaturesArray(self, originalLayer):
        arrayFeatures = []
        features = originalLayer.getFeatures()

        for feature in features:
            arrayFeatures.append([feature,0])

        return arrayFeatures

    def getLinesStartPoints(self, featuresArray):
        startPointsList = []

        for feature in featuresArray:
            for geom in feature[0].geometry().constGet():
                if geom[0] not in startPointsList:
                    startPointsList.append(geom[0])

        return startPointsList

    def orderLines(self, featuresArray, streamStartPoints, order=0):
        newOrder = order+1
        actualLine = self.nextLine(featuresArray, streamStartPoints)
        
        for feature in featuresArray:
            if feature[0].attributes()[0] in actualLine:
                feature[1]= newOrder
                for geom in feature[0].geometry().constGet():
                    if geom[0] in streamStartPoints:
                        streamStartPoints.remove(geom[0])
                    if not len(streamStartPoints):
                        return featuresArray

        featuresArray=self.orderLines(featuresArray, streamStartPoints, newOrder)

        return featuresArray
        
    def nextLine(self, featuresArray, streamStartPoints):
        streamStartPointsCopy = streamStartPoints.copy()
        newLineList = []
        repeatedPoints = []

        for feature in featuresArray:
            attr = feature[-1]
            for geom in feature[0].geometry().constGet():
                if geom[-1] in streamStartPointsCopy  and (attr==0):
                    repeatedPoints.append(geom[-1])
            
        [streamStartPointsCopy.remove(point) for point in repeatedPoints if point in streamStartPointsCopy]

        for feature in featuresArray:
                for geom in feature[0].geometry().constGet():
                    if geom[0] in streamStartPointsCopy:
                        newLineList.append(feature[0].attributes()[0])
        return sorted(newLineList)
    
    def orderedLayer(self, parameters, context, originalLayer, orderedFeatures):

        newField = originalLayer.fields()
        #newField.append(QgsField('id', QVariant.Int))
        newField.append(QgsField('ordem', QVariant.Int))
        features = orderedFeatures

        (sink, newLayer) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            newField,
            originalLayer.wkbType(),
            originalLayer.sourceCrs()
        )
        
        for feature in features:
            newFeat = QgsFeature()
            newFeat.setGeometry(feature[0].geometry())
            newFeat.setFields(newField)
            for field in  range(len(feature[0].fields())):
                newFeat.setAttribute((field), feature[0].attribute((field)))
            newFeat['ordem'] = feature[-1]
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
        
        return newLayer

    def tr(self, string):

        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return streamOrder()

    def name(self):
        return 'ordenafluxo'

    def displayName(self):
        return self.tr('Ordenar Fluxo')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo orderna ou direciona fluxo, como linhas de drenagem ")
    
