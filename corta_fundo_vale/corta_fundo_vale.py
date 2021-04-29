from PyQt5 import QtWidgets
from qgis import core
import processing
from qgis.utils import iface

def cortaFundoVale(distance):
    try:
        layer = iface.activeLayer()
        if not layer:
            raise Exception('Selecione uma camada!')
        if layer.geometryType() != core.QgsWkbTypes.LineGeometry:
            raise Exception('Selecione uma camada do tipo "Linha"!')
        if not layer.isEditable():
            raise Exception('Inicie a edição da camada!')
        if len(layer.selectedFeatures()) == 0:
            raise Exception('Selecione uma feição!')
        cutFeatureSelected(layer, distance)
    except Exception as e:
        showQgisErrorMessage('Erro', str(e))

def showQgisErrorMessage(title, text):
    QtWidgets.QMessageBox.critical(
        iface.mainWindow(),
        title, 
        text
    )

def cutFeatureSelected(layer, distance):
    feats = list(layer.selectedFeatures())
    layer.removeSelection()
    newFeaturesId = []
    for featOrigin in feats:
        length = featOrigin.geometry().length()
        if length > distance*1.2:
            layer.select(featOrigin.id())
            attributes = featOrigin.attributes()
            attributes[0] = None
            featSubstringA = getLineSubstring(layer, 0, distance)
            f = core.QgsFeature()
            f.setAttributes(attributes)
            f.setGeometry(featSubstringA.geometry())
            layer.addFeature(f)
            newFeaturesId.append(f.id())
            featSubstringB = getLineSubstring(layer, distance, length)
            featOrigin.setGeometry( featSubstringB.geometry() )
            layer.updateFeature(featOrigin)
            layer.deselect(featOrigin.id())
    iface.mapCanvas().refresh()
    layer.selectByIds(newFeaturesId)

def getLineSubstring(layer, startDistance, endDistance):
    r = processing.run(
        'native:linesubstring',
        {   'END_DISTANCE' : endDistance, 
            'INPUT' : core.QgsProcessingFeatureSourceDefinition(
                layer.source(), 
                selectedFeaturesOnly=True
            ), 
            'OUTPUT' : 'TEMPORARY_OUTPUT', 
            'START_DISTANCE' : startDistance 
        }
    )
    it = r['OUTPUT'].getFeatures()
    feat = core.QgsFeature()
    it.nextFeature(feat)
    return feat

def addFeature(layer, attributes, geometry):
    f = core.QgsFeature()
    f.setAttributes(attributes)
    f.setGeometry(geometry)
    layer.addFeature(f)
    return f.id()
    