# -*- coding: utf-8 -*-

from qgis import processing
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsRectangle, QgsProcessing, QgsProject,
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
                       QgsFields, QgsWkbTypes, QgsPointXY,
                       QgsProperty, QgsFeatureRequest,
                       QgsGeometryUtils, QgsLineString,
                       QgsRasterLayer, QgsRaster, QgsRasterShader,
                       QgsCoordinateReferenceSystem,
                       QgsProcessingParameterRasterDestination, QgsProcessingParameterRasterLayer, QgsProcessingContext)

class QuadtreeDivisionVec(QgsProcessingAlgorithm):
    INPUT_VECTOR = 'INPUT_VECTOR'
    THRESHOLD = 'THRESHOLD'
    OUTPUT_AREAS = 'OUTPUT_AREAS'

    def initAlgorithm(self, config = None):
        self.addParameter(
                QgsProcessingParameterVectorLayer(
                self.INPUT_VECTOR,
                self.tr('Select vector layers to be analyzed:'),
                [ QgsProcessing.TypeVectorLine ],
                optional = False
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.THRESHOLD,
                self.tr('Maximum value of the sum of attributes:'),
                QgsProcessingParameterNumber.Double,
                defaultValue = 20
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_AREAS,
                self.tr('Divided polygon'),
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.inicialVectorLayer(parameters, self.INPUT_VECTOR, context)
        inputLayer = self.parameterAsVectorLayer(parameters, self.INPUT_VECTOR, context)
        threshold = self.parameterAsDouble(parameters, self.THRESHOLD, context)
        crs = inputLayer.crs().authid().lower()

        notapproved = [layer]
        approved = []

        while len(notapproved) > 0:
            l = notapproved.pop(0)
            l_sum = self.calcSumPoly(inputLayer, l)
            feature = list(l_sum.getFeatures())[0]
            if feature['LENGTH'] > threshold:
                halflayer = self.breakPolygon(parameters, l, context, inputLayer)
                notapproved.extend(list(halflayer))
            else:
                approved.append(l_sum)
                
        newLayer = processing.run(
            "qgis:mergevectorlayers",
            {
              'LAYERS': approved, 
              'CRS': crs, 
              'OUTPUT': 'TEMPORARY_OUTPUT'
            }
        )

        fields = QgsFields()
        fields.append(QgsField('soma', QVariant.Double))
        (sink_l, sinkId_l) = self.parameterAsSink(
            parameters,
            self.OUTPUT_AREAS,
            context,
            fields,
            QgsWkbTypes.MultiPolygon,
            QgsCoordinateReferenceSystem(crs)
        )
        self.addSink(newLayer['OUTPUT'], sink_l, fields)
        return {self.OUTPUT_AREAS : sinkId_l}

    def addSink(self, inputLayer, sink, fields):
        for oldFeat in inputLayer.getFeatures():
            newFeat = QgsFeature()
            newFeat.setFields(fields)
            newFeat['soma'] = oldFeat['LENGTH']
            newFeat.setGeometry(oldFeat.geometry())
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)

    def inicialVectorLayer(self, parameters, inputLayer, context):
        inputLayer = self.parameterAsVectorLayer(parameters, self.INPUT_VECTOR, context)
        crs = inputLayer.crs().authid().lower()
        geom = QgsGeometry.fromRect(inputLayer.extent())
        ftr = QgsFeature()
        ftr.setGeometry(geom)
        layer = QgsVectorLayer('Polygon?crs={}'.format(crs), 'Polygon_0', 'memory')
        layer.dataProvider().addFeatures([ftr])

        return layer

    def breakPolygon(self, parameters, layer, context, inputLayer):
        inputLayer = self.parameterAsVectorLayer(parameters, self.INPUT_VECTOR, context)
        crs = inputLayer.crs().authid().lower()
        coord = layer.extent()
        xmax = coord.xMaximum()
        ymax = coord.yMaximum()
        xmin = coord.xMinimum()
        ymin = coord.yMinimum()

        rect1 = QgsRectangle(xmin, ymin, (xmin + xmax)/2, (ymin + ymax)/2)
        geom1 = QgsGeometry.fromRect(rect1)
        ftr1 = QgsFeature()
        ftr1.setGeometry(geom1)
        halflayer1 = QgsVectorLayer('Polygon?crs={}'.format(crs), 'Test_Polygon_1', 'memory')
        halflayer1.dataProvider().addFeatures([ftr1])

        rect2 = QgsRectangle((xmin + xmax)/2, ymin, xmax, (ymin + ymax)/2)
        geom2 = QgsGeometry.fromRect(rect2)
        ftr2 = QgsFeature()
        ftr2.setGeometry(geom2)
        halflayer2 = QgsVectorLayer('Polygon?crs={}'.format(crs), 'Test_Polygon_2', 'memory')
        halflayer2.dataProvider().addFeatures([ftr2])
        
        rect3 = QgsRectangle(xmin, (ymin + ymax)/2, (xmin + xmax)/2, ymax)
        geom3 = QgsGeometry.fromRect(rect3)
        ftr3 = QgsFeature()
        ftr3.setGeometry(geom3)
        halflayer3 = QgsVectorLayer('Polygon?crs={}'.format(crs), 'Test_Polygon_3', 'memory')
        halflayer3.dataProvider().addFeatures([ftr3])

        rect4 = QgsRectangle((xmin + xmax)/2, (ymin + ymax)/2, xmax, ymax)
        geom4 = QgsGeometry.fromRect(rect4)
        ftr4 = QgsFeature()
        ftr4.setGeometry(geom4)
        halflayer4 = QgsVectorLayer('Polygon?crs={}'.format(crs), 'Test_Polygon_4', 'memory')
        halflayer4.dataProvider().addFeatures([ftr4])

        return halflayer1, halflayer2, halflayer3, halflayer4
    
    def calcSumPoly(self, inputLayer, polygon):
        params = {
            'LINES' : inputLayer,
            'POLYGONS' : polygon,
            'LEN_FIELD' : 'LENGTH',
            'COUNT_FIELD' : 'COUNT',
            'OUTPUT' : 'TEMPORARY_OUTPUT'
        }
        result = processing.run('native:sumlinelengths', params)
        
        return result['OUTPUT']

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return QuadtreeDivisionVec()

    def name(self):
        return 'quadtreeDivisionVec'

    def displayName(self):
        return self.tr('quadtreeDivisionVec')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("QuadtreeDivisionVec")