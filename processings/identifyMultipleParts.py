# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsCoordinateReferenceSystem,
                       QgsProcessingParameterMultipleLayers,
                       QgsFeatureRequest,
                       QgsExpression,
                       QgsFeature
                       )
from qgis import processing
from qgis.utils import iface
class IdentifyMultipleParts(QgsProcessingAlgorithm): 

    INPUT_LAYERS = 'INPUT_LAYER_LIST'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                'INPUT_LAYER_LIST',
                self.tr('Selecionar camadas'),
                QgsProcessing.TypeVectorAnyGeometry
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Flag Multiplas Partes')
            )
        ) 
    def processAlgorithm(self, parameters, context, feedback):      
        feedback.setProgressText('Procurando multi geometria com mais de uma parte...')
        layerList = self.parameterAsLayerList(parameters,'INPUT_LAYER_LIST', context)
        CRSstr = iface.mapCanvas().mapSettings().destinationCrs().authid()
        CRS = QgsCoordinateReferenceSystem(CRSstr)
        #4 = multipoint, 5 = multiline, 6 = multipolygon
        featuresToAdd = {4:[], 5:[], 6:[]}
        newLayer = {4:False, 5:False, 6:False}
        step = 0
        listSize = len(layerList)
        progressStep = 100/listSize if listSize else 0
        returnMessage = 'nenhuma inconsistência encontrada'

        for step,layer in enumerate(layerList):
            if feedback.isCanceled():
                return {self.OUTPUT: outputLog}
            expr = QgsExpression( "num_geometries( $geometry ) > 1" )
            for feature in layer.getFeatures(QgsFeatureRequest(expr)): 
                featuresToAdd[feature.geometry().wkbType()].append(feature) 
            feedback.setProgress( step * progressStep )
        for key in featuresToAdd:
            if not len(featuresToAdd[key]) == 0:
                newLayer[key] = self.outLayer(parameters, context, featuresToAdd[key], CRS, key)
                returnMessage = 'camada(s) com inconsistência(s) gerada(s)'
        return{self.OUTPUT: returnMessage}
  
    def outLayer(self, parameters, context, features, CRS, geomType):
        newFields = features[0].fields()

        (sink, newLayer) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            newFields,
            geomType,
            CRS
        )
        
        for feature in features:
            newFeat = QgsFeature()
            newFeat.setGeometry(feature.geometry())
            newFeat.setFields(newFields)
            for field in  range(len(feature.fields())):
                newFeat.setAttribute((field), feature.attribute((field)))
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
        
        return newLayer
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return IdentifyMultipleParts()

    def name(self):
        return 'identifymultipleparts'

    def displayName(self):
        return self.tr('Identifica Geometria com Multiplas Partes')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo identifica se existe alguma geometria com mais de uma parte")
    
