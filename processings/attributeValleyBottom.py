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
                       QgsProcessingFeatureSourceDefinition,
                       QgsProcessingParameterNumber,
                       QgsFeature, QgsVectorLayer,
                       QgsProcessingParameterVectorDestination,
                       QgsGeometry, QgsField, QgsPoint,
                       QgsFields, QgsWkbTypes
                       )

class AttributeValleyBottom(QgsProcessingAlgorithm):

    INPUT_FRAMES = 'INPUT_FRAMES'
    LAYER = 'LAYER'
    WATERBODY = 'WATERBODY'
    CUT_DISTANCE = 'CUT_DISTANCE'
    TOLERANCE = 'TOLERANCE'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_FRAMES,
                self.tr('Select frame layer'),
                [QgsProcessing.TypeVectorPolygon, QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.LAYER,
                self.tr('Layers to attribute'),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.WATERBODY,
                self.tr('Selct the water body layer'),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.CUT_DISTANCE,
                self.tr('Distance to cut'),
                QgsProcessingParameterNumber.Double,
                defaultValue=0.1
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.TOLERANCE,
                self.tr('Maximum distance between initial vertex and frames'),
                QgsProcessingParameterNumber.Double,
                defaultValue=0.1
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        extents = self.parameterAsSource(parameters, self.INPUT_FRAMES, context)
        layer = self.parameterAsVectorLayer(parameters, self.LAYER, context)
        waterbody = self.parameterAsVectorLayer(parameters, self.WATERBODY, context)
        cut_size = self.parameterAsDouble(parameters, self.CUT_DISTANCE, context)
        tol = self.parameterAsDouble(parameters, self.TOLERANCE, context)

        crs = QgsProject.instance().crs()

        extentsLayer = self.setupExtentsLayer(extents, crs)

        if extentsLayer.geometryType() == QgsWkbTypes.PolygonGeometry:
            extentsLayerL = self.extentsAsLines(context, feedback, extentsLayer)
            extentsLayerA = extentsLayer
        elif extentsLayer.geometryType() == QgsWkbTypes.LineGeometry :
            extentsLayerL = extentsLayer
            extentsLayerA = self.extentsAsPolygons(context, feedback, extentsLayer)

        bufferedExtentsLayerL = self.bufferExtents(context, feedback, extentsLayerL, tol)
        dissolvedExtentsLayerA = self.dissolve(context, feedback, extentsLayerA)

        # Filters features with 1st vertex is inside extents
        filteredFeats = self.getFilteredFeats(dissolvedExtentsLayerA, layer.getFeatures(), predicate=True)
        print(len(filteredFeats))

        # Filters features that not intersects bufferedExtentsLayerL
        filteredFeats = self.getFilteredFeats(bufferedExtentsLayerL, filteredFeats, predicate=False)
        print(len(filteredFeats))

        # Gets only features that do not touch waterbody
        filteredFeats = self.filterOnIntersection(waterbody.getFeatures(), filteredFeats)
        print(len(filteredFeats))

        self.cutfeatures(layer, filteredFeats, cut_size)

        # Cuts and attributes if necessary
        return {}

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

    def extentsAsPolygons(self, context, feedback, extents):
        lines = processing.run(
            'qgis:linestopolygons',
            {
                'INPUT': extents,
                'OUTPUT': 'memory:'
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback)['OUTPUT']
        lines = context.takeResultLayer(lines)
        return lines

    def dissolve(self, context, feedback, extents):
        dissolved = processing.run(
            'qgis:dissolve',
            {
                'INPUT': extents,
                'OUTPUT': 'memory:'
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback)['OUTPUT']
        dissolved = context.takeResultLayer(dissolved)
        return dissolved

    def bufferExtents(self, context, feedback, lines, tol=0.1):
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
    
    def getFilteredFeats(self, ref, feats, predicate):
        '''
        When predicate=True, filters features from layer that intersects ref.
        Filters non-intersected features otherwise.
        '''
        filtered = []
        refFeatGeom = next(ref.getFeatures()).geometry()
        for feat in feats:
            vertices = list(feat.geometry().vertices())
            if not vertices:
                continue
            v = vertices[0].asWkt()
            v = QgsGeometry.fromWkt(v)
            if predicate and v.intersects(refFeatGeom):
                filtered.append(feat)
            elif not predicate and not v.intersects(refFeatGeom):
                filtered.append(feat)
        return filtered

    def filterOnIntersection(self, ref, to_filter):
        filtered = []
        for feat1 in to_filter:
            touches = False
            gfeat1 = feat1.geometry()
            for feat2 in ref:
                gfeat2 = feat2.geometry()
                if gfeat1.intersects(gfeat2):
                    touches = True
                    break
            if not touches:
                filtered.append(feat1)
        return filtered

    def cutfeatures(self, layer, feats, cut_size):
        layer.startEditing()
        for featOrigin in feats:
            geom = featOrigin.geometry()
            length = geom.length()
            if geom.length() > 1.2*cut_size:
                g1, g2 = self.divideGeometries(geom, cut_size)
                attributes = featOrigin.attributes()
                attributes[0] = None
                f = QgsFeature()
                f.setAttributes(attributes)
                f.setAttribute('tipo', 3)
                f.setGeometry(g1)
                layer.addFeature(f)
                featOrigin.setGeometry(g2)
                layer.updateFeature(featOrigin)
            else:
                featOrigin.setAttribute('tipo', 3)
                layer.updateFeature(featOrigin)
        # iface.mapCanvas().refresh()

    def divideGeometries(self, geom, cut_size):
        interpolate = geom.interpolate()
        _, near_p, _ , _ = geom.closestSegmentWithContext(interpolate)
        seg_left = []
        seg_right = []
        flow = 'L'
        for v in geom.vertices():
            if v.distanceSquared(near_p.x(), near_p.y()) < 1e-6:
                flow = 'R'
            if flow == 'L':
                seg_left.append(v)
            else:
                seg_right.append(v)
        g_seg_left = QgsGeometry.fromPolyline(seg_left)
        g_seg_right = QgsGeometry.fromPolyline(seg_right)
        return g_seg_left, g_seg_right

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return AttributeValleyBottom()

    def name(self):
        return 'Attribute valley bottoms'

    def displayName(self):
        return self.tr('Attribute valley bottoms')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("Atribute valley bottoms")
