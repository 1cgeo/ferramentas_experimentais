# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsCoordinateReferenceSystem,
                       QgsProcessingParameterMultipleLayers,
                       QgsFeature,
                       QgsProcessingParameterVectorLayer,
                       QgsFields,
                       QgsFeatureRequest,
                       QgsProcessingParameterNumber,
                       QgsGeometry,
                       QgsPointXY
                       )
from qgis import processing
from qgis import core, gui
from qgis.utils import iface
import math
class IdentifyUndershootLines(QgsProcessingAlgorithm): 

    INPUT_LAYERS = 'INPUT_LAYER_LIST'
    INPUT_MIN_DIST= 'INPUT_MIN_DIST'
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
            QgsProcessingParameterNumber(
                'INPUT_MIN_DIST',
                self.tr('Insira o valor da distância'), 
                type=QgsProcessingParameterNumber.Double, 
                minValue=0)
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
                self.tr('Flag Linha Próxima à Moldura')
            )
        ) 
    def processAlgorithm(self, parameters, context, feedback):      
        feedback.setProgressText('Procurando linhas...')
        layerList = self.parameterAsLayerList(parameters,'INPUT_LAYER_LIST', context)
        frameLayer = self.parameterAsVectorLayer(parameters,'INPUT_FRAME', context)
        minDist = self.parameterAsDouble(parameters,'INPUT_MIN_DIST', context)
        CRSstr = iface.mapCanvas().mapSettings().destinationCrs().authid()
        CRS = QgsCoordinateReferenceSystem(CRSstr)
        
        points = []
        
        listSize = len(layerList)
        progressStep = 100/listSize if listSize else 0
        step = 0
        for frame in frameLayer.getFeatures():
            FrameArea = frame.geometry().boundingBox()
            request = QgsFeatureRequest().setFilterRect(FrameArea)
            multiPointGeom = core.QgsGeometry.fromMultiPointXY([ core.QgsPointXY( v ) for v in frame.geometry().vertices() ])
            for step,layer in enumerate(layerList):
                if feedback.isCanceled():
                    return {self.OUTPUT: points}       
                features = layer.getFeatures(request)
                for feature in features:
                    featgeom = feature.geometry()
                    for geometry in featgeom.constGet():
                        ptIni = QgsGeometry.fromPointXY(QgsPointXY(geometry[0]))
                        ptFin = QgsGeometry.fromPointXY(QgsPointXY(geometry[-1]))
                        if not(multiPointGeom.intersects(ptIni)) and not( self.touchesOtherLine(layer, feature, ptIni) ) and frame.geometry().closestSegmentWithContext(QgsPointXY(geometry[0]))[0] < minDist:
                            points.append(geometry[0])
                        if not(multiPointGeom.intersects(ptFin)) and not( self.touchesOtherLine(layer, feature, ptFin) ) and frame.geometry().closestSegmentWithContext(QgsPointXY(geometry[-1]))[0] < minDist:
                            points.append(geometry[-1])            
            feedback.setProgress( step * progressStep )
        returnMessage = ('Nenhuma linha encontrada!')
        if not len(points) == 0 :
            newLayerId = self.outLayer(parameters, context, points, CRS, 4)
            returnMessage = newLayerId
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
  
    def outLayer(self, parameters, context, geometry, CRS, geomType):
        newField = QgsFields()
        

        (sink, newLayerId) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            newField,
            geomType,
            CRS
        )
        
        for geom in geometry:
            newFeat = QgsFeature()
            newFeat.setGeometry(geom)
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
        
        return newLayerId
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return IdentifyUndershootLines()

    def name(self):
        return 'identifyundershootlines'

    def displayName(self):
        return self.tr('Identifica Linhas Próximas à Moldura')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo identifica se existe alguma linha próxima a moldura")
    
