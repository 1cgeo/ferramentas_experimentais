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
                       QgsFeatureRequest,
                       QgsExpression,
                       QgsFeature,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterVectorLayer,
                       QgsField,
                       QgsFields
                       )
from qgis import processing
from qgis.utils import iface
import csv
class IdentifySmallFeatures(QgsProcessingAlgorithm): 

    INPUT_LAYERS = 'INPUT_LAYER_LIST'
    INPUT_CSV = 'INPUT_CSV'
    INPUT_FRAME = 'INPUT_FRAME'
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
            QgsProcessingParameterFile(
                'INPUT_CSV',
                self.tr('Selecionar arquivo CSV contendo nome das camadas e tamanho minimo das feições'),
                extension = 'csv'
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_FRAME',
                self.tr('Selecionar camada correspondente à moldura'),
                [2]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Camada de Inconsistências:')
            )
        ) 
    def processAlgorithm(self, parameters, context, feedback):      
        feedback.setProgressText('Procurando feições menores que tolerância...')
        layerList = self.parameterAsLayerList(parameters,'INPUT_LAYER_LIST', context)
        frameLayer = self.parameterAsVectorLayer(parameters,'INPUT_FRAME', context)
        CSVTable = self.parameterAsFile(parameters,'INPUT_CSV', context)
        CRSstr = iface.mapCanvas().mapSettings().destinationCrs().authid()
        CRS = QgsCoordinateReferenceSystem(CRSstr)
        outputLog = []
        NameAndSize = []
        lines = []
        polygons = []
        with open(CSVTable, newline = '') as csvFile:
            NameAndSizeTable = csv.reader(csvFile, delimiter = ',', quotechar='"')
            for row in NameAndSizeTable:
                try: 
                    size = float(row[1])
                except (ValueError, IndexError):
                    continue
                NameAndSize.append([row[0], size])
        listSize = len(layerList)
        progressStep = 100/listSize if listSize else 0
        step = 0
        returnMessage = 'nenhuma inconsistência encontrada'
        for frames in frameLayer.getFeatures():
            frame = frames
        for step,layer in enumerate(layerList):
            if layer.geometryType() == 0:
                continue
            if feedback.isCanceled():
                return {self.OUTPUT: outputLog}
            if len(NameAndSize) == 0:
                returnMessage = "tabela vazia"
                break
            for row in NameAndSize:
                if layer.sourceName() == row[0]:
                    size = row[1]
                    break
            for feature in layer.getFeatures():
                geom = feature.geometry()
                if not geom.within(frame.geometry()):
                    continue
                if geom.wkbType() == 4:
                    break
                if geom.wkbType() == 5:
                    if geom.length()<size:
                        lines.append([feature, layer.sourceName()])
                if geom.wkbType() == 6:
                    if geom.area()<size:
                        polygons.append([feature, layer.sourceName()])
            
            feedback.setProgress( step * progressStep )
        if not len(lines)==0:
            self.outLayer(parameters, context, lines, CRS, 5)
            returnMessage = 'camada(s) com inconsistência(s) gerada(s)'
        if not len(polygons)==0:
            self.outLayer(parameters, context, polygons, CRS, 6)
            returnMessage = 'camada(s) com inconsistência(s) gerada(s)'

        return{self.OUTPUT: returnMessage}
  
    def outLayer(self, parameters, context, features, CRS, geomType):
        newField = QgsFields()
        newField.append(QgsField('id', QVariant.Int))
        newField.append(QgsField('nome_da_camada', QVariant.String))
        

        (sink, newLayer) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            newField,
            geomType,
            CRS
        )
        
        for feature in features:
            onlyfeature = feature[0]
            newFeat = QgsFeature()
            newFeat.setGeometry(onlyfeature.geometry())
            newFeat.setFields(newField)
            newFeat['id'] = onlyfeature['id']
            newFeat['nome_da_camada'] = feature[1]
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
        
        return newLayer
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return IdentifySmallFeatures()

    def name(self):
        return 'identifysmallfeatures'

    def displayName(self):
        return self.tr('Identifica Feições Menores que Tolerância')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo identifica se existe alguma geometria menor que a definida em tabela CSV")
    
