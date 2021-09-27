from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterNumber,
                       QgsFeature,
                       QgsGeometry,
                       QgsProcessingUtils)
from qgis import processing


class MergeLinesBySize(QgsProcessingAlgorithm):
 
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    ITERATION = 'ITERATION'
    TOLERANCE = 'TOLERANCE'

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input layer'),
                [QgsProcessing.TypeVectorLine]
            )
        )
      
        self.addParameter(
            QgsProcessingParameterNumber(
                self.TOLERANCE,
                self.tr('Minimum segment Length (meters)'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=300,
                minValue=0,
            )
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.ITERATION,
                self.tr('Iteration Number'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=20,
                minValue=1,
            )
        )


        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Merged Lines')
            )
        )
        
        self.g = dict()
        self.g_dir = dict()
        self.points = list()

    def processAlgorithm(self, parameters, context, feedback):


        source = self.parameterAsVectorLayer(
            parameters,
            self.INPUT,
            context
        )

        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        
        tolerance = self.parameterAsInt(
            parameters,
            self.TOLERANCE,
            context
        )
        
        iteration = self.parameterAsInt(
            parameters,
            self.ITERATION,
            context
        )

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            source.fields(),
            source.wkbType(),
            source.sourceCrs()
        )
        

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        # Compute the number of steps to display within the progress bar and
        # get features from source
        bar = 100.0 / iteration
        
        
        parametros_proj_1 = {'INPUT':source,
                            'INTERSECT': source,
                            'OUTPUT':'memory:point.shp'}
        all_point = processing.run('native:lineintersections', parametros_proj_1,
                                        context=context, feedback=feedback,
                                        is_child_algorithm=True)['OUTPUT']
        
        parametros_proj_2 = {'INPUT':all_point,
                            'OUTPUT':'memory:'}
        path_point = processing.run('native:deleteduplicategeometries', parametros_proj_2,
                                        context=context, feedback=feedback,
                                        is_child_algorithm=True)['OUTPUT']
        
        point =QgsProcessingUtils.mapLayerFromString(path_point, context)
        feedback.setProgress(int(2))
        
        merged = []
        lista_pontos = [ p.geometry().asPoint() for p in point.getFeatures()]
        lista_feat = [l for l in source.getFeatures() if l.id() not in merged]
        
        for l in lista_feat:
            if l.geometry().isMultipart():
                if l.geometry().asMultiPolyline()[0][0] not in lista_pontos and l.geometry().length()>tolerance:
                    feat = QgsFeature(point.fields())
                    feat.setGeometry(QgsGeometry.fromPointXY(l.geometry().asMultiPolyline()[0][0]))
                    point.dataProvider().addFeatures([feat])
            else:
                if l.geometry().asPolyline()[0] not in lista_pontos and l.geometry().length()>tolerance:
                	feat = QgsFeature(point.fields())
                	feat.setGeometry(QgsGeometry.fromPointXY(l.geometry().asPolyline()[0]))
                	point.dataProvider().addFeatures([feat])
        
        a=0
        while a<iteration:
            lista_feat = [l for l in source.getFeatures() if l.id() not in merged]
            self.buildGrafos(point,lista_feat)
            lista_pontos = [ p for p in point.getFeatures() if p.id not in self.points]
            
            maior_caminho =[]
            total = 0
            for p in lista_pontos:
                for q in lista_pontos:
                    if p.id()==q.id():
                        continue
                    try:
                        for caminho in self.buildPath([p.id()], q.id()):
                            legth_path = 0
                            for i in caminho:
                                legth_path+=self.g[i].geometry().length()
                            if total < legth_path:
                                total = legth_path
                                maior_caminho = caminho
                    except:
                        pass
                        
            if len(maior_caminho)==0:
                feedback.setProgress(int('100'))
                break
                
            resultado = [self.g[i].id() for i in maior_caminho]
            
            source.selectByIds(resultado)
            selection = source.selectedFeatures()
            new_geom = selection[0].geometry()
            for seg in selection[1:]:
                new_geom = new_geom.combine(seg.geometry())
            new_feat = QgsFeature(source.fields())
            new_feat.setAttributes(selection[0].attributes())
            new_feat.setGeometry(new_geom)
            sink.addFeature(new_feat, QgsFeatureSink.FastInsert)
            
            merged +=resultado
            feedback.pushInfo('Iteration {}: '.format(str(a+1))+'{} features merged'.format(str(len(selection))))
                
            a+=1
            feedback.setProgress(int(a * bar))
            
            if feedback.isCanceled():
                break
        
        for feature in source.getFeatures():
            if feature.id() not in merged:
                sink.addFeature(feature, QgsFeatureSink.FastInsert)
            else:
                pass
        
        feedback.setProgress(int(100))
        return {self.OUTPUT: dest_id}
    
    def buildPath(self,caminho, final):
        if caminho[-1] == final:
            yield caminho
            return

        for vizinho in self.g_dir[caminho[-1]]:

            if vizinho in caminho:
                continue
            
            for caminho_maior in self.buildPath(caminho + [vizinho], final):
                yield caminho_maior
    
    def buildGrafos(self,point,lista_feat):
        self.g ={}
        self.g_dir = {}
        self.points=[]
        for p in point.getFeatures():
            add = True
            for l in lista_feat:
                if l.geometry().touches(p.geometry()):
                    add = False
                    if l.geometry().isMultipart():
                        if l.geometry().asMultiPolyline()[0][0] ==p.geometry().asPoint():
                        	self.g[p.id()] = l
                        	self.g_dir[p.id()] = [q.id() for q in point.getFeatures() if l.geometry().asMultiPolyline()[-1][-1] ==q.geometry().asPoint()]
                    else:
                        if l.geometry().asPolyline()[0] ==p.geometry().asPoint():
                        	self.g[p.id()] = l
                        	self.g_dir[p.id()] = [q.id() for q in point.getFeatures() if l.geometry().asPolyline()[-1] ==q.geometry().asPoint()]
            if add:
                self.points.append(p.id)
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return MergeLinesBySize()

    def name(self):
        return 'mergelinesbysize'

    def displayName(self):
        return self.tr('Mescla Linhas Pelo Tamanho')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
    
        return 'missoes'

    def shortHelpString(self):
    
        return self.tr("Esse algoritmo mescla linhas conectadas. Em caso de bifurcação, percorre-se o caminho de maior tamanho para mesclar. Considera-se o sentido das linhas para conectar.")
    
