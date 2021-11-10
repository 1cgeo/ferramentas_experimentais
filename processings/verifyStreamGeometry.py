# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from qgis.core import (QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsFeature,
                       QgsProcessingParameterVectorLayer,
                       QgsPointXY,
                       QgsField,
                       QgsFields,
                       QgsProcessingParameterField,
                       QgsFeatureRequest,
                       QgsGeometry,
                       QgsWkbTypes,
                       QgsProcessing
                       )
from qgis import processing
from qgis.utils import iface
import csv
class VerifyStreamGeometry(QgsProcessingAlgorithm): 

    STREAM = 'STREAM'
    FIELDS = 'FIELDS'
    OUTPUT = 'OUTPUT'
    
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'STREAM',
                self.tr('Selecionar camada de rede'),
                [QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                'FIELDS',
                self.tr('Selecionar os campos:'),
                parentLayerParameterName = 'STREAM',
                allowMultiple = True
            )
        )


        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Flag Geometria de Rede')
            )
        ) 

    def processAlgorithm(self, parameters, context, feedback):      
        feedback.setProgressText('Iniciando...')
        returnMessage = 'Nenhuma inconsistência encontrada'
        inputStreamLayer = self.parameterAsVectorLayer(parameters, 'STREAM', context)
        fields = self.parameterAsFields(parameters, 'FIELDS', context)
        streamLayer = self.runAddCount(inputStreamLayer)
        self.runCreateSpatialIndex(streamLayer)
        progressStep = 100/streamLayer.featureCount() if streamLayer.featureCount() else 0
        flagsGeomPoints = []
        flagsGeomMoreThan2Inter = []
        flagsGeomSeg = []
        flagsGeomNotInter = []
        for step, line1 in enumerate(streamLayer.getFeatures()):
            line1Geom = line1.geometry()
            flag1, flag2 = self.verifyLineEndPoints(streamLayer, line1, flagsGeomPoints, fields)
            flagsGeomMoreThan2Inter.extend(flag1)
            flagsGeomSeg.extend(flag2)
            flagsGeomPoints.extend(flag1)
            flagsGeomPoints.extend(flag2)
            flag = self.verifyNotInterLines(streamLayer, line1Geom, flagsGeomPoints)
            flagsGeomNotInter.extend(flag)
            flagsGeomPoints.extend(flag)
            feedback.setProgress( step * progressStep )
        flags = []
        for flag1 in flagsGeomMoreThan2Inter:
            flags.append([flag1, 1])
        for flag2 in flagsGeomSeg:
            flags.append([flag2, 2])
        for flag3 in flagsGeomNotInter:
            flags.append([flag3, 3])
        if flags:
            newLayer = self.outLayer(parameters, context, flags, streamLayer)
            returnMessage = 'Camada de flags gerada'
        
        return{self.OUTPUT: returnMessage}

    def verifyLineEndPoints(self, layer, line1, flags, fields):
        flagsGeomMoreThan2Inter = [] # geom p/ verif pto não repetido, feat pode ser dif, mas a geom ser igual
        flagsGeomSeg = []
        line1Geom = line1.geometry()
        points = self.getFirstAndLastPoints(line1Geom)
        for pt in points:
            if self.geomInGeomList(pt, flags) or self.geomInGeomList(pt, flagsGeomMoreThan2Inter) or self.geomInGeomList(pt, flagsGeomSeg):
                continue
            AreaOfInterest = pt.boundingBox()
            request = QgsFeatureRequest().setFilterRect(AreaOfInterest)
            numberOfIntersections = 0
            isEqual = True
            for line2 in layer.getFeatures(request):
                line2Geom = line2.geometry()
                if line1Geom.equals(line2Geom):
                    continue
                if pt.touches(line2Geom):
                    numberOfIntersections += 1
                    for field in fields:
                        if not line1[field]==line2[field]:
                            isEqual = False
                            break
            maxIntersecionsPoints = 2
            if numberOfIntersections>maxIntersecionsPoints:
                flagsGeomMoreThan2Inter.append(pt)
            if numberOfIntersections==1 and isEqual:
                flagsGeomSeg.append(pt)
        return (flagsGeomMoreThan2Inter, flagsGeomSeg)
    
    def verifyNotInterLines(self, layer, line1Geom, flags):
        shouldBeIntersected = []
        AreaOfInterest = line1Geom.boundingBox()
        request = QgsFeatureRequest().setFilterRect(AreaOfInterest)
        for line2 in layer.getFeatures(request):
            line2Geom = line2.geometry()
            if line1Geom.equals(line2Geom):
                continue
            interPt =  line1Geom.intersection(line2Geom)
            interPtList = []
            if not (interPt.type()==QgsWkbTypes.PointGeometry ):
                if interPt.isNull() or interPt.isEmpty():
                    continue
                for geom in interPt.constGet():
                    try:
                        pt = QgsGeometry().fromPointXY(QgsPointXY(geom[0]))
                    except:
                        pt = QgsGeometry().fromPointXY(QgsPointXY(geom))
                shouldBeIntersected.append(pt)
                continue
            if interPt.isMultipart():
                for eachPt in interPt.constGet():
                    interPtList.append(QgsGeometry().fromPointXY(QgsPointXY(eachPt)))
            else:
                interPtList.append(interPt)
            touches = False
            points = self.getFirstAndLastPoints(line2Geom)
            for pt1 in interPtList:
                if self.geomInGeomList(pt1, flags) or self.geomInGeomList(pt1, shouldBeIntersected):
                    continue
                for pt2 in points:
                    if pt2.intersects(interPt):
                        touches = True
                        break
                if not touches:
                    shouldBeIntersected.append(pt1)
        
        return shouldBeIntersected


    def getFirstAndLastPoints(self, lineGeometry):
        if lineGeometry.isMultipart():
            for geometry in lineGeometry.constGet():
                ptLast = QgsGeometry().fromPointXY(QgsPointXY(geometry[-1]))
                ptFirst = QgsGeometry().fromPointXY(QgsPointXY(geometry[0]))
        else:
            geometry = lineGeometry.asPolyline()
            ptLast = QgsGeometry().fromPointXY(QgsPointXY(geometry[-1]))
            ptFirst = QgsGeometry().fromPointXY(QgsPointXY(geometry[0]))
        return [ptFirst, ptLast]
    
    def geomInGeomList(self, geom, geomlist):
        for geometry in geomlist:
            if geom.equals(geometry):
                return True
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

    def outLayer(self, parameters, context, flags, streamLayer):
        newField = QgsFields()
        newField.append(QgsField('id', QVariant.Int))
        newField.append(QgsField('erro', QVariant.String))

        (sink, newLayer) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            newField,
            1,
            streamLayer.sourceCrs()
        )

        idcounter = 1
        dicterro = {
            1:'Interseção com mais de 2 linhas',
            2:'Não está mergeada',
            3:'Não está cortada'
         }
        for flagarray in flags:
            newFeat = QgsFeature()
            newFeat.setGeometry(flagarray[0])
            newFeat.setFields(newField)
            newFeat['id'] = idcounter
            newFeat['erro'] = dicterro[flagarray[1]]
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
            idcounter +=1
        return newLayer
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return VerifyStreamGeometry()

    def name(self):
        return 'verifystreamgeometry'

    def displayName(self):
        return self.tr('Verificar Geometria da Rede')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo identifica se existe inconsistências na geometria da rede. Os campos selecionados são analisados para verificar linhas que deveriam estar mergeadas por possuir atributos iguais.")
    
