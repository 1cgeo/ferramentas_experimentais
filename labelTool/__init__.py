from qgis import gui, core
from qgis.utils import iface
from PyQt5 import QtCore, uic, QtWidgets, QtGui
import os


class LabelTool(QtWidgets.QWidget):
    def __init__(self, menuActions):
        super(LabelTool, self).__init__()
        self.menuActions = menuActions
    
    def createAction(self, text, callback):
        action = QtWidgets.QAction(
            text
        )
        action.triggered.connect( callback )
        self.menuActions.addAction( action )
        return action

    def showQgisErrorMessage(self, title, text):
        QtWidgets.QMessageBox.critical(
            iface.mainWindow(),
            title, 
            text
        )

    def connectReturnLayerTarget(self, labelLayer, layerTargetName):
        self.setTargetLabelName( layerTargetName )
        try:
            labelLayer.featureAdded.disconnect( self.returnTargetLayer )
        except:
            pass
        finally:
            labelLayer.featureAdded.connect( self.returnTargetLayer )

    def setTargetLabelName(self, layerTargetName):
        self.layerTargetName = layerTargetName

    def getTargetLabelName(self):
        return self.layerTargetName

    def returnTargetLayer(self):
        targetLayer = self.getLayer( self.getTargetLabelName() )
        iface.setActiveLayer( targetLayer )

    def getLayer(self, layerName):
        loadedLayers = core.QgsProject.instance().mapLayers().values()
        for layer in loadedLayers:
            if not(
                    layer.name() == layerName
                ):
                continue
            return layer

    def setFieldValue(self, fieldName, fieldValue, layer):
        fieldIndex = layer.fields().indexOf( fieldName )
        configField = layer.defaultValueDefinition( fieldIndex )
        configField.setExpression("'{0}'".format( fieldValue) )
        layer.setDefaultValueDefinition(fieldIndex, configField)

class HydroLabelTool(LabelTool):

    def __init__(self, menuActions):
        super(HydroLabelTool, self).__init__(menuActions=menuActions)
        uic.loadUi(self.getUiPath(), self)
        self.addRioAction = self.createAction(
            'Rótulo Rio', 
            self.addRioBtn.click
        )
        self.addLagoAction = self.createAction(
            'Rótulo Lago', 
            self.addLagoBtn.click
        )
        iface.registerMainWindowAction(self.addRioAction, '')
        iface.registerMainWindowAction(self.addLagoAction, '')
        self.loadScales()

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'ui',
            'hydroLabelTool.ui'
        )
    
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

    @QtCore.pyqtSlot(bool)
    def on_addRioBtn_clicked(self):
        try:
            layer = iface.activeLayer()
            if not layer:
                raise Exception('Selecione uma feição!')
            targetLayerName = 'elemnat_trecho_drenagem_l'
            if not( layer.name() == targetLayerName ):
                raise Exception('Selecione uma feição da camada "{0}" !'.format( targetLayerName ) )
            selectedFeatures = layer.selectedFeatures()
            if not len(selectedFeatures) == 1:
                raise Exception('Selecione apenas uma feição!')
            labelLayerName = 'edicao_simb_hidrografia_l'
            labelLayer = self.getLayer(labelLayerName)
            if not labelLayer:
                raise Exception('Carregue a camada de rótulo "{0}"!'.format( labelLayerName ))
            feature = selectedFeatures[0]
            self.setFieldValue('texto_edicao', feature['nome'], labelLayer )
            self.setFieldValue('carta_mini', False, labelLayer )
            self.setFieldValue('classe', self.getClasseNameByType( feature['situacao_em_poligono'] ), labelLayer )
            self.setFieldValue('tamanho', feature.geometry().length(), labelLayer )
            self.setFieldValue('escala', self.scaleMapCb.itemData( self.scaleMapCb.currentIndex() ), labelLayer )
            iface.setActiveLayer( labelLayer )
            labelLayer.startEditing()
            self.connectReturnLayerTarget( labelLayer, targetLayerName )
            iface.actionAddFeature().trigger()
        except Exception as e:
            self.showQgisErrorMessage('Erro', str(e))

    @QtCore.pyqtSlot(bool)
    def on_addLagoBtn_clicked(self):
        try:
            layer = iface.activeLayer()
            if not layer:
                raise Exception('Selecione uma feição!')
            targetLayerName = 'cobter_massa_dagua_a'
            if not( layer.dataProvider().uri().table() == targetLayerName ):
                raise Exception('Selecione uma feição da camada "{0}" !'.format( targetLayerName ) )
            selectedFeatures = layer.selectedFeatures()
            if not len(selectedFeatures) == 1:
                raise Exception('Selecione apenas uma feição!')
            labelLayerName = 'edicao_simb_hidrografia_p'
            labelLayer = self.getLayer(labelLayerName)
            if not labelLayer:
                raise Exception('Carregue a camada de rótulo "{0}"!'.format( labelLayerName ))
            feature = selectedFeatures[0]
            self.setFieldValue('texto_edicao', feature['nome'], labelLayer )
            self.setFieldValue('carta_mini', False, labelLayer )
            self.setFieldValue('classe', 'cobter_massa_dagua_a', labelLayer ) 
            self.setFieldValue('tamanho', feature.geometry().area(), labelLayer )
            self.setFieldValue('escala', self.scaleMapCb.itemData( self.scaleMapCb.currentIndex() ), labelLayer )
            iface.setActiveLayer( labelLayer )
            labelLayer.startEditing()
            self.connectReturnLayerTarget( labelLayer, targetLayerName )
            iface.actionAddFeature().trigger()
        except Exception as e:
            self.showQgisErrorMessage('Erro', str(e))

    def getClasseNameByType(self, typeValue):
        if typeValue == 1:
            return 'elemnat_trecho_drenagem_l'
        return 'cobter_massa_dagua_a'


class HighwayLabelTool(LabelTool):

    def __init__(self, menuActions):
        super(HighwayLabelTool, self).__init__(menuActions=menuActions)
        uic.loadUi(self.getUiPath(), self)
        self.addFeatureAction = self.createAction(
            'Rótulo Rodovia', 
            self.addFeatureBtn.click
        )
        iface.registerMainWindowAction(self.addFeatureAction, '')

    def getUiPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'ui',
            'highwayLabelTool.ui'
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
            labelLayerName = self.getLabelLayerName()
            labelLayer = self.getLayer( labelLayerName )
            if not labelLayer:
                raise Exception('Carregue a camada de rótulo "{0}"!'.format( self.getLabelLayerName() ))
            feature = selectedFeatures[0]
            if not self.isValidAttributes( feature ):
                raise Exception('Os atributos não atendem os pré-requisitos!')
            self.setFieldValue(
                'sigla', 
                feature['sigla'].split('-')[-1] if not( ';' in feature['sigla'] ) else '|'.join([ s.split('-')[-1] for s in feature['sigla'].split(';') ]), 
                labelLayer 
            )
            self.setFieldValue('jurisdicao', feature['jurisdicao'], labelLayer )
            iface.setActiveLayer( labelLayer )
            labelLayer.startEditing()
            self.connectReturnLayerTarget( labelLayer, targetLayerName )
            iface.actionAddFeature().trigger()
        except Exception as e:
            self.showQgisErrorMessage('Erro', str(e))

    def isValidAttributes(self, feature):
        if not feature['sigla']:
            return False
        if not( feature['jurisdicao'] in [1,2] ):
            return False
        return True

    def getTargetLayerName(self):
        return 'infra_via_deslocamento_l'

    def getLabelLayerName(self):
        return 'edicao_identificador_trecho_rod_p'