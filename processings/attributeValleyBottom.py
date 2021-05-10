# -*- coding: utf-8 -*-

from qgis import processing
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing, QgsProject,
                       QgsFeatureSink, QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingParameterString,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingFeatureSourceDefinition,
                       QgsProcessingParameterNumber,
                       QgsFeature, QgsVectorLayer,
                       QgsProcessingParameterVectorDestination,
                       QgsGeometry, QgsField, QgsPoint,
                       QgsFields, QgsWkbTypes,
                       QgsProcessingFeatureSourceDefinition,
                       QgsProperty, QgsFeatureRequest
                       )

class AttributeValleyBottom(QgsProcessingAlgorithm):

    INPUT_FRAMES = 'INPUT_FRAMES'
    LAYER = 'LAYER'
    WATERBODY = 'WATERBODY'
    CUT_DISTANCE = 'CUT_DISTANCE'
    TOLERANCE = 'TOLERANCE'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_FRAMES,
                self.tr('Select frame layer'),
                [QgsProcessing.TypeVectorPolygon, QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.LAYER,
                self.tr('Layers to attribute'),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.WATERBODY,
                self.tr('Selct the water body layer'),
                types=[QgsProcessing.TypeVectorPolygon, QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.CUT_DISTANCE,
                self.tr('Distance to cut'),
                QgsProcessingParameterNumber.Double,
                defaultValue=20.0
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.TOLERANCE,
                self.tr('Maximum distance between initial vertex and frames'),
                QgsProcessingParameterNumber.Double,
                defaultValue=2.0
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        extents = self.parameterAsSource(parameters, self.INPUT_FRAMES, context)
        layer = self.parameterAsVectorLayer(parameters, self.LAYER, context)
        waterbody = self.parameterAsVectorLayer(parameters, self.WATERBODY, context)
        cut_size = self.parameterAsDouble(parameters, self.CUT_DISTANCE, context)
        tol = self.parameterAsDouble(parameters, self.TOLERANCE, context)

        crs = QgsProject.instance().crs()

        extentsLayer = self.setupExtentsLayer(extents, crs)

        lineList, areaList = self.addLayerInList(waterbody, extentsLayer)

        dangles_points = self.identifyDangles(layer, tol, lineFilterLayers=lineList, areaFilterLayers=areaList)

        feats_to_cut = self.verifyIfFirstVertex(dangles_points, layer)

        self.setupNewFeats(feats_to_cut, layer, cut_size)

        return {self.OUTPUT: f'{len(feats_to_cut)} feições alteradas'}

    def setupExtentsLayer(self, extents, sourceCrs):
        feats = list(extents.getFeatures())
        wkb_list = {
            2: 'LineString',
            3: 'Polygon',
            5: 'MultiLineString',
            6: 'MultiPolygon',
        }
        wkb_id = feats[0].geometry().wkbType()
        uri = f"{wkb_list.get(wkb_id)}?crs={sourceCrs.authid().lower()}"
        vectorLayer = QgsVectorLayer(uri, "Scratch",  "memory")
        dataProvider = vectorLayer.dataProvider() 
        for feat in feats:
            to_insert = QgsFeature()
            to_insert.setGeometry(feat.geometry())
            dataProvider.addFeatures([to_insert])
        return vectorLayer

    def addLayerInList(self, *layers):
        lineList = []
        areaList = []
        for layer in layers:
            if layer.geometryType() == QgsWkbTypes.LineGeometry:
                lineList.append(layer)
            elif layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                areaList.append(layer)
        return lineList, areaList

    def identifyDangles(self, layer, radius, lineFilterLayers=None, areaFilterLayers=None):
        dangles = processing.run(
            'dsgtools:identifydangles',
            {
                'INPUT': layer,
                'SELECTED': False,
                'LINEFILTERLAYERS': lineFilterLayers,
                'POLYGONFILTERLAYERS': areaFilterLayers,
                'IGNOREINNER': True,
                'TYPE': False,
                'TOLERANCE': radius,
                'FLAGS': 'memory:'
            }
        )['FLAGS']
        return dangles

    def verifyIfFirstVertex(self, lyrPoints, lyrLines):
        lines_to_cut = []
        spatial_joined = processing.run(
            'native:joinattributesbylocation',
            {
                'INPUT': lyrPoints,
                'JOIN': lyrLines,
                'PREDICATE': [3], # Touches
                'OUTPUT': 'memory:',
            }
        )['OUTPUT']
        for point in spatial_joined.getFeatures():
            request = QgsFeatureRequest().setFilterExpression(f'"id"={point.attribute("id")}')
            lineFeat = next(lyrLines.getFeatures(request))
            locate = lineFeat.geometry().lineLocatePoint(point.geometry())
            if locate < 0.01:
                lines_to_cut.append(lineFeat)
        lyrLines.selectByIds([x.id() for x in lines_to_cut])
        return lines_to_cut
            
    def getLineSubstring(self, layer, startDistance, endDistance):
        r = processing.run(
            'native:linesubstring',
            {   'END_DISTANCE' : endDistance, 
                'INPUT' : QgsProcessingFeatureSourceDefinition(
                    layer.source(),
                    selectedFeaturesOnly=True
                ), 
                'OUTPUT' : 'memory:', 
                'START_DISTANCE' : startDistance 
            }
        )
        return r['OUTPUT']
    
    def setupNewFeats(self, feats_to_cut, layer, cut_distance):
        layer.startEditing()
        newFeats = self.getLineSubstring(layer, 0, cut_distance)
        updatedFeats = self.getLineSubstring(layer, cut_distance, QgsProperty.fromExpression('length( $geometry)'))
        for f in newFeats.getFeatures():
            layer.addFeature(f)
            layer.changeAttributeValue(f.id(), f.fieldNameIndex('tipo'), 3)
            layer.changeAttributeValue(f.id(), f.fieldNameIndex('id'), None)
        for f in feats_to_cut:
            request = QgsFeatureRequest().setFilterExpression(f'"id" = {f.attribute("id")}')
            upfeat = next(updatedFeats.getFeatures(request))
            layer.changeGeometry(f.id(), upfeat.geometry())
            # layer.updateFeature(f)
        layer.removeSelection()

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return AttributeValleyBottom()

    def name(self):
        return 'Attribute valley bottoms'

    def displayName(self):
        return self.tr('Attribute valley bottoms')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("Atribute valley bottoms")
