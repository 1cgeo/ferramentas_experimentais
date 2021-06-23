from qgis import gui, core
from qgis.utils import iface
from PyQt5 import QtCore, uic, QtWidgets, QtGui
import os
from .labelMapTool import LabelMapTool

class LabelTool(QtWidgets.QWidget):
    def __init__(self, 
            menuActions, 
            labelMapTool=LabelMapTool( iface.mapCanvas() )
        ):
        super(LabelTool, self).__init__()
        self.labelMapTool = labelMapTool
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
        layers = core.QgsProject.instance().mapLayersByName( layerName )
        return core.QgsProject.instance().mapLayersByName( layerName )[0] if layers else None

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
        iface.registerMainWindowAction(self.addRioAction, '')
        self.addLagoAction = self.createAction(
            'Rótulo Lago', 
            self.addLagoBtn.click
        )
        iface.registerMainWindowAction(self.addLagoAction, '')
        self.loadScales()
        self.riverTargetLayerName = 'elemnat_trecho_drenagem_l'
        self.riverLabelLayerName = 'edicao_simb_hidrografia_l'
        self.lakeTargetLayerName = 'cobter_massa_dagua_a'
        self.lakeLabelLayerName = 'edicao_simb_hidrografia_p'

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
    def on_addRioBtn_clicked(self, b):
        try:
            self.labelMapTool.setCallback( self.addHydroLabelFeature )
            self.labelMapTool.start( True )
        except Exception as e:
            self.addRioBtn.setChecked( False )
            self.labelMapTool.start( False )
            self.showQgisErrorMessage('Erro', str(e))

    def addHydroLabelFeature(self, feature, geometry):
        layer = iface.activeLayer()
        if not layer:
            raise Exception('Selecione uma camada!')
        if not( layer.name() == self.riverTargetLayerName ):
            raise Exception('Selecione uma feição da camada "{0}" !'.format( self.riverTargetLayerName ) )
        labelLayer = self.getLayer( self.riverLabelLayerName )
        if not labelLayer:
            raise Exception('Carregue a camada de rótulo "{0}"!'.format( self.riverLabelLayerName ))
        newFeature = core.QgsFeature( labelLayer.fields() )
        newFeature.setGeometry( geometry )
        newFeature['texto_edicao'] = feature['nome']
        newFeature['carta_mini'] = False
        newFeature['classe'] = self.getClasseNameByType( feature['situacao_em_poligono'] )
        newFeature['tamanho'] = feature.geometry().length()
        newFeature['escala'] = self.scaleMapCb.itemData( self.scaleMapCb.currentIndex() )
        iface.setActiveLayer( labelLayer )
        labelLayer.startEditing()
        iface.actionAddFeature().trigger()
        labelLayer.addFeature( newFeature )
        iface.setActiveLayer( layer )

    @QtCore.pyqtSlot(bool)
    def on_addLagoBtn_clicked(self):
        try:
            self.labelMapTool.setCallback( self.addLakeLabelFeature )
            self.labelMapTool.start( True )
        except Exception as e:
            self.addLagoBtn.setChecked( False )
            self.labelMapTool.start( False )
            self.showQgisErrorMessage('Erro', str(e))

    def addLakeLabelFeature(self, feature, geometry):
        layer = iface.activeLayer()
        if not layer:
            raise Exception('Selecione uma camada!')
        if not( layer.name() == self.riverTargetLayerName ):
            raise Exception('Selecione uma feição da camada "{0}" !'.format( self.riverTargetLayerName ) )
        labelLayer = self.getLayer( self.riverLabelLayerName )
        if not labelLayer:
            raise Exception('Carregue a camada de rótulo "{0}"!'.format( self.riverLabelLayerName ))
        newFeature = core.QgsFeature( labelLayer.fields() )
        newFeature.setGeometry( geometry )
        newFeature['texto_edicao'] = feature['nome']
        newFeature['carta_mini'] = False
        newFeature['classe'] = self.getClasseNameByType( feature['situacao_em_poligono'] )
        newFeature['tamanho'] = feature.geometry().area()
        newFeature['escala'] = self.scaleMapCb.itemData( self.scaleMapCb.currentIndex() )
        iface.setActiveLayer( labelLayer )
        labelLayer.startEditing()
        iface.actionAddFeature().trigger()
        labelLayer.addFeature( newFeature )
        iface.setActiveLayer( layer )

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

    def on_addFeatureBtn_clicked(self):
        try:
            self.labelMapTool.setCallback( self.addHighwayLabelFeature )
            self.labelMapTool.start( True )
        except Exception as e:
            self.addFeatureBtn.setChecked( False )
            self.labelMapTool.start( False )
            self.showQgisErrorMessage('Erro', str(e))
        
    def addHighwayLabelFeature(self, feature, geometry):
        layer = iface.activeLayer()
        if not layer:
            raise Exception('Selecione uma camada!')
        targetLayerName = self.getTargetLayerName()
        if not( layer.name() == targetLayerName ):
            raise Exception('Selecione uma feição da camada "{0}" !'.format( targetLayerName ) )
        labelLayerName = self.getLabelLayerName()
        labelLayer = self.getLayer( labelLayerName )
        if not labelLayer:
            raise Exception('Carregue a camada de rótulo "{0}"!'.format( self.getLabelLayerName() ))
        if not self.isValidAttributes( feature ):
            raise Exception('Os atributos não atendem os pré-requisitos!')
        newFeature = core.QgsFeature( labelLayer.fields() )
        newFeature.setGeometry( geometry )
        newFeature['sigla'] = feature['sigla'].split('-')[-1] if not( ';' in feature['sigla'] ) else '|'.join([ s.split('-')[-1] for s in feature['sigla'].split(';') ])
        newFeature['jurisdicao'] = feature['jurisdicao']
        iface.setActiveLayer( labelLayer )
        labelLayer.startEditing()
        iface.actionAddFeature().trigger()
        labelLayer.addFeature( newFeature )
        iface.setActiveLayer( layer )  

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