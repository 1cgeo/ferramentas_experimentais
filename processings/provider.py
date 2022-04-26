import os
import xml.etree.ElementTree as ET
from os import listdir
from os.path import dirname, isfile, join

from processing.core.ProcessingConfig import ProcessingConfig, Setting
from qgis.core import (QgsProcessingModelAlgorithm, QgsProcessingProvider,
                       QgsXmlUtils)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtXml import QDomDocument

from .atribuirsrc import AtribuirSRC
from .attributeValleyBottom import AttributeValleyBottom
from .bridgeAndManholeRotation import BridgeAndManholeRotation
from .bridgeAndManholeWidth import BridgeAndManholeWidth
from .clipLayerInFrame import ClipLayerInFrame
from .createLandCover import CreateLandCover
from .damWidth import DamWidth
from .defineEditTextField import DefineEditTextField
from .fixMissingVertexOnIntersection import FixMissingVertexOnIntersection
from .generalizeBuildings import GeneralizeBuildings
from .identifyCloseFeatures import IdentifyCloseFeatures
from .identifyDiscontinuitiesInLines import IdentifyDiscontinuitiesInLines
from .identifyInvalidGeometry import IdentifyInvalidGeometry
from .identifyMultipleParts import IdentifyMultipleParts
from .identifyOverlaps import IdentifyOverlaps
from .identifySameAttributesInNeighbouringPolygons import \
    IdentifySameAttributesInNeighbouringPolygons
from .identifySmallFeatures import IdentifySmallFeatures
from .identifySmallLines import IdentifySmallLines
from .identifySmallNeighbouringSameAttributesPolygons import \
    IdentifySmallNeighbouringSameAttributesPolygons
from .identifySplittedLines import IdentifySplittedLines
from .identifyUndershootLines import IdentifyUndershootLines
from .line2Multiline import Line2Multiline
from .mergeLinesBySize import MergeLinesBySize
from .prepareMiniMap import PrepareMiniMap
from .rapidsAndWaterfallRotation import RapidsAndWaterfallRotation
from .removeDuplicatePoints import RemoveDuplicatePoints
from .removeHoles import RemoveHoles
from .removePoints import RemovePoints
from .removercamadavazia import RemoveEmptyLayers
from .rotation import Rotation
from .snapBetweenLines import SnapBetweenLines
from .snapLineInAnchor import SnapLineInAnchor
from .snapLinesInFrame import SnapLinesInFrame
from .snapPointsInLines import SnapPointsInLines
from .snapPointsInLinesIntersection import SnapPointsInLinesIntersection
from .snapPolygons import SnapPolygons
from .snapPolygonsInFrame import SnapPolygonsInFrame
from .streamCountourConsistency import StreamCountourConsistency
from .streamOrder import StreamOrder
from .streamPolygonCountourConsistency import StreamPolygonCountourConsistency
from .verifyAngles import VerifyAngles
from .verifyHydro import VerifyHydrography
from .verifyLayersConnection import VerifyLayersConnection
from .verifyStreamGeometry import VerifyStreamGeometry
from .verifyTransports import VerifyTransports
from .verifyValleyBottom import VerifyValleyBottom
from .quadtreeDivision import QuadtreeDivision
from .quadtreeDivisionVec import QuadtreeDivisionVec
#from .checkNeighboringGeometries import CheckNeighboringGeometries
# from .verifyCountourStacking import VerifyCountourStacking
# from .uuidCheckerAlg import UuidCheckerAlg
# from .spellCheckerAlg import SpellCheckerAlg
# from .verifyZAngles import VerifyZAngles
# from .loadShapefilesAlg import LoadShapefilesAlg
# from .identifySmallHoles import identifySmallHoles
# from .identifyCountourStreamIntersection import \
#     IdentifyCountourStreamIntersection
from .insertMASACODE import InsertMASACODE


class Provider(QgsProcessingProvider):

    def __init__(self):
        super(Provider, self).__init__()

    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(AtribuirSRC())
        self.addAlgorithm(RemoveEmptyLayers())
        self.addAlgorithm(StreamOrder())
        self.addAlgorithm(StreamCountourConsistency())
        self.addAlgorithm(VerifyValleyBottom())
        self.addAlgorithm(IdentifyInvalidGeometry())
        self.addAlgorithm(IdentifyMultipleParts())
        self.addAlgorithm(VerifyLayersConnection())
        # self.addAlgorithm(identifySmallHoles()) # DSGTools
        self.addAlgorithm(IdentifySmallFeatures())
        self.addAlgorithm(IdentifySmallLines())
        self.addAlgorithm(IdentifyUndershootLines())
        self.addAlgorithm(IdentifyDiscontinuitiesInLines())
        self.addAlgorithm(RemoveHoles())
        self.addAlgorithm(AttributeValleyBottom())
        # self.addAlgorithm(LoadShapefilesAlg()) # DSGTools
        # self.addAlgorithm(SpellCheckerAlg()) # DSGTools
        # self.addAlgorithm(UuidCheckerAlg()) # DSGTools
        self.addAlgorithm(SnapLinesInFrame())
        self.addAlgorithm(ClipLayerInFrame())
        self.addAlgorithm(VerifyAngles())
        self.addAlgorithm(IdentifySplittedLines())
        self.addAlgorithm(IdentifySameAttributesInNeighbouringPolygons())
        self.addAlgorithm(SnapBetweenLines())
        self.addAlgorithm(FixMissingVertexOnIntersection())
        self.addAlgorithm(IdentifyOverlaps())
        # self.addAlgorithm(VerifyZAngles()) # DSGTools
        self.addAlgorithm(SnapPolygons())
        self.addAlgorithm(RemovePoints())
        self.addAlgorithm(IdentifySmallNeighbouringSameAttributesPolygons())
        self.addAlgorithm(SnapPolygonsInFrame())
        self.addAlgorithm(Line2Multiline())
        self.addAlgorithm(VerifyHydrography())
        self.addAlgorithm(Rotation())
        # self.addAlgorithm(VerifyCountourStacking()) # DSGTools
        self.addAlgorithm(DamWidth())
        self.addAlgorithm(StreamPolygonCountourConsistency())
        self.addAlgorithm(SnapPointsInLines())
        self.addAlgorithm(SnapPointsInLinesIntersection())
        self.addAlgorithm(SnapLineInAnchor())
        self.addAlgorithm(RemoveDuplicatePoints())
        self.addAlgorithm(BridgeAndManholeWidth())
        self.addAlgorithm(BridgeAndManholeRotation())
        self.addAlgorithm(RapidsAndWaterfallRotation())
        self.addAlgorithm(VerifyTransports())
        self.addAlgorithm(GeneralizeBuildings())
        self.addAlgorithm(DefineEditTextField())
        self.addAlgorithm(PrepareMiniMap())
        # self.addAlgorithm(IdentifyCountourStreamIntersection()) # DSGTools
        self.addAlgorithm(IdentifyCloseFeatures())
        self.addAlgorithm(MergeLinesBySize())
        self.addAlgorithm(CreateLandCover())
        self.addAlgorithm(VerifyStreamGeometry())
        self.addAlgorithm(QuadtreeDivision())
        self.addAlgorithm(QuadtreeDivisionVec())
        self.addAlgorithm(InsertMASACODE())
        for model in self.modelsAlg():
            self.addAlgorithm(model)

    def modelsAlg(self):
        models = []
        pathFolder = join(dirname(__file__), "Models")
        pathfileList = [join(pathFolder, f) for f in listdir(pathFolder) if isfile(join(pathFolder, f))]
        for pathfile in pathfileList:
            model = self.loadModel(self.getXmlData(pathfile))
            models.append(model)
        return models

    def loadModel(self, xmlData):
        doc = QDomDocument()
        doc.setContent(xmlData)
        model = QgsProcessingModelAlgorithm('modelo', "Missoes", 'missoes')
        model.loadVariant(QgsXmlUtils.readVariant( doc.firstChildElement() ))
        model.setGroup('Missoes')
        return model
    
    def getXmlData(self, pathfile):
        tree = ET.parse(pathfile)
        root = tree.getroot()
        elem = tree.findall('Option')
        for elem1 in elem:
            if elem1.attrib["name"] == "model_group":
                elem1.attrib["value"] = "missoes"
        with open(pathfile, 'w') as f:
            tree.write(pathfile)
        with open(pathfile, 'r') as f:
            return f.read()

    def load(self):
        ProcessingConfig.settingIcons[self.name()] = self.icon()
        ProcessingConfig.addSetting(
            Setting(
                self.name(),
                'ACTIVATE_FerramentasExperimentais',
                'Activate',
                True
            )
        )
        ProcessingConfig.addSetting(Setting(
            ProcessingConfig.tr('General'),
            ProcessingConfig.RESULTS_GROUP_NAME,
            ProcessingConfig.tr("Results group name"),
            "results",
            valuetype=Setting.STRING,
            placeholder=ProcessingConfig.tr("Leave blank to avoid loading results in a predetermined group")
        ))
        ProcessingConfig.readSettings()
        self.refreshAlgorithms()
        return True

    def id(self, *args, **kwargs):
        return 'FerramentasExperimentaisProvider'

    def name(self, *args, **kwargs):
        return self.tr('Ferramentas Experimentais')

    def icon(self):
        return QIcon(
            os.path.join(
                os.path.abspath(os.path.join(
                    os.path.dirname(__file__)
                )),
                '..',
                'icons',
                'lab.png'
            )
        )
