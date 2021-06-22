# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsPointXY,
                       QgsGeometry,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterField,
                       QgsFields,
                       QgsFeature,
                       QgsField,
                       QgsWkbTypes
                       )

class StreamPolygonCountourConsistency(QgsProcessingAlgorithm):

    INPUT_WATER_BODY = 'INPUT_WATER_BODY'
    INPUT_STREAM = 'INPUT_STREAM'
    INPUT_CONTOUR_LINES = 'INPUT_CONTOUR_LINES'
    INPUT_COUNTOUR_ID_FIELD = 'INPUT_COUNTOUR_ID_FIELD'
    INPUT_LEVES_FIELD = 'INPUT_LEVES_FIELD'
    OUTPUT = 'OUTPUT'
    OUTPUT_NEW_LAYER = 'OUTPUT_NEW_LAYER'
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_WATER_BODY',
                self.tr('Selecione a camada contendo as massas d\'água'),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
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
            QgsProcessingParameterField(
                'INPUT_LEVES_FIELD',
                self.tr('Selecione o campo que contém as cotas das curvas de nível'), 
                type=QgsProcessingParameterField.Numeric, 
                parentLayerParameterName='INPUT_COUNTOUR_LINES', 
                allowMultiple=False, 
                defaultValue='cota')
            )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Flag Massa d\'Água Inconsistente Com Curva de Nivel')
            )
        ) 

    def processAlgorithm(self, parameters, context, feedback):

        streamLayerInput = self.parameterAsVectorLayer( parameters,'INPUT_STREAM', context )
        waterbodyLayerInput = self.parameterAsVectorLayer( parameters,'INPUT_WATER_BODY', context )
        countourLayer = self.parameterAsVectorLayer( parameters,'INPUT_COUNTOUR_LINES', context )
        levelsField = self.parameterAsFields( parameters,'INPUT_LEVES_FIELD', context )[0]

        outputLines = []
        outputPoints = []

        streamLayerFeatures = self.createFeaturesArray(streamLayerInput)
        countourLayerFeatures = self.createFeaturesArray(countourLayer)
        waterbodyLayerFeatures = self.createFeaturesArray(waterbodyLayerInput)
        feedback.setProgressText('Verificando inconsistencias ')
        self.checkFeatures(streamLayerFeatures, countourLayerFeatures, waterbodyLayerFeatures, levelsField, outputLines, outputPoints)
        
        allOK = True
        if not len(outputLines)==0:
            newLayer = self.outLayer(parameters, context, outputLines, countourLayer, 5)
            allOK = False
        if not len(outputPoints)==0:
            newLayer = self.outLayer(parameters, context, outputPoints, countourLayer, 1)
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

    def checkFeatures(self, streamLayerFeatures, countourLayerFeatures, waterbodyLayerFeatures, levelsField, outputLines, outputPoints):
        NoFlow = [3, 4, 5, 6, 7, 11]
        insidePoly = [2, 3, 4]
        for waterbody in waterbodyLayerFeatures:
            levelsIntersected = []
            for countour in countourLayerFeatures:
                if countour.geometry().touches(waterbody.geometry()):
                    continue
                if countour.geometry().crosses(waterbody.geometry()):
                    intersectionCW = waterbody.geometry().intersection(countour.geometry())
                    if intersectionCW.isMultipart():
                        for inter in intersectionCW.asGeometryCollection():
                            if inter.type():
                                if waterbody['tipo'] in NoFlow:
                                    outputLines.append([inter, 1])
                                    continue
                                outputLines.append([inter, 2])
                        continue
                    else:
                        if waterbody['tipo'] in NoFlow:
                            outputLines.append([intersectionCW, 1])
                            continue

                        if intersectionCW.type() == QgsWkbTypes.PointGeometry:
                            outputPoints.append([intersectionCW, 3])
                            continue

                        vertices = intersectionCW.asPolyline()
                        if len(vertices)>2:
                            outputLines.append([intersectionCW, 3])
                            continue
                    for geometry in countour.geometry().constGet():
                        ptIni = QgsGeometry.fromPointXY(QgsPointXY(geometry[0]))
                        ptFin = QgsGeometry.fromPointXY(QgsPointXY(geometry[-1]))
                    if ptIni.within(waterbody.geometry()) or outputPoints.append([ptFin, 4]):
                        if ptIni.within(waterbody.geometry()) :
                            outputPoints.append([ptIni, 4])
                        if ptFin.within(waterbody.geometry()):
                            outputPoints.append([ptFin, 4])
                    intersectedRiver = False
                    for stream in streamLayerFeatures:
                        if intersectionCW.intersects(stream.geometry()):
                            if stream['situacao_em_poligono'] in insidePoly:
                                intersectedRiver = True
                                continue
                    if not intersectedRiver:
                        outputLines.append([intersectionCW, 5])
                        continue
                    if not len(levelsIntersected) == 0:
                        for levelI in levelsIntersected:
                            if levelI[1]==countour[levelsField]:
                                outputLines.append([intersectionCW, 6])
                                outputLines.append([levelI[0], 6])
                    levelsIntersected.append([intersectionCW, countour[levelsField]])
                    

                    

    def outLayer(self, parameters, context, output, countourLayer, geomtype):
        newFields = QgsFields()
        newFields.append(QgsField('erro', QVariant.String))
        
        (sink, newLayer) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            newFields,
            geomtype, #2line #1point
            countourLayer.sourceCrs()
        )
        dicterro = {
            1: "Curva de nível não pode intersectar massa d\'água sem fluxo",
            2: "Curvas de nível devem atravessar massa d\'água apenas uma vez",
            3: "Interseção com massa d\'água não são apenas 2 pontos",
            4: "Curva de nível deve atravessar massa d\'água",
            5: "Curva de nível em massa d\'água deve cruzar trecho de drenagem dentro de polígono",
            6: "Massa d\'água não pode intersectar mais de uma curva de nível com a mesma cota"
        }
        for line in output:
            newFeat = QgsFeature()
            newFeat.setGeometry(line[0])
            newFeat.setFields(newFields)
            newFeat['erro'] = dicterro[line[1]]
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
        
        return newLayer
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return StreamPolygonCountourConsistency()

    def name(self):
        return 'consistenciafluxonivelpoligono'

    def displayName(self):
        return self.tr('Consistência entre Fluxo (Polígono) e Curva de Nível')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo verifica a consistência entre uma camada de fluxo (drenagem) em relação a outra contendo curvas de nível")
    
