import os
from PyQt5 import QtWidgets, QtGui, QtCore, uic

class CortaTool(QtWidgets.QWidget):

    def __init__(self, callback):
        super(CortaTool, self).__init__()
        uic.loadUi(self.getUiPath(), self)
        self.cutButton.setIcon(QtGui.QIcon( self.getCutButtonIconPath() ))
        self.distanceLineEdit.setValidator(QtGui.QIntValidator(0, 1000000))
        self.distanceLineEdit.setText('500')
        self.callback = callback

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'uis',
            'tool.ui'
        )

    def getCutButtonIconPath(self):
        return os.path.join(
            os.path.abspath(os.path.join(
                os.path.dirname(__file__)
            )),
            '..',
            '..',
            'icons',
            'scissors.svg'
        )

    def getDistance(self):
        return int(self.distanceLineEdit.text())

    @QtCore.pyqtSlot(bool)
    def on_cutButton_clicked(self):
        self.callback( self.getDistance() )