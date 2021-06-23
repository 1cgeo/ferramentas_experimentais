from os import stat
from qgis import processing
from qgis.gui import QgsMapToolEmitPoint, QgsMessageBar
from qgis.utils import iface
from qgis.core import (
    QgsRectangle, QgsFeatureRequest, QgsFeature, QgsProject,
    QgsPoint, QgsGeometry, QgsProcessingFeatureSourceDefinition
)
from qgis.utils import iface
from PyQt5 import QtGui, QtCore

class LabelMapTool(QgsMapToolEmitPoint):
    def __init__(self, canvas) -> None:
        super(LabelMapTool, self).__init__(canvas)
        self.canvas = canvas
        self.feat = None
        self.callback = None
        self.canvasClicked.connect(self.mouseClick)

    def setCallback(self, function):
        self.callback = function

    def getCallback(self):
        return self.callback

    def start(self, b):
        if b:
            iface.mapCanvas().setMapTool(self)
        else:
            iface.mapCanvas().unsetMapTool(self)

    def mouseClick(self, currentPos, clickedBtn):
        if clickedBtn == QtCore.Qt.LeftButton:
            self.layer = iface.activeLayer()
            tol = 50
            self.point = QgsPoint(currentPos)
            bbox = QgsRectangle(self.point.x() - tol, self.point.y() - tol, self.point.x() + tol, self.point.y() + tol)
            request = QgsFeatureRequest().setFilterRect(bbox).setFlags(QgsFeatureRequest.ExactIntersect)
            try:
                self.feat = next(self.layer.getFeatures(request))
                self.layer.select(self.feat.id())
            except StopIteration:
                pass
        elif clickedBtn == QtCore.Qt.RightButton and self.feat:
            _geom = QgsGeometry.fromWkt(self.point.asWkt())
            l = self.feat.geometry().lineLocatePoint(_geom)
            d = self.getGeomLength()
            _lyr = self.getLineSubstring(l-d, l+d)
            _feat = next(_lyr.getFeatures())
            _centroid = _feat.geometry().centroid().asPoint()
            _geom = _feat.geometry()
            _geom.translate(currentPos.x() - _centroid.x(), currentPos.y() - _centroid.y())
            self.layer.deselect(self.feat.id())
            self.getCallback()( self.feat, _geom )
            
    def getGeomLength(self):
        charCount = len(str(self.feat['nome']))
        length = self.feat.geometry().length()
        if length < 4000:
            return 30*charCount
        elif length < 6000:
            return 35*charCount
        elif length < 8000:
            return 40*charCount
        else:
            return 45*charCount

    def getLineSubstring(self, startDistance, endDistance):
        r = processing.run(
            'native:linesubstring',
            {   'END_DISTANCE' : endDistance, 
                'INPUT' : QgsProcessingFeatureSourceDefinition(
                    self.layer.source(),
                    selectedFeaturesOnly=True
                ), 
                'OUTPUT' : 'memory:', 
                'START_DISTANCE' : startDistance 
            }
        )
        return r['OUTPUT']