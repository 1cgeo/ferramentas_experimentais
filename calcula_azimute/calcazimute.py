# -*- coding: utf-8 -*-
from qgis.core import (QgsField,
                       QgsAuxiliaryStorage,
                       QgsPropertyDefinition,
                       QgsFeature,
                       Qgis,
                       QgsWkbTypes
                       )
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from qgis.utils import iface

def calazim():
    confirmation = confirmAction()
    if not confirmation:
        iface.messageBar().pushMessage("Cancelado", u"ação cancelada pelo usuário",
                                        level=Qgis.Warning, duration=5)
        return
    layer = iface.activeLayer()
    if not layer:
        iface.messageBar().pushMessage("Erro", u"Selecione uma camada válida",
                                        level=Qgis.Critical, duration=5)
        return
    if not (layer.geometryType() == QgsWkbTypes.LineGeometry or layer.geometryType() == QgsWkbTypes.PolygonGeometry):
        iface.messageBar().pushMessage("Erro", u"Entrada não é camada vetorial tipo linha ou poligono!",
                                        level=Qgis.Critical, duration=5)
        return
    field = QgsField('id', QVariant.Double)
    cal = QgsAuxiliaryStorage()
    auxlyr = cal.createAuxiliaryLayer(field, layer)
    layer.setAuxiliaryLayer(auxlyr)
    auxLayer = layer.auxiliaryLayer()
    vdef = QgsPropertyDefinition(
        "azim",
        2,
        "azimute",
        "calcula angulo azimute",
        "angulo"
    )
    auxLayer.addAuxiliaryField(vdef)
    auxFields = auxLayer.fields()
    for feature in layer.getFeatures():
        geom = feature.geometry()
        ombb = geom.orientedMinimumBoundingBox()
        auxFeature = QgsFeature(auxFields)
        auxFeature['ASPK'] = feature['id']
        angazim = ombb[2]
        if ombb[4] < ombb[3]:
            angazim = ombb[2]-90
            if angazim < 0:
                angazim = ombb[2]+90
        auxFeature['angulo_azim'] = round(angazim)
        auxLayer.addFeature(auxFeature)
    iface.messageBar().pushMessage("Executado", "Campo angulo_azim adicionado a tabela de atributos!",
                                    level=Qgis.Success, duration=5)

def confirmAction():
    confirmation = False
    reply = QMessageBox.question(iface.mainWindow(), 'Continuar?', 
                 'Será criado um campo auxiliar com atributo de azimute. Deseja continuar?', QMessageBox.Yes, QMessageBox.No)
    if reply == QMessageBox.Yes:
        confirmation = True
    return confirmation