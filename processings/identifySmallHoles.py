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
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterNumber,
                       QgsGeometry,
                       QgsField,
                       QgsFeature,
                       QgsFields
                       )
from qgis import processing

class identifySmallHoles(QgsProcessingAlgorithm): 

    INPUT_LAYER = 'INPUT_LAYER'
    MAX_HOLE_SIZE = 'MAX_HOLE_SIZE'
    OUTPUT = 'OUTPUT'


    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_LAYER',
                self.tr('Selecionar camada'),
                [2]
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                'MAX_HOLE_SIZE',
                self.tr('Insira o valor máximo para tolerância'), 
                type=QgsProcessingParameterNumber.Double, 
                minValue=0)
            )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Camada de Saída')
            )
        )
    def processAlgorithm(self, parameters, context, feedback):      
        feedback.setProgressText('Procurando holes menor que a tolerância..')
        layer = self.parameterAsVectorLayer(parameters,'INPUT_LAYER', context)
        maxSize = self.parameterAsDouble (parameters,'MAX_HOLE_SIZE', context) 

        smallRings = []
        print(maxSize)

        for feature in layer.getFeatures():
            if not feature.hasGeometry():
                continue
            for poly in feature.geometry().asMultiPolygon():
                onlyrings = poly[1:]
                for ring in onlyrings:
                    newRing = QgsGeometry.fromPolygonXY([ring])
                    print(newRing.area())
                    if newRing.area()<maxSize:
                        smallRings.append(newRing)
        
        if len(smallRings) == 0:
            flagLayer = ("não foram encontrados holes com área menor menor que " + str(maxSize))
            return{self.OUTPUT: flagLayer}
        flagLayer = self.outputLayer(parameters, context, layer, smallRings)
                

        return{self.OUTPUT: flagLayer}

    def outputLayer(self, parameters, context, originalLayer, smallRings):

        newField = QgsFields()
        newField.append(QgsField('area', QVariant.Double))
        features = smallRings

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
            newFeat.setGeometry(feature)
            newFeat.setFields(newField)
            newFeat['area'] = feature.area()
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
        
        return newLayer

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return identifySmallHoles()

    def name(self):
        return 'identifysmallholes'

    def displayName(self):
        return self.tr('Identifica Holes Menores que Tolerância')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo identifica se existe algum hole menor que a tolerância definida pelo usuário")
    
