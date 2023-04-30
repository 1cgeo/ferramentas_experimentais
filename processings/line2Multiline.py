# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import QCoreApplication, QVariant
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
                        QgsPointXY,
                        QgsProcessingParameterFile,
                        QgsLineString
                    )
from qgis import processing
from qgis import core, gui
from qgis.utils import iface
import math
import uuid

class Line2Multiline(QgsProcessingAlgorithm): 

    INPUT_LINE = 'INPUT_LINE'
    OUTPUT_L = 'OUTPUT_L'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LINE,
                self.tr('Selecionar camada:'),
                [QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_L,
                self.tr('multiline')
            )
        ) 


    def processAlgorithm(self, parameters, context, feedback):      
        lines = self.parameterAsVectorLayer(parameters, self.INPUT_LINE, context)

        fields = core.QgsFields()
        fields.append(core.QgsField('length', QVariant.String))
        (sink_l, sinkId_l) = self.parameterAsSink(
            parameters,
            self.OUTPUT_L,
            context,
            fields,
            core.QgsWkbTypes.MultiLineString,
            QgsCoordinateReferenceSystem( iface.mapCanvas().mapSettings().destinationCrs().authid() )
        )

        lines = self.runAddCount(lines, feedback=feedback)
        self.runCreateSpatialIndex(lines, feedback=feedback)
        spatialJoinOutput = self.runSpatialJoin(lines, lines, feedback=feedback)

        self.id_to_feature = {}
        self.ids_in_stack = []
        for currentFeature in lines.getFeatures():
            self.id_to_feature[currentFeature['AUTO']] = currentFeature
            self.ids_in_stack.append(currentFeature['AUTO'])

        self.matching_features = {}
        for feat in spatialJoinOutput.getFeatures():
            if feat['AUTO'] not in self.matching_features:
                self.matching_features[feat['AUTO']] = []
            if feat['AUTO'] != feat['AUTO_2']:
                	self.matching_features[feat['AUTO']].append(feat['AUTO_2'])

        while len(self.ids_in_stack) > 0:
            currentid = self.ids_in_stack[0]
            del self.ids_in_stack[0]

            mls_array = self.aggregate(currentid)

            mls = core.QgsMultiLineString()
            for el in mls_array:
                mls.addGeometry( QgsLineString( list(el.vertices()) ) )
            self.addSink( QgsGeometry( mls ), sink_l, fields)

        return {self.OUTPUT_L: sinkId_l}


    def aggregate(self, featureId):
        currentfeature = self.id_to_feature[featureId]
        currentgeom = currentfeature.geometry()
        mls_array = []
        mls_array.append(currentgeom)

        matching_features_id = [el for el in self.matching_features[featureId] if el in self.ids_in_stack]
        
        for match_id in matching_features_id:
            self.ids_in_stack.remove(match_id)
        
        for match_id in matching_features_id:
            agg_array = self.aggregate(match_id)
            mls_array = mls_array + agg_array

        return mls_array

    def runSpatialJoin(self, streamLayerInput, countourLayer, feedback):
        output = processing.run(
            'native:joinattributesbylocation',
            {
                'INPUT': streamLayerInput,
                'JOIN': countourLayer,
                'PREDICATE': [0],
                'JOIN_FIELDS': [],
                'METHOD': 0,
                'DISCARD_NONMATCHING': True,
                'PREFIX': '',
                'OUTPUT': 'TEMPORARY_OUTPUT' 
            },
            feedback=feedback
        )
        return output['OUTPUT']
    
    def runAddCount(self, inputLyr, feedback):
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
            },
            feedback=feedback
        )
        return output['OUTPUT']

    def runCreateSpatialIndex(self, inputLyr, feedback):
        processing.run(
            "native:createspatialindex",
            {'INPUT':inputLyr},
            feedback=feedback
        )

    def addSink(self, geom, sink, fields):
        newFeat = QgsFeature(fields)
        newFeat.setGeometry(geom)
        newFeat['length'] = geom.length()
        sink.addFeature(newFeat, QgsFeatureSink.FastInsert)

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Line2Multiline()

    def name(self):
        return 'line2multiline'

    def displayName(self):
        return self.tr('Converte linha para multilinha')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo converte linhas que se tocam para multilinha")
    
