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
                        QgsProcessingParameterFolderDestination,
                        QgsGeometry,
                        QgsPointXY
                    )
from qgis import processing
from qgis import core, gui
from qgis.utils import iface
import os

class SaveLayerStylesToFile(QgsProcessingAlgorithm): 

    INPUT_LAYERS = 'INPUT_LAYER_LIST'
    FOLDER_OUTPUT = 'FOLDER_OUTPUT'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS,
                self.tr('Selecionar camadas'),
                QgsProcessing.TypeVectorAnyGeometry
            )
        )

        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.FOLDER_OUTPUT,
                self.tr('Pasta destino treino')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):      
        layerList = self.parameterAsLayerList(parameters, self.INPUT_LAYERS, context)
        folderOutput = self.parameterAsFileOutput(parameters, self.FOLDER_OUTPUT, context)

        listSize = len(layerList)
        progressStep = 100/listSize if listSize else 0
        step = 0

        for step, layer in enumerate(layerList):
            styleName = layer.styleManager().currentStyle()
            xmlData = layer.styleManager().style( styleName ).xmlData()
            self.exportToFile(
                os.path.join( folderOutput, '{0}.qml'.format(layer.name()) ),
                xmlData
            )
            feedback.setProgress( step * progressStep )
        
        return{ self.OUTPUT: '' }


    def exportToFile(self, filePath, data):
        print(filePath, data)
        with open(filePath, 'w') as f:
            f.write( data )
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return SaveLayerStylesToFile()

    def name(self):
        return 'savelayerstylestofile'

    def displayName(self):
        return self.tr('Exporta estilos para arquivo (QML)')

    def group(self):
        return self.tr('Edição')

    def groupId(self):
        return 'edicao'

    def shortHelpString(self):
        return self.tr("O algoritmo ...")
    
