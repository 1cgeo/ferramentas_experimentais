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
import os
from .verifyAngles import VerifyAngles
from .identifySameAttributesInNeighbouringPolygons import IdentifySameAttributesInNeighbouringPolygons
from .identifySplittedLines import IdentifySplittedLines 
from .snapBetweenLines import SnapBetweenLines

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
