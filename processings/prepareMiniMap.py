# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import (QCoreApplication)
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterVectorLayer,
                       QgsExpression, 
                       QgsFeatureRequest,
                       QgsProcessingParameterNumber,
                       QgsGeometry,
                       QgsFeature,
                       NULL
                       )

class PrepareMiniMap(QgsProcessingAlgorithm):
    
    INPUT_IDENTIFICADOR_TRECHO_ROD_P = 'INPUT_IDENTIFICADOR_TRECHO_ROD_P'
    INPUT_LLP_LOCALIDADE_P = 'INPUT_LLP_LOCALIDADE_P'
    INPUT_EDICAO_SIMB_HIDROGRAFIA_P = 'INPUT_EDICAO_SIMB_HIDROGRAFIA_P'
    INPUT_EDICAO_SIMB_HIDROGRAFIA_L= 'INPUT_EDICAO_SIMB_HIDROGRAFIA_L'
    INPUT_ELEMNAT_TOPONIMO_FISIOGRAFICO_NATURAL_P = 'INPUT_ELEMNAT_TOPONIMO_FISIOGRAFICO_NATURAL_P'
    INPUT_ELEMNAT_TOPONIMO_FISIOGRAFICO_NATURAL_L = 'INPUT_ELEMNAT_TOPONIMO_FISIOGRAFICO_NATURAL_L'
    INPUT_EDICAO_TEXTO_GENERICO_P = 'INPUT_EDICAO_TEXTO_GENERICO_P'
    INPUT_EDICAO_TEXTO_GENERICO_L = 'INPUT_EDICAO_TEXTO_GENERICO_L'
    INPUT_LLP_LIMITE_ESPECIAL_A = 'INPUT_LLP_LIMITE_ESPECIAL_A'
    INPU_ESCALA = 'INPU_ESCALA'
    OUTPUT = 'OUTPUT'
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_IDENTIFICADOR_TRECHO_ROD_P',
                self.tr('Selecione a camada identificador_trecho_rod_p'),
                types=[QgsProcessing.TypeVectorPoint],
                defaultValue = 'identificador_trecho_rod_p'
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_LLP_LOCALIDADE_P',
                self.tr('Selecione a camada llp_localidade_p'), 
                types=[QgsProcessing.TypeVectorPoint],
                defaultValue = 'llp_localidade_p'
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_EDICAO_SIMB_HIDROGRAFIA_P',
                self.tr('Selecione a camada edicao_simb_hidrografia_p'), 
                types=[QgsProcessing.TypeVectorPoint],
                defaultValue = 'edicao_simb_hidrografia_p'
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_EDICAO_SIMB_HIDROGRAFIA_L',
                self.tr('Selecione a camada edicao_simb_hidrografia_l'), 
                types=[QgsProcessing.TypeVectorLine],
                defaultValue = 'edicao_simb_hidrografia_l'
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_ELEMNAT_TOPONIMO_FISIOGRAFICO_NATURAL_P',
                self.tr('Selecione a camada elemnat_toponimo_fisiografico_natural_p'), 
                types=[QgsProcessing.TypeVectorPoint],
                defaultValue = 'elemnat_toponimo_fisiografico_natural_p'
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_ELEMNAT_TOPONIMO_FISIOGRAFICO_NATURAL_L',
                self.tr('Selecione a camada elemnat_toponimo_fisiografico_natural_l'), 
                types=[QgsProcessing.TypeVectorLine],
                defaultValue = 'elemnat_toponimo_fisiografico_natural_l'
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_EDICAO_TEXTO_GENERICO_P',
                self.tr('Selecione a camada edicao_texto_generico_p'), 
                types=[QgsProcessing.TypeVectorPoint],
                defaultValue = 'edicao_texto_generico_p'
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_EDICAO_TEXTO_GENERICO_L',
                self.tr('Selecione a camada edicao_texto_generico_l'), 
                types=[QgsProcessing.TypeVectorLine],
                defaultValue = 'edicao_texto_generico_l'
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_LLP_LIMITE_ESPECIAL_A',
                self.tr('Selecione a camada llp_limite_especial_a'),
                types=[QgsProcessing.TypeVectorPolygon],
                defaultValue = 'llp_limite_especial_a'
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                'INPU_ESCALA',
                self.tr('Insira a escala'), 
                type=QgsProcessingParameterNumber.Integer,
                minValue=0)
            )
    def processAlgorithm(self, parameters, context, feedback):

        identificador_trecho_rod_p_layer = self.parameterAsVectorLayer( parameters,'INPUT_IDENTIFICADOR_TRECHO_ROD_P', context )
        llp_localidade_p_layer = self.parameterAsVectorLayer( parameters,'INPUT_LLP_LOCALIDADE_P', context )
        edicao_simb_hidrografia_p_layer = self.parameterAsVectorLayer( parameters,'INPUT_EDICAO_SIMB_HIDROGRAFIA_P', context )
        edicao_simb_hidrografia_l_layer = self.parameterAsVectorLayer( parameters,'INPUT_EDICAO_SIMB_HIDROGRAFIA_L', context )
        elemnat_toponimo_fisiografico_natural_p_layer = self.parameterAsVectorLayer( parameters,'INPUT_ELEMNAT_TOPONIMO_FISIOGRAFICO_NATURAL_P', context )
        elemnat_toponimo_fisiografico_natural_l_layer = self.parameterAsVectorLayer( parameters,'INPUT_ELEMNAT_TOPONIMO_FISIOGRAFICO_NATURAL_L', context )
        edicao_texto_generico_p_layer = self.parameterAsVectorLayer( parameters,'INPUT_EDICAO_TEXTO_GENERICO_P', context )
        edicao_texto_generico_l_layer = self.parameterAsVectorLayer( parameters,'INPUT_EDICAO_TEXTO_GENERICO_L', context )
        llp_limite_especial_a_layer = self.parameterAsVectorLayer( parameters,'INPUT_LLP_LIMITE_ESPECIAL_A', context )
        escala_input = self.parameterAsInt( parameters,'INPU_ESCALA', context )
        step = 1
        progressStep = 100/10
        feedback.setProgress( step * progressStep )
        self.editLayer(identificador_trecho_rod_p_layer, False, escala_input, False, 6, False, 0, False, False)
        step +=1
        feedback.setProgress( step * progressStep )
        self.editLayer(llp_localidade_p_layer, False, escala_input, False, 0, False, 6, True, False)
        step +=1
        feedback.setProgress( step * progressStep )
        self.editLayer(edicao_simb_hidrografia_p_layer, True, escala_input, False, 6, False, 0, False, False)
        step +=1
        feedback.setProgress( step * progressStep )
        self.editLayer(edicao_simb_hidrografia_l_layer, True, escala_input, False, 6, False, 0, False, True)
        step +=1
        feedback.setProgress( step * progressStep )
        self.editLayer(elemnat_toponimo_fisiografico_natural_p_layer, False, escala_input, False, 6, True, 6, False, False)
        step +=1
        feedback.setProgress( step * progressStep )
        self.editLayer(elemnat_toponimo_fisiografico_natural_l_layer, False, escala_input, True, 2, True, 6, False, True)
        step +=1
        feedback.setProgress( step * progressStep )
        self.editLayer(edicao_texto_generico_p_layer, False, escala_input, True, 0, True, 6, False, False)
        step +=1
        feedback.setProgress( step * progressStep )
        self.editLayer(edicao_texto_generico_l_layer, False, escala_input, True, 0, True, 6, False, True)
        step +=1
        feedback.setProgress( step * progressStep )
        newFields = edicao_texto_generico_p_layer.fields()
        pointsToAdd = []
        for feature in llp_limite_especial_a_layer.getFeatures():
            centroidgeom = feature.geometry().centroid()
            newFeat = QgsFeature()
            newFeat.setGeometry(centroidgeom)
            newFeat.setFields(newFields)
            newFeat['carta_mini'] = True
            newFeat['espacamento'] = 0
            newFeat['tamanho_txt'] = 6
            newFeat['cor'] = '#000000'
            newFeat['estilo_fonte'] = 'Condensed Light'
            newFeat['texto_edicao'] = feature['nome'].upper()
            pointsToAdd.append(newFeat)
        edicao_texto_generico_p_layer.startEditing()
        edicao_texto_generico_p_layer.addFeatures(pointsToAdd)
        step +=1
        feedback.setProgress( step * progressStep )
        
        return {self.OUTPUT: 'Camadas editadas com sucesso'}

    def editLayer(self, layer, changeEscala, escala_input, changeEspacamento, espacamento, changeTamanho, tamanho_txt, verifyTipo, isLine):
        exp = QgsExpression('carta_mini IS False')
        if verifyTipo:
            exp = QgsExpression('carta_mini is False AND NOT (tipo = 8 OR tipo=9 OR tipo=10)')
        request = QgsFeatureRequest(exp)
        features = []
        for feature in layer.getFeatures(request):
            feature['id'] = NULL
            feature['carta_mini'] = True 
            if changeEscala:
                feature['escala'] = escala_input 
            if isLine:
                for geom in feature.geometry().constGet():
                    ptIni = geom[0]
                    ptFin = geom[-1]
                feature.setGeometry(QgsGeometry().fromPolyline([ptIni, ptFin]))
            if changeEspacamento:
                feature['espacamento'] = espacamento 
            if changeTamanho:
                feature['tamanho_txt'] = tamanho_txt
            features.append(feature)
        layer.startEditing()
        layer.addFeatures(features)
        return False
        
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return PrepareMiniMap()

    def name(self):
        return 'prepareminimap'

    def displayName(self):
        return self.tr('Prepara Carta Mini')

    def group(self):
        return self.tr('Edição')

    def groupId(self):
        return 'edicao'

    def shortHelpString(self):
        return self.tr("Prepara as camadas para carta mini.")
    
