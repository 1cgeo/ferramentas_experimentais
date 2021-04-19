from os import listdir, fdopen, remove
from tempfile import mkstemp
from shutil import move, copymode
import tempfile
import shutil
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
from .identifyEmptyGeometry import IdentifyEmptyGeometry
from .identifyMultipleParts import IdentifyMultipleParts
from .verifyLayersConnection import VerifyLayersConnection

class Provider(QgsProcessingProvider):

    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(AtribuirSRC())
        self.addAlgorithm(ExportarParaShapefile())
        self.addAlgorithm(RemoveEmptyLayers())
        self.addAlgorithm(StreamOrder())
        self.addAlgorithm(StreamCountourConsistency())
        self.addAlgorithm(VerifyValleyBottom())
        self.addAlgorithm(IdentifyEmptyGeometry())
        self.addAlgorithm(IdentifyMultipleParts())
        #self.addAlgorithm(VerifyLayersConnection())
        for model in self.modelsAlg():
            self.addAlgorithm(model)

    def modelsAlg(self):
        models = []
        mainFolder = dirname(__file__)
        pathFolder = join(mainFolder, "Models")
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
        ProcessingConfig.settingIcons["Ferramentas Experimentais"] = self.icon()
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
        return QIcon(':/plugins/Ferramentas_Experimentais/icons/lab.png')
