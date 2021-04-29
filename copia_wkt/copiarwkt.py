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
                       QgsWkbTypes
                       )
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.Qt import QApplication
from qgis.utils import iface

def copywkt():
    layer = iface.activeLayer()
    wktcoord = []
    for feature in layer.getSelectedFeatures():
        geom = feature.geometry()
        wktcoord.append(geom.asWkt())
    QApplication.clipboard().setText(
        '\n'.join(wktcoord)
    )
    iface.messageBar().pushMessage("Executado",
                                    u" As coordenadas das feições selecionadas foram copiadas em WKT", level=Qgis.Success, duration=5)
