# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
                        QgsProcessing,
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

class MergeRivers(QgsProcessingAlgorithm): 

    INPUT_LAYER_L = 'INPUT_LAYER_L'
    INPUT_FRAME_A = 'INPUT_FRAME_A'
    OUTPUT_LAYER_L = 'OUTPUT_LAYER_L'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER_L,
                self.tr('Selecionar camada de drenagem'),
                [QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_FRAME_A,
                self.tr('Selecionar camada de moldura'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LAYER_L,
                self.tr('drenagem_mesclada')
            )
        ) 

    def processAlgorithm(self, parameters, context, feedback):      
        drainageLayer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER_L, context)
        frameLayer = self.parameterAsVectorLayer(parameters, self.INPUT_FRAME_A, context)

        (sink_l, sinkId_l) = self.parameterAsSink(
            parameters,
            self.OUTPUT_LAYER_L,
            context,
            drainageLayer.fields(),
            core.QgsWkbTypes.MultiLineString,
            QgsCoordinateReferenceSystem( iface.mapCanvas().mapSettings().destinationCrs().authid() )
        )

        clippedDrainageLayer = self.clipLayer( drainageLayer, frameLayer)

        merge = {}
        for drainageFeature in clippedDrainageLayer.getFeatures():
            if not drainageFeature['nome']:
                continue
            if not( drainageFeature['tipo'] in [1,2] ):
                continue
            mergeKey = '{0}_{1}'.format( drainageFeature['nome'].lower(), drainageFeature['tipo'])
            if not( mergeKey in merge):
                merge[ mergeKey ] = []
            merge[ mergeKey ].append( drainageFeature )

        for mergeKey in merge:
            self.mergeLineFeatures( merge[ mergeKey ], clippedDrainageLayer )

        for feature in clippedDrainageLayer.getFeatures():
            self.addSink( feature, sink_l)
        return {self.OUTPUT_LAYER_L: sinkId_l}
    
    def addSink(self, feature, sink):
        newFeature = QgsFeature( feature.fields() )
        newFeature.setAttributes( feature.attributes() )
        newFeature.setGeometry( feature.geometry() )
        sink.addFeature( newFeature )

    def mergeLineFeatures(self, features, layer):
        layer.startEditing()
        idsToRemove = []
        featureIds = [ f.id() for f in features ]
        for featureAId in featureIds:
            if featureAId in idsToRemove:
                continue
            for featureBId in featureIds:
                if featureAId == featureBId or featureBId in idsToRemove:
                    continue
                featureA = layer.getFeature( featureAId )
                featureB = layer.getFeature( featureBId )
                if not featureA.geometry().touches( featureB.geometry() ):
                    continue
                newGeometry = featureA.geometry().combine( featureB.geometry() ).mergeLines()
                featureA.setGeometry( newGeometry )
                layer.updateFeature( featureA )
                idsToRemove.append( featureBId )
        layer.deleteFeatures( idsToRemove )
        #layer.commitChanges()

    def clipLayer(self, layer, frame):
        r = processing.run(
            'native:clip',
            {   'FIELD' : [], 
                'INPUT' : core.QgsProcessingFeatureSourceDefinition(
                    layer.source()
                ), 
                'OVERLAY' : frame,
                'OUTPUT' : 'TEMPORARY_OUTPUT'
            }
        )
        return r['OUTPUT']

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return MergeRivers()

    def name(self):
        return 'mergerivers'

    def displayName(self):
        return self.tr('Mescla rios')

    def group(self):
        return self.tr('Edi????o')

    def groupId(self):
        return 'edicao'

    def shortHelpString(self):
        return self.tr("O algoritmo ...")
    
