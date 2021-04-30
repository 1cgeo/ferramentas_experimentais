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
                       QgsFields,
                       QgsFeatureRequest,
                       QgsGeometryUtils,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsGeometry
                       )
from qgis import processing
from qgis.utils import iface
import math
class IdentifyDiscontinuitiesInLines(QgsProcessingAlgorithm): 

    INPUT_LAYER = 'INPUT_LAYER'
    INPUT_FIELDS = 'INPUT_FIELDS'
    INPUT_ANGLE = 'INPUT_ANGLE'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_LAYER',
                self.tr('Selecione a camada'),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                'INPUT_FIELDS',
                self.tr('Selecione os campos que serão analisados'), 
                type=QgsProcessingParameterField.Any, 
                parentLayerParameterName='INPUT_LAYER', 
                defaultValue = 'nome',
                allowMultiple=True)
            )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                'INPUT_ANGLE',
                self.tr('Insira o desvio máximo (em graus) para detectar continuidade'), 
                type=QgsProcessingParameterNumber.Double, 
                minValue=0)
            )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Camada de Inconsistências:')
            )
        ) 
    def processAlgorithm(self, parameters, context, feedback):      
        feedback.setProgressText('Procurando descontinuidades...')
        layer = self.parameterAsVectorLayer(parameters,'INPUT_LAYER', context)
        inputFields = self.parameterAsFields( parameters,'INPUT_FIELDS', context )
        angle = self.parameterAsDouble(parameters,'INPUT_ANGLE', context)
        pointsAndFields= []
        for feature in layer.getFeatures():
            if feedback.isCanceled():
                return {self.OUTPUT: pointsAndfields}
            featgeom = feature.geometry()
            for geometry in featgeom.constGet():
                ptFin = QgsGeometry.fromPointXY(QgsPointXY(geometry[-1]))
                lineTouched = self.linesTouched(layer, feature, ptFin)
            if len(lineTouched) == 0:
                continue 
            for line in lineTouched:
                fieldsChanged = []
                if self.anglesBetweenLines(feature, line, ptFin) < (180 + angle) and self.anglesBetweenLines(feature, line, ptFin) > (180 - angle):
                    fieldsChanged = self.changedFields(inputFields, feature, line)
                    nameOfFields = self.fieldsName(fieldsChanged)
                    if len(fieldsChanged) == 0:
                        continue
                    if [ptFin,nameOfFields] not in pointsAndFields:
                        pointsAndFields.append([ptFin, nameOfFields])
                
        if len(pointsAndFields)==0:
            return{self.OUTPUT: 'nenhuma descontinuidade encontrada'}
        newLayer = self.outLayer(parameters, context, pointsAndFields, layer, 4)
        return{self.OUTPUT: newLayer}

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
    
    def adjacentPoint(self, line, point):
        vertexPoint = line.geometry().closestVertexWithContext(point)[1]
        adjpoints = line.geometry().adjacentVertices(vertexPoint)
        adjptvertex = adjpoints[0]
        if adjptvertex<0:
            adjptvertex = adjpoints[1]
        adjpt = line.geometry().vertexAt(adjptvertex)
        return QgsPointXY(adjpt)

    def anglesBetweenLines(self, line1, line2, point):
        pointB = QgsPointXY(point.asPoint())
        pointA = self.adjacentPoint(line1, pointB)
        pointC = self.adjacentPoint(line2, pointB)
        angleRad = QgsGeometryUtils().angleBetweenThreePoints(pointA.x(), pointA.y(), pointB.x(), pointB.y(), pointC.x(), pointC.y())
        angle = math.degrees(angleRad)

        return abs(angle)


    
    def changedFields(self, inputFields, feature1, feature2):
        equalFields = []
        for field in inputFields:
            if not feature1[field] == feature2[field]:
                equalFields.append(field)
        return equalFields

    def fieldsName(self, inputFields):
        text = ''
        for field in inputFields:
            if text =='':
                text = field
            else:
                text += ', ' + field
        return text
    def outLayer(self, parameters, context, pointsAndFields, layer, geomType):
        newField = QgsFields()
        newField.append(QgsField('Campos que Mudaram', QVariant.String))
        

        (sink, newLayer) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            newField,
            geomType,
            layer.sourceCrs()
        )
        
        for feature in pointsAndFields:
            newFeat = QgsFeature()
            newFeat.setGeometry(feature[0])
            newFeat.setFields(newField)
            newFeat['Campos que Mudaram'] = feature[1]
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
        
        return newLayer
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return IdentifyDiscontinuitiesInLines()

    def name(self):
        return 'identifydiscontinuitiesinlines'

    def displayName(self):
        return self.tr('Identifica Descontinuidade em Linhas')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo identifica se existe alguma descontinuidade entre linhas nos campos escolhidos e dentro da tolerância para continuidade")
    