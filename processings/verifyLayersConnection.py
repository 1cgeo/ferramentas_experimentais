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
                       QgsProcessingParameterString,
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
                       QgsFields,
                       QgsFeatureRequest
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
            QgsProcessingParameterString(
                self.IGNORE_LIST,
                self.tr('Fields to be ignored (separeted by ;)'),
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

    def processAlgorithm(self, parameters, context, feedback):
        extents = self.parameterAsSource(parameters, self.INPUT_FRAMES, context)
        layers = self.parameterAsLayerList(parameters, self.LAYERS, context)
        ignored_fields = self.parameterAsString(parameters, self.IGNORE_LIST, context)
        ignored_fields = ignored_fields.split(';')
        tol = self.parameterAsDouble(parameters, self.TOLERANCE, context)

        extents = [x for x in extents.getFeatures()]

        bbox = self.getExtentsIntersection(extents, tol)

        feats_inside = self.getPointsInsideIntersection(bbox, layers[0])

        # feats_bbox = self.getFeatsFromIntersection(bbox, layers[0])

        no_touch, attr_error = self.checkIntersection(feats_inside, ignored_fields)

        print(no_touch,attr_error)
        if no_touch:
            sink_no_touch, _ = self.parameterAsSink(parameters, self.NO_TOUCH, context, no_touch[0].fields(),
                no_touch[0].geometry().wkbType(), layers[0].sourceCrs())
            for feat in no_touch:
                sink_no_touch.addFeature(feat)
        if attr_error:
            sink_attr_error, _ = self.parameterAsSink(parameters, self.ATTR_ERROR, context, attr_error[0].fields(),
                attr_error[0].geometry().wkbType(), layers[0].sourceCrs())
            for feat in attr_error:
                sink_attr_error.addFeature(feat)
        return {
            self.NO_TOUCH: no_touch,
            self.ATTR_ERROR: attr_error
        }
    # TODO: verify buffer type
    def getExtentsIntersection(self, extents, tol):
        flyr1, flyr2 = extents[0], extents[1]
        gflyr1, gflyr2 = flyr1.geometry(), flyr2.geometry()
        if gflyr1.intersects(gflyr2):
            intersection = gflyr1.intersection(gflyr2)
            bbox = intersection.boundingBox().buffered(tol).asWktPolygon()
            bbox = QgsGeometry.fromWkt(bbox)
            return bbox
        return None

    def getPointsInsideIntersection(self, bbox, layer):
        v_to_analyse = []
        feats = layer.getFeatures(QgsFeatureRequest().setFilterRect(bbox.boundingBox()))
        for feat in feats:
            vertices = list(feat.geometry().vertices())
            vi = vertices[0].asWkt()
            vi = QgsGeometry.fromWkt(vi)
            vf = vertices[-1].asWkt()
            vf = QgsGeometry.fromWkt(vf)
            if any((vi.intersection(bbox), vf.intersection(bbox))):
                v_to_analyse.append((feat, vi, vf))
        return v_to_analyse
    
    def checkIntersection(self, bbox, feats):
        no_touch = []
        attr_error = []
        for feat1 in feats:
            ft1, vi1, vf1 = feat1
            touches = False
            for feat2 in feats:
                ft2, vi2, vf2 = feat2
                if ft1.geometry().touches(ft2.geometry()):
                    touches = True
                    if not self.checkFieldsOnFeatureIntersection(ft1, ft2, self.ignored_fields):
                        attr_error.append(feat1)
            if not touches:
                no_touch.append(feat1)
        return no_touch, attr_error

                    

    def getFeatsFromIntersection(self, intersection, layer):
        return [x for x in layer.getFeatures() if intersection.intersects(x.geometry())]

    def checkFeatureIntersection(self, feats, ignore_list):
        no_touch = []
        attr_error = []
        for feat1 in feats:
            touches = False
            for feat2 in feats:
                if feat1.geometry().touches(feat2.geometry()):
                    touches = True
                    print(f"{feat1} touches {feat2}!")
                    if not self.checkFieldsOnFeatureIntersection(feat1, feat2, ignore_list):
                        print("diff attrs!")
                        attr_error.append(feat1)
                    break
            if not touches:
                no_touch.append(feat1)
        return no_touch, attr_error

        # Verificar se a interseção está contida no polígono para ver caso do snap
        # Trabalhar a ideia do dissolve
        # Há casos de layers área em cima de outro layer? (não fazendo um hole)

    def checkFieldsOnFeatureIntersection(self, feat1, feat2, ignore_list):
        attrs_to_loop = (x for x in feat1.fields().names() if x not in ignore_list)
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
