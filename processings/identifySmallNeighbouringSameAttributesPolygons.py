# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsCoordinateReferenceSystem,
                       QgsProcessingParameterMultipleLayers,
                       QgsFeature,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterVectorLayer,
                       QgsField,
                       QgsFields,
                       QgsFeatureRequest,
                       QgsGeometry,
                       QgsProcessingParameterString,
                       QgsProcessingFeatureSourceDefinition
                       )
from qgis import processing
from qgis.utils import iface
import csv
class IdentifySmallNeighbouringSameAttributesPolygons(QgsProcessingAlgorithm): 

    INPUT_LAYERS = 'INPUT_LAYER_LIST'
    INPUT_CSV = 'INPUT_CSV'
    INPUT_FIELDS = 'INPUT_FIELDS'
    INPUT_FRAME = 'INPUT_FRAME'
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
            QgsProcessingParameterFile(
                'INPUT_CSV',
                self.tr('Selecionar arquivo CSV contendo nome das camadas e tamanho minimo dos poligonos'),
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
            QgsProcessingParameterString(
                'INPUT_FIELDS',
                self.tr('Digite os campos que não serão analisados separados por vírgula')
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Flag Poligons Pequenos com os Mesmos Atributos')
            )
        ) 
    def processAlgorithm(self, parameters, context, feedback):      
        feedback.setProgressText('Procurando poligonos menores que tolerância...')
        layerList = self.parameterAsLayerList(parameters,'INPUT_LAYER_LIST', context)
        frameLayer = self.parameterAsVectorLayer(parameters,'INPUT_FRAME', context)
        inputFieldsString = self.parameterAsString( parameters,'INPUT_FIELDS', context )
        inputFields =  inputFieldsString.split(",")
        for field in inputFields:
            field.strip()
        CSVTable = self.parameterAsFile(parameters,'INPUT_CSV', context)
        CRSstr = iface.mapCanvas().mapSettings().destinationCrs().authid()
        CRS = QgsCoordinateReferenceSystem(CRSstr)
        NameAndSize = []
        polygonsFlag = []
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
        returnMessage = ('nenhum poligono menor que a tolerancia e com os mesmos atributos encontrado')
        allFramesFeature = next(self.dissolveFrame(frameLayer).getFeatures())
        allFramesGeom = allFramesFeature.geometry()
        FrameArea = allFramesGeom.boundingBox()
        request1 = QgsFeatureRequest().setFilterRect(FrameArea)
        for step,layer in enumerate(layerList):
            if feedback.isCanceled():
                return {self.OUTPUT: polygonsFlag}
            if len(NameAndSize) == 0:
                returnMessage = "tabela vazia"
                break
            for row in NameAndSize:
                if layer.sourceName() == row[0]:
                    size = row[1]
                    break
            
            for feature in layer.getFeatures(request1):
                featgeom = feature.geometry()
                if not featgeom.area()<size:
                    continue
                if not featgeom.within(allFramesGeom):
                    print(feature['id'])
                    continue
                neighbouringPolygons = self.polygonsTouched(layer, feature)
                if len(neighbouringPolygons) == 0:
                    continue 
                for neighbourPolygon in neighbouringPolygons:
                    fieldsChanged = []
                    fieldsChanged = self.ChangedFields(inputFields, neighbourPolygon, feature)
                    if len(fieldsChanged) == 0:
                        polygonsFlag.append([feature, layer.sourceName()])
            feedback.setProgress( step * progressStep )
        if not len(polygonsFlag)==0:
            self.outLayer(parameters, context, polygonsFlag, CRS, 6)
            returnMessage = 'camada(s) gerada(s)'

        return{self.OUTPUT: returnMessage}

    def dissolveFrame(self, layer):
        r = processing.run(
            'native:dissolve',
            {   'FIELD' : [], 
                'INPUT' : QgsProcessingFeatureSourceDefinition(
                    layer.source()
                ), 
                'OUTPUT' : 'TEMPORARY_OUTPUT'
            }
        )
        return r['OUTPUT']


    def polygonsTouched(self, layer, polygon):
        polygons = []
        AreaOfInterest = polygon.geometry().boundingBox()
        request = QgsFeatureRequest().setFilterRect(AreaOfInterest)
        for feat in layer.getFeatures(request):
            if polygon.geometry().touches(feat.geometry()) or polygon.geometry().intersects(feat.geometry()):
                if not str(polygon.geometry())==str(feat.geometry()):
                    polygons.append(feat)
        return polygons

    def ChangedFields(self, inputFields, feature1, feature2):
        equalFields = []
        for field in feature1.fields():
            if not feature1[field.name()] == feature2[field.name()]:
                if field.name() in inputFields:
                    continue
                equalFields.append(field.name())
        return equalFields

    def outLayer(self, parameters, context, features, CRS, geomType):
        newField = QgsFields()
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
            newFeat['nome_da_camada'] = feature[1]
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
        
        return newLayer
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return IdentifySmallNeighbouringSameAttributesPolygons()

    def name(self):
        return 'identifysmallneighbouringsameattributespolygons'

    def displayName(self):
        return self.tr('Identifica Poligonos Vizinhos Pequenos sem Mudança de Atributos')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo identifica poligonos vizinhos com área menor que a definida cujos atributos não mudaram")
    
