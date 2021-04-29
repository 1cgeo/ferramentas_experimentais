import os
import sys
import inspect

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
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.Qt import QApplication, QClipboard
from qgis.utils import iface


def startCopyButton():
    try:
        layer = iface.activeLayer()
        validLayer(layer)
        feature = next(layer.getSelectedFeatures())
        copygeom(layer, feature)
        iface.messageBar().pushMessage('Executado', 'A geometria da feição foi copiada', level=Qgis.Success, duration=5)
    except Exception as e:
        iface.messageBar().pushMessage('Erro', str(e), level=Qgis.Critical, duration=5)

def copygeom(layer, feature):
    geom = QgsSettings()
    geom.setValue("Ferramentas_Experimentais/geometriatipo", layer.geometryType())
    geom.setValue("Ferramentas_Experimentais/geometria", feature.geometry())

def validLayer(layer):
    if not layer:
        raise Exception('Selecione uma camada')
    featcount = layer.selectedFeatureCount()
    if featcount != 1:
        raise Exception('Selecione uma e apenas uma feição')

def startPasteButton():
    try:
        layer = self.iface.activeLayer()
        self.validLayer(layer)
        geom = QgsSettings()
        geometria = geom.value("Ferramentas_Experimentais/geometria", False)
        feature = next(layer.getSelectedFeatures())
        self.validGeometry(layer, geometria)
        self.pastegeom(layer, geometria, feature)
        self.iface.messageBar().pushMessage('Executado', 'A geometria da feição foi modificada',
                                        level=Qgis.Success, duration=5)
    except Exception as e:
        self.iface.messageBar().pushMessage('Erro', str(e), level=Qgis.Critical, duration=5)

def pastegeom(layer, geometria, feature):
    layer.dataProvider().changeGeometryValues({feature.id(): geometria})
    layer.reload()

def validGeometry(layer, geometria):
    geometryType = QgsSettings().value("Ferramentas_Experimentais/geometriatipo", False)
    if not geometria:
        raise Exception('Sem geometria copiada')
    elif not (layer.geometryType() == int(geometryType)):
        raise Exception('Camada destino tem tipo de geometria diferente de camada origem')
