from qgis.core import Qgis, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsCoordinateTransformContext
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.Qt import QApplication
from PyQt5 import uic
from qgis.utils import iface
import os

class GetCrsDialog(QDialog):

    def __init__(self):
        super(GetCrsDialog, self).__init__()
        uic.loadUi(self.getUiPath(), self)
        self.buttonBox.addButton("Sim", QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton("Não", QDialogButtonBox.RejectRole)
    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'ui',
            'changeCRS.ui'
        )

    def getCrs(self):
        return self.selectCRS.crs()


def copywkt():
    layer = iface.activeLayer()
    getCrsDialog = GetCrsDialog()
    result, destCrs = callDialog()
    wktcoord = []
    for feature in layer.getSelectedFeatures():
        geom = feature.geometry()
        if result:
            transformcrs = getGeometryTransforms(layer.crs(), destCrs)
            geom.transform(transformcrs)
        wktcoord.append(geom.asWkt())
    QApplication.clipboard().setText(
        '\n'.join(wktcoord)
    )
    iface.messageBar().pushMessage("Executado",
                                    u" As coordenadas das feições selecionadas foram copiadas em WKT", level=Qgis.Success, duration=5)
def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'ui',
            'changeCRS.ui'
        )
def callDialog():
    getCrsDialog = GetCrsDialog()
    result = getCrsDialog.exec_()
    crs = getCrsDialog.getCrs()
    retry = False
    if result and not crs.isValid():
        errorAction()
        return callDialog()
    return result, crs
def errorAction():
    reply = QMessageBox.question(iface.mainWindow(), 'CRS Invalido', 
                 'Se deseja mudar o CRS, selecione um CRS valido', QMessageBox.Ok)
    return False

def getGeometryTransforms(sourceCrs, destCrs):
    destTransform = QgsCoordinateTransform(sourceCrs, destCrs, QgsCoordinateTransformContext())
    return destTransform
