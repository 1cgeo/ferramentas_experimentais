# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterNumber,
                       QgsCoordinateReferenceSystem,
                       QgsGeometry,
                       QgsField,
                       QgsFeature,
                       QgsFields,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterMultipleLayers
                       )
from qgis import processing
from qgis.utils import iface

class identifySmallHoles(QgsProcessingAlgorithm): 

    INPUT_LAYER_LIST = 'INPUT_LAYER_LIST'
    MAX_HOLE_SIZE = 'MAX_HOLE_SIZE'
    OUTPUT = 'OUTPUT'


    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                'INPUT_LAYER_LIST',
                self.tr('Selecionar camadas'),
                QgsProcessing.TypeVectorPolygon
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
                self.tr('Flag Holes Pequenos)
            )
        )
    def processAlgorithm(self, parameters, context, feedback):      
        feedback.setProgressText('Procurando holes menor que a tolerância..')
        layerList = self.parameterAsLayerList(parameters,'INPUT_LAYER_LIST', context)
        maxSize = self.parameterAsDouble (parameters,'MAX_HOLE_SIZE', context) 
        CRSstr = iface.mapCanvas().mapSettings().destinationCrs().authid()
        CRS = QgsCoordinateReferenceSystem(CRSstr)
        smallRings = []
        listSize = len(layerList)
        progressStep = 100/listSize if listSize else 0
        step = 0
        for step,layer in enumerate(layerList):
            if feedback.isCanceled():
                return {self.OUTPUT: smallRings}
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
            feedback.setProgress( step * progressStep )
        
        if len(smallRings) == 0:
            flagLayer = ("não foram encontrados holes com área menor menor que " + str(maxSize))
            return{self.OUTPUT: flagLayer}
        flagLayer = self.outputLayer(parameters, context, smallRings, CRS, 6)
                

        return{self.OUTPUT: flagLayer}

    def outputLayer(self, parameters, context, smallRings, CRS, geomType):

        newField = QgsFields()
        newField.append(QgsField('area', QVariant.Double))
        features = smallRings

        (sink, newLayer) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            newField,
            geomType,
            CRS
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
    
