import math

from qgis import processing
from qgis.core import (QgsCoordinateReferenceSystem,
                       QgsCoordinateTransformContext, QgsDistanceArea,
                       QgsFeature, QgsFeatureRequest, QgsGeometry,
                       QgsProcessing, QgsProcessingAlgorithm,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingParameterNumber, QgsUnitTypes)
from qgis.PyQt.QtCore import QCoreApplication


class PrepareOrtho(QgsProcessingAlgorithm): 

    INPUT_LAYERS = 'INPUT_LAYERS'
    SCALE = 'SCALE'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS,
                self.tr('Selecionar camadas:'),
                QgsProcessing.TypeVectorAnyGeometry
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.SCALE,
                self.tr('Inserir escala:'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=50000
            )
        )

    def processAlgorithm(self, parameters, context, feedback):      
        layers = self.parameterAsLayerList(parameters, self.INPUT_LAYERS, context)
        scale = self.parameterAsInt(parameters, self.SCALE, context)
        layersToCalculateDefaults = [
            'infra_obstaculo_vertical_p',
            'infra_pista_pouso_p',
            'infra_pista_pouso_l',
            'infra_pista_pouso_a',
            'elemnat_curva_nivel_l'
        ]
        layersToCalculateSobreposition = [
            'llp_area_pub_militar_l',
            'llp_limite_legal_l',
            'llp_terra_indigena_l',
            'llp_unidade_conservacao_l'
        ]
        _refLayersNamesSobreposition = [
            'elemnat_trecho_drenagem_l',
            'infra_via_deslocamento_l',
            'infra_ferrovia_l'
        ]
        layerToCreateSpacedSymbolsCase1 = {
            'infra_elemento_energia_l':'edicao_simb_torre_energia_p'
        }
        layerToCreateSpacedSymbolsCase2 = {
            'infra_via_deslocamento_l':'edicao_identificador_trecho_rod_p'
        }
        refLayersSobreposition = [x for x in layers if x.dataProvider().uri().table() in _refLayersNamesSobreposition]
        destLayersToCreateSpacedSymbolsCase1 = filter(
            lambda x: x.dataProvider().uri().table() in layerToCreateSpacedSymbolsCase1.values(), layers)
        destLayersToCreateSpacedSymbolsCase2 = filter(
            lambda x: x.dataProvider().uri().table() in layerToCreateSpacedSymbolsCase2.values(), layers)

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

        for lyr in layers:
            lyrName = lyr.dataProvider().uri().table()
            # self.updateLayer(lyr, lyrName)
            if lyrName in attrDefault:
                valeusToCommit = attrDefault.get(lyrName)
                self.setDefaultAttr(lyr, valeusToCommit)
            if lyrName in layersToCalculateDefaults:
                self.setDefaultAttrCalc(lyrName, lyr)
            if lyrName in layersToCalculateSobreposition:
                self.checkIntersectionAndSetAttr(lyr, refLayersSobreposition)
            if lyrName in layerToCreateSpacedSymbolsCase1:
                distance = self.getChopDistance(lyr, scale * 0.02)
                pointsAndAngles = self.chopLineLayer(lyr, distance)
                self.populateEnergyTowerSymbolLayer(next(destLayersToCreateSpacedSymbolsCase1),pointsAndAngles)
            if lyrName in layerToCreateSpacedSymbolsCase2:
                distance = self.getChopDistance(lyr, scale * 0.2)
                pointsAndAngles = self.chopLineLayer(lyr, distance, ['sigla'])
                self.populateRoadIndentificationSymbolLayer(next(destLayersToCreateSpacedSymbolsCase2),pointsAndAngles)
                    
        return {self.OUTPUT: ''}

    def updateLayer(self, layer, layerName):
        if layerName in [
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
        
        elif layerName in [ 'infra_vala_l' ]:
            for feature in layer.getFeatures():
                feature[ 'texto_edicao' ] = 'Vala'
                self.updateLayerFeature( layer, feature)
        
        elif layerName in [ 'infra_trecho_duto_l' ]:
            for feature in layer.getFeatures():
                if not( feature['tipo'] == 301 ):
                    continue
                feature[ 'texto_edicao' ] = 'Água'
                self.updateLayerFeature( layer, feature)

        elif layerName in [ 'infra_trecho_hidroviario_l' ]:
            for feature in layer.getFeatures():
                if not( feature['tipo'] == 1 ):
                    continue
                feature[ 'texto_edicao' ] = 'Balsa'
                self.updateLayerFeature( layer, feature)

        elif layerName in [ 'llp_limite_especial_l' ]:
            for feature in layer.getFeatures():
                feature[ 'texto_edicao' ] = 'Aproximado'
                self.updateLayerFeature( layer, feature)
            
        elif layerName in [ 'infra_pista_pouso_p' ]:
            for feature in layer.getFeatures():
                feature[ 'texto_edicao' ] = feature[ 'nome' ]
                self.updateLayerFeature( layer, feature)

        elif layerName in [ 
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

        elif layerName in [ 'constr_edificacao_a', 'constr_edificacao_p' ]:
            for feature in layer.getFeatures():
                if feature['tipo'] == 1218:
                    feature[ 'texto_edicao' ] = 'Curral'
                else:
                    feature[ 'texto_edicao' ] = feature[ 'nome' ]
                self.updateLayerFeature( layer, feature)

        elif layerName in [ 'infra_elemento_viario_p', 'infra_elemento_viario_l' ]:
            for feature in layer.getFeatures():
                if not( feature['tipo'] in [401,402] ):
                    continue
                feature[ 'texto_edicao' ] = 'Vau'
                self.updateLayerFeature( layer, feature)

    @staticmethod
    def updateLayerFeature(layer, feature):
        '''Helper function to update layer feature
        '''
        layer.startEditing()
        layer.updateFeature(feature)

    @staticmethod
    def setDefaultAttr(lyr, mapping):
        '''Updates features according to the mapping. If any item from the mapping has a "nome" value, 
        the feature is updated with feature's attribute "nome" 
        '''
        provider = lyr.dataProvider()
        changeAttrMap = {}
        for feat in lyr.getFeatures():
            featAttrMap = {}
            for key, value in mapping.items():
                if value == 'nome':
                    featAttrMap.update({provider.fieldNameIndex(key):feat.attribute(value)})
                else:
                    featAttrMap.update({provider.fieldNameIndex(key):value})
            changeAttrMap.update({feat.id():featAttrMap})
        provider.changeAttributeValues(changeAttrMap)

    def setDefaultAttrCalc(self, lyrName, lyr):
        '''Updates "texto_edicao" attribute by joining attribute values. The joining process
        is coordinated by the functions coalesceAttributeV[1,2,3]
        '''
        provider = lyr.dataProvider()
        fieldIdx = provider.fieldNameIndex('texto_edicao')
        if lyrName == 'infra_obstaculo_vertical_p':
            lyr.startEditing()
            for feat in lyr.getFeatures():
                text = self.coalesceAttributeV1(feat, 'nome', 'altitude', 'altura')
                lyr.changeAttributeValue(feat.id(), fieldIdx, text)
        elif lyrName in ('infra_pista_pouso_p', 'infra_pista_pouso_l', 'infra_pista_pouso_a'):
            lyr.startEditing()
            for feat in lyr.getFeatures():
                text = self.coalesceAttributeV2(feat, 'nome', 'situacao_fisica', 'revestimento', 'altitude')
                lyr.changeAttributeValue(feat.id(), fieldIdx, text)
        elif lyrName == 'elemnat_curva_nivel_l':
            lyr.startEditing()
            for feat in lyr.getFeatures():
                text = self.coalesceAttributeV3(feat, 'cota')
                lyr.changeAttributeValue(feat.id(), fieldIdx, text)
        # lyr.commitChanges()

    @staticmethod
    def coalesceAttributeV1(feat, *fields):
        '''Join attribute values for the layer 'infra_obstaculo_vertical_p'
        '''
        _first = True
        for field in fields:
            if feat.attibute(field):
                if _first:
                    _first = False
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
    def coalesceAttributeV2(feat, *fields):
        '''Join attribute values for the layers 'infra_pista_pouso_p', 'infra_pista_pouso_l' and 'infra_pista_pouso_a'
        '''
        _first = True
        for field in fields:
            if feat.attribute(field):
                if _first:
                    _first = False
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
        '''Join attribute values for the layer 'elemnat_curva_nivel_l'
        '''
        expression = ''
        if elevation:=lyr.attribute(field) is not None:
            if elevation == 0:
                expression = 'ZERO'
            else:
                expression = f'{elevation}'
        return expression

    @staticmethod
    def checkIntersectionAndSetAttr(lyr, lyrsRef):
        '''Updates the attribute 'sobreposto' if lyr limits are within lrysRef 
        '''
        _updated = False
        provider = lyr.dataProvider()
        lyr.startEditing()
        for feat1 in lyr.getFeatures():
            request = QgsFeatureRequest().setFilterRect(feat1.geometry().boundingBox())
            geomEngine = QgsGeometry.createGeometryEngine(feat1.geometry().constGet())
            geomEngine.prepareGeometry()
            for lyrRef in lyrsRef:
                for feat2 in lyrRef.getFeatures(request):
                    intersection = geomEngine.intersection(feat2.geometry().constGet())
                    if intersection.geometryType() in ('LineString','MultiLineString'):
                        _updated = True
                        lyr.changeAttributeValue(feat1.id(), provider.fieldNameIndex('sobreposto'), 3)
                        break
                if _updated is True:
                    _updated = False
                    break
            # lyr.commitChanges()

    @staticmethod
    def getChopDistance(layer, distance):
        '''Helper function to get distances in decimal degrees
        '''
        if layer.crs().isGeographic():
            d = QgsDistanceArea()
            d.setSourceCrs(QgsCoordinateReferenceSystem('EPSG:3857'), QgsCoordinateTransformContext())
            return d.convertLengthMeasurement(distance, QgsUnitTypes.DistanceDegrees)
        else:
            return distance

    def chopLineLayer(self, layer, cutDistance, requiredAttrs=None):
        '''Chops layer using cutDistance, returning initial points of chopped features and its angles.
        If the point touches the initial/final point of any original feature the point is discarded.
        If requiredAttrs is provided, the mapping {attr:feat[attr] for attr in requiredAttrs} is also returned
        '''
        attributeMapping = {}
        pointsAndAngles = []
        output = processing.run(
            'native:splitlinesbylength', {
                'INPUT': layer,
                'LENGTH': cutDistance,
                'OUTPUT' : 'TEMPORARY_OUTPUT'
            })['OUTPUT']
        bounds = processing.run(
            'native:boundary', {
                'INPUT': layer,
                'OUTPUT' : 'TEMPORARY_OUTPUT'
            })['OUTPUT']
        for feat in output.getFeatures():
            if requiredAttrs and \
                all((x in layer.fields().names() for x in requiredAttrs)) and \
                all((feat.attribute(x) for x in requiredAttrs)):
                attributeMapping = {x:feat.attribute(x) for x in requiredAttrs}
            isBoundVertex = False
            request = QgsFeatureRequest().setFilterRect(feat.geometry().boundingBox())
            geomEngine = QgsGeometry.createGeometryEngine(feat.geometry().constGet())
            geomEngine.prepareGeometry()
            for featBound in bounds.getFeatures(request):
                if geomEngine.touches(featBound.geometry().constGet()):
                    isBoundVertex = True
                    break
            if not isBoundVertex:
                geom = feat.geometry()
                point = geom.vertexAt(0)
                angle = (geom.angleAtVertex(0) + (math.pi/2))*180/math.pi
                pointsAndAngles.append((point, angle, attributeMapping))
        return pointsAndAngles

    def populateEnergyTowerSymbolLayer(self, layer, pointsAndAngles):
        '''Populates the layer edicao_simb_torre_energia_p
        '''
        fields = layer.fields()
        layer.startEditing()
        for point, angle, _ in pointsAndAngles:
            feat = QgsFeature(fields)
            geom = QgsGeometry.fromWkt(point.asWkt())
            feat.setGeometry(geom)
            feat.setAttribute('simb_rot', angle)
            layer.addFeature(feat)
        # layer.commitChanges()

    def populateRoadIndentificationSymbolLayer(self, layer, pointsAndAngles):
        '''Populates the layer edicao_identificador_trecho_rod_p
        '''
        fields = layer.fields()
        layer.startEditing()
        for point, angle, mapping in pointsAndAngles:
            feat = QgsFeature(fields)
            geom = QgsGeometry.fromWkt(point.asWkt())
            feat.setGeometry(geom)
            if sigla:=mapping.get('sigla'):
                name = sigla.split(';')[0].split('-')[0]
                feat.setAttribute('sigla', name)
            layer.addFeature(feat)
        # layer.commitChanges()

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
    
