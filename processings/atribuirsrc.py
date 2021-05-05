# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProject,
                       QgsProcessingParameterCrs,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingParameterBoolean
                       )

class AtribuirSRC(QgsProcessingAlgorithm): 

    INPUT_LAYERS = 'InpLayers'
    INPUT_SRC = 'INPUT'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterCrs(
                'INPUT',
                self.tr('SRC padrao')
            )
        )
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                'InpLayers',
                self.tr('Selecionar camadas'),
                QgsProcessing.TypeMapLayer,
                optional=True
            )
        )
        
        self.addParameter(
            QgsProcessingParameterBoolean(
                'checkBox',
                self.tr('Atribuir SRC para camadas com SRC invalido')
            )
        )
        
    def processAlgorithm(self, parameters, context, feedback):      
        source = self.parameterAsSource(
            parameters,
            'INPUT',
            context
        )
        feedback.setProgressText('Atruibuindo SRC...')
        SRCInput = parameters['INPUT']
        Layers = self.parameterAsLayerList(parameters,'InpLayers', context)
        SRCInvalido = self.parameterAsBool(parameters,'checkBox', context)
        outputLayers = []
        step = 0
        step2 = 0
        listSize = len(Layers)
        if SRCInvalido:
            listSize = len(Layers) + len(QgsProject.instance().mapLayers())
        progressStep = 100/listSize if listSize else 0


        for step,layer in enumerate(Layers):
            if feedback.isCanceled():
                return {self.OUTPUT: outputLayers}
            layer.setCrs(SRCInput)
            outputLayers.append(layer.name())
            feedback.setProgress( step * progressStep )
        if not SRCInvalido:
             return { self.OUTPUT: outputLayers }
        for step2,layer in enumerate(QgsProject.instance().mapLayers().values()):
            crs=layer.crs()
            if feedback.isCanceled():
                return {self.OUTPUT: outputLayers}
            if not crs.isValid():
                layer.setCrs(SRCInput)
                outputLayers.append(layer.name())
            steps=step+step2
            feedback.setProgress(steps*progressStep)
        return{self.OUTPUT: outputLayers}
  
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return AtribuirSRC()

    def name(self):
        return 'atribui_src'

    def displayName(self):
        return self.tr('Atribuir SRC')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo atribui um SRC definido pelo usuario a camadas cujo SRC nao estava definido")
    
