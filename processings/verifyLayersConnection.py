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
                       QgsFeatureRequest,
                       QgsProcessingOutputVectorLayer,
                       QgsProject,
                       QgsWkbTypes
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
                self.tr('Select frames layer')
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

        final_no_touch = []
        final_attr_error = []
        layer_list = [[],[]]

        # Get VectorLayer from extents
        extentsLayer = self.setupExtentsLayer(extents, layers[0].sourceCrs())

        # If VectorLayer is a polygon, transform into lines
        # TODO: When QGIS migrates to py3.8, use walrus on getFeatures() to delete it later?
        if next(extentsLayer.getFeatures()).geometry().wkbType() in [QgsWkbTypes.MultiPolygon, QgsWkbTypes.Polygon]:
                extentsLayer = self.extentsAsLines(context, feedback, extentsLayer)

        # Gets buffered frame intersections -> bbox
        inter_zones = self.bufferExtents(context, feedback, extentsLayer, tol)

        # Iterates over every layer
        for layer in layers:
            # Gets points inside inter_zones
            feats_inside_intersection = self.getPointsInsideIntersection(layer, inter_zones)
            # Check intersection
            no_touch, attr_error = self.checkIntersection(feats_inside_intersection, ignored_fields)
            # Appends to total results
            final_no_touch.extend(no_touch)
            final_attr_error.extend(attr_error)
            # Identifies from which layer the error is originated
            layer_list[0].extend([layer.name() for x in range(len(no_touch))])
            layer_list[1].extend([layer.name() for x in range(len(attr_error))])

        field =  QgsFields()
        field.append(QgsField('camada', QVariant.String))

        # Outputs to sinks
        if final_no_touch:
            sink_no_touch, _ = self.parameterAsSink(parameters, self.NO_TOUCH, context, field,
                no_touch[0].geometry().wkbType(), layers[0].sourceCrs())
            for idx, feat in enumerate(final_no_touch):
                feat.setFields(field)
                feat.setAttribute('camada', layer_list[0][idx])
                sink_no_touch.addFeature(feat)
        if final_attr_error:
            sink_attr_error, _ = self.parameterAsSink(parameters, self.ATTR_ERROR, context, field,
                attr_error[0].geometry().wkbType(), layers[0].sourceCrs())
            for idx, feat in enumerate(final_attr_error):
                feat.setFields(field)
                feat.setAttribute('camada', layer_list[1][idx])
                sink_attr_error.addFeature(feat)
        return {
            self.NO_TOUCH: no_touch,
            self.ATTR_ERROR: attr_error
        }

    def setupExtentsLayer(self, extents, sourceCrs):
        feats = list(extents.getFeatures())
        wkb_list = {
            2: 'LineString',
            3: 'Polygon',
            5: 'MultiLineString',
            6: 'MultiPolygon',
        }
        wkb_id = feats[0].geometry().wkbType()
        uri = f"{wkb_list.get(wkb_id)}?crs={sourceCrs.authid().lower()}"
        vectorLayer = QgsVectorLayer(uri, "Scratch",  "memory")
        dataProvider = vectorLayer.dataProvider() 
        for feat in feats:
            to_insert = QgsFeature()
            to_insert.setGeometry(feat.geometry())
            dataProvider.addFeatures([to_insert])
        return vectorLayer

    def extentsAsLines(self, context, feedback, extents):
        lines = processing.run(
            'qgis:polygonstolines',
            {
                'INPUT': extents,
                'OUTPUT': 'memory:'
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback)['OUTPUT']
        lines = context.takeResultLayer(lines)
        return lines

    def bufferExtents(self, context, feedback, lines, tol):
        buffer = processing.run(
            'qgis:buffer',
            {
                'INPUT': lines,
                'DISTANCE': tol,
                'OUTPUT': 'memory:',
                'DISSOLVE': True
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback)['OUTPUT']
        buffer = context.takeResultLayer(buffer)
        return buffer

    def getPointsInsideIntersection(self, layer, ref):
        v_to_analyse = []
        ref = next(ref.getFeatures()).geometry()
        feats = layer.getFeatures()
        for feat in feats:
            vertices = list(feat.geometry().vertices())
            vi = vertices[0].asWkt()
            vi = QgsGeometry.fromWkt(vi)
            vf = vertices[-1].asWkt()
            vf = QgsGeometry.fromWkt(vf)
            if any((vi.intersection(ref), vf.intersection(ref))):
                v_to_analyse.append(feat)
        return v_to_analyse
    
    def checkIntersection(self, feats, ignored_fields):
        no_touch = []
        attr_error = []
        for ft1 in feats:
            touches = False
            for ft2 in feats:
                if ft1.geometry().equals(ft2.geometry()):
                    continue
                if ft1.geometry().touches(ft2.geometry()):
                    touches = True
                    if not self.checkFieldsOnFeatureIntersection(ft1, ft2, ignored_fields):
                        attr_error.append(ft1)
            if not touches:
                no_touch.append(ft1)
        return no_touch, attr_error

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
