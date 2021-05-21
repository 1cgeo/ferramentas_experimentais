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
                        QgsProcessingParameterFile
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
        
        multiGeometries = []
        features = list(lines.getFeatures())
        for currentFeature in features:
            mls = core.QgsMultiLineString()
            mls.addGeometry( core.QgsLineString( list(currentFeature.geometry().vertices()) ) )
            for idx, currenMls in enumerate(multiGeometries):
                if not currenMls:
                    continue
                if core.QgsGeometry( mls.clone() ).intersects( core.QgsGeometry( currenMls.clone() ) ):
                    for element in core.QgsGeometry( currenMls.clone() ).asGeometryCollection():
                        mls.addGeometry( core.QgsLineString( list(element.vertices()) ) )
                    multiGeometries[idx] = None
            multiGeometries.append(mls)

        for currenMls in multiGeometries:
            if not currenMls:
                continue
            self.addSink( core.QgsGeometry( currenMls.clone() ), core.QgsGeometry( currenMls.clone() ).length(), sink_l, fields)
        return {self.OUTPUT_L: sinkId_l}

    def addSink(self, geom, length, sink, fields):
        newFeat = QgsFeature(fields)
        newFeat.setGeometry(geom)
        newFeat['length'] = length
        sink.addFeature(newFeat)

    def getFeatureRequest(self, geometry, crs, distance, segment=5):
        return QgsFeatureRequest().setFilterRect(
            geometry.buffer(distance, segment).boundingBox()
        )

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
        return self.tr("O algoritmo ...")
    