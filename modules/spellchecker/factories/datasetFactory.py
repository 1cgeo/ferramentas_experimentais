from ferramentas_experimentais.modules.spellchecker.datasets.ptBR import PtBR 
from ferramentas_experimentais.modules.spellchecker.structures.ternarySearchTree import Trie

class DatasetFactory:

    def getDataset(self, dataset):
        methods = {
            'pt-BR': PtBR
        }
        return methods[dataset]()