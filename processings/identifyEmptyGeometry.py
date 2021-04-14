# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import QCoreApplication
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
                       QgsProcessingParameterString
                       )
from qgis import processing

class IdentifyEmptyGeometry(QgsProcessingAlgorithm): 

    INPUT_LAYERS = 'INPUT_LAYER_LIST'
    INPUT_FIELD_STRING = 'INPUT_FIELD_STRING'
    OUTPUT = 'OUTPUT'

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
        feedback.setProgressText('Procurando geometria vazia...')
        layerList = self.parameterAsLayerList(parameters,'INPUT_LAYER_LIST', context)
        idField = self.parameterAsString(parameters,'INPUT_FIELD_STRING', context)

        outputLog = {}
        step = 0
        listSize = len(layerList)
        progressStep = 100/listSize if listSize else 0


        for step,layer in enumerate(layerList):
            if feedback.isCanceled():
                return {self.OUTPUT: outputLog}
            outputLog[layer.sourceName()] = []
            fieldIndex = layer.fields().indexFromName(idField)
            if fieldIndex == -1:
                outputLog = 'campo {} não existe em {}'.format(idField, layer.sourceName())
                break
            for feature in layer.getFeatures():
                if not feature.hasGeometry():
                    outputLog[layer.sourceName()].append(feature[idField])
            if len(outputLog[layer.sourceName()]) == 0:
                del outputLog[layer.sourceName()]
            feedback.setProgress( step * progressStep )
        if len(outputLog) == 0:
            outputLog = 'nenhuma feição nula encontrada'
        return{self.OUTPUT: outputLog}
  
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return IdentifyEmptyGeometry()

    def name(self):
        return 'identifyemptygeometry'

    def displayName(self):
        return self.tr('Identifica Geometria Vazia ou Nula')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo identifica geometrias vazias ou nulas")
    
