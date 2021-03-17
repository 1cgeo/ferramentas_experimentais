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

    def copygeom(self):
        layer=iface.activeLayer()
        featcount=layer.selectedFeatureCount()
        if featcount>1:
            iface.messageBar().pushMessage("Erro", u" Selecione apenas uma feição", level=Qgis.Critical, duration=5)
        elif featcount<1:
            iface.messageBar().pushMessage("Erro", u" Selecione pelo menos uma feição", level=Qgis.Critical, duration=5)
        else:
            features=layer.getSelectedFeatures()
            geom=QgsSettings()
            geom.setValue("Ferramentas_Experimentais/geometriatipo", layer.geometryType())
            for feature in features:
                geom.setValue("Ferramentas_Experimentais/geometria", feature.geometry())
            iface.messageBar().pushMessage("Executado", u" A geometria da feição selecionada foi copiada", level=Qgis.Success, duration=5)
            

    def pastegeom(self):
        layer=iface.activeLayer()
        featcount=layer.selectedFeatureCount()
        geom=QgsSettings()
        geometria=geom.value("Ferramentas_Experimentais/geometria", False)
        if featcount>1:
             iface.messageBar().pushMessage("Erro", u" Selecione apenas uma feição", level=Qgis.Critical, duration=5)
        elif featcount<1:
            iface.messageBar().pushMessage("Erro", u" Selecione pelo menos uma feição", level=Qgis.Critical, duration=5)
        elif not geometria:
            iface.messageBar().pushMessage("Erro", u"Sem geometria copiada", level=Qgis.Critical, duration=5)
        elif not layer.geometryType()==geom.value("Ferramentas_Experimentais/geometriatipo", False):
            iface.messageBar().pushMessage("Erro", u"Camada destino tem tipo de geometria diferente de camada origem", level=Qgis.Critical, duration=5)
        else:
            features=layer.getSelectedFeatures()
            for feature in features:
                layer.dataProvider().changeGeometryValues({ feature.id() : geometria })
                layer.reload()
            iface.messageBar().pushMessage("Executado", u" A geometria da feição foi modificada", level=Qgis.Success, duration=5)
            

