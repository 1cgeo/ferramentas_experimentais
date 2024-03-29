from qgis.core import (QgsField,
                       QgsAuxiliaryStorage,
                       QgsPropertyDefinition,
                       QgsFeature,
                       Qgis,
                       QgsWkbTypes
                       )
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QSettings
from qgis import core, gui
from qgis.utils import iface
import json

def cleanAllFilters():
    loadedLayers = core.QgsProject.instance().mapLayers().values()    
    for layer in loadedLayers:
        layer.setSubsetString('')
    iface.mapCanvas().refresh()

def filterBySelectedGeometries():
    layer = iface.activeLayer()
    if not layer:
        return
    selectedFeatures = layer.selectedFeatures()
    if not selectedFeatures:
        return
    if not( layer.geometryType() == core.QgsWkbTypes.PolygonGeometry ):
        return
    multiPolygon = core.QgsMultiPolygon()
    for feature in selectedFeatures:
        for geometry in feature.geometry().asGeometryCollection():
            multiPolygon.addGeometry( geometry.constGet().clone() )
    multiPolygon = core.QgsGeometry(multiPolygon).makeValid()
    textFilter = "(geom && st_geomfromewkt('SRID={0};{1}') ) AND st_relate(geom, st_geomfromewkt('SRID={0};{1}'), 'T********')".format( 
        layer.crs().authid().split(':')[-1], 
        multiPolygon.asWkt()
    )
    layersBacklist = [ 'aux_moldura_a' ]
    loadedLayers = core.QgsProject.instance().mapLayers().values()    
    for loadedLayer in loadedLayers:
        if not isinstance(loadedLayer, core.QgsVectorLayer) or \
            loadedLayer.dataProvider().name() != 'postgres' or \
            loadedLayer.dataProvider().uri().table() in layersBacklist:
            continue
        loadedLayer.setSubsetString( textFilter )
    iface.mapCanvas().refresh()

def filterSelections():
    layer = iface.activeLayer()
    if not layer:
        return
    selectedFeatures = layer.selectedFeatures()
    if not selectedFeatures:
        return
    primaryKeyIndex = layer.primaryKeyAttributes()[0]
    primaryKeyName = layer.fields().names()[ primaryKeyIndex ]
    layer.setSubsetString( 
        '"{0}" in ({1})'.format( 
            primaryKeyName, 
            ','.join([ 
                "'{}'".format(str(i[primaryKeyName])) if not isinstance(i[primaryKeyName], int) else str(i[primaryKeyName])
                for i in selectedFeatures
            ]) 
        ) 
    )