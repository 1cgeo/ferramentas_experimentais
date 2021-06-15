from qgis import gui, core
from qgis.utils import iface
from PyQt5 import QtCore, uic, QtWidgets, QtGui
import os

class LabelTool(QtWidgets.QWidget):

    def __init__(self):
        super(LabelTool, self).__init__()
        uic.loadUi(self.getUiPath(), self)
        self.addFeatureAction = self.createAction(
            'start', 
            self.addFeatureBtn.click
        )
        iface.registerMainWindowAction(self.addFeatureAction, '')
        self.loadScales()

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'ui',
            'labelTool.ui'
        )

    def createAction(self, text, callback):
        action = QtWidgets.QAction(
            text,
            iface.mainWindow()
        )
        action.triggered.connect(callback)
        return action
    
    def loadScales(self):
        for item in self.getScalesMap():
            self.scaleMapCb.addItem( item['key'], item['value'] )

    def getScalesMap(self):
        return [
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
        ]

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
            targetLayerName = self.getTargetLayerName()
            if not( layer.dataProvider().uri().table() == targetLayerName ):
                raise Exception('Selecione uma feição da camada "{0}" !'.format( targetLayerName ) )
            selectedFeatures = layer.selectedFeatures()
            if not len(selectedFeatures) == 1:
                raise Exception('Selecione apenas uma feição!')
            labelLayer = self.getLabelLayer()
            if not labelLayer:
                raise Exception('Carregue a camada de rótulo "{0}"!'.format( self.getLabelLayerName() ))
            feature = selectedFeatures[0]
            self.setFieldValue('texto', feature['nome'], labelLayer ) #if not( layer.fields().indexOf( 'nome' ) < 0 ) else ''
            self.setFieldValue('carta_mini', False, labelLayer )
            self.setFieldValue('classe', self.getClasseNameByType( feature['situacao_em_poligono'] ), labelLayer ) #if not( layer.fields().indexOf( 'tipo' ) < 0 ) else ''
            self.setFieldValue('tamanho', feature.geometry().length(), labelLayer )
            self.setFieldValue('escala', self.scaleMapCb.itemData( self.scaleMapCb.currentIndex() ), labelLayer )
            iface.setActiveLayer( labelLayer )
            labelLayer.startEditing()
            iface.actionAddFeature().trigger()
        except Exception as e:
            self.showQgisErrorMessage('Erro', str(e))

    def getTargetLayerName(self):
        return 'elemnat_trecho_drenagem_l'

    def getClasseNameByType(self, typeValue):
        if typeValue == 1:
            return 'elemnat_trecho_drenagem_l'
        return 'cobter_massa_dagua_a'

    def getLabelLayer(self):
        loadedLayers = core.QgsProject.instance().mapLayers().values()
        labelLayerName = self.getLabelLayerName()
        for layer in loadedLayers:
            if not(
                    layer.dataProvider().uri().table() == labelLayerName
                ):
                continue
            return layer

    def getLabelLayerName(self):
        return 'edicao_simb_hidrografia_l'

    def setFieldValue(self, fieldName, fieldValue, layer):
        fieldIndex = layer.fields().indexOf( fieldName )
        configField = layer.defaultValueDefinition( fieldIndex )
        configField.setExpression("'{0}'".format( fieldValue) )
        layer.setDefaultValueDefinition(fieldIndex, configField)