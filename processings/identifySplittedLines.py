# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsPointXY,
                       QgsFeature,
                       QgsProcessingParameterString,
                       QgsField,
                       QgsFeatureRequest,
                       QgsGeometry,
                       QgsCoordinateReferenceSystem,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingFeatureSourceDefinition,
                       QgsFields
                       )
from qgis import processing
from qgis.utils import iface
class IdentifySplittedLines(QgsProcessingAlgorithm): 

    INPUT_LAYER_LIST = 'INPUT_LAYER_LIST'
    INPUT_FIELDS = 'INPUT_FIELDS'
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
            QgsProcessingParameterString(
                'INPUT_FIELDS',
                self.tr('Digite os campos que não serão analisados separados por vírgula'),
                defaultValue = 'observacao,data_modificacao,controle_uuid,usuario_criacao,usuario_atualizacao,length_otf,id,lenght_otf'
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
                self.tr('Flag Quebra de Linha Desnecessaria ')
            )
        ) 
    def processAlgorithm(self, parameters, context, feedback):      
        feedback.setProgressText('Procurando linhas seccionadas...')
        layerList = self.parameterAsLayerList(parameters,'INPUT_LAYER_LIST', context)
        frameLayer = self.parameterAsVectorLayer(parameters,'INPUT_FRAME', context)
        inputFieldsString = self.parameterAsString( parameters,'INPUT_FIELDS', context )
        inputFields =  inputFieldsString.split(",")
        for field in inputFields:
            field.strip()
        CRSstr = iface.mapCanvas().mapSettings().destinationCrs().authid()
        CRS = QgsCoordinateReferenceSystem(CRSstr)
        listSize = len(layerList)
        progressStep = 100/listSize if listSize else 0
        step = 0
        pointsGeomAndLayer= []
        InitFinPoint = [0,-1]
        pointsInFrame = QgsFeature()
        pointsToAdd = []
        for frame in frameLayer.getFeatures():
            framegeom = frame.geometry().asMultiPolygon()[0][0]
            n = len(framegeom)
            for i in range(n):
                pointsToAdd.append(framegeom[i])
        pointsInFrame.setGeometry(QgsGeometry().fromMultiPointXY(pointsToAdd))
        allFramesFeature = next(self.dissolveFrame(frameLayer).getFeatures())
        allFramesGeom = allFramesFeature.geometry()
        FrameArea = allFramesGeom.boundingBox()
        request1 = QgsFeatureRequest().setFilterRect(FrameArea)

        for step,layer in enumerate(layerList):
            for feature in layer.getFeatures(request1):
                if feedback.isCanceled():
                    return {self.OUTPUT: pointsGeomAndLayer}
                featgeom = feature.geometry()
                featgeom.convertToMultiType()    
                for i in InitFinPoint:
                    for geometry in featgeom.constGet():
                        pt = QgsGeometry.fromPointXY(QgsPointXY(geometry[i]))
                        lineTouched= self.linesTouched(layer, feature, pt)
                    if not pt.within(allFramesGeom):
                            continue
                    if len(lineTouched) == 0 or len(lineTouched) > 1:
                        continue 
                    fieldsChanged = self.changedFields(inputFields, feature, lineTouched[0])
                    if not len(fieldsChanged) == 0:
                        continue
                    alreadythere = False
                    if pt.intersects(pointsInFrame.geometry()):
                        continue
                    for point in pointsGeomAndLayer:
                        if str(pt) == str(point[0]):
                            alreadythere = True
                    if not alreadythere:
                        pointsGeomAndLayer.append([pt, layer.name()])
            feedback.setProgress( step * progressStep )    
        if len(pointsGeomAndLayer)==0:
            return{self.OUTPUT: 'nenhuma linha encontrada'}
        newLayer = self.outLayer(parameters, context, pointsGeomAndLayer, CRS, 4)
        return{self.OUTPUT: newLayer}

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

    def linesTouched(self, layer, feature, point):
        lines = []
        AreaOfInterest = feature.geometry().boundingBox()
        request = QgsFeatureRequest().setFilterRect(AreaOfInterest)
        for feat in layer.getFeatures(request):
            if feat.geometry().intersects(point):
                if str(feature.geometry())==str(feat.geometry()):
                    continue
                lines.append(feat)
        return lines
    
    def changedFields(self, inputFields, feature1, feature2):
        equalFields = []
        for field in feature1.fields():
            if not feature1[field.name()] == feature2[field.name()]:
                if field.name() in inputFields:
                    continue
                equalFields.append(field.name())
        return equalFields

    def outLayer(self, parameters, context, pointsGeomAndLayer, CRS, geomType):
        newField = QgsFields()
        newField.append(QgsField('Camada original', QVariant.String))
        

        (sink, newLayer) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            newField,
            geomType,
            CRS
        )
        
        for feature in pointsGeomAndLayer:
            newFeat = QgsFeature()
            newFeat.setGeometry(feature[0])
            newFeat.setFields(newField)
            newFeat['Camada original'] = feature[1]
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
        
        return newLayer
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return IdentifySplittedLines()

    def name(self):
        return 'identifysplittedlines'

    def displayName(self):
        return self.tr('Identifica Linhas Seccionadas sem Motivo')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo identifica se existe alguma linhas que estão seccionadas sem motivo: não é interseção nem há mudança de atributos")
    
