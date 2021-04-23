# -*- coding: utf-8 -*-

from qgis import processing
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsFeatureSink, QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProject,
                       QgsMapLayer,
                       QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsProject,
                       QgsPointXY,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterBoolean,
                       QgsProcessingRegistry,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsFeature,
                       QgsVectorLayer,
                       QgsPoint,
                       QgsGeometry,
                       QgsProcessingParameterVectorDestination,
                       QgsField,
                       QgsFields
                       )


class VerifyLayersConnection(QgsProcessingAlgorithm):

    INPUT_FRAMES = 'INPUT_FRAMES'
    LAYERS = 'LAYERS'
    TOLERANCE = 'TOLERANCE'
    IGNORE_LIST = 'IGNORE_LIST'
    NO_TOUCH = 'NO_TOUCH'
    ATTR_ERROR = 'ATTR_ERROR'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_FRAMES,
                self.tr('Select (two) frames')
            )
        )
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.LAYERS,
                self.tr('Layers to be verified')
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.IGNORE_LIST,
                self.tr('Fields to be ignored'),
                parentLayerParameterName=self.LAYERS,
                allowMultiple=True,
                optional=True
            )
        )
        self.addParameter(
                QgsProcessingParameterNumber(
                self.TOLERANCE,
                self.tr('Tolerance'),
                QgsProcessingParameterNumber.Double
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.NO_TOUCH,
                self.tr('Revisar ligação')
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.ATTR_ERROR,
                self.tr('Revisar atributos na ligação')
            )
        )

    # Better to clip
    def processAlgorithm(self, parameters, context, feedback):
        extents = self.parameterAsSource(parameters, self.INPUT_FRAMES, context)
        layers = self.parameterAsLayerList(parameters, self.LAYERS, context)
        ignored_fields = self.parameterAsFields(parameters, self.IGNORE_LIST, context)
        tol = self.parameterAsDouble(parameters, self.TOLERANCE, context)

        extents = [x for x in extents.getFeatures()]
        extents_intersection = self.getExtentsIntersection(extents, tol)
        feats_lyr1 = self.getFeatsFromIntersection(extents_intersection, layers[0])
        # feats_lyr2 = self.getFeatsFromIntersection(extents_intersection, layers[1])

        no_touch, attr_error = self.checkFeatureIntersection(feats_lyr1, ignored_fields)
        print(no_touch, attr_error)
        

    def getExtentsIntersection(self, extents, tol):
        flyr1, flyr2 = extents[0], extents[1]
        gflyr1, gflyr2 = flyr1.geometry(), flyr2.geometry()
        if gflyr1.intersects(gflyr2):
            gflyr1, gflyr2 = gflyr1.buffer(tol,10), gflyr2.buffer(tol,10)
            intersection = gflyr1.intersection(gflyr2)
            return intersection if intersection else None
        return None

    def getFeatsFromIntersection(self, intersection, layer):
        return filter(lambda x: x.geometry().intersects(intersection), layer.getFeatures())     

    def checkFeatureIntersection(self, feats, ignore_list):
        no_touch = []
        attr_error = []
        for feat1 in feats:
            touches = False
            for feat2 in feats:
                if feat1.geometry().touches(feat2.geometry()):
                    touches = True
                    if not self.checkFieldsOnFeatureIntersection(feat1, feat2, ignore_list):
                        attr_error.append(feat1)
                    break
            if not touches:
                no_touch.append(feat1)
        return no_touch, attr_error
                    
        # Verificar se a interseção está contida no polígono para ver caso do snap

        # Trabalhar a ideia do dissolve

        # Há casos de layers área em cima de outro layer? (não fazendo um hole)

    def checkFieldsOnFeatureIntersection(self, feat1, feat2, ignore_list):
        assert feat1.attributes() == feat2.attributes()
        attrs_to_loop = (x for x in feat1.attributes() if x not in ignore_list)
        return all(feat1.attribute(x) == feat2.attribute(x) for x in attrs_to_loop)

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return VerifyLayersConnection()

    def name(self):
        return 'Verify layers connection'

    def displayName(self):
        return self.tr('VerifyLayersConnection')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("Verifica a conexão de layers entre molduras distintas")

# TODO: check if 2 layers were selected
class ValidateQgsProcessingParameterFeatureSource(QgsProcessingParameterFeatureSource):
    '''
    Auxiliary class for validationg the number of layers
    '''
    def __init__(self, name, description='', types=[QgsProcessing.TypeVectorAnyGeometry]):
        super().__init__(name, description, types)

    def checkValueIsAcceptable(self, feats, context=None):
        if len(feats) == 2:
            return True
        return False