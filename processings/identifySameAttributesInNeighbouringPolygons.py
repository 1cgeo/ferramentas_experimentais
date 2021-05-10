from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsPointXY,
                       QgsFeature,
                       QgsProcessingParameterVectorLayer,
                       QgsField,
                       QgsFields,
                       QgsFeatureRequest,
                       QgsGeometryUtils,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsGeometry,
                       QgsFeatureRequest,
                       QgsExpression
                       )
from qgis import processing
import math
class IdentifySameAttributesInNeighbouringPolygons(QgsProcessingAlgorithm): 

    INPUT_LAYER = 'INPUT_LAYER'
    INPUT_FIELDS = 'INPUT_FIELDS'
    INPUT_MAX_AREA = 'INPUT_MAX_AREA'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_LAYER',
                self.tr('Selecione a camada'),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                'INPUT_FIELDS',
                self.tr('Selecione os campos que serão analisados'), 
                type=QgsProcessingParameterField.Any, 
                parentLayerParameterName='INPUT_LAYER',
                allowMultiple=True)
            )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                'INPUT_MAX_AREA',
                self.tr('Insira a área máxima dos poligonos analisados'), 
                type=QgsProcessingParameterNumber.Double, 
                optional = True,
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
        maxArea = self.parameterAsDouble(parameters,'INPUT_MAX_AREA', context)
        allFeatures = layer.getFeatures()
        if  maxArea>0:
            expr = QgsExpression( "$area < " + str(maxArea))
            allFeatures = layer.getFeatures(QgsFeatureRequest(expr))
        polygonsFlag = []
        

        for feature in allFeatures:
            if feedback.isCanceled():
                return {self.OUTPUT: polygonsAndfields}
            featgeom = feature.geometry()
            neighbouringPolygons = self.polygonsTouched(layer, feature)
            if len(neighbouringPolygons) == 0:
                continue 
            for neighbourPolygon in neighbouringPolygons:
                fieldsNotChanged = []
                fieldsNotChanged = self.nonChangedFields(inputFields, neighbourPolygon, feature)
                if len(fieldsNotChanged) == len(inputFields):
                    polygonsFlag.append(feature)
                
        if len(polygonsFlag)==0:
            return{self.OUTPUT: 'nenhuma imutabilidade de atributos encontrada'}
        newLayer = self.outLayer(parameters, context, polygonsFlag, layer, 6)
        return{self.OUTPUT: newLayer}

    def polygonsTouched(self, layer, polygon):
        polygons = []
        AreaOfInterest = polygon.geometry().boundingBox()
        request = QgsFeatureRequest().setFilterRect(AreaOfInterest)
        for feat in layer.getFeatures(request):
            if polygon.geometry().touches(feat.geometry()) or polygon.geometry().intersects(feat.geometry()):
                if not str(polygon.geometry())==str(feat.geometry()):
                    polygons.append(feat)
        return polygons
    
    def nonChangedFields(self, inputFields, feature1, feature2):
        equalFields = []
        for field in inputFields:
            if feature1[field] == feature2[field]:
                equalFields.append(field)
        return equalFields
    def outLayer(self, parameters, context, features, layer, geomType):
        newField = features[0].fields()
        

        (sink, newLayer) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            newField,
            geomType,
            layer.sourceCrs()
        )
        
        for feature in features:
            newFeat = QgsFeature()
            newFeat.setGeometry(feature.geometry())
            newFeat.setFields(newField)
            for field in  range(len(feature.fields())):
                newFeat.setAttribute((field), feature.attribute((field)))
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
        
        return newLayer
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return IdentifySameAttributesInNeighbouringPolygons()

    def name(self):
        return 'identifysameattributesinneighbouringpolygons'

    def displayName(self):
        return self.tr('Identifica Imutabilidade de Atributo em Poligonos Vizinhos')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo identifica se existe algum atributo não mudou entre poligonos vizinhos e com área menor que a definida")
    
