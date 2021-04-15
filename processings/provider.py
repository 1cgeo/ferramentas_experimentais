from qgis.core import QgsProcessingProvider
from processing.core.ProcessingConfig import ProcessingConfig, Setting
from qgis.PyQt.QtGui import QIcon
from .atribuirsrc import AtribuirSRC
from .exportarparashapefile import ExportarParaShapefile
from .removercamadavazia import RemoveEmptyLayers
from .streamOrder import StreamOrder
from .streamCountourConsistency import StreamCountourConsistency
from .verifyValleyBottom import VerifyValleyBottom
from .identifyEmptyGeometry import IdentifyEmptyGeometry
from .identifyMultipleParts import IdentifyMultipleParts

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
