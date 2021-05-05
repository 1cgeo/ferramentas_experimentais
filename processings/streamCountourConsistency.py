# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsPointXY,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterBoolean,
                       QgsProcessingRegistry,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsFeature,
                       QgsField
                       )
from qgis import processing

class StreamCountourConsistency(QgsProcessingAlgorithm):

    INPUT_STREAM = 'INPUT_STREAM'
    INPUT_CONTOUR_LINES = 'INPUT_CONTOUR_LINES'
    INPUT_STREAM_ID_FIELD = 'INPUT_STREAM_ID_FIELD'
    INPUT_COUNTOUR_ID_FIELD = 'INPUT_COUNTOUR_ID_FIELD'
    INPUT_LEVES_FIELD = 'INPUT_LEVES_FIELD'
    INPUT_LEVEL_GAP = 'INPUT_LEVEL_GAP'
    OUTPUT = 'OUTPUT'
    OUTPUT_NEW_LAYER = 'OUTPUT_NEW_LAYER'
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_STREAM',
                self.tr('Selecione a camada contendo os trechos de drenagem'),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                'INPUT_STREAM_ID_FIELD',
                self.tr('Selecione o campo que contém as chaves primárias das linhas de drenagem'), 
                type=QgsProcessingParameterField.Any, 
                parentLayerParameterName='INPUT_STREAM', 
                allowMultiple=False, 
                defaultValue='id')
            )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_COUNTOUR_LINES',
                self.tr('Selecione a camada contendo as curvas de nível'),
                types=[QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                'INPUT_LEVES_FIELD',
                self.tr('Selecione o campo que contém as cotas das curvas de nível'), 
                type=QgsProcessingParameterField.Numeric, 
                parentLayerParameterName='INPUT_COUNTOUR_LINES', 
                allowMultiple=False, 
                defaultValue='cota')
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                'INPUT_LEVEL_GAP',
                self.tr('Insira o valor da equidistância entre as cotas das curvas de nível'), 
                type=QgsProcessingParameterNumber.Double, 
                minValue=0)
            )
        
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Camada de Inconsistências:')
            )
        ) 

    def processAlgorithm(self, parameters, context, feedback):

        streamLayerInput = self.parameterAsVectorLayer( parameters,'INPUT_STREAM', context )
        
        streamLayerOrdered = self.orderAndAddFieldToLayer(context, feedback, streamLayerInput)
        outputPoints = []
        streamIdField = self.parameterAsFields( parameters,'INPUT_STREAM_ID_FIELD', context )[0]
        countourLayer = self.parameterAsVectorLayer( parameters,'INPUT_COUNTOUR_LINES', context )
        levelsField = self.parameterAsFields( parameters,'INPUT_LEVES_FIELD', context )[0]
        levelGap = self.parameterAsDouble (parameters,'INPUT_LEVEL_GAP', context) 

        ordemIndex = streamLayerOrdered.fields().indexFromName('ordem')
        maxOrder = streamLayerOrdered.maximumValue(ordemIndex)

        streamLayerFeatures = self.createFeaturesArray(streamLayerOrdered)
        countourLayerFeatures = self.createFeaturesArray(countourLayer)
        intersectionsNoDist = self.intersectionsPoints(context, feedback, streamLayerOrdered, countourLayer)
        intersectionsPoints = self.addDistField(streamLayerFeatures, intersectionsNoDist,  streamIdField)
        feedback.setProgressText('Verificando inconsistencias ')
        outPoints = self.intersectPointOrderCheck(streamLayerFeatures, intersectionsPoints, streamIdField, levelsField, levelGap, outputPoints, maxOrder)
        if outPoints:
            newLayer = self.outLayer(parameters, context, outPoints, streamLayerOrdered)
        else: 
            newLayer = 'nenhuma inconsistência verificada'
        return {self.OUTPUT: newLayer}


    def orderAndAddFieldToLayer(self, context, feedback, streamLayer):
        streamLayerOrdered = context.takeResultLayer(processing.run('FerramentasExperimentaisProvider:ordenafluxo', 
                {
                    'INPUT_STREAM': streamLayer,
                    'OUTPUT': 'memory:'
                },
                is_child_algorithm=True,
                context=context,
                feedback=feedback)['OUTPUT'])
        pr = streamLayerOrdered.dataProvider()
        attr = pr.addAttributes([QgsField('dist', QVariant.Double)])
        streamLayerOrdered.updateFields()
        return streamLayerOrdered

    def createFeaturesArray(self, originalLayer):
        arrayFeatures = []
        features = originalLayer.getFeatures()

        for feature in features:
            arrayFeatures.append(feature)

        return arrayFeatures

    def intersectionsPoints(self, context, feedback, streamLayer, countourLayer):
        intersectionLayerStr = processing.run (
                'qgis:lineintersections',
                {
                    'INPUT': streamLayer,
                    'INTERSECT': countourLayer,
                    'OUTPUT': 'memory:'
                },
                is_child_algorithm=True,
                context=context,
                feedback=feedback)['OUTPUT']
        intersectionLayer = context.takeResultLayer(intersectionLayerStr)
        return self.createFeaturesArray(intersectionLayer)

    def addDistField(self, streamLayerFeatures, intersectionsNoDist, streamIdField):
        pointsList = []
        for line in streamLayerFeatures:
            points = self.getPointFromLine(intersectionsNoDist, line[streamIdField], streamIdField)
            for point in points:
                dist = line.geometry().lineLocatePoint(point.geometry())
                point['dist']=dist
                pointsList.append(point)
        return pointsList

    def getPointFromLine(self, pointList, lineId, pointIdField):
        pointsSelected = []
        for point in pointList:
            if point[pointIdField] == lineId:
                pointsSelected.append(point)
        return pointsSelected

    def intersectPointOrderCheck(self, streamLayerFeatures, intersectionPoints, streamIdField, levelsField, levelGap, outputPoints, maxOrder, order=0):
        order += 1
        if order == (maxOrder+1):
            return False

        lines, linesIdList = self.getLineFromOrder(streamLayerFeatures, streamIdField, order)
        self.checkPointOnLineAddLastPoint(streamLayerFeatures, lines, intersectionPoints, streamIdField, levelsField, levelGap, linesIdList,outputPoints)        
        if not len(outputPoints) == 0:
            return outputPoints
        self.intersectPointOrderCheck(streamLayerFeatures, intersectionPoints, streamIdField, levelsField, levelGap, outputPoints, maxOrder, order)
        return outputPoints
    
    def getLineFromOrder(self, streamLayerFeatures, streamIdField, order):
        linesSelected = []
        lineIdList = []
        for line in streamLayerFeatures:
            if line['ordem'] == order:
                linesSelected.append(line)
                lineIdList.append(line[streamIdField])
        return linesSelected, lineIdList

    def checkPointOnLineAddLastPoint(self, streamLayerFeatures, lines, intersectionPoints, streamIdField,levelsField, levelGap, linesIdList, outputPoints):
        for lineId in linesIdList:
            pointList = []
            for point in intersectionPoints:
                if point[streamIdField] == lineId:
                    pointList.append(point)
            
            if len(pointList)<1:
                continue
            pointList.sort(key = lambda p: p['dist'])
            for position in range (len(pointList)):
                if len(pointList)<2:
                    continue
                if not position:
                    continue
                diff = pointList[position-1][levelsField] - pointList[position][levelsField]
                if not ( diff == levelGap):    
                    outputPoints.append(pointList[position-1])
                    outputPoints.append(pointList[position])
            lastIntersectionPoint = pointList[-1]
            self.addToPointsList(streamLayerFeatures, lines, intersectionPoints, lastIntersectionPoint, streamIdField, levelsField, outputPoints)
        return True

    def addToPointsList(self, streamLayerFeatures, lines, intersectionPoints, pointToAdd, streamIdField, levelsField, outputPoints):
        newPoint = QgsFeature()
        newPoint.setFields(pointToAdd.fields())
        newPoint.setAttributes(pointToAdd.attributes())

        alreadyInList = False
        for line in lines:
            if pointToAdd[streamIdField] == line[streamIdField]:
                for geom in line.geometry().constGet():
                    newPoint.setGeometry(geom[-1])

        for point in intersectionPoints:
            if not (str(newPoint.geometry())==str(point.geometry())):
                continue
            if not newPoint[levelsField] == point[levelsField]:
                outputPoints.append(point)
                outputPoints.append(pointToAdd)
                continue
            alreadyInList  = True

        if not alreadyInList:
            self.lastPointToFirstPoint(newPoint, streamLayerFeatures, intersectionPoints, streamIdField, outputPoints)
        return True

    def lastPointToFirstPoint(self, point, streamLayerFeatures, intersectionPoints, streamIdField, outputPoints):
        for line in streamLayerFeatures:
            if line['ordem']<point['ordem']:
                continue
            for geom in line.geometry().constGet():
                if QgsPointXY(geom[0]) == point.geometry().asPoint():
                    newIntersection = QgsFeature()
                    newIntersection.setFields(point.fields())
                    newIntersection.setAttributes(point.attributes())
                    newIntersection.setGeometry(geom[0])
                    newIntersection[streamIdField] = line[streamIdField]
                    newIntersection['dist'] = 0
                    newIntersection['ordem'] = line['ordem']
                    intersectionPoints.append(newIntersection)
                    break
        return False

    def outLayer(self, parameters, context, points, streamLayer):
        newFields = points[0].fields()

        (sink, newLayer) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            newFields,
            1, #point
            streamLayer.sourceCrs()
        )
        
        for point in points:
            newFeat = QgsFeature()
            newFeat.setGeometry(point.geometry())
            newFeat.setFields(newFields)
            for field in  range(len(point.fields())):
                newFeat.setAttribute((field), point.attribute((field)))
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
        
        return newLayer
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return StreamCountourConsistency()

    def name(self):
        return 'consistenciafluxonivel'

    def displayName(self):
        return self.tr('Consistência entre Fluxo e Curva de Nível')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo verifica a consistência entre uma camada de fluxo (drenagem) em relação a outra contendo curvas de nível")
    
