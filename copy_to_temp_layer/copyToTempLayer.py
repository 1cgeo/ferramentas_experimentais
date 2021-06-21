# -*- coding: utf-8 -*-
from qgis.core import (QgsProject,
                       Qgis,
                       QgsVectorLayer
                       )
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from qgis.utils import iface

def copyToTempLayer():
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
    features = layer.selectedFeatures()
    newFields = layer.fields()
    name = layer.name()
    geomtype = layer.geometryType()
    print(geomtype)
    print(type(geomtype))
    newName = name + '_temp'
    geomdict = {0:'multipoint', 1:'multilinestring', 2:'multipolygon'}
    selection = QgsVectorLayer(geomdict[int(geomtype)], newName , 'memory')
    selection.startEditing()
    selection.setCrs(layer.crs())
    dp = selection.dataProvider()
    dp.addAttributes(newFields)
    dp.addFeatures(features)
    selection.commitChanges()
    selection.updateExtents()
    QgsProject.instance().addMapLayer(selection)
    iface.messageBar().pushMessage("Executado", "Camada temporária criada: "+newName,
                                    level=Qgis.Success, duration=5)

def confirmAction():
    confirmation = False
    reply = QMessageBox.question(iface.mainWindow(), 'Continuar?', 
                 'Será criado uma nova camada com as feições selecionadas. Deseja continuar?', QMessageBox.Yes, QMessageBox.No)
    if reply == QMessageBox.Yes:
        confirmation = True
    return confirmation