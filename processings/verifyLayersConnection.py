# -*- coding: utf-8 -*-

from qgis import processing
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing, QgsProject,
                       QgsFeatureSink, QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingParameterString,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterNumber,
                       QgsFeature, QgsVectorLayer,
                       QgsProcessingParameterVectorDestination,
                       QgsGeometry, QgsField,
                       QgsFields, QgsWkbTypes
                       )


class VerifyLayersConnection(QgsProcessingAlgorithm):

    INPUT_FRAMES = 'INPUT_FRAMES'
    LAYERS = 'LAYERS'
    TOLERANCE = 'TOLERANCE'
    IGNORE_LIST = 'IGNORE_LIST'
    NO_TOUCH_L = 'NO_TOUCH_L'
    NO_TOUCH_A = 'NO_TOUCH_A'
    ATTR_ERROR_L = 'ATTR_ERROR_L'
    ATTR_ERROR_A = 'ATTR_ERROR_A'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_FRAMES,
                self.tr('Select frame layer'),
                [QgsProcessing.TypeVectorPolygon, QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            ValidateQgsProcessingParameterMultipleLayers(
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
                QgsProcessingParameterNumber.Double,
                defaultValue=0.1,
                minValue=0.0001,
                maxValue=100
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.NO_TOUCH_L,
                self.tr('Revisar ligação (linha)')
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.ATTR_ERROR_L,
                self.tr('Revisar atributos na ligação (linha)')
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.NO_TOUCH_A,
                self.tr('Revisar ligação (área)')
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.ATTR_ERROR_A,
                self.tr('Revisar atributos na ligação (área)')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        extents = self.parameterAsSource(parameters, self.INPUT_FRAMES, context)
        layers = self.parameterAsLayerList(parameters, self.LAYERS, context)
        ignored_fields = self.parameterAsString(parameters, self.IGNORE_LIST, context)
        ignored_fields = ignored_fields.split(';')
        tol = self.parameterAsDouble(parameters, self.TOLERANCE, context)

        final_no_touch_l = []
        final_no_touch_a = []
        final_attr_error_l = []
        final_attr_error_a = []
        layer_list_l = [[],[]]
        layer_list_a = [[],[]]

        # Get VectorLayer from extents
        extentsLayer = self.setupExtentsLayer(extents, layers[0].sourceCrs())

        # If VectorLayer is a polygon, transform into lines
        # TODO: When QGIS migrates to py3.8, use walrus on getFeatures() to delete it later?
        if extentsLayer.geometryType() == QgsWkbTypes.PolygonGeometry:
                extentsLayer = self.extentsAsLines(context, feedback, extentsLayer)

        # Gets only intersection between frames
        extentsLayer = self.filterExtents(context, feedback, extentsLayer)

        # Gets buffered frame intersections -> bbox
        inter_zones = self.bufferExtents(context, feedback, extentsLayer, tol)

        # Iterates over every layer
        for layer in layers:
            if layer.geometryType() == QgsWkbTypes.LineGeometry:
                # Gets points inside inter_zones
                feats_inside_intersection = self.getPointsInsideIntersectionL(layer, inter_zones)
                # Check intersection
                no_touch, attr_error = self.checkIntersection(feats_inside_intersection, ignored_fields)
                # Appends to total results
                final_attr_error_l.extend(attr_error)
                final_no_touch_l.extend(no_touch)
                # Identifies from which layer the error is originated
                layer_list_l[0].extend([layer.name() for x in range(len(no_touch))])
                layer_list_l[1].extend([layer.name() for x in range(len(attr_error))])
            elif layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                # Same as before, but for area layers
                feats_inside_intersection = self.getPointsInsideIntersectionA(layer, inter_zones)
                no_touch, attr_error = self.checkIntersection(feats_inside_intersection, ignored_fields)
                final_no_touch_a.extend(no_touch)
                final_attr_error_a.extend(attr_error)
                layer_list_a[0].extend([layer.name() for x in range(len(no_touch))])
                layer_list_a[1].extend([layer.name() for x in range(len(attr_error))])

        field =  QgsFields()
        field.append(QgsField('camada', QVariant.String))

        # Outputs to sinks
        if final_no_touch_l:
            sink_no_touch_l, _ = self.parameterAsSink(parameters, self.NO_TOUCH_L, context, field,
                final_no_touch_l[0].geometry().wkbType(), layers[0].sourceCrs())
            for idx, feat in enumerate(final_no_touch_l):
                feat.setFields(field)
                feat.setAttribute('camada', layer_list_l[0][idx])
                sink_no_touch_l.addFeature(feat)
        if final_attr_error_l:
            sink_attr_error_l, _ = self.parameterAsSink(parameters, self.ATTR_ERROR_L, context, field,
                final_attr_error_l[0].geometry().wkbType(), layers[0].sourceCrs())
            for idx, feat in enumerate(final_attr_error_l):
                feat.setFields(field)
                feat.setAttribute('camada', layer_list_l[1][idx])
                sink_attr_error_l.addFeature(feat)
        if final_no_touch_a:
            sink_no_touch_a, _ = self.parameterAsSink(parameters, self.NO_TOUCH_A, context, field,
                final_no_touch_a[0].geometry().wkbType(), layers[0].sourceCrs())
            for idx, feat in enumerate(final_no_touch_a):
                feat.setFields(field)
                feat.setAttribute('camada', layer_list_a[0][idx])
                sink_no_touch_a.addFeature(feat)
        if final_attr_error_a:
            sink_attr_error_a, _ = self.parameterAsSink(parameters, self.ATTR_ERROR_A, context, field,
                final_attr_error_a[0].geometry().wkbType(), layers[0].sourceCrs())
            for idx, feat in enumerate(final_attr_error_a):
                feat.setFields(field)
                feat.setAttribute('camada', layer_list_a[1][idx])
                sink_attr_error_a.addFeature(feat)
        return {
            self.NO_TOUCH_L: final_no_touch_l,
            self.ATTR_ERROR_L: final_attr_error_l,
            self.NO_TOUCH_A: final_no_touch_a,
            self.ATTR_ERROR_A: final_attr_error_a
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

    def filterExtents(self, context, feedback, extents):
        intersection = processing.run(
            'qgis:intersection',
            {
                'INPUT': extents,
                'OVERLAY': extents,
                'OUTPUT': 'memory:'
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback)['OUTPUT']
        intersection = context.takeResultLayer(intersection)
        ids_and_areas = []
        feats_to_delete = []
        provider = intersection.dataProvider()
        max_len = 0
        for feat in intersection.getFeatures():
            length = feat.geometry().length()
            max_len = max(max_len, length)
            ids_and_areas.append((feat.id(), length))
        for item in ids_and_areas:
            feat_id, length = item
            if length > max_len/2:
                feats_to_delete.append(feat_id)
        provider.deleteFeatures(feats_to_delete)
        return intersection

    def getPointsInsideIntersectionL(self, layer, ref):
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

    def getPointsInsideIntersectionA(self, layer, ref):
        v_to_analyse = []
        ref = next(ref.getFeatures()).geometry()
        feats = layer.getFeatures()
        for feat in feats:
            for v in feat.geometry().vertices():
                v = v.asWkt()
                v = QgsGeometry.fromWkt(v)
                if v.intersects(ref):
                    v_to_analyse.append(feat)
                    break
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

class ValidateQgsProcessingParameterMultipleLayers(QgsProcessingParameterMultipleLayers):
    '''
    Auxiliary class for validationg the number of layers
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def checkValueIsAcceptable(self, layers_names, context=None):
        import inspect
        print(inspect.getmembers(self))
        mapLayers = QgsProject.instance().mapLayers()
        for lyr_name in layers_names:
            lyr = mapLayers.get(lyr_name, None)
            if lyr is None:
                continue
            elif lyr and (lyr.geometryType() in (QgsWkbTypes.LineString, QgsWkbTypes.MultiLineString, QgsWkbTypes.MultiPolygon, 
                                                    QgsWkbTypes.Polygon, QgsWkbTypes.LineGeometry, QgsWkbTypes.PolygonGeometry)):
                continue
            else:
                return False
        return True