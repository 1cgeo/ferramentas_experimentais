# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsCoordinateReferenceSystem,
                       QgsPointXY,
                       QgsProcessingParameterMultipleLayers,
                       QgsFeature,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterVectorLayer,
                       QgsField,
                       QgsFields,
                       QgsFeatureRequest,
                       QgsGeometry
                       )
from qgis import processing
from qgis.utils import iface
import csv
class IdentifySmallLines(QgsProcessingAlgorithm): 

    INPUT_LAYERS = 'INPUT_LAYER_LIST'
    INPUT_CSV = 'INPUT_CSV'
    INPUT_FRAME = 'INPUT_FRAME'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                'INPUT_LAYER_LIST',
                self.tr('Selecionar camadas'),
                QgsProcessing.TypeVectorLine
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                'INPUT_CSV',
                self.tr('Selecionar arquivo CSV contendo nome das camadas e tamanho minimo das linhas'),
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
                self.tr('Flag Linhas Pequenas')
            )
        ) 
    def processAlgorithm(self, parameters, context, feedback):      
        feedback.setProgressText('Procurando linhas menores que tolerância...')
        layerList = self.parameterAsLayerList(parameters,'INPUT_LAYER_LIST', context)
        frameLayer = self.parameterAsVectorLayer(parameters,'INPUT_FRAME', context)
        CSVTable = self.parameterAsFile(parameters,'INPUT_CSV', context)
        CRSstr = iface.mapCanvas().mapSettings().destinationCrs().authid()
        CRS = QgsCoordinateReferenceSystem(CRSstr)
        NameAndSize = []
        lines = []
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
        returnMessage = ('nenhuma linha menor que a tolerancia encontrada')
        for frames in frameLayer.getFeatures():
            frame = frames
            FrameArea = frame.geometry().boundingBox()
            request1 = QgsFeatureRequest().setFilterRect(FrameArea)
            for step,layer in enumerate(layerList):
                if feedback.isCanceled():
                    return {self.OUTPUT: lines}
                if len(NameAndSize) == 0:
                    returnMessage = "tabela vazia"
                    break
                for row in NameAndSize:
                    if layer.sourceName() == row[0]:
                        size = row[1]
                        break
                
                for feature in layer.getFeatures(request1):
                    featgeom = feature.geometry()
                    if not featgeom.length()<size:
                        continue
                    if not featgeom.within(frame.geometry()):
                        continue
                    for geometry in featgeom.constGet():
                        touches = False
                        ptIni = QgsGeometry.fromPointXY(QgsPointXY(geometry[0]))
                        ptFin = QgsGeometry.fromPointXY(QgsPointXY(geometry[-1]))
                        if self.touchesOtherLine(layer, feature, ptIni) and self.touchesOtherLine(layer, feature, ptFin):
                            touches = True
                    if not touches:
                        lines.append([feature, layer.sourceName()])
            
            feedback.setProgress( step * progressStep )
        if not len(lines)==0:
            self.outLayer(parameters, context, lines, CRS, 5)
            returnMessage = 'camada(s) gerada(s)'

        return{self.OUTPUT: returnMessage}

    def touchesOtherLine(self, layer, feature, point):
        AreaOfInterest = feature.geometry().boundingBox()
        request = QgsFeatureRequest().setFilterRect(AreaOfInterest)
        for feat in layer.getFeatures(request):
            if feat.geometry().intersects(point):
                if str(feature.geometry())==str(feat.geometry()):
                    continue
                return True
        return False

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
        return IdentifySmallLines()

    def name(self):
        return 'identifysmalllines'

    def displayName(self):
        return self.tr('Identifica Linhas Soltas Menores que Tolerância')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo identifica se existe alguma linha solta menor que a definida em tabela CSV")
    
