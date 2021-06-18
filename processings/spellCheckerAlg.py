from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QColor
from qgis.PyQt.Qt import QVariant
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsFeature,
                       QgsDataSourceUri,
                       QgsProcessingOutputVectorLayer,
                       QgsProcessingParameterVectorLayer,
                       QgsWkbTypes,
                       QgsAction,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingUtils,
                       QgsSpatialIndex,
                       QgsGeometry,
                       QgsProcessingParameterField,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterExpression,
                       QgsProcessingException,
                       QgsProcessingParameterString,
                       QgsProcessingParameterDefinition,
                       QgsProcessingParameterType,
                       QgsProcessingParameterCrs,
                       QgsCoordinateTransform,
                       QgsProject,
                       QgsCoordinateReferenceSystem,
                       QgsField,
                       QgsFields,
                       QgsProcessingOutputMultipleLayers,
                       QgsProcessingParameterString,
                       QgsConditionalStyle,
                       QgsVectorLayer)
import os
from qgis import core
from qgis.utils import iface
from .processingAlg import ProcessingAlg
from ..modules.spellchecker.spellCheckerCtrl import SpellCheckerCtrl
import re

class SpellCheckerAlg(ProcessingAlg):

    INPUT_LAYER = 'INPUT_LAYER'
    ATTRIBUTE_NAME = 'ATTRIBUTE_NAME'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super(SpellCheckerAlg, self).__init__()

    def initAlgorithm(self, config):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr('Selecionar a camada'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.ATTRIBUTE_NAME,
                description =  self.tr('Nome do Atributo'),
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('digitacao_flags')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(
            parameters,
            self.INPUT_LAYER,
            context
        )
        attributeName = self.parameterAsFile(
            parameters,
            self.ATTRIBUTE_NAME,
            context
        )
        spellchecker = SpellCheckerCtrl('pt-BR')
        errors = []
        output_dest_id = ''
        
        errorFieldName = '{}_erro'.format(attributeName)
        #field = core.QgsField('{}_erro'.format(attributeName))
        fieldRelation = core.QgsField('id', QVariant.Double)
        layer.startEditing()
        attributeIndex = self.getAttributeIndex(attributeName, layer)
        if attributeIndex < 0:
            return {self.OUTPUT: ''}
        auxLayer = core.QgsAuxiliaryStorage().createAuxiliaryLayer(fieldRelation, layer)
        #layer.setAuxiliaryLayer(auxlayer)
        #auxLayer = layer.auxiliaryLayer()
        vdef = core.QgsPropertyDefinition(
            errorFieldName,
            core.QgsPropertyDefinition.DataType.DataTypeString,
            "",
            "",
            ""
        )
        auxLayer.addAuxiliaryField(vdef)
        layer.setAuxiliaryLayer(auxLayer)
        idx = layer.fields().indexOf('auxiliary_storage__{}'.format(errorFieldName))
        layer.setFieldAlias(idx, errorFieldName)
        auxFields = auxLayer.fields()
        for feature in layer.getFeatures():
            if feedback.isCanceled():
                return {self.OUTPUT: output_dest_id}
            attributeValue = feature[attributeIndex]
            if not attributeValue:
                continue
            attributeValue = ''.join(e for e in attributeValue if not(e in [',', ';', '&', '.'] or e.isdigit()))
            wordlist = re.split(' |/', attributeValue)
            wordlist = [ w for w in wordlist if not w in ['-'] ]
            wrongWords = [ word for word in wordlist if not spellchecker.hasWord(word.lower())]
            if len(wrongWords) == 0:
                continue
            auxFeature = QgsFeature(auxFields)
            auxFeature['ASPK'] = feature['id']
            auxFeature['_{}'.format(errorFieldName)] = ';'.join(wrongWords)
            auxLayer.addFeature(auxFeature)
        return {self.OUTPUT: ''}

    def getFlagWkbType(self):
        return QgsWkbTypes.Point

    def getFlagFields(self):
        sinkFields = QgsFields()
        sinkFields.append(QgsField('erro', QVariant.String))
        sinkFields.append(QgsField('correcao', QVariant.String))
        sinkFields.append(QgsField('outras_opcoes', QVariant.String))
        return sinkFields

    def name(self):
        return 'spellchecker'

    def displayName(self):
        return self.tr('Verificador ortográfico')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def tr(self, string):
        return QCoreApplication.translate('SpellCheckerAlg', string)

    def createInstance(self):
        return SpellCheckerAlg()