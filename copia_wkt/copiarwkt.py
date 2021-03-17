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
                       QgsWkbTypes
                       )
from PyQt5.QtWidgets import * 
from PyQt5 import QtCore, QtGui 
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 
from PyQt5.Qt import QApplication, QClipboard
from qgis.utils import iface
from CopiarWkt import resources

class WktButton():

    def __init__(self, iface):
        self.iface = iface
        #self.b="teste123"
    def copywkt(self):
        layer=iface.activeLayer()
        wktcoord=[]
        features=layer.getSelectedFeatures()
        for feature in features:
            geom=feature.geometry()
            wktcoord.append(geom.asWkt())
            wktcoord.append("\n")
            wktcoord.append("\n")
        QApplication.clipboard().setText([''.join(wktcoord[:-2])][0])
        iface.messageBar().pushMessage("Executado", u" As coordenadas das feições selecionadas foram copiadas em WKT", level=Qgis.Success, duration=5)
