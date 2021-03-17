# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QCoreApplication
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
                       QgsVectorLayer,
                       QgsFeature,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterFile
                       )
from qgis import processing
import os
from shutil import *
import datetime
import subprocess
import shutil

class ExportarParaShapefile (QgsProcessingAlgorithm):
    INPUT_LAYERS = 'INPUT_LAYERS'
    INPUT_FOLDER = 'INPUT_FOLDER'
    OUTPUT_FOLDER = 'OUTPUT_FOLDER'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
             QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS,
                self.tr('Camadas'),
                QgsProcessing.TypeVectorAnyGeometry
            )
        )

        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_FOLDER,
                self.tr('Pasta contendo os modelos'),
                behavior=QgsProcessingParameterFile.Folder,
                
            )
        )

        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT_FOLDER,
                self.tr('Salvar em:'),
                
            )
        )
        
        
    def processAlgorithm(self, parameters, context, feedback):
        inputLyrList = self.parameterAsLayerList(
            parameters,
            self.INPUT_LAYERS,
            context
        )

        inputFolderPath = self.parameterAsString(
            parameters,
            self.INPUT_FOLDER,
            context
        )

        outputFolderPath = self.parameterAsString(
            parameters,
            self.OUTPUT_FOLDER,
            context
        )

        folderDestinationPath = self.createFolderDestination(outputFolderPath)
        
        outputLayers = []

        listSize = len(inputLyrList)
        progressStep = 100/listSize if listSize else 0

        extension = 'shp'

        inputFilesName = [ fileName.split('.')[0] for fileName in os.listdir(inputFolderPath) if fileName.split('.')[-1] == extension ]
        
        for step, layer in enumerate(inputLyrList):
            if feedback.isCanceled():
                return {self.OUTPUT: outputLayers}
            layerName = layer.name().upper()
            if not (layerName in inputFilesName):
                continue
            fileName = "{0}.{1}".format(layerName, extension)
            inputFilePath = os.path.join(inputFolderPath, fileName)
            outputFilePath = os.path.join( folderDestinationPath, fileName )
            self.convertUTF8( inputFilePath, outputFilePath )
            self.copyPasteLayer(layer, outputFilePath)
            outputLayers.append(layerName)
            feedback.setProgress(step*progressStep)

        return {self.OUTPUT: outputLayers}
        
    def createFolderDestination(self, outputFolder):
        folderDestinationPath = os.path.join( outputFolder, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") )
        os.makedirs(folderDestinationPath)
        return folderDestinationPath

    def convertUTF8(self, inputFile, outputFile):
        command = ['ogr2ogr' ,outputFile, inputFile ,'-lco','ENCODING=UTF-8']
        subprocess.call(command, shell=True)

    def copyPasteLayer(self, layer, outputFile):  
        if not os.path.exists(outputFile):
            return 
        outputLayer = QgsVectorLayer(outputFile, 'TMP', 'ogr')    
        fieldsToCpy = outputLayer.fields().names()         
        if 'FCODE' in fieldsToCpy:
            fieldsToCpy.remove('FCODE')
        newFeaturesList  = []   
        for count, featureToCopy in enumerate(layer.getFeatures()):
            newFeature =  QgsFeature()
            newFeature.setFields(outputLayer.fields())
            newFeature.setGeometry(featureToCopy.geometry())
            for fieldName in fieldsToCpy:
                newFeature[fieldName] = featureToCopy[fieldName.lower()]
            newFeature['FCODE'] = layer.name().upper()[1:] #revisar
            newFeaturesList.append(newFeature)           
        outputLayer.startEditing()
        dataProvider = outputLayer.dataProvider()
        dataProvider.addFeatures(newFeaturesList)
        outputLayer.commitChanges()    

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ExportarParaShapefile()

    def name(self):
        return 'exportar_para_shapefile'

    def displayName(self):
        return self.tr('Exportar para Shapefile')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo exporta camadas de um projeto para o formato shapefile ")

        
    
