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
    for feat in layer.selectedFeatures():
        length = feat.geometry().length()
        if length < distance*1.2:
            layer.deselect(feat.id())

    if layer.selectedFeatureCount() > 0:
        newFeaturesId = []
        newFeats = getLineSubstring(layer, 0, distance)
        for f in newFeats.getFeatures():
            f['id'] = None
            layer.addFeature(f)
            newFeaturesId.append(f.id())

        updateFeats = getLineSubstring(layer, distance, core.QgsProperty.fromExpression('length( $geometry)'))
        for f in layer.selectedFeatures():
            request = core.QgsFeatureRequest().setFilterExpression('"id" = {}'.format(f["id"]))
            upfeat = next(updateFeats.getFeatures(request))
            f.setGeometry(upfeat.geometry())
            layer.updateFeature(f)

        layer.removeSelection()
        layer.selectByIds(newFeaturesId)
        iface.mapCanvas().refresh()

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
    return r['OUTPUT']

def addFeature(layer, attributes, geometry):
    f = core.QgsFeature()
    f.setAttributes(attributes)
    f.setGeometry(geometry)
    layer.addFeature(f)
    return f.id()
    