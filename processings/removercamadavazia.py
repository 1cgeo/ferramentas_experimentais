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
                       Qgis)
from qgis import processing
from qgis.utils import iface
class RemoveEmptyLayers(QgsProcessingAlgorithm):
    OUTPUT = 'OUTPUT'
    def initAlgorithm(self, config=None):
        'pass'
    def processAlgorithm(self, parameters, context, feedback):
        outputLayers = []

        listSize = len(QgsProject.instance().mapLayers())
        progressStep = 100/listSize if listSize else 0

        toBeRemoved = []
        step=0
        feedback.setProgressText('Removendo camadas...')
       
        for key, layer in QgsProject.instance().mapLayers().items():
            if feedback.isCanceled():
                return {self.OUTPUT: outputLayers}
            if layer.type() == QgsMapLayer.VectorLayer:
                if layer.featureCount() == 0:
                    outputLayers.append(layer.name())
                    toBeRemoved.append(layer.id())
            step+=1
            feedback.setProgress(step*progressStep)
        if toBeRemoved:
            QgsProject.instance().removeMapLayers( toBeRemoved )
        iface.messageBar().pushMessage("Executado", u"Camadas vazias apagadas", level=Qgis.Success, duration=5)

        return{self.OUTPUT: outputLayers}
  
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return RemoveEmptyLayers()

    def name(self):
        return 'remove_empty_layers'

    def displayName(self):
        return self.tr('Remove Empty Layers')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo remove camadas vazias")
    
    


        
  
      
        
