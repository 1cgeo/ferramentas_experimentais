from qgis.core import (QgsField,
                       QgsAuxiliaryStorage,
                       QgsPropertyDefinition,
                       QgsFeature,
                       Qgis,
                       QgsWkbTypes
                       )
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QSettings
from qgis.utils import iface
import json

CONFIG_KEY = 'defaultFieldsBackupV1'

def showQgisErrorMessage(title, text):
    QMessageBox.critical(
        iface.mainWindow(),
        title, 
        text
    )

def setSettingsVariable(key, value):
    qsettings = QSettings()
    qsettings.setValue(key, value)

def getSettingsVariable(key):
    qsettings = QSettings()
    return qsettings.value(key)

def updateBackup(layerId, attributesBackup):
    data = getSettingsVariable( CONFIG_KEY )
    if not data:
        data = { layerId: attributesBackup }
    else:
        data = json.loads(data)
        data[layerId] = attributesBackup
    setSettingsVariable( CONFIG_KEY, json.dumps(data) )

def getBackup(layerId):
    data = getSettingsVariable( CONFIG_KEY )
    if not data or ( data and not( layerId in data) ):
        return {}
    return json.loads(data)[layerId]

def getAttributeBacklist():
    return [ 'data_modificacao', 'controle_uuid', 'usuario_criacao', 'usuario_atualizacao']

def setDefaultFields():
    try:
        layer = iface.activeLayer()
        if not layer:
            raise Exception('Selecione uma feição!')
        selectedFeatures = layer.selectedFeatures()
        if not len(selectedFeatures) == 1:
            raise Exception('Selecione apenas uma feição!')
        attributesBackup = {}
        feature = selectedFeatures[0]
        ignore = layer.dataProvider().pkAttributeIndexes()
        ignore += getAttributeBacklist()
        for fieldIndex in layer.attributeList():
            if fieldIndex in ignore:
                continue
            configField = layer.defaultValueDefinition( fieldIndex )
            configField.setExpression("'{0}'".format( feature.attribute(fieldIndex) ) )
            layer.setDefaultValueDefinition(fieldIndex, configField)
            attributesBackup[fieldIndex] = configField.expression()
        updateBackup(layer.id(), attributesBackup)
    except Exception as e:
        showQgisErrorMessage('Erro', str(e))

def restoreFields():
    try:
        layer = iface.activeLayer()
        if not layer:
            raise Exception('Selecione uma feição!')
        attributesBackup = getBackup(layer.id())
        if not attributesBackup:
            raise Exception('Camada já está na versão original!')
        for fieldIndex in attributesBackup:
            configField = layer.defaultValueDefinition( int(fieldIndex) )
            configField.setExpression("'{0}'".format( attributesBackup[fieldIndex] ) )
            layer.setDefaultValueDefinition(int(fieldIndex), configField)
        updateBackup(layer.id(), {})
    except Exception as e:
        showQgisErrorMessage('Erro', str(e))
