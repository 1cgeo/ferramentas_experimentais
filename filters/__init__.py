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

def filterBySelection():
    selectedFeatureIds = iface.activeLayer().selectedFeatureIds()
    if not selectedFeatureIds:
        return
    primaryKeyIndex = iface.activeLayer().primaryKeyAttributes()[0]
    primaryKeyName = iface.activeLayer().fields().names()[ primaryKeyIndex ]
    iface.activeLayer().setSubsetString( '"{0}" in ({1})'.format( primaryKeyName, ','.join([ str(i) for i in selectedFeatureIds]) ) )