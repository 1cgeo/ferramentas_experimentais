# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from qgis.core import (QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsFeature,
                       QgsProcessingParameterFile,
                       QgsProject,
                       QgsField,
                       QgsFields,
                       QgsProcessingMultiStepFeedback,
                       QgsCoordinateReferenceSystem,
                       QgsGeometry,
                       QgsProcessingParameterNumber
                       )
from qgis import processing
from qgis.utils import iface
import csv
class IdentifyCloseFeatures(QgsProcessingAlgorithm): 

    INPUT_CSV = 'INPUT_CSV'
    INPUT_LINE_DISTANCE = 'INPUT_LINE_DISTANCE'
    # INPUT_FRAME = 'INPUT_FRAME'
    OUTPUT = 'OUTPUT'
    OUTPUTPXP = 'OUTPUTPXP'
    OUTPUTPXL = 'OUTPUTPXL'
    OUTPUTLXL = 'OUTPUTLXL'
    
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFile(
                'INPUT_CSV',
                self.tr('Selecionar arquivo CSV:'),
                extension = 'csv'
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                'INPUT_LINE_DISTANCE',
                self.tr('Insira a distância mínima para considerar uma linha próxima'), 
                type=QgsProcessingParameterNumber.Double, 
                minValue=0)
            )
        # self.addParameter(
        #     QgsProcessingParameterVectorLayer(
        #         'INPUT_FRAME',
        #         self.tr('Selecionar camada correspondente à moldura'),
        #         [2]
        #     )
        # )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUTPXP,
                self.tr('Flag Feições Próximas Ponto x Ponto')
            )
        ) 
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUTPXL,
                self.tr('Flag Feições Próximas Ponto x Linha')
            )
        ) 
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUTLXL,
                self.tr('Flag Feições Próximas Linha x Linha')
            )
        ) 

    def processAlgorithm(self, parameters, context, feedback):      
        feedback.setProgressText('Iniciando...')
        returnMessage = 'Nenhum erro encontrado'
        #frameLayer = self.parameterAsVectorLayer(parameters,'INPUT_FRAME', context)
        CRSstr = iface.mapCanvas().mapSettings().destinationCrs().authid()
        setCRS = QgsCoordinateReferenceSystem(CRSstr)
        lineDistance = self.parameterAsDouble(parameters,'INPUT_LINE_DISTANCE', context)
        CSVTable = self.parameterAsFile(parameters,'INPUT_CSV', context)
        AllOK, returnMessage, layerCounter = self.verifyCSV(CSVTable)
        pointVsPoint = []
        pointVsLine = []
        lineVsLine = []
        if (not AllOK):
            return{self.OUTPUT: returnMessage}
        multiStepFeedback = QgsProcessingMultiStepFeedback(layerCounter+3, feedback)
        multiStepFeedback.setCurrentStep(0)
        multiStepFeedback.pushInfo("Procurando feições próximas.")
        self.readCSV(CSVTable, pointVsPoint, pointVsLine, lineVsLine, lineDistance, multiStepFeedback)
        if not len(pointVsPoint)==0:
            self.outLayerPxP(parameters, context, pointVsPoint, setCRS)
            returnMessage = 'camada(s) com inconsistência(s) gerada(s)'
        multiStepFeedback.setCurrentStep(layerCounter+1)
        if not len(pointVsLine)==0:
            self.outLayerPxL(parameters, context, pointVsLine, setCRS)
            returnMessage = 'camada(s) com inconsistência(s) gerada(s)'
        multiStepFeedback.setCurrentStep(layerCounter+2)
        if not len(lineVsLine)==0:
            self.outLayerLxL(parameters, context, lineVsLine, setCRS)
            returnMessage = 'camada(s) com inconsistência(s) gerada(s)'
        multiStepFeedback.setCurrentStep(layerCounter+3)
        return{self.OUTPUT: returnMessage}

    def verifyCSV(self, CSVTable):
        CSVOK=True
        message = 'Nenhum erro encontrado'
        layerCounter = 0
        with open(CSVTable, newline = '') as csvFile:
            table = csv.reader(csvFile, delimiter = ',', quotechar='"')
            i=0
            names = []
            for row in table:
                layerCounter+=1
                j=len(row)
                if (i==0):
                    i+=1
                    names = row
                    continue
                CSVOK, message = self.verifyLayerNameProblems(row[0])
                if (not CSVOK):
                    return (CSVOK, message, layerCounter)
                for k in range(i, j):
                    newNumber = row[k].replace(',', '.')
                    try:
                        float(newNumber)
                    except ValueError:
                        CSVOK=False
                        message = 'Linha ' + str(i+1) + ' x Coluna ' + str(k+1) + ' não é um número.'
                        return (CSVOK, message, layerCounter)
                    CSVOK, message = self.verifyLayerNameProblems(names[k])
                    if (not CSVOK):
                        return (CSVOK, message, layerCounter)
                i+=1
        layerCounter-=1 #a primeira linha não contem nenhuma camada na coluna 1
        return (CSVOK, message, layerCounter)

    def verifyLayerNameProblems(self, name):
        geomTypes = [0,1] #ponto e linha, respectivamente
        layerList =  QgsProject.instance().mapLayersByName(name)
        CSVOK=True
        message = 'Nenhum erro encontrado'
        if (len(layerList)==0):
            CSVOK=False
            message = 'Nenhuma camada "' + name +'" encontrada'
            return (CSVOK, message)
        if (len(layerList)>1):
            CSVOK=False
            message = 'Mais de uma camada "' + name +'" encontrada'
            return (CSVOK, message)
        if (layerList[0].geometryType() not in geomTypes):
            CSVOK=False
            message = 'Camada "' + name +'" não é do tipo ponto ou linha'
        return (CSVOK, message)
  
    def verifyPointVsPoint(self, layer1pre, layer2pre, distance, pointVsPoint):
        layer1 = self.runAddCount(layer1pre)
        self.runCreateSpatialIndex(layer1)
        if (layer1pre==layer2pre):
            layer1FeaturesArray = self.createFeaturesArray(layer1)
            for i in range(0, len(layer1FeaturesArray)-1):
                geom1 = layer1FeaturesArray[i].geometry()
                for j in range(i+1, len(layer1FeaturesArray)):
                    geom2 = layer1FeaturesArray[j].geometry()
                    distancePxP = geom1.distance(geom2)
                    if (distancePxP<=distance):
                        pointVsPoint.append([geom1, geom2, layer1pre.sourceName(), layer2pre.sourceName(), distancePxP])
        else:
            layer2 = self.runAddCount(layer2pre)
            self.runCreateSpatialIndex(layer2)
            for feat1 in layer1.getFeatures():
                geom1 = feat1.geometry()
                for feat2 in layer2.getFeatures():
                    geom2 = feat2.geometry()
                    distancePxP = geom1.distance(geom2)
                    if (distancePxP<=distance):
                        pointVsPoint.append([geom1, geom2, layer1pre.sourceName(), layer2pre.sourceName(), distancePxP])

        return False
    
    def verifyPointVsLine(self, layer1pre, layer2pre, distance, pointVsLine):
        layer1 = self.runAddCount(layer1pre)
        self.runCreateSpatialIndex(layer1)
        layer2 = self.runAddCount(layer2pre)
        self.runCreateSpatialIndex(layer2)
        for feat1 in layer1.getFeatures():
            geom1 = feat1.geometry()
            for feat2 in layer2.getFeatures():
                geom2 = feat2.geometry()
                distancePxL = geom1.distance(geom2)
                if (distancePxL<=distance):
                    pointVsLine.append([geom1, layer1pre.sourceName(), layer2pre.sourceName(), distancePxL])

        return False
    
    def verifyLineVsLine(self, layer1pre, layer2pre, distance, lineVsLine, lineDistance):
        layer1 = self.runAddCount(layer1pre)
        self.runCreateSpatialIndex(layer1)
        if (layer1pre==layer2pre):
            layer1FeaturesArray = self.createFeaturesArray(layer1)
            for i in range(0, len(layer1FeaturesArray)-1):
                geom1 = layer1FeaturesArray[i].geometry().buffer(distance, 5)
                for j in range(i+1, len(layer1FeaturesArray)):
                    geom2 = layer1FeaturesArray[j].geometry()
                    inter = geom2.intersection(geom1)
                    if (inter.isEmpty()):
                        continue
                    if (inter.isMultipart):
                        for part in inter.constParts():
                            lineLength = part.length()
                    else:
                        lineLength = inter.length()
                    if (lineDistance<lineLength):
                        lineVsLine.append([layer1FeaturesArray[i].geometry(), geom2, layer1pre.sourceName(), layer2pre.sourceName(), lineLength])
        else:
            layer2 = self.runAddCount(layer2pre)
            self.runCreateSpatialIndex(layer2)
            for feat1 in layer1.getFeatures():
                geom1 = feat1.geometry().buffer(distance, 5)
                for feat2 in layer2.getFeatures():
                    geom2 = feat2.geometry()
                    inter = geom2.intersection(geom1)
                    if (inter.isEmpty()):
                        continue
                    if (inter.isMultipart):
                        for part in inter.constParts():
                            lineLength = part.length()
                    else:
                        lineLength = inter.length()
                    if (lineDistance<lineLength):
                        lineVsLine.append([feat1.geometry(), geom2, layer1pre.sourceName(), layer2pre.sourceName(), lineLength])
        return False

    def createFeaturesArray(self, originalLayer):
        arrayFeatures = []
        features = originalLayer.getFeatures()

        for feature in features:
            arrayFeatures.append(feature)

        return arrayFeatures

    def readCSV(self, CSVTable, pointVsPoint, pointVsLine, lineVsLine, lineDistance, multiStepFeedback):
        with open(CSVTable, newline = '') as csvFile:
            table = csv.reader(csvFile, delimiter = ',', quotechar='"')
            i=0
            names = []
            for row in table:
                j=len(row)
                if (i==0):
                    i+=1
                    names = row
                    continue
                multiStepFeedback.setCurrentStep(i)
                for k in range(i, j):
                    
                    distance = float(row[k].replace(',', '.'))
                    layer1pre = QgsProject.instance().mapLayersByName(row[0])[0]
                    layer2pre = QgsProject.instance().mapLayersByName(names[k])[0]
                    geomType1 = layer1pre.geometryType()
                    geomType2 = layer2pre.geometryType()
                    multiStepFeedback.setCurrentStep(i)
                    if (geomType1==0 and geomType2==0):
                        self.verifyPointVsPoint(layer1pre, layer2pre, distance, pointVsPoint)
                    if (geomType1==0 and geomType2==1):
                        self.verifyPointVsLine(layer1pre, layer2pre, distance, pointVsLine)
                    if (geomType1==1 and geomType2==0):
                        self.verifyPointVsLine(layer2pre, layer1pre, distance, pointVsLine)
                    if (geomType1==1 and geomType2==1):
                        self.verifyLineVsLine(layer1pre, layer2pre, distance, lineVsLine, lineDistance)
                i+=1
        return False

    def runAddCount(self, inputLyr):
        output = processing.run(
            "native:addautoincrementalfield",
            {
                'INPUT':inputLyr,
                'FIELD_NAME':'AUTO',
                'START':0,
                'GROUP_FIELDS':[],
                'SORT_EXPRESSION':'',
                'SORT_ASCENDING':False,
                'SORT_NULLS_FIRST':False,
                'OUTPUT':'TEMPORARY_OUTPUT'
            }
        )
        return output['OUTPUT']
    
    def runCreateSpatialIndex(self, inputLyr):
        processing.run(
            "native:createspatialindex",
            {'INPUT':inputLyr}
        )

        return False

    def outLayerPxP(self, parameters, context, pointVsPoint, setCRS):
        newField = QgsFields()
        newField.append(QgsField('id', QVariant.Int))
        newField.append(QgsField('nome_da_camada1', QVariant.String))
        newField.append(QgsField('nome_da_camada2', QVariant.String))
        newField.append(QgsField('distancia', QVariant.Double))
        

        (sink, newLayer) = self.parameterAsSink(
            parameters,
            self.OUTPUTPXP,
            context,
            newField,
            4,
            setCRS
        )

        idcounter = 1
        for pointarray in pointVsPoint:
            geom1 = pointarray[0]
            geom2 = pointarray[1]
            combinegeom = geom1.combine(geom2)
            newFeat = QgsFeature()
            newFeat.setGeometry(combinegeom)
            newFeat.setFields(newField)
            newFeat['id'] = idcounter
            newFeat['nome_da_camada1'] = pointarray[2]
            newFeat['nome_da_camada2'] = pointarray[3]
            newFeat['distancia'] = pointarray[4]
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
            idcounter +=1
        return newLayer
    
    def outLayerPxL(self, parameters, context, pointVsLine, setCRS):
        newField = QgsFields()
        newField.append(QgsField('id', QVariant.Int))
        newField.append(QgsField('nome_da_camada1', QVariant.String))
        newField.append(QgsField('nome_da_camada2', QVariant.String))
        newField.append(QgsField('distancia', QVariant.Double))
        

        (sink, newLayer) = self.parameterAsSink(
            parameters,
            self.OUTPUTPXL,
            context,
            newField,
            1,
            setCRS
        )

        idcounter = 1
        for pointarray in pointVsLine:
            geom = pointarray[0]
            newFeat = QgsFeature()
            newFeat.setGeometry(geom)
            newFeat.setFields(newField)
            newFeat['id'] = idcounter
            newFeat['nome_da_camada1'] = pointarray[1]
            newFeat['nome_da_camada2'] = pointarray[2]
            newFeat['distancia'] = pointarray[3]
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
            idcounter +=1
        return newLayer
    
    def outLayerLxL(self, parameters, context, lineVsLine, setCRS):
        newField = QgsFields()
        newField.append(QgsField('id', QVariant.Int))
        newField.append(QgsField('nome_da_camada1', QVariant.String))
        newField.append(QgsField('nome_da_camada2', QVariant.String))
        newField.append(QgsField('comprimento dentro do buffer', QVariant.Double))
        

        (sink, newLayer) = self.parameterAsSink(
            parameters,
            self.OUTPUTLXL,
            context,
            newField,
            5,
            setCRS
        )

        idcounter = 1
        for linearray in lineVsLine:
            geom1 = linearray[0]
            geom2 = linearray[1]
            combinegeom = geom1.combine(geom2)
            newFeat = QgsFeature()
            newFeat.setGeometry(combinegeom)
            newFeat.setFields(newField)
            newFeat['id'] = idcounter
            newFeat['nome_da_camada1'] = linearray[2]
            newFeat['nome_da_camada2'] = linearray[3]
            newFeat['comprimento dentro do buffer'] = linearray[4]
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
            idcounter +=1
        return newLayer
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return IdentifyCloseFeatures()

    def name(self):
        return 'identifyclosefeatures'

    def displayName(self):
        return self.tr('Identifica Feições Próximas')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo identifica se existe feições cuja distância entre si é menor que a definida em tabela CSV para cada combinação de camadas. Serão considerados apenas os valores acima da diagonal")
    
