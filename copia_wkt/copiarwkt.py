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
        self.buttonBox.addButton("Não mudar", QDialogButtonBox.RejectRole)
        

    def setCrsValue(self, value):
        self.selectCRS.setCrs( value)

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
    
    result, destCrs = callDialog(layer.crs())
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
                                    u" As coordenadas das feições selecionadas foram copiadas em WKT para o sistema {}".format(destCrs.authid()), level=Qgis.Success, duration=5)

def callDialog(crsvalue):
    getCrsDialog = GetCrsDialog()
    getCrsDialog.setCrsValue(crsvalue)
    result = getCrsDialog.exec_()
    crs = getCrsDialog.getCrs()
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
