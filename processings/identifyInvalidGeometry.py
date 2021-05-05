# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingParameterString
                       )
from qgis import processing

class IdentifyInvalidGeometry(QgsProcessingAlgorithm): 

    INPUT_LAYERS = 'INPUT_LAYER_LIST'
    INPUT_FIELD_STRING = 'INPUT_FIELD_STRING'
    OUTPUT = 'OUTPUT'
    OUTPUT_TYPE = "Feições com geometria diferente de MultiPoint, MultiLineString ou MultiPolygon"
    OUTPUT_NULL = 'Feições com geometria nula ou vazia'
    OUTPUT_INVALID = 'Feições com geometria invalida'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                'INPUT_LAYER_LIST',
                self.tr('Selecionar camadas'),
                QgsProcessing.TypeVector
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                'INPUT_FIELD_STRING',
                self.tr('Digitar nome do campo correspondente a chave primaria (id)'),
                'id'
            )
        )
        
    def processAlgorithm(self, parameters, context, feedback):      
        feedback.setProgressText('Procurando geometria invalida...')
        layerList = self.parameterAsLayerList(parameters,'INPUT_LAYER_LIST', context)
        idField = self.parameterAsString(parameters,'INPUT_FIELD_STRING', context)

        geomType = [4, 5, 6]
        outputLog = {}
        outputLogType = {}
        outputLogNull = {}
        outputLogInvalid = {}
        step = 0
        listSize = len(layerList)
        progressStep = 100/listSize if listSize else 0


        for step,layer in enumerate(layerList):
            if feedback.isCanceled():
                return {self.OUTPUT: outputLog}
            outputLog[layer.sourceName()] = []
            outputLogType[layer.sourceName()] = []
            outputLogNull[layer.sourceName()] = []
            outputLogInvalid[layer.sourceName()] = []
            fieldIndex = layer.fields().indexFromName(idField)
            if fieldIndex == -1:
                outputLog = 'campo {} não existe em {}'.format(idField, layer.sourceName())
                return{self.OUTPUT: outputLog}
            for feature in layer.getFeatures():
                if feature.geometry().wkbType() not in geomType:
                    outputLog[layer.sourceName()].append(feature[idField])
                    outputLogType[layer.sourceName()].append(feature[idField])
                if not feature.hasGeometry():
                    if not (feature[idField] in outputLog[layer.sourceName()]):
                        outputLogNull[layer.sourceName()].append(feature[idField])
                        outputLog[layer.sourceName()].append(feature[idField])
                if not (len(feature.geometry().validateGeometry()) == 0):
                    if feature[idField] not in outputLog[layer.sourceName()]:
                        outputLogInvalid[layer.sourceName()].append(feature[idField])
                        outputLog[layer.sourceName()].append(feature[idField])
            if len(outputLog[layer.sourceName()]) == 0:
                del outputLog[layer.sourceName()]
            if len(outputLogType[layer.sourceName()]) == 0:
                del outputLogType[layer.sourceName()]
            if len(outputLogNull[layer.sourceName()]) == 0:
                del outputLogNull[layer.sourceName()]
            if len(outputLogInvalid[layer.sourceName()]) == 0:
                del outputLogInvalid[layer.sourceName()]
            feedback.setProgress( step * progressStep )
        if len(outputLog) == 0:
            outputLog = 'nenhuma feição com geometria invalida encontrada'
            return{self.OUTPUT: outputLog}
        return{self.OUTPUT_TYPE: outputLogType, self.OUTPUT_NULL: outputLogNull, self.OUTPUT_INVALID: outputLogInvalid}
  
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return IdentifyInvalidGeometry()

    def name(self):
        return 'identifyinvalidgeometry'

    def displayName(self):
        return self.tr('Identifica Geometria Invalida')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo identifica geometrias invalidas")
    
