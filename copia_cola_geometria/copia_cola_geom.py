import os
import sys
import inspect

from qgis.core import(QgsProcessing,
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
                       QgsAbstractFeatureSource,
                       QgsExpression,
                       QgsVectorLayer,
                       QgsField,
                       QgsExpressionContext,
                       QgsExpressionContextScope,
                       QgsAuxiliaryStorage,
                       QgsPropertyDefinition,
                       QgsFeature,
                       Qgis,
                       QgsWkbTypes,
                       QgsSettings
                       )

from PyQt5.QtWidgets import * 
from PyQt5 import QtCore, QtGui 
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 
from PyQt5.Qt import QApplication, QClipboard

from qgis.utils import iface
from CopiarWkt import resources


class CCGButton():

    def __init__(self, iface):
        self.iface = iface

    def startCopyButton(self, b):
        try:
            layer=iface.activeLayer()
            self.validLayer(layer)
            features=layer.getSelectedFeatures()
            self.copygeom(layer, features)
            iface.messageBar().pushMessage( 'Executado', 'A geometria da feição foi copiada', level=Qgis.Success, duration=5)
        except Exception as e:
            iface.messageBar().pushMessage( 'Erro', str(e), level=Qgis.Critical, duration=5)

    def copygeom(self, layer, features):
        geom = QgsSettings()
        geom.setValue("Ferramentas_Experimentais/geometriatipo", layer.geometryType())
        for feature in features:
            geom.setValue("Ferramentas_Experimentais/geometria", feature.geometry())

    def validLayer(self, layer):
        if not layer:
            raise Exception('Selecione uma camada')
        featcount = layer.selectedFeatureCount()
        if featcount > 1 or featcount < 1:
            raise Exception('Selecione uma e apenas uma feição')

    def startPasteButton(self, b):
        try:
            layer = iface.activeLayer()
            self.validLayer(layer)
            geom = QgsSettings()
            geometria = geom.value("Ferramentas_Experimentais/geometria", False)
            features = layer.getSelectedFeatures()
            self.validGeometry(layer, geometria)
            self.pastegeom(layer, geometria, features)
            iface.messageBar().pushMessage( 'Executado', 'A geometria da feição foi modificada', level=Qgis.Success, duration=5)
        except Exception as e:
            iface.messageBar().pushMessage( 'Erro', str(e), level=Qgis.Critical, duration=5)

    def pastegeom(self, layer, geometria, features):
        for feature in features:
            layer.dataProvider().changeGeometryValues({ feature.id() : geometria })
        layer.reload()

    def validGeometry(self, layer, geometria):
        geometryType = QgsSettings().value("Ferramentas_Experimentais/geometriatipo", False)
        if not geometria:
            raise Exception('Sem geometria copiada')
        elif not (layer.geometryType() == int(geometryType)):
            raise Exception('Camada destino tem tipo de geometria diferente de camada origem')


        
            

