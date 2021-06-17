# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsPointXY,
                       QgsProcessingParameterVectorLayer,
                       QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsGeometry,
                       NULL
                       )
from qgis import processing

class VerifyTransports(QgsProcessingAlgorithm):

    INPUT_STREAM = 'INPUT_STREAM'
    INPUT_DAM_LINE = 'INPUT_DAM_LINE'
    INPUT_ROADS = 'INPUT_ROADS'
    INPUT_ROADS_ELEM_POINT = 'INPUT_ROADS_ELEM_POINT'
    INPUT_ROADS_ELEM_LINE = 'INPUT_ROADS_ELEM_LINE'
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
                'INPUT_ROADS_ELEM_POINT',
                self.tr('Selecione a camada contendo os elementos viários (pontos)'), 
                types=[QgsProcessing.TypeVectorPoint]
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_ROADS_ELEM_LINE',
                self.tr('Selecione a camada contendo os elementos viários (linhas)'), 
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_ROADS',
                self.tr('Selecione a camada contendo as vias de deslocamento'), 
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_DAM_LINE',
                self.tr('Selecione a camada contendo as barragens'),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Flag Verificar Transportes')
            )
        ) 

    def processAlgorithm(self, parameters, context, feedback):

        streamLayerInput = self.parameterAsVectorLayer( parameters,'INPUT_STREAM', context )
        outputPoints = []
        outputLines = []
        roadslayer = self.parameterAsVectorLayer( parameters,'INPUT_ROADS', context )
        roadElemPointLayer = self.parameterAsVectorLayer( parameters,'INPUT_ROADS_ELEM_POINT', context )
        roadElemLineLayer = self.parameterAsVectorLayer( parameters,'INPUT_ROADS_ELEM_LINE', context )
        damLineLayer = self.parameterAsVectorLayer( parameters,'INPUT_DAM_LINE', context )
        roadslayerFeatures = self.createFeaturesArray(roadslayer)
        roadElemPointLayerFeatures = self.createFeaturesArray(roadElemPointLayer)
        damLineFeatures = self.createFeaturesArray(damLineLayer)
        roadElemLineLayerFeatures = self.createFeaturesArray(roadElemLineLayer)
        feedback.setProgressText('Verificando inconsistencias ')
        step =1
        progressStep = 100/3
        RSintersections = self.roadStreamIntersection(roadslayer, streamLayerInput, context, feedback)
        feedback.setProgress( step * progressStep )
        self.verifRoadElem(roadslayerFeatures, roadElemPointLayerFeatures, roadElemLineLayerFeatures, RSintersections, outputPoints, outputLines, feedback, step, progressStep)
        step +=1
        feedback.setProgress( step * progressStep )
        self.verifDamRoad(roadslayerFeatures, damLineFeatures, outputLines, feedback, step, progressStep)
        step +=1
        feedback.setProgress( step * progressStep )
        if feedback.isCanceled():
            return {self.OUTPUT: 'execução cancelada pelo usuário'}
        
        allOK = True
        if not len(outputPoints)==0 :
            newLayer = self.outLayer(parameters, context, outputPoints, streamLayerInput, 1)
            allOK = False
        
        if not len(outputLines)==0 :
            newLayer = self.outLayer(parameters, context, outputLines, streamLayerInput, 2)
            allOK = False
        
        
        if allOK:
            newLayer = 'nenhuma inconsistência verificada'
        
        return {self.OUTPUT: newLayer}

    def createFeaturesArray(self, originalLayer):
        arrayFeatures = []
        features = originalLayer.getFeatures()

        for feature in features:
            arrayFeatures.append(feature)
            
        return arrayFeatures

    def verifRoadElem(self, roadslayerFeatures, roadElemPointLayerFeatures, roadElemLineLayerFeatures, RSintersections, outputPoints, outputLines,feedback, step, progressStep):
        ponte = 200
        bueiro = 500
        vau = 400
        auxProgressStep = len(roadElemPointLayerFeatures) + len(roadElemLineLayerFeatures)
        for count,roadElemPoint in enumerate(roadElemPointLayerFeatures):
            auxstep = count+1
            if roadElemPoint['tipo'] is NULL:
                feedback.setProgress( step*(1+(auxstep/auxProgressStep)) * progressStep )
                continue
            elemType = roadElemPoint['tipo']-roadElemPoint['tipo']%100
            
            isOnIntersection = False
            if elemType in [ponte, vau, bueiro]:
                for inter in RSintersections:
                    if roadElemPoint.geometry().intersects(inter.geometry()):
                        isOnIntersection = True
                if not isOnIntersection:
                    outputPoints.append([roadElemPoint.geometry(), 1])
            feedback.setProgress( step*(1+(auxstep/auxProgressStep)) * progressStep )
        for count,roadElemLine in enumerate(roadElemLineLayerFeatures):
            auxstep = count+1
            if roadElemLine['tipo'] ==NULL:
                feedback.setProgress( step*(1+((auxstep+len(roadElemPointLayerFeatures))/auxProgressStep)) * progressStep )
                continue
            elemType = roadElemLine['tipo']-((roadElemLine['tipo'])%100)
            interIni = False
            interFin = False
            for geometry in roadElemLine.geometry().constGet():
                ptIni = QgsGeometry.fromPointXY(QgsPointXY(geometry[0]))
                ptFin = QgsGeometry.fromPointXY(QgsPointXY(geometry[-1]))
            for road in roadslayerFeatures:
                if elemType == ponte:
                    if road.geometry().intersects(roadElemLine.geometry()):
                        if not roadElemLine.geometry().within(road.geometry()):
                            outputLines.append([roadElemLine.geometry(), 2])
                if elemType == vau:        
                    if roadElemLine.geometry().crosses(road.geometry()) or roadElemLine.geometry().within(road.geometry()) or roadElemLine.geometry().overlaps(road.geometry()):
                        outputLines.append([roadElemLine.geometry(), 3])
                    if ptIni.intersects(road.geometry()):
                        interIni = True
                    if ptFin.intersects(road.geometry()):
                        interFin = True
            if elemType == vau:
                if not(interIni and interFin):
                    outputLines.append([roadElemLine.geometry(), 4])
            feedback.setProgress( step*(1+((auxstep+len(roadElemPointLayerFeatures))/auxProgressStep)) * progressStep )
        return False
    
    def verifDamRoad(self, roadslayerFeatures, damLineFeatures, outputLines, feedback, step, progressStep):
        for count,dam in enumerate(damLineFeatures):
            auxstep = count+1
            for road in roadslayerFeatures:
                DRintersect = dam.geometry().intersection(road.geometry())
                if dam['em_via_deslocamento']==1:
                    if not (DRintersect.isNull() or DRintersect.isEmpty() or DRintersect.type() in [1,4]):
                        if not dam.geometry().within(road.geometry()):
                            outputLines.append([dam.geometry(), 5])
                if dam['em_via_deslocamento']==2:
                    if dam.geometry().crosses(road.geometry()) or dam.geometry().within(road.geometry()) or dam.geometry().overlaps(road.geometry()):
                        outputLines.append([dam.geometry(), 6])
            feedback.setProgress( step*(1+((auxstep)/len(damLineFeatures))) * progressStep )
        return False
    def roadStreamIntersection(self, roadslayer, streamLayerInput, context, feedback):
        intersectionLayerStr = processing.run (
                'qgis:lineintersections',
                {
                    'INPUT': streamLayerInput,
                    'INTERSECT': roadslayer,
                    'OUTPUT': 'memory:'
                },
                is_child_algorithm=True,
                context=context,
                feedback=feedback)['OUTPUT']
        intersectionLayer = context.takeResultLayer(intersectionLayerStr)
        return self.createFeaturesArray(intersectionLayer)
    def outLayer(self, parameters, context, geometry, streamLayer, geomType):
        newField = QgsFields()
        newField.append(QgsField('id', QVariant.Int))
        newField.append(QgsField('erro', QVariant.String))

        (sink, newLayer) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            newField,
            geomType, #1point 2line 3polygon
            streamLayer.sourceCrs()
        )
        
        idcounter = 1
        dicterro = {
            1:'Bueiro, Ponte ou Vau não está na interseção entre um trecho de drenagem e uma via de deslocamento',
            2:'Ponte não está exatamente sobre uma via de deslocamento',
            3:'Vau não deve sobrepor uma via de deslocamento',
            4:'Vau deve intersectar vias de deslocamento em pontos finais e iniciais',
            5:'Barragem em_via_deslocamento = sim(1) deve estar completamente sobre uma via de deslocamento',
            6:'Barragem com em_via_deslocamento =não(2) não deve sobrepor uma via de deslocamento'
        }
        for geom in geometry:
            newFeat = QgsFeature()
            newFeat.setGeometry(geom[0])
            newFeat.setFields(newField)
            newFeat['id'] = idcounter
            newFeat['erro'] = dicterro[geom[1]]
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
            idcounter +=1
        return newLayer
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return VerifyTransports()

    def name(self):
        return 'verifytransports'

    def displayName(self):
        return self.tr('Verifica Transportes')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo verifica a consistência lógica de elementos viários")
    
