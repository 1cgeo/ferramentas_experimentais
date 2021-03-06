from os import listdir
import xml.etree.ElementTree as ET 
from os.path import isfile, join, dirname
from qgis.core import QgsProcessingProvider, QgsProcessingModelAlgorithm, QgsXmlUtils
from processing.core.ProcessingConfig import ProcessingConfig, Setting
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtXml import QDomDocument
from .atribuirsrc import AtribuirSRC
from .exportarparashapefile import ExportarParaShapefile
from .removercamadavazia import RemoveEmptyLayers
from .streamOrder import StreamOrder
from .streamCountourConsistency import StreamCountourConsistency
from .verifyValleyBottom import VerifyValleyBottom
from .identifyInvalidGeometry import IdentifyInvalidGeometry
from .identifyMultipleParts import IdentifyMultipleParts
from .verifyLayersConnection import VerifyLayersConnection
from .identifySmallHoles import identifySmallHoles
from .identifySmallFeatures import IdentifySmallFeatures
from .identifySmallLines import IdentifySmallLines
from .identifyUndershootLines import IdentifyUndershootLines
from .identifyDiscontinuitiesInLines import IdentifyDiscontinuitiesInLines
from .removeHoles import RemoveHoles
from .attributeValleyBottom import AttributeValleyBottom
from .loadShapefilesAlg import LoadShapefilesAlg
from .spellCheckerAlg import SpellCheckerAlg
from .uuidCheckerAlg import UuidCheckerAlg
from .snapLinesInFrame import SnapLinesInFrame
from .clipLayerInFrame import ClipLayerInFrame
from .fixMissingVertexOnIntersection import FixMissingVertexOnIntersection
from .identifyOverlaps import IdentifyOverlaps
import os
from .verifyAngles import VerifyAngles
from .identifySameAttributesInNeighbouringPolygons import IdentifySameAttributesInNeighbouringPolygons
from .identifySplittedLines import IdentifySplittedLines 
from .snapBetweenLines import SnapBetweenLines
from .verifyZAngles import VerifyZAngles
from .snapPolygons import SnapPolygons
from .removePoints import RemovePoints
from .identifySmallNeighbouringSameAttributesPolygons import IdentifySmallNeighbouringSameAttributesPolygons
from .snapPolygonsInFrame import SnapPolygonsInFrame
#from .checkNeighboringGeometries import CheckNeighboringGeometries
from .line2Multiline import Line2Multiline
from .saveLayerStylesToFile import SaveLayerStylesToFile
from .verifyHydro import VerifyHydrography
from .rotation import Rotation
from .verifyCountourStacking import VerifyCountourStacking
from .damWidth import DamWidth
from .orderEditLayers import OrderEditLayers
from .streamPolygonCountourConsistency import StreamPolygonCountourConsistency
from .snapPointsInLines import SnapPointsInLines
from .snapPointsInLinesIntersection import SnapPointsInLinesIntersection
from .loadMasks import LoadMasks
from .saveMasks import SaveMasks
from .snapLineInAnchor import SnapLineInAnchor
from .removeDuplicatePoints import RemoveDuplicatePoints
from .bridgeAndManholeWidth import BridgeAndManholeWidth
from .bridgeAndManholeRotation import BridgeAndManholeRotation
from .verifyTransports import VerifyTransports
from .rapidsAndWaterfallRotation import RapidsAndWaterfallRotation
from .mergeRivers import MergeRivers
from .highestSpotOnTheFrame import HighestSpotOnTheFrame
from .generalizeBuildings import GeneralizeBuildings
from .defineEditTextField import DefineEditTextField
from .prepareMiniMap import PrepareMiniMap
from .identifyCountourStreamIntersection import IdentifyCountourStreamIntersection
from .mergeHighway import MergeHighway

class Provider(QgsProcessingProvider):

    def __init__(self):
        super(Provider, self).__init__()

    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(AtribuirSRC())
        self.addAlgorithm(ExportarParaShapefile())
        self.addAlgorithm(RemoveEmptyLayers())
        self.addAlgorithm(StreamOrder())
        self.addAlgorithm(StreamCountourConsistency())
        self.addAlgorithm(VerifyValleyBottom())
        self.addAlgorithm(IdentifyInvalidGeometry())
        self.addAlgorithm(IdentifyMultipleParts())
        self.addAlgorithm(VerifyLayersConnection())
        self.addAlgorithm(identifySmallHoles())
        self.addAlgorithm(IdentifySmallFeatures())
        self.addAlgorithm(IdentifySmallLines())
        self.addAlgorithm(IdentifyUndershootLines())
        self.addAlgorithm(IdentifyDiscontinuitiesInLines())
        self.addAlgorithm(RemoveHoles())
        self.addAlgorithm(AttributeValleyBottom())
        self.addAlgorithm(LoadShapefilesAlg())
        self.addAlgorithm(SpellCheckerAlg())
        self.addAlgorithm(UuidCheckerAlg())
        self.addAlgorithm(SnapLinesInFrame())
        self.addAlgorithm(ClipLayerInFrame())
        self.addAlgorithm(VerifyAngles())
        self.addAlgorithm(IdentifySplittedLines())
        self.addAlgorithm(IdentifySameAttributesInNeighbouringPolygons())
        self.addAlgorithm(SnapBetweenLines())
        self.addAlgorithm(FixMissingVertexOnIntersection())
        self.addAlgorithm(IdentifyOverlaps())
        self.addAlgorithm(VerifyZAngles())
        self.addAlgorithm(SnapPolygons())
        self.addAlgorithm(RemovePoints())
        self.addAlgorithm(IdentifySmallNeighbouringSameAttributesPolygons())
        self.addAlgorithm(SnapPolygonsInFrame())
        #self.addAlgorithm(CheckRelationships())
        self.addAlgorithm(Line2Multiline())
        self.addAlgorithm(SaveLayerStylesToFile())
        self.addAlgorithm(VerifyHydrography())
        self.addAlgorithm(Rotation())
        self.addAlgorithm(VerifyCountourStacking())
        self.addAlgorithm(DamWidth())
        self.addAlgorithm(OrderEditLayers())
        self.addAlgorithm(StreamPolygonCountourConsistency())
        self.addAlgorithm(SnapPointsInLines())
        self.addAlgorithm(SnapPointsInLinesIntersection())
        self.addAlgorithm(LoadMasks())
        self.addAlgorithm(SaveMasks())
        self.addAlgorithm(SnapLineInAnchor())
        self.addAlgorithm(RemoveDuplicatePoints())
        self.addAlgorithm(BridgeAndManholeWidth())
        self.addAlgorithm(BridgeAndManholeRotation())
        self.addAlgorithm(RapidsAndWaterfallRotation())
        self.addAlgorithm(VerifyTransports())
        self.addAlgorithm(MergeRivers())
        self.addAlgorithm(HighestSpotOnTheFrame())
        self.addAlgorithm(GeneralizeBuildings())
        self.addAlgorithm(DefineEditTextField())
        self.addAlgorithm(PrepareMiniMap())
        self.addAlgorithm(IdentifyCountourStreamIntersection())
        self.addAlgorithm(MergeHighway())
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
