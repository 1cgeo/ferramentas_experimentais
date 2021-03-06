# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsFeature,
                       QgsField,
                       QgsProcessingFeatureSourceDefinition,
                       QgsFeatureRequest
                       )
from qgis import processing

class VerifyCountourStacking(QgsProcessingAlgorithm):

    INPUT_CONTOUR_LINES = 'INPUT_CONTOUR_LINES'
    INPUT_LEVES_FIELD = 'INPUT_LEVES_FIELD'
    INPUT_IS_DEPRESSION_FIELD = 'INPUT_IS_DEPRESSION_FIELD'
    INPUT_LEVEL_GAP = 'INPUT_LEVEL_GAP'
    OUTPUT = 'OUTPUT'
    OUTPUT_NEW_LAYER = 'OUTPUT_NEW_LAYER'
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_COUNTOUR_LINES',
                self.tr('Selecione a camada contendo as curvas de nível'),
                types=[QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                'INPUT_LEVES_FIELD',
                self.tr('Selecione o campo que contém as cotas das curvas de nível'), 
                type=QgsProcessingParameterField.Numeric, 
                parentLayerParameterName='INPUT_COUNTOUR_LINES', 
                allowMultiple=False, 
                defaultValue='cota')
            )
        self.addParameter(
            QgsProcessingParameterField(
                'INPUT_IS_DEPRESSION_FIELD',
                self.tr('Selecione o campo que informação se é depressão ou não'), 
                type=QgsProcessingParameterField.Numeric, 
                parentLayerParameterName='INPUT_COUNTOUR_LINES', 
                allowMultiple=False, 
                defaultValue='depressao')
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                'INPUT_LEVEL_GAP',
                self.tr('Insira o valor da equidistância entre as cotas das curvas de nível'), 
                type=QgsProcessingParameterNumber.Double, 
                minValue=0)
            )
        
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Flag Empilhamento Curva de Nivel')
            )
        ) 

    def processAlgorithm(self, parameters, context, feedback):
        countourLayer = self.parameterAsVectorLayer( parameters,'INPUT_COUNTOUR_LINES', context )
        levelsField = self.parameterAsFields( parameters,'INPUT_LEVES_FIELD', context )[0]
        levelGap = self.parameterAsDouble (parameters,'INPUT_LEVEL_GAP', context)
        isDepressionField = self.parameterAsFields (parameters,'INPUT_IS_DEPRESSION_FIELD', context)[0]
        feedback.setProgressText('Verificando inconsistencias ')
        step =1
        progressStep = 100/4
        countourLayerPolyHoles = self.lineToPolygons(countourLayer,context, feedback)
        step +=1
        feedback.setProgress( step * progressStep )
        countourLayerPoly = self.fillHoles(countourLayerPolyHoles, context, feedback)
        step +=1
        feedback.setProgress( step * progressStep )
        outputPolygons = []
        self.fillField(countourLayer, countourLayerPoly)
        step +=1
        feedback.setProgress( step * progressStep )
        self.compareLevel(levelsField, levelGap, isDepressionField, countourLayerPoly, outputPolygons, feedback, step, progressStep)
        if outputPolygons:
            newLayer = self.outLayer(parameters, context, outputPolygons, countourLayer)
        else: 
            newLayer = 'nenhuma inconsistência verificada'
        return {self.OUTPUT: newLayer}

    def lineToPolygons(self, layer,context, feedback):
        r = processing.run(
            'native:polygonize',
            {   'INPUT' : QgsProcessingFeatureSourceDefinition(
                    layer.source()
                ), 
                'KEEP_FIELDS' : True,
                'OUTPUT' : 'TEMPORARY_OUTPUT'
            },
            context = context,
            feedback = feedback
        )
        return r['OUTPUT']  
    def createFeaturesArray(self, originalLayer):
        arrayFeatures = []
        features = originalLayer.getFeatures()

        for feature in features:
            arrayFeatures.append(feature)

        return arrayFeatures
        
    def fillHoles(self, layer, context, feedback):
        r = processing.run(
            'native:deleteholes',
            {   'INPUT' : layer,
                'OUTPUT' : 'TEMPORARY_OUTPUT'
            },
            context = context,
            feedback = feedback
        )
        return r['OUTPUT']  
    def fillField(self, countourLayer, countourLayerPoly):
        countourLayerPoly.startEditing()
        pr = countourLayerPoly.dataProvider()
        updateMap = {}
        for feature1 in pr.getFeatures():
            AreaOfInterest = feature1.geometry().boundingBox()
            request = QgsFeatureRequest().setFilterRect(AreaOfInterest)
            for feature2 in countourLayer.getFeatures(request):
                if feature2.geometry().touches(feature1.geometry()):
                    fv = {}
                    for field in feature2.fields():
                        fieldIdx = pr.fields().indexFromName( field.name())
                        fv[fieldIdx] = feature2[field.name()]
                        
                        feature1[field.name()] =  feature2[field.name()]
                    updateMap[feature1.id()] = fv
        pr.changeAttributeValues( updateMap )
        countourLayerPoly.commitChanges()
        return False
    def compareLevel(self, levelsField, levelGap, isDepressionField, countourLayerPoly, outputPolygons, feedback, step, progressStep):
        isDep = 1
        isNotDep = 0  
        auxstep = 0
        AUXCOUNT = 0
        auxProgressStep = countourLayerPoly.featureCount()
        for feature1 in countourLayerPoly.getFeatures():
            AUXCOUNT += 1
            auxcount=0
            auxstep+=1
            feedback.setProgress( step*(1+(auxstep/auxProgressStep)) * progressStep )
            toCompare = []
            areaComp = []
            skip = True
            AreaOfInterest = feature1.geometry().boundingBox()
            request = QgsFeatureRequest().setFilterRect(AreaOfInterest)
            for feature2 in countourLayerPoly.getFeatures(request):
                auxcount+=1
                if str(feature1.geometry())==str(feature2.geometry()):
                    continue
                if feature1.geometry().within(feature2.geometry()):
                    toCompare.append(feature2)
                    areaComp.append(feature2.geometry().area())
                    skip = False
            if skip:
                continue
            fToCompare = toCompare[areaComp.index(min(areaComp))]                
            if fToCompare[isDepressionField] == isNotDep:
                if feature1[isDepressionField] == isNotDep:
                    if not((feature1[levelsField] - fToCompare[levelsField])==levelGap):
                        outputPolygons.append([feature1, 1])
                if feature1[isDepressionField] == isDep:
                    if not(feature1[levelsField] == fToCompare[levelsField]):
                        outputPolygons.append([feature1, 3])
            if fToCompare[isDepressionField] == isDep:
                if feature1[isDepressionField] == isDep:
                    if not((fToCompare[levelsField] - feature1[levelsField])==levelGap):
                        outputPolygons.append([feature1, 2])
                if feature1[isDepressionField] == isNotDep:
                    if not(feature1[levelsField] == fToCompare[levelsField]):
                        outputPolygons.append([feature1, 4])
        return False
    def outLayer(self, parameters, context, polygons, streamLayer):
        newFields = polygons[0][0].fields()
        newFields.append(QgsField('erro', QVariant.String))
        
        (sink, newLayer) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            newFields,
            3, #polygon
            streamLayer.sourceCrs()
        )
        dicterro = {
            1: "Externo e interno (esse) são normais, mas a diferença de cota não é de mais uma equidistância",
            2: "Externo e interno (esse) são depressões, mas a diferença de cota não é de menos uma equidistância",
            3: "Externo é normal, interno (esse) é depressão, mas a cota não é a mesma",
            4: "Externo é depressão, interno (esse) é normal, mas a cota não é a mesma"
        }
        for polygon in polygons:
            newFeat = QgsFeature()
            newFeat.setGeometry(polygon[0].geometry())
            newFeat.setFields(newFields)
            for field in  range(len(polygon[0].fields())):
                newFeat.setAttribute((field), polygon[0].attribute((field)))
            newFeat['erro'] = dicterro[polygon[1]]
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
        
        return newLayer
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return VerifyCountourStacking()

    def name(self):
        return 'verifycountourstacking'

    def displayName(self):
        return self.tr('Verifica Empilhamento de Curva de Nível')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo verifica o empilhamento de curvas de nível, comparado as cotas de acordo com o tipo de cada uma")
    
