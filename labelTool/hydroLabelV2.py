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

class HydroLabelV2(QgsMapToolEmitPoint):
    def __init__(self, canvas) -> None:
        super().__init__(canvas)
        self.canvas = canvas
        self.isActive = False
        self.canvasClicked.connect(self.mouseClick)

    def start(self):
        self.isActive = not self.isActive
        if self.isActive:
            iface.mapCanvas().setMapTool(self)
        else:
            iface.mapCanvas().unsetMapTool(self)

    def mouseClick(self, currentPos, clickedBtn):
        if self.isActive:
            self.destLayer = QgsProject.instance().mapLayersByName('edicao_simb_hidrografia_p')
            if not self.destLayer:
                iface.messageBar().pushCritical('Erro', 'Camada edicao_simb_hidrografia_p não encontrada')

            elif clickedBtn == QtCore.Qt.LeftButton:
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
                self.destLayer = self.destLayer[0]
                _geom = QgsGeometry.fromWkt(self.point.asWkt())
                l = self.feat.geometry().lineLocatePoint(_geom)
                d = self.getGeomLength()
                _lyr = self.getLineSubstring(l-d, l+d)
                _feat = next(_lyr.getFeatures())
                _centroid = _feat.geometry().centroid().asPoint()
                _geom = _feat.geometry()
                _geom.translate(currentPos.x() - _centroid.x(), currentPos.y() - _centroid.y())
                _fields = self.destLayer.dataProvider().fields()
                newFeat = QgsFeature(_fields)
                newFeat.setGeometry(_geom)
                newFeat['nome'] = self.feat['nome']
                self.destLayer.startEditing()
                self.destLayer.addFeature(newFeat)
                self.resetState()
                # self.layer.commitChanges()

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
    
    def resetState(self):
        self.layer.deselect(self.feat.id())
        self.destLayer = None
        self.feat = None

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