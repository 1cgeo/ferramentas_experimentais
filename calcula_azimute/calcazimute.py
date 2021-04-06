# -*- coding: utf-8 -*-
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
                       QgsApplication
                       )
from PyQt5.QtWidgets import * 
from PyQt5 import QtCore, QtGui 
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 
from qgis.utils import iface
from Ferramentas_Experimentais import resources

class AzimButton:

    def __init__(self, iface):
        self.iface = iface
        
    def calazim(self):
        layer=iface.activeLayer()
        if not (layer.geometryType()==QgsWkbTypes.LineGeometry or layer.geometryType()==QgsWkbTypes.PolygonGeometry):
            iface.messageBar().pushMessage("Erro", u"Entrada não é camada vetorial tipo linha ou poligono!", level=Qgis.Critical, duration=5)
            return
        field = QgsField( 'id', QVariant.Double )
        cal=QgsAuxiliaryStorage()
        auxlyr=cal.createAuxiliaryLayer(field,layer)
        layer.setAuxiliaryLayer(auxlyr)
        auxLayer = layer.auxiliaryLayer()
        vdef=QgsPropertyDefinition(
            "azim", 
            2, 
            "azimute", 
            "calcula angulo azimute",
            "angulo"
        ) 
        auxLayer.addAuxiliaryField(vdef)
        auxFields = auxLayer.fields()
        features=layer.getFeatures()
        for feature in features:
            geom=feature.geometry()
            ombb=geom.orientedMinimumBoundingBox()
            auxFeature = QgsFeature(auxFields)
            auxFeature['ASPK']= feature['id']
            angazim=ombb[2]
            if ombb[4]<ombb[3]:
                angazim=ombb[2]-90
                if angazim<0:
                    angazim=ombb[2]+90
            auxFeature['angulo_azim'] = round(angazim)
            auxLayer.addFeature(auxFeature)
        iface.messageBar().pushMessage("Executado", "Campo angulo_azim adicionado a tabela de atributos!", level=Qgis.Success, duration=5)
