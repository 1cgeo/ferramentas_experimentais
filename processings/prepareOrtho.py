# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import NULL, QCoreApplication
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

class PrepareOrtho(QgsProcessingAlgorithm): 

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
        layersNames = [x.dataProvider().uri().table() for x in layers]
        layersToCalculateDefaults = [
            'infra_obstaculo_vertical_p',
            'infra_pista_pouso_p',
            'infra_pista_pouso_l',
            'infra_pista_pouso_a',
            'elemnat_curva_nivel_l'
        ]

        attrDefault = {
            'constr_extracao_mineral_p': {
                'texto_edicao': 'nome',
                'visivel': 1,
                'justificativa_txt': 1
            },
            'elemnat_elemento_hidrografico_p': {
                'texto_edicao': 'nome',
                'justificativa_txt': 1
            },
            'elemnat_ilha_p': {
                'texto_edicao': 'nome',
                'tamanho_txt': 6,
                'justificativa_txt': 1,
                'rotular_carta_mini': 1
            },
            'elemnat_ponto_cotado_p': {
                'visivel': 1
            },
            'elemnat_toponimo_fisiografico_natural_p': {
                'texto_edicao': 'nome',
                'tamanho_txt': 6,
                'justificativa_txt': 1,
                'espacamento': 0,
                'rotular_carta_mini': 1
            },
            'infra_elemento_energia_p': {
                'texto_edicao': 'nome',
                'visivel': 1,
                'justificativa_txt': 1
            },
            'infra_elemento_infraestrutura_p': {
                'texto_edicao': 'nome',
                'justificativa_txt': 1
            },
            'infra_obstaculo_vertical_p': {
                'visivel': 1,
                'justificativa_txt': 1
            },
            'infra_pista_pouso_p': {
                'justificativa_txt': 2
            },
            'llp_aglomerado_rural_p': {
                'texto_edicao': 'nome',
                'justificativa_txt': 2,
                'rotular_carta_mini': 1
            },
            'llp_localidade_p': {
                'texto_edicao': 'nome',
                'justificativa_txt': 2,
                'rotular_carta_mini': 1
            },
            'llp_nome_local_p': {
                'texto_edicao': 'nome',
                'justificativa_txt': 2
            },
            'elemnat_curva_nivel_l': {
                'visivel': 1
            },
            'elemnat_elemento_hidrografico_l': {
                'texto_edicao': 'nome',
                'justificativa_txt': 2
            },
            'elemnat_toponimo_fisiografico_natural_l': {
                'texto_edicao': 'nome',
                'tamanho_txt': 6,
                'espacamento': 0,
                'rotular_carta_mini': 1
            },
            'elemnat_trecho_drenagem_l': {
                'texto_edicao': 'nome',
                'tamanho_txt': 6,
                'visivel': 1,
                'simbolizar_carta_mini': 1,
                'rotular_carta_mini': 1
            },
            'infra_elemento_energia_l': {
                'visivel': 1
            },
            'infra_ferrovia_l': {
                'visivel': 1,
                'simbolizar_carta_mini': 1
            },
            'infra_pista_pouso_l': {
                'justificativa_txt': 2
            },
            'infra_via_deslocamento_l': {
                'visivel': 1,
                'simbolizar_carta_mini': 1
            },
            'llp_area_pub_militar_l': {
                'sobreposto': 2,
                'exibir_rotulo_aproximado': 1
            },
            'llp_limite_legal_l': {
                'sobreposto': 2,
                'exibir_rotulo_aproximado': 1
            },
            'llp_terra_indigena_l': {
                'sobreposto': 2,
                'exibir_rotulo_aproximado': 1
            },
            'llp_unidade_conservacao_l': {
                'sobreposto': 2,
                'exibir_rotulo_aproximado': 1
            },
            'aux_area_sem_dados_a': {
                'tamanho_txt': 8,
                'justificativa_txt': 1,
                'rotular_carta_mini': 1
            },
            'cobter_massa_dagua_a': {
                'texto_edicao': 'nome',
                'tamanho_txt': 6,
                'justificativa_txt': 1,
                'rotular_carta_mini': 1
            },
            'constr_extracao_mineral_a': {
                'texto_edicao': 'nome',
                'visivel': 1,
                'justificativa_txt': 1
            },
            'elemnat_elemento_hidrografico_a': {
                'texto_edicao': 'nome',
                'justificativa_txt': 1
            },
            'elemnat_ilha_a': {
                'texto_edicao': 'nome',
                'tamanho_txt': 6,
                'justificativa_txt': 1,
                'rotular_carta_mini': 1
            },
            'infra_elemento_energia_a': {
                'texto_edicao': 'nome',
                'visivel': 1,
                'justificativa_txt': 1
            },
            'infra_pista_pouso_a': {
                'justificativa_txt': 2
            },
            'llp_area_pub_militar_a': {
                'texto_edicao': 'nome',
                'tamanho_txt': 8,
                'justificativa_txt': 1,
                'rotular_carta_mini': 1
            },
            'llp_terra_indigena_a': {
                'texto_edicao': 'nome',
                'tamanho_txt': 8,
                'justificativa_txt': 1,
                'rotular_carta_mini': 1
            },
            'llp_unidade_conservacao_a': {
                'texto_edicao': 'nome',
                'tamanho_txt': 8,
                'justificativa_txt': 1,
                'rotular_carta_mini': 1
            }  
        }

        for lyrName, lyr in zip(layersNames, layers):
            if lyrName in attrDefault:
                valeusToCommit = attrDefault.get(lyrName)
                self.setDefaultAttr(lyr, valeusToCommit)
                if lyrName in layersToCalculateDefaults:
                    self.setDefaultAttrCalc(lyrName, lyr)

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
                    feature[ 'texto_edicao' ] = 'Vau'
                    self.updateLayerFeature( layer, feature)



        return {self.OUTPUT: ''}

    def updateLayerFeature(self, layer, feature):
        layer.startEditing()
        layer.updateFeature(feature)

    @staticmethod
    def setDefaultAttr(lyr, mapping):
        provider = lyr.dataProvider()
        changeAttrMap = {}
        for feat in lyr.getFeatures():
            featAttrMap = {}
            for key, value in mapping.items():
                if value == 'name':
                    featAttrMap.update({provider.fieldNameIndex(key):feat.attribute('name')})
                else:
                    featAttrMap.update({provider.fieldNameIndex(key):value})
            changeAttrMap.update({feat.id():featAttrMap})
        provider.changeAttributeValues(changeAttrMap)

    def setDefaultAttrCalc(self,lyrName, lyr):
        provider = lyr.dataProvider()
        fieldIdx = provider.fieldNameIndex('texto_edicao')
        if lyrName in ('infra_pista_pouso_p', 'infra_pista_pouso_l', 'infra_pista_pouso_a'):
            lyr.startEditing()
            for feat in lyr.getFeatures():
                text = self.coalesceAttributeV1(
                    ('name', lyr.attribute('name')),
                    ('altitude', lyr.attribute('altitude')),
                    ('altura', lyr.attrubute('altura'))
                )
                feat.setAttribute(fieldIdx, text)
        elif lyrName == 'infra_obstaculo_vertical_p':
            lyr.startEditing()
            for feat in lyr.getFeatures():
                text = self.coalesceAttributeV2(lyr, 'nome', 'situacaofisica', 'revestimento', 'altitude')
                feat.setAttribute(fieldIdx, text)
        elif lyrName == 'elemnat_curva_nivel_l':
            pass

    @staticmethod
    def coalesceAttributeV1(lyr, *fields):
        expression = ''
        for i, field in enumerate(fields):
            if lyr.attibute(field):
                if i == 0:
                    if field == 'altura':
                        expression = f'\'(\' || "{field}" || \')\''
                    else:
                        expression = f'"{field}"'
                else:
                    if field == 'altura':
                        expression = f'{expression} || \'\\n\' || \'(\' || "{field}" || \')\''
                    else:
                        expression = f'"{expression}" || \'\\n\' || "{field}"'
        return expression

    @staticmethod
    def coalesceAttributeV2(lyr, *fields):
        for i, field in enumerate(fields):
            if lyr.attribute(field):
                if i == 0:
                    if field == 'situacaofisica':
                        expression = f'\'(\' || "{field}" || \')\''
                    else:
                        expression = f'"{field}"'
                else:
                    if field == 'situacaofisica':
                        expression = f'{expression} || \'\\n\' || \'(\' || "{field}" || \')\''
                    else:
                        expression = f'{expression} || \'\\n\' || "{field}"'
        return expression          

    @staticmethod
    def coalesceAttributeV3(lyr, field):
        expression = ''
        if elevation:=lyr.attribute(field) is not None:
            if elevation == 0:
                expression = 'ZERO'
            else:
                expression = f'{elevation}'
        return expression

    @staticmethod
    def checkIntersectionAndSetAttr(lyrsRef, *lyrs):
        feats = []
        ids = []
        for lyrRef in lyrsRef:
            feats.extend(x for x in lyrRef.getFeatures())
        for lyr in lyrs:
            lyr.startEditing()
            provider = lyr.dataProvider()
            for feat1 in lyr.getFeatures():
                for feat2 in feats:
                    if feat1.geom().within(feat2.geom()):
                        lyr.changeAttributeValue(feat1.id(), provider.fieldNameIndex('sobreposto'), True)
                        break
            # lyr.commitChanges()
        

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return PrepareOrtho()

    def name(self):
        return 'prepareortho'

    def displayName(self):
        return self.tr('Prepara carta ortoimagem')

    def group(self):
        return self.tr('Edição')

    def groupId(self):
        return 'edicao'

    def shortHelpString(self):
        return self.tr("O algoritmo prepara os atributos para carta ortoimagem")
    
