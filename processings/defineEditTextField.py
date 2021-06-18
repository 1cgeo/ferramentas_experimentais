# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
                        QgsProcessing,
                        QgsFeatureSink,
                        QgsProcessingAlgorithm,
                        QgsProcessingParameterFeatureSink,
                        QgsCoordinateReferenceSystem,
                        QgsProcessingParameterMultipleLayers,
                        QgsFeature,
                        QgsProcessingParameterVectorLayer,
                        QgsFields,
                        QgsFeatureRequest,
                        QgsProcessingParameterNumber,
                        QgsGeometry,
                        QgsPointXY
                    )
from qgis import processing
from qgis import core, gui
from qgis.utils import iface
import math

class DefineEditTextField(QgsProcessingAlgorithm): 

    INPUT_LAYERS = 'INPUT_LAYERS'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS,
                self.tr('Selecionar camadas:'),
                QgsProcessing.TypeVectorAnyGeometry
            )
        )

    def processAlgorithm(self, parameters, context, feedback):      
        layers = self.parameterAsLayerList(parameters, self.INPUT_LAYERS, context)

        for layer in layers:
            tableName = layer.dataProvider().uri().table()
            
            if tableName in [
                    "elemnat_elemento_hidrografico_a",
                    "infra_elemento_energia_a",
                    "infra_alteracao_fisiografica_antropica_a",
                    "constr_ocupacao_solo_a",
                    "elemnat_elemento_hidrografico_l",
                    "constr_ocupacao_solo_l",
                    "elemnat_elemento_hidrografico_p",
                    "constr_deposito_a",
                    "constr_deposito_p",
                    "infra_elemento_infraestrutura_p",
                    "infra_elemento_energia_p",
                    "constr_ocupacao_solo_p  ",
                    "llp_limite_especial_a",
                    "elemnat_ilha_a",
                    "elemnat_toponimo_fisiografico_natural_l",
                    "elemnat_toponimo_fisiografico_natural_p",
                    "llp_localidade_p"
                ]:
                for feature in layer.getFeatures():
                    feature[ 'texto_edicao' ] = feature[ 'nome' ]
                    self.updateLayerFeature( layer, feature)
            
            elif tableName in [ 'infra_vala_l' ]:
                for feature in layer.getFeatures():
                    feature[ 'texto_edicao' ] = 'Vala'
                    self.updateLayerFeature( layer, feature)
            
            elif tableName in [ 'infra_trecho_duto_l' ]:
                for feature in layer.getFeatures():
                    if not( feature['tipo'] == 301 ):
                        continue
                    feature[ 'texto_edicao' ] = 'Água'
                    self.updateLayerFeature( layer, feature)

            elif tableName in [ 'infra_trecho_hidroviario_l' ]:
                for feature in layer.getFeatures():
                    if not( feature['tipo'] == 1 ):
                        continue
                    feature[ 'texto_edicao' ] = 'Balsa'
                    self.updateLayerFeature( layer, feature)

            elif tableName in [ 'llp_limite_especial_l' ]:
                for feature in layer.getFeatures():
                    feature[ 'texto_edicao' ] = 'Aproximado'
                    self.updateLayerFeature( layer, feature)
                
            elif tableName in [ 'infra_pista_pouso_p' ]:
                for feature in layer.getFeatures():
                    feature[ 'texto_edicao' ] = feature[ 'nome' ]
                    self.updateLayerFeature( layer, feature)

            elif tableName in [ 
                    'infra_pista_pouso_a',
                    'infra_pista_pouso_l'
                ]:
                for feature in layer.getFeatures():
                    if not( feature['tipo'] == 9 ):
                        continue
                    text = feature[ 'nome' ]
                    if feature[ 'revestimento' ] in [1,2,3]:
                        valueMap = {
                            1: 'Leito natural',
                            2: 'Revestimento primário',
                            3: 'Pavimentado'
                        }
                        value = valueMap[ feature[ 'revestimento' ] ]
                        if not text:
                            text = value
                        else:
                            text = '{0} | {1}'.format(text, value)
                    feature[ 'texto_edicao' ] = text
                    self.updateLayerFeature( layer, feature)

            elif tableName in [ 'constr_edificacao_a', 'constr_edificacao_p' ]:
                for feature in layer.getFeatures():
                    if feature['tipo'] == 1218:
                        feature[ 'texto_edicao' ] = 'Curral'
                    else:
                        feature[ 'texto_edicao' ] = feature[ 'nome' ]
                    self.updateLayerFeature( layer, feature)

            elif tableName in [ 'infra_elemento_viario_p', 'infra_elemento_viario_l' ]:
                for feature in layer.getFeatures():
                    if not( feature['tipo'] in [401,402] ):
                        continue
                    feature[ 'texto_edicao' ] = 'Val'
                    self.updateLayerFeature( layer, feature)



        return {self.OUTPUT: ''}

    def updateLayerFeature(self, layer, feature):
        layer.startEditing()
        layer.updateFeature(feature)


    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DefineEditTextField()

    def name(self):
        return 'defineedittextfield'

    def displayName(self):
        return self.tr('Definir campo "texto_edicao"')

    def group(self):
        return self.tr('Edição')

    def groupId(self):
        return 'edicao'

    def shortHelpString(self):
        return self.tr("O algoritmo ...")
    
