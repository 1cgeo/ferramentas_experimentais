# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterVectorLayer,
                       QgsFeature,
                       QgsField,
                       QgsGeometry,
                       QgsPointXY
                       )

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
        self.orderLines(featuresArray, streamStartPoints, 0)
        newLayer = self.orderedLayer(parameters, context, originalLayer, featuresArray)

        return {self.OUTPUT: newLayer}

    def createFeaturesArray(self, originalLayer):
        arrayFeatures = []
        features = originalLayer.getFeatures()

        for feature in features:
            arrayFeatures.append([feature,0])

        return arrayFeatures

    def getLinesStartPoints(self, featuresArray):
        startPointsList = []
        pointControl = []
        for feature in featuresArray:
            for geom in feature[0].geometry().constGet():
                if geom[0] not in pointControl:
                    startPointsList.append(QgsGeometry.fromPointXY(QgsPointXY(geom[0])))
                    pointControl.append(geom[0])

        return startPointsList

    def orderLines(self, featuresArray, streamStartPoints, order=0):
        if order ==0:
            self.verticesIntersectOneRiver(featuresArray, streamStartPoints)
            order +=1
            self.orderLines(featuresArray, streamStartPoints, 1)
        if len(streamStartPoints)==0:
            return False
        while (not len(streamStartPoints)==0):
            self.verticesIntersectUnknownOrderRiver(featuresArray, streamStartPoints)

        return False
    def verticesIntersectOneRiver(self, featuresArray, streamStartPoints):
        toBeRemoved = []
        for point in streamStartPoints:
            riversIntersected = []
            for riverIndex in range(len(featuresArray)):
                river  =featuresArray[riverIndex]
                if point.intersects(river[0].geometry()):
                    riversIntersected.append(riverIndex)
            if len(riversIntersected)==1:
                featuresArray[riversIntersected[0]][1]=1
                toBeRemoved.append(point)
        for pt in toBeRemoved:
            streamStartPoints.remove(pt)
        return False
    def verticesIntersectUnknownOrderRiver(self, featuresArray, streamStartPoints):
        toBeRemoved = []
        for point in streamStartPoints:
            maxOrder = 0
            riversIntersected = []
            riverUnknownOrderIntersected = []
            intersectsEndOfUnknownRiver = False
            for riverIndex in range(len(featuresArray)):
                river  =featuresArray[riverIndex]
                if point.intersects(river[0].geometry()):
                    riversIntersected.append(riverIndex)
                    if river[1]>maxOrder:
                        maxOrder = river[1]
                    for geom in river[0].geometry().constGet():
                        ptIni = QgsGeometry.fromPointXY(QgsPointXY(geom[0]))
                        ptFin = QgsGeometry.fromPointXY(QgsPointXY(geom[-1]))
                    if river[1]==0 and point.intersects(ptFin):
                        intersectsEndOfUnknownRiver = True
                    if river[1]==0 and point.intersects(ptIni):
                        riverUnknownOrderIntersected.append(riverIndex)
            if (not len(riverUnknownOrderIntersected)==0) and (not len(riversIntersected)==len(riverUnknownOrderIntersected)) and (not intersectsEndOfUnknownRiver):
                for riverUnkownOrder in riverUnknownOrderIntersected:
                    featuresArray[riverUnkownOrder][1]=maxOrder+1
                toBeRemoved.append(point)
        for pt in toBeRemoved:
            streamStartPoints.remove(pt)
        return False
    
    def orderedLayer(self, parameters, context, originalLayer, orderedFeatures):

        newField = originalLayer.fields()
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
        return StreamOrder()

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
    
