from qgis import gui, core
from qgis.utils import iface
from PyQt5 import QtCore, uic, QtWidgets, QtGui
import os

class LabelTool(QtWidgets.QWidget):

    def __init__(self):
        super(LabelTool, self).__init__()
        uic.loadUi(self.getUiPath(), self)
        self.addFeatureIcon = self.getAddFeatureIcon()
        self.addFeatureBtn.setIcon( self.addFeatureIcon )
        self.addFeatureAction = self.createAction(
            'start', 
            self.addFeatureIcon,
            self.addFeatureBtn.click
        )
        iface.registerMainWindowAction(self.addFeatureAction, '')
        self.layerCombo = gui.QgsMapLayerComboBox()
        self.layerCombo.setFixedWidth(100)
        self.layerCombo.setFilters(core.QgsMapLayerProxyModel.LineLayer)
        self.layerLayout.addWidget( self.layerCombo )
        self.loadScales()

    def createAction(self, text, icon, callback):
        action = QtWidgets.QAction(
            icon,
            text,
            iface.mainWindow()
        )
        action.triggered.connect(callback)
        return action
    
    def getAddFeatureIcon(self):
        return QtGui.QIcon(
             os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                '..',
                'icons',
                'labelTool.svg'
            )
         )
         

    def loadScales(self):
        for item in [
                {
                    'key': '1:250.000',
                    'value': 250000
                },
                {
                    'key': '1:100.000',
                    'value': 100000
                },
                {
                    'key': '1:50.000',
                    'value': 50000
                },
                {
                    'key': '1:25.000',
                    'value': 25000
                }
            ]:
            self.scaleMapCb.addItem( item['key'], item['value'] )

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'ui',
            'labelTool.ui'
        )

    def showQgisErrorMessage(self, title, text):
        QtWidgets.QMessageBox.critical(
            iface.mainWindow(),
            title, 
            text
        )

    @QtCore.pyqtSlot(bool)
    def on_addFeatureBtn_clicked(self):
        try:
            layer = iface.activeLayer()
            if not layer:
                raise Exception('Selecione uma feição!')
            selectedFeatures = layer.selectedFeatures()
            if not len(selectedFeatures) == 1:
                raise Exception('Selecione apenas uma feição!')
            feature = selectedFeatures[0]
            labelLayer = self.layerCombo.currentLayer()
            self.setFieldValue('texto', feature['texto'], labelLayer ) if not( layer.fields().indexOf( 'texto' ) < 0 ) else ''
            self.setFieldValue('classe', layer.name(), labelLayer )
            self.setFieldValue('tamanho', feature.geometry().length(), labelLayer )
            self.setFieldValue('escala', self.scaleMapCb.itemData( self.scaleMapCb.currentIndex() ), labelLayer )
            #iface.activeLayer().startEditing()
            #iface.actionAddFeature().trigger()
        except Exception as e:
            self.showQgisErrorMessage('Erro', str(e))

    def setFieldValue(self, fieldName, fieldValue, layer):
        fieldIndex = layer.fields().indexOf( fieldName )
        configField = layer.defaultValueDefinition( fieldIndex )
        configField.setExpression("'{0}'".format( fieldValue) )
        layer.setDefaultValueDefinition(fieldIndex, configField)