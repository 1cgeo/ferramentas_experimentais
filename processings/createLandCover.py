# -*- coding: utf-8 -*-

import os
import processing

import concurrent.futures

from qgis.core import (QgsFeature, QgsFeatureRequest, QgsFeatureSink, QgsField,
                       QgsFields, QgsProcessing, QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterField,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingFeatureSourceDefinition,
                       QgsProcessingParameterVectorLayer, QgsSpatialIndex, QgsGeometry,
                        QgsWkbTypes
                       )
from qgis.PyQt.QtCore import QCoreApplication, QVariant


class CreateLandCover(QgsProcessingAlgorithm):

    INPUT_FRAME = 'INPUT_FRAME'
    INPUT_CENTROID = 'INPUT_CENTROID'
    INPUT_ATTRIBUTES_CENTROID = 'INPUT_ATTRIBUTES_CENTROID'
    INPUT_BOUNDARY_LINES = 'INPUT_BOUNDARY_LINES'
    INPUT_BOUNDARY_AREAS = 'INPUT_BOUNDARY_AREAS'
    INPUT_DELIMITERS = 'INPUT_DELIMITERS'
    OUTPUT1 = 'OUTPUT1'
    OUTPUT2 = 'OUTPUT2'
    OUTPUT3 = 'OUTPUT3'
    OUTPUT4 = 'OUTPUT4'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_FRAME,
                self.tr('Selecione a moldura'),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_CENTROID,
                self.tr('Selecione o centroide'),
                types=[QgsProcessing.TypeVectorPoint]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.INPUT_ATTRIBUTES_CENTROID,
                self.tr('Selecione os atributos do centroide'),
                type=QgsProcessingParameterField.Any, 
                parentLayerParameterName=self.INPUT_CENTROID,
                allowMultiple=True
            )
        )
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_BOUNDARY_LINES,
                self.tr('Selecione as linhas de limite'),
                QgsProcessing.TypeVectorLine
            )
        )
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_BOUNDARY_AREAS,
                self.tr('Selecione as áreas de limite'),
                QgsProcessing.TypeVectorPolygon
            )
        )
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_DELIMITERS,
                self.tr('Selecione os delimitarores'),
                QgsProcessing.TypeVectorLine
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT1,
                self.tr('cobertura')
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT2,
                self.tr('delimitadores_sem_uso')
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT3,
                self.tr('cobertura_sem_centroide')
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT4,
                self.tr('cobertura_com_centroides_diferente')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        frameLayer = self.parameterAsVectorLayer(parameters, self.INPUT_FRAME, context)
        frameLayer = self.addAutoIncrementalField( frameLayer, feedback )
        self.createSpatialIndex( frameLayer, feedback )

        centroidLayer = self.parameterAsVectorLayer(parameters, self.INPUT_CENTROID, context)
        centroidLayer = self.addAutoIncrementalField( centroidLayer, feedback )
        self.createSpatialIndex( centroidLayer, feedback )

        centroidFieldNames = self.parameterAsFields(parameters, self.INPUT_ATTRIBUTES_CENTROID, context)

        boundaryLineLayers = self.parameterAsLayerList(parameters, self.INPUT_BOUNDARY_LINES, context)
        boundaryLineLayer = self.mergeVectorLayers( 
            boundaryLineLayers, 
            frameLayer.sourceCrs(), 
            feedback=feedback 
        )
        self.createSpatialIndex( boundaryLineLayer, feedback )

        boundaryAreasLayers = self.parameterAsLayerList(parameters, self.INPUT_BOUNDARY_AREAS, context)
        boundaryAreasLayer = self.mergeVectorLayers( 
            boundaryAreasLayers, 
            frameLayer.sourceCrs(), 
            feedback=feedback 
        )
        self.createSpatialIndex( boundaryAreasLayer, feedback )

        delimitersLayers = self.parameterAsLayerList(parameters, self.INPUT_DELIMITERS, context)
        delimitersLayer = self.mergeVectorLayers( 
            delimitersLayers, 
            frameLayer.sourceCrs(), 
            feedback=feedback 
        )
        self.createSpatialIndex( delimitersLayer, feedback )

        feedback.setProgressText( 'Iniciando construção da cobertura terrestre...' ) 
        multiStepFeedback = QgsProcessingMultiStepFeedback( 13, feedback )
        multiStepFeedback.setCurrentStep( 0 )

        multiStepFeedback.pushInfo( 'Convertendo moldura em linha...' )
        frame2LineLayer = self.convertPolygonToLines( 
            frameLayer, 
            feedback=multiStepFeedback 
        )
        multiStepFeedback.setCurrentStep( 1 )

        multiStepFeedback.pushInfo( 'Convertendo áreas de limites em linha...' )
        boundaryAreas2LineLayer = self.convertPolygonToLines( 
            boundaryAreasLayer, 
            feedback=multiStepFeedback 
        )
        multiStepFeedback.setCurrentStep( 2 )
        
        multiStepFeedback.pushInfo( 'Mergeando linhas...' )
        allLineLayers = [ boundaryAreas2LineLayer, boundaryLineLayer, delimitersLayer ]
        allMergedLinesLayer = self.mergeVectorLayers( 
            allLineLayers, 
            frameLayer.sourceCrs(), 
            feedback=multiStepFeedback 
        )
        multiStepFeedback.setCurrentStep( 3 )

        multiStepFeedback.pushInfo( 'Mergeando linhas com moldura...' )
        mergedLinesWithFrame = self.mergeVectorLayers( 
            [ allMergedLinesLayer , frame2LineLayer ], 
            frameLayer.sourceCrs(), 
            feedback=multiStepFeedback 
        )
        multiStepFeedback.setCurrentStep( 4 )

        multiStepFeedback.pushInfo( 'Seccionando linhas...' )
        sectionedLinesLayer = self.lineOnLineOverlayer( mergedLinesWithFrame, feedback )
        multiStepFeedback.setCurrentStep( 5 )

        multiStepFeedback.pushInfo( 'Gerando áreas...' )
        polygonLayer = self.polygonize(sectionedLinesLayer, feedback)
        multiStepFeedback.setCurrentStep( 6 )

        multiStepFeedback.pushInfo( 'Clipando polígonos na moldura...' )
        self.createSpatialIndex(
            polygonLayer, 
            feedback=multiStepFeedback
        )
        allClippedPolygonsLayer = self.clipLayer( 
            polygonLayer, 
            frameLayer, 
            feedback=multiStepFeedback
        )
        multiStepFeedback.setCurrentStep( 7 )

        multiStepFeedback.pushInfo( 'Removendo áreas de limite...' )
        landCoverLayer = allClippedPolygonsLayer
        self.createSpatialIndex(landCoverLayer, feedback=multiStepFeedback)
        self.removeIntersectionFeatures(landCoverLayer, boundaryAreasLayer)
        multiStepFeedback.setCurrentStep( 8 )

        multiStepFeedback.pushInfo( 'Verficando delimitadores não utilizados...' )
        boundaryLandCoverLayer = self.convertPolygonToLines( 
            landCoverLayer, 
            feedback=multiStepFeedback 
        )
        boundaryLandCoverLayer = self.addAutoIncrementalField( boundaryLandCoverLayer, feedback )
        self.createSpatialIndex( boundaryLandCoverLayer, feedback )
        unusedFeatures = self.checkUnusedDelimiters( boundaryLandCoverLayer, delimitersLayer, feedback=multiStepFeedback )
        multiStepFeedback.setCurrentStep( 9 )

        multiStepFeedback.pushInfo( 'Verficando áreas sem centroides...' )
        featuresWithoutCentroid = self.checkLandCoverWithoutCentroids( landCoverLayer, centroidLayer )
        multiStepFeedback.setCurrentStep( 10 )

        multiStepFeedback.pushInfo( 'Verficando áreas com centroides conflitantes...' )
        featuresDifferentCentroid = self.checkLandCoverDifferentCentroids( landCoverLayer, centroidLayer, centroidFieldNames )

        unusedFeatureLayer = None
        featuresWithoutCentroidLayer = None
        featuresDifferentCentroidLayer = None
        if unusedFeatures:
            unusedFeatureLayer = self.outFeatures(
                self.OUTPUT2, 
                parameters, 
                context, 
                unusedFeatures, 
                frameLayer.sourceCrs(), 
                geometryType=QgsWkbTypes.LineString
            )
        if featuresWithoutCentroid:
            featuresWithoutCentroidLayer = self.outFeatures( 
                self.OUTPUT3,
                parameters, 
                context, 
                featuresWithoutCentroid, 
                frameLayer.sourceCrs(), 
                geometryType=QgsWkbTypes.Polygon
            )
        if featuresDifferentCentroid:
            featuresDifferentCentroidLayer = self.outFeatures( 
                self.OUTPUT4,
                parameters, 
                context, 
                featuresDifferentCentroid, 
                frameLayer.sourceCrs(), 
                geometryType=QgsWkbTypes.Polygon
            )
        if unusedFeatures or featuresDifferentCentroid or featuresWithoutCentroid:
            return {
                self.OUTPUT2: unusedFeatureLayer, 
                self.OUTPUT3: featuresWithoutCentroidLayer, 
                self.OUTPUT4: featuresDifferentCentroidLayer
            }
        multiStepFeedback.setCurrentStep( 11 )

        multiStepFeedback.pushInfo( 'Atributando cobertura terrestre...' )
        attributedLandCoverLayer = self.joinAttributesByLocation( landCoverLayer, centroidLayer, centroidFieldNames, feedback )
        multiStepFeedback.setCurrentStep( 12 )
        
        newLayer = self.outLayer( 
            self.OUTPUT1,
            parameters, 
            context, 
            attributedLandCoverLayer, 
            frameLayer.sourceCrs(), 
            geometryType=QgsWkbTypes.Polygon
        )
        return {self.OUTPUT1: newLayer}
    
    def addAutoIncrementalField(self, inputLyr, feedback):
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

    def convertPolygonToLines(self, inputLayer, feedback):
        output = processing.run(
            "native:polygonstolines",
            {
                'INPUT': inputLayer,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            },
            feedback=feedback
        )
        return output['OUTPUT']

    def difference(self, inputLayer, overlayLayer, feedback):
        output = processing.run(
            "native:difference",
            {
                'INPUT': inputLayer,
                'OVERLAY': overlayLayer,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            },
            feedback=feedback
        )
        return output['OUTPUT']

    def aggregate(self, inputLayer, primaryKeyName, feedback):
        output = processing.run(
            "native:aggregate",
            {
                'AGGREGATES': [{
                    'aggregate': 'sum',
                    'delimiter': ',',
                    'input': '"{0}"'.format(primaryKeyName),
                    'length': 0,
                    'name': primaryKeyName,
                    'precision': 0,
                    'type': 4
                }],
                'GROUP_BY': 'NULL',
                'INPUT': inputLayer,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            },
            feedback=feedback
        )
        return output['OUTPUT']

    def mergeVectorLayers(self, inputLayers, sourceCrs, feedback):
        output = processing.run(
            "native:mergevectorlayers",
            {
                'CRS': sourceCrs,
                'LAYERS': inputLayers,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            },
            feedback=feedback
        )
        return output['OUTPUT']

    def clipLayer(self, layer, frame, feedback):
        r = processing.run(
            'native:clip',
            {   'FIELD' : [], 
                'INPUT' : layer, 
                'OVERLAY' : frame,
                'OUTPUT' : 'TEMPORARY_OUTPUT'
            },
            feedback=feedback
        )
        return r['OUTPUT']

    def lineOnLineOverlayer(self, layer, feedback, selected=False, tolerance=0):
        r = processing.run(
            'dsgtools:lineonlineoverlayer',
            {
                'INPUT' : layer, 
                'SELECTED' : selected,
                'TOLERANCE': tolerance,
                'OUTPUT' : 'TEMPORARY_OUTPUT'
            },
            feedback=feedback
        )
        return r['OUTPUT']

    def createSpatialIndex(self, inputLyr, feedback):
        processing.run(
            "native:createspatialindex",
            {
                'INPUT':inputLyr
            },
            feedback=feedback
        )

    def polygonize(self, layer, feedback):
        output = processing.run(
            "native:polygonize",
            {
                'INPUT': layer,
                'KEEP_FIELDS': False,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            },
            feedback=feedback
        )
        return output['OUTPUT']

    def removeIntersectionFeatures(self, inputLayer, overlayLayer):
        idsToDelete = []
        for inputFeature in inputLayer.getFeatures():
            for overlayFeature in overlayLayer.getFeatures():
                if not overlayFeature.geometry().intersects( inputFeature.geometry().pointOnSurface() ):
                    continue
                idsToDelete.append( inputFeature.id() )
        inputLayer.startEditing()
        inputLayer.deleteFeatures( idsToDelete )

    def checkUnusedDelimiters(self, boundaryLandCoverLayer, delimiterLayer, feedback):
        aggregatedBoundaryLandCoverLayer = self.aggregate( boundaryLandCoverLayer, primaryKeyName='AUTO', feedback=feedback )
        unusedFeatures = []
        diffLayer = self.difference( delimiterLayer, aggregatedBoundaryLandCoverLayer, feedback=feedback )
        return list(diffLayer.getFeatures())

    def checkLandCoverWithoutCentroids(self, landCoverLayer, centroidLayer):
        featuresWithoutCentroid = []
        for landCoverFeature in landCoverLayer.getFeatures():
            hasCeontrid = False
            for centroidFeature in centroidLayer.getFeatures():
                if not( landCoverFeature.geometry().intersects( centroidFeature.geometry() ) ):
                    continue
                hasCeontrid = True
            if hasCeontrid:
                continue
            featuresWithoutCentroid.append( landCoverFeature )
        return featuresWithoutCentroid

    def checkLandCoverDifferentCentroids(self, landCoverLayer, centroidLayer, centroidFieldNames):
        featuresDifferentCentroid = []
        for landCoverFeature in landCoverLayer.getFeatures():
            centroids = []
            for centroidFeature in centroidLayer.getFeatures():
                if not( landCoverFeature.geometry().intersects( centroidFeature.geometry() ) ):
                    continue
                centroids.append( centroidFeature )
            if len(centroids) == 1:
                continue
            different = False
            for i in range(0, len(centroids)):   
                if different:
                    break
                featureA = centroids[i]
                for j in range(i, len(centroids)):
                    if different:
                        break
                    if i == j:
                        continue
                    featureB = centroids[j]
                    for attribute in centroidFieldNames:
                        if featureA[attribute] == featureB[attribute]:
                            continue
                        different = True
                        break
            featuresDifferentCentroid.append( landCoverFeature ) if different else ''
        return featuresDifferentCentroid    

    def joinAttributesByLocation(self, inputLayer, joinLayer, fieldNames, feedback):
        output = processing.run(
            'native:joinattributesbylocation',
            {
                'INPUT': inputLayer,
                'JOIN': joinLayer,
                'PREDICATE': [0],
                'JOIN_FIELDS': fieldNames,
                'METHOD': 0,
                'DISCARD_NONMATCHING': True,
                'PREFIX': '',
                'OUTPUT': 'TEMPORARY_OUTPUT' 
            },
            feedback=feedback
        )
        return output['OUTPUT']

    def outLayer(self, parameterKey, parameters, context, layer, sourceCrs, geometryType):
        (sink, newLayer) = self.parameterAsSink(
            parameters,
            parameterKey,
            context,
            layer.fields(),
            geometryType,
            sourceCrs
        )
        for feature in layer.getFeatures():
            newFeat = QgsFeature()
            newFeat.setFields( layer.fields() )
            newFeat.setGeometry( feature.geometry() )
            newFeat.setAttributes( feature.attributes() )
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
        return newLayer

    def outFeatures(self, parameterKey, parameters, context, features, sourceCrs, geometryType):
        newFields = QgsFields()
        newFields.append(QgsField('id', QVariant.Int))
        (sink, newLayer) = self.parameterAsSink(
            parameters,
            parameterKey,
            context,
            newFields,
            geometryType,
            sourceCrs
        )
        idcounter = 1
        for feature in features:
            newFeat = QgsFeature()
            newFeat.setGeometry( feature.geometry() )
            newFeat.setFields( newFields )
            newFeat['id'] = idcounter
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
            idcounter +=1
        return newLayer

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return CreateLandCover()

    def name(self):
        return 'createLandCover'

    def displayName(self):
        return self.tr('Gerador de cobertura terrestre')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("Cria a cobertura terrestre ( caso haja erros retorna flags para correção )")
    
