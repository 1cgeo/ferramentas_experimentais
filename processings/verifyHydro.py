# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsPointXY,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterVectorLayer,
                       QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsGeometry,
                       QgsProcessingFeatureSourceDefinition,
                       QgsFeatureRequest
                       )
from qgis import processing

class VerifyHydrography(QgsProcessingAlgorithm):

    INPUT_STREAM = 'INPUT_STREAM'
    INPUT_WATER_BODY = 'INPUT_WATER_BODY'
    INPUT_SPILLWAY = 'INPUT_SPILLWAY'
    INPUT_FRAME = 'INPUT_FRAME'
    INPUT_DAM_LINE = 'INPUT_DAM_LINE'
    INPUT_DAM_POLYGON = 'INPUT_DAM_POLYGON'
    INPUT_HYDRO_ELEM_POINT = 'INPUT_HYDRO_ELEM_POINT'
    INPUT_HYDRO_ELEM_LINE = 'INPUT_HYDRO_ELEM_LINE'
    INPUT_HYDRO_ELEM_POLYGON = 'INPUT_HYDRO_ELEM_POLYGON'
    OUTPUT = 'OUTPUT'
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_STREAM',
                self.tr('Selecione a camada contendo os trechos de drenagem'),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_DAM_LINE',
                self.tr('Selecione a camada contendo as barragens (linha)'), 
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_DAM_POLYGON',
                self.tr('Selecione a camada contendo as barragens (poligono)'), 
                [2]
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_WATER_BODY',
                self.tr('Selecione a camada contendo as massas d\'agua'), 
                [2]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_SPILLWAY',
                self.tr('Selecione a camada contendo os vertedouros/sumidouros'),
                types=[QgsProcessing.TypeVectorPoint]
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_HYDRO_ELEM_POINT',
                self.tr('Selecione a camada contendo os elementos hidrográficos (ponto)'),
                types=[QgsProcessing.TypeVectorPoint]
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_HYDRO_ELEM_LINE',
                self.tr('Selecione a camada contendo os elementos hidrográficos (linha)'),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_HYDRO_ELEM_POLYGON',
                self.tr('Selecione a camada contendo os elementos hidrográficos (poligono)'),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_FRAME',
                self.tr('Selecionar camada correspondente à moldura'),
                [2]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Flag Verificar Hidrografia')
            )
        ) 

    def processAlgorithm(self, parameters, context, feedback):

        streamLayerInput = self.parameterAsVectorLayer( parameters,'INPUT_STREAM', context )
        outputPoints = []
        outputLines = []
        outputPolygons = []
        frameLayer = self.parameterAsVectorLayer(parameters,'INPUT_FRAME', context)
        waterBodylayer = self.parameterAsVectorLayer( parameters,'INPUT_WATER_BODY', context )
        spillwayLayer = self.parameterAsVectorLayer( parameters,'INPUT_SPILLWAY', context )
        damPolyLayer = self.parameterAsVectorLayer( parameters,'INPUT_DAM_POLYGON', context )
        damLineLayer = self.parameterAsVectorLayer( parameters,'INPUT_DAM_LINE', context )
        hydroElemPointLayer = self.parameterAsVectorLayer( parameters,'INPUT_HYDRO_ELEM_POINT', context )
        hydroElemLineLayer = self.parameterAsVectorLayer( parameters,'INPUT_HYDRO_ELEM_LINE', context )
        hydroElemPolygonLayer = self.parameterAsVectorLayer( parameters,'INPUT_HYDRO_ELEM_POLYGON', context )
        step =1
        progressStep = 100/5
        streamLayerFeatures = self.createFeaturesArray(streamLayerInput)
        waterBodyFeatures = self.createFeaturesArray(waterBodylayer)
        spillwayFeatures = self.createFeaturesArray(spillwayLayer)
        damLineFeatures = self.createFeaturesArray(damLineLayer)
        damPolyFeatures = self.createFeaturesArray(damPolyLayer)
        hydroElemPointFeatures = self.createFeaturesArray(hydroElemPointLayer)
        hydroElemLineFeatures = self.createFeaturesArray(hydroElemLineLayer)
        hydroElemPolygonFeatures = self.createFeaturesArray(hydroElemPolygonLayer)
        feedback.setProgressText('Verificando inconsistencias ')
        feedback.setProgress( step * progressStep )
        if feedback.isCanceled():
            return {self.OUTPUT: 'execução cancelada pelo usuário'}
        returnNow = self.verifyRiverAndWaterBodyGeometry(streamLayerFeatures, waterBodyFeatures, outputLines)
        if returnNow:
            newLayer = self.outLayer(parameters, context, outputLines, streamLayerInput, 2)
            return {self.OUTPUT: newLayer}
        step+=1
        feedback.setProgress( step * progressStep )
        if feedback.isCanceled():
            return {self.OUTPUT: 'execução cancelada pelo usuário'}
        
        self.verifyTypeRiver(streamLayerInput, streamLayerFeatures, waterBodyFeatures, spillwayFeatures, damLineFeatures, damPolyFeatures, outputPoints, outputLines, outputPolygons, feedback, step, progressStep)
        step +=1
        feedback.setProgress( step * progressStep )
        if feedback.isCanceled():
            return {self.OUTPUT: 'execução cancelada pelo usuário'}
        self.verifyWaterBodyVsRiverAndDam(streamLayerFeatures, waterBodyFeatures,damLineFeatures,  damPolyFeatures, outputLines, outputPolygons, feedback, step, progressStep)
        step+=1
        feedback.setProgress( step * progressStep )

        if feedback.isCanceled():
            return {self.OUTPUT: 'execução cancelada pelo usuário'}
        self.verifySpillway(streamLayerFeatures, spillwayFeatures, outputPoints)
        
        if feedback.isCanceled():
            return {self.OUTPUT: 'execução cancelada pelo usuário'}
        self.verifyRegimeRivers(streamLayerInput, streamLayerFeatures, outputPoints)
        
        if feedback.isCanceled():
            return {self.OUTPUT: 'execução cancelada pelo usuário'}
        
        self.verifyHydroElements(hydroElemPointFeatures, hydroElemLineFeatures, hydroElemPolygonFeatures, streamLayerFeatures, waterBodyFeatures, outputPoints, outputLines, outputPolygons)
        
        if feedback.isCanceled():
            return {self.OUTPUT: 'execução cancelada pelo usuário'}
        self.deleteEqualPoints(outputPoints)
        
        if feedback.isCanceled():
            return {self.OUTPUT: 'execução cancelada pelo usuário'}
        self.verifyFrameFlags(outputPoints, outputLines, frameLayer)
        self.shouldBeIgnored(outputLines, outputPolygons, frameLayer)
        step +=1
        feedback.setProgress( step * progressStep )
        if feedback.isCanceled():
            return {self.OUTPUT: 'execução cancelada pelo usuário'}
        
        allOK = True
        if not len(outputPoints)==0 :
            newLayer = self.outLayer(parameters, context, outputPoints, streamLayerInput, 1)
            allOK = False
        
        if not len(outputLines)==0 :
            newLayer = self.outLayer(parameters, context, outputLines, streamLayerInput, 2)
            allOK = False
        
        if not len(outputPolygons)==0 :
            newLayer = self.outLayer(parameters, context, outputPolygons, streamLayerInput, 3)
            allOK = False
        
        if allOK:
            newLayer = 'nenhuma inconsistência verificada'
        
        return {self.OUTPUT: newLayer}

    def createFeaturesArray(self, originalLayer):
        arrayFeatures = []
        features = originalLayer.getFeatures()

        for feature in features:
            arrayFeatures.append(feature)
            
        return arrayFeatures

    def verifyRiverAndWaterBodyGeometry(self, streamLayerFeatures, waterBodyFeatures, outputLines):
        returnNow = False
        for river in streamLayerFeatures:
            outsideWaterbody = True
            crossedWaterbody = False
            for waterBody in waterBodyFeatures:
                if river.geometry().crosses(waterBody.geometry()):
                    outputLines.append([river.geometry(), 4])
                    returnNow = True
                    crossedWaterbody = True
                    break
                if river.geometry().within(waterBody.geometry()):
                    outsideWaterbody = False

            if outsideWaterbody and not crossedWaterbody:
                if not river['situacao_em_poligono']==1:
                    outputLines.append([river.geometry(), 5])
                    returnNow = True
        return returnNow
    def verifyTypeRiver(self, streamLayerInput, streamLayerFeatures, waterBodyFeatures, spillwayFeatures, damLineFeatures, damPolyFeatures, points, outputLines, outputPolygons, feedback, step, progressStep):
        waterBodyRiverTypes = [1,2,4]
        spillwayRiverTypes = [1]
        auxProgress = 1/len(streamLayerFeatures)
        for index, river in enumerate(streamLayerFeatures):
            auxStep = index+1
            for geometry in river.geometry().constGet():
                ptIni = QgsGeometry.fromPointXY(QgsPointXY(geometry[0]))
                ptFin = QgsGeometry.fromPointXY(QgsPointXY(geometry[-1]))
                lineTouched = self.linesTouched(streamLayerInput, river, ptIni)
            for waterBody in waterBodyFeatures:
                if waterBody.geometry().intersects(ptIni) and (river['tipo'] not in waterBodyRiverTypes):
                    points.append([ptIni, 35])
            for spillway in spillwayFeatures:
                if not spillway['tipo'] == 5:
                    continue
                if spillway.geometry().intersects(ptIni) and (river['tipo'] not in spillwayRiverTypes):
                    points.append([ptIni, 36])
            self.verifyRiverVsWaterBody(river, waterBodyFeatures, outputLines, outputPolygons)
            for damLine in damLineFeatures:
                if river.geometry().intersects(damLine.geometry()) and not (river.geometry().intersection(damLine.geometry()).equals(ptIni) or river.geometry().intersection(damLine.geometry()).equals(ptFin)):
                    outputLines.append([river.geometry(), 11])
            for damPoly in damPolyFeatures:
                if river.geometry().intersects(damPoly.geometry()) and not (river.geometry().intersection(damPoly.geometry()).equals(ptIni) or river.geometry().intersection(damPoly.geometry()).equals(ptFin)):
                    outputLines.append([river.geometry(), 11])
            if river['situacao_em_poligono'] in [1,2,4]:
                self.verifyStretchs(river, streamLayerFeatures, waterBodyFeatures,ptIni, ptFin, points, outputLines, index)
            initRiverOptions = waterBodyFeatures + spillwayFeatures
            if len(lineTouched) == 0:
                intersectedWaterbodyOrSpillway = False
                for feature in initRiverOptions:
                    if feature.geometry().intersects(ptIni):
                        intersectedWaterbodyOrSpillway = True
                        break
                if (not river['tipo']==3) and not intersectedWaterbodyOrSpillway:
                    points.append([ptIni, 37])
                        
            else: 
                if river['tipo']==3:
                    for line in lineTouched:
                        if not line['tipo'] ==3:
                            points.append([ptIni, 38])
            feedback.setProgress( (step +(auxStep*auxProgress)) * progressStep )
            if feedback.isCanceled():
                return {self.OUTPUT: 'execução cancelada pelo usuário'}
            
        return False

    def verifyStretchs(self, river, streamLayerFeatures, waterBodyFeatures, ptIni, ptFin, points, outputLines, i):
        NoFlow = [3, 4, 5, 6, 7, 11]
        Flow = [1,2,9,10]
        finIntersectedSecondaryRiver = 0
        finIntersectedPrimaryRiver = 0
        finIntersectedOutsideRiver = False
        iniIntersectedOutsideRiver = False
        iniIntersectedPrimaryRiver = False
        finIntersectedSharedRiver = False
        finTouchedFlow = 0
        finTouchedNoFlow = False
        finIntersectedAnyRiver = False
        iniTouchedFlow = 0
        iniIntersectedFlow = False
        finIntersectedFlow = False
        iniIntersectedSecondaryRiver = False
        for anotherRiver in streamLayerFeatures:
            if river == anotherRiver:
                continue
            if ptIni.intersects(anotherRiver.geometry()):
                if anotherRiver['situacao_em_poligono' ] ==1:
                    iniIntersectedOutsideRiver = True
                if anotherRiver['situacao_em_poligono' ] ==2:
                    iniIntersectedPrimaryRiver = True
                if anotherRiver['situacao_em_poligono' ] ==3:
                    iniIntersectedSecondaryRiver = True
            if ptFin.intersects(anotherRiver.geometry()):
                finIntersectedAnyRiver = True
                if anotherRiver['situacao_em_poligono' ] ==1:
                    finIntersectedOutsideRiver = True
                if anotherRiver['situacao_em_poligono' ] ==2:
                    finIntersectedPrimaryRiver += 1
                if anotherRiver['situacao_em_poligono' ] ==3:
                    finIntersectedSecondaryRiver += 1
                if anotherRiver['situacao_em_poligono' ] ==4:
                    finIntersectedSharedRiver = True
        if river['situacao_em_poligono'] == 2 or river['situacao_em_poligono'] == 1 or river['situacao_em_poligono'] == 4:
            for waterBody in waterBodyFeatures:
                if ptIni.intersects(waterBody.geometry()):
                    if waterBody['tipo'] in Flow:
                        iniIntersectedFlow = True
                if ptFin.intersects(waterBody.geometry()):
                    if waterBody['tipo'] in Flow:
                        finIntersectedFlow = True
                if ptFin.touches(waterBody.geometry()):
                    if waterBody['tipo'] in Flow:
                        finTouchedFlow += 1
                    if waterBody['tipo'] in NoFlow:
                        finTouchedNoFlow = True
                if ptIni.touches(waterBody.geometry()):
                    if waterBody['tipo'] in Flow:
                        iniTouchedFlow +=1
                if river['situacao_em_poligono'] == 4:
                    continue
                if river.geometry().within(waterBody.geometry()):
                    if not river['nome']==waterBody['nome']:
                        outputLines.append([river.geometry(), 19])
        if river['situacao_em_poligono'] == 4:
            if (not iniIntersectedFlow) or (not finIntersectedFlow):
                outputLines.append([river.geometry(), 33])
            if (not iniIntersectedOutsideRiver) and iniTouchedFlow==1:
                points.append([ptIni, 12])
            if iniTouchedFlow==2 and not (iniIntersectedPrimaryRiver or iniIntersectedSecondaryRiver):
                points.append([ptIni, 34])
            if (not finIntersectedPrimaryRiver>1) and (not finIntersectedSecondaryRiver>1) and finTouchedFlow<1:
                points.append([ptFin, 13])
            if (iniTouchedFlow<1 and not (iniIntersectedPrimaryRiver or iniIntersectedSecondaryRiver)):
                points.append([ptIni, 31])
            if finTouchedFlow>0 and not(finIntersectedPrimaryRiver>1 or finIntersectedSecondaryRiver>1 or finIntersectedOutsideRiver):
                points.append([ptFin, 31])
        if river['situacao_em_poligono'] == 2:
            if finTouchedNoFlow:
                if finIntersectedAnyRiver:
                    points.append([ptFin, 16])
            elif finTouchedFlow>1:
                if (not finIntersectedSharedRiver) and (finIntersectedPrimaryRiver<1):
                    points.append([ptFin, 15])
            elif (not finIntersectedOutsideRiver) and finIntersectedPrimaryRiver<1:
                points.append([ptFin, 14])
            if (not iniIntersectedOutsideRiver) and (not iniIntersectedPrimaryRiver):
                points.append([ptIni, 17])
        if river['situacao_em_poligono'] == 1:
            if finTouchedFlow>0:
                if (finIntersectedPrimaryRiver<1) and (not finIntersectedSharedRiver):
                    points.append([ptFin, 18])

        
        return False



    def verifyRiverVsWaterBody(self, river, waterBodyFeatures, outputLines,outputPolygons):
        NoFlow = [3, 4, 5, 6, 7, 11]
        Flow = [1,2,9,10]
        for waterBody in waterBodyFeatures:
            if river.geometry().within(waterBody.geometry()):
                if waterBody['regime']==1 and (not river['regime']==1):
                    outputLines.append([river.geometry(), 2])
                if waterBody['tipo'] in NoFlow:
                    outputPolygons.append([waterBody.geometry(), 6])
        return False
    def verifyWaterBodyVsRiverAndDam(self, streamLayerFeatures, waterBodyFeatures, damLineFeatures,  damPolyFeatures, outputLines, outputPolygons, feedback, step, progressStep):
        Flow = [1,2,9,10]
        NoFlow = [3, 4, 5, 6, 7, 11]
        riversInWaterbody = []
        containsRiver = False
        containsPrimaryRiver = False
        auxProgressGeneral = 1/3
        auxStepGeneral = 0
        auxProgressSub = len(waterBodyFeatures)
        auxStepSub = 0
        for waterBody in waterBodyFeatures:
            auxStepSub+=1
            intersectsIni = False
            intersectsFin = False
            for river in streamLayerFeatures:
                for geometry in river.geometry().constGet():
                    ptIni = QgsGeometry.fromPointXY(QgsPointXY(geometry[0]))
                    ptFin = QgsGeometry.fromPointXY(QgsPointXY(geometry[-1]))
                if river.geometry().within(waterBody.geometry()):
                    containsRiver = True
                    if river['situacao_em_poligono']==2:
                        containsPrimaryRiver = True
                if waterBody.geometry().intersects(ptIni):
                    intersectsIni = True
                if waterBody.geometry().intersects(ptFin):
                    intersectsFin = True
            if intersectsIni and intersectsFin:
                if waterBody['tipo'] in NoFlow:
                    outputPolygons.append([waterBody.geometry(), 9])
            else:
                if waterBody['tipo'] in Flow:
                    outputPolygons.append([waterBody.geometry(), 10])
            if not containsRiver:
                if waterBody['tipo'] in Flow:
                    outputPolygons.append([waterBody.geometry(), 7])
            '''
            if containsRiver:
                if not waterBody['tipo'] in Flow:
                    outputPolygons.append([waterBody.geometry(), 6])
                else:
                    if not containsPrimaryRiver:
                        outputPolygons.append([waterBody.geometry(), 8])
            '''
            feedback.setProgress( (step +((auxStepGeneral+(auxStepSub*auxProgressSub))*auxProgressGeneral)) * progressStep )
        auxStepGeneral += 1
        feedback.setProgress( (step +(auxStepGeneral*auxProgressGeneral)) * progressStep )
        if feedback.isCanceled():
            return {self.OUTPUT: 'execução cancelada pelo usuário'}
        for damPoly in damPolyFeatures:
            abstractGeomDam = damPoly.geometry().constGet()
            geomEng = QgsGeometry().createGeometryEngine(abstractGeomDam)
            intersectsCorrectWaterbody = False
            for waterBody in waterBodyFeatures:
                if waterBody['tipo'] ==10 or waterBody['tipo'] ==11 or waterBody['tipo'] ==1:
                    if damPoly.geometry().intersects(waterBody.geometry()):
                        intersectsCorrectWaterbody = True
                        abstractGeomWaterbody = waterBody.geometry().constGet()
                        if not geomEng.relatePattern(abstractGeomWaterbody, 'FF2F11212'):
                            outputPolygons.append([damPoly.geometry(), 29])
            if not intersectsCorrectWaterbody:
                outputPolygons.append([damPoly.geometry(), 28])
        auxStepGeneral += 1
        feedback.setProgress( (step +(auxStepGeneral*auxProgressGeneral)) * progressStep )
        if feedback.isCanceled():
            return {self.OUTPUT: 'execução cancelada pelo usuário'}
        for damLine in damLineFeatures:
            abstractGeomDam = damLine.geometry().constGet()
            geomEng = QgsGeometry().createGeometryEngine(abstractGeomDam)
            intersectsCorrectWaterbody = False
            for waterBody in waterBodyFeatures:
                if waterBody['tipo'] ==10 or waterBody['tipo'] ==11 or waterBody['tipo'] ==1:
                    if damLine.geometry().intersects(waterBody.geometry()):
                        intersectsCorrectWaterbody = True
                        abstractGeomWaterbody = waterBody.geometry().constGet()
                        if not geomEng.relatePattern(abstractGeomWaterbody, 'F1*F**212'):
                            outputLines.append([damLine.geometry(), 30])
            if not intersectsCorrectWaterbody:
                outputLines.append([damLine.geometry(), 28])
        auxStepGeneral += 1
        feedback.setProgress( (step +(auxStepGeneral*auxProgressGeneral)) * progressStep )
        if feedback.isCanceled():
            return {self.OUTPUT: 'execução cancelada pelo usuário'}
        return False
    def verifySpillway(self, streamLayerFeatures, spillwayFeatures, points):
        for spillway in spillwayFeatures:
            spillwayTouches = 0
            for river in streamLayerFeatures:
                for geometry in river.geometry().constGet():
                    ptIni = QgsGeometry.fromPointXY(QgsPointXY(geometry[0]))
                    ptFin = QgsGeometry.fromPointXY(QgsPointXY(geometry[-1]))
                if spillway.geometry().intersects(river.geometry()):
                    spillwayTouches+=1
                    if spillway['tipo']==5:
                        if not spillway.geometry().intersects(ptIni):
                            points.append([spillway.geometry(), 3])
                    if spillway['tipo']==4:
                        if not spillway.geometry().intersects(ptFin):
                            points.append([spillway.geometry(), 3])
            if spillwayTouches<1:
                points.append([spillway.geometry(), 3])
        return False
    def verifyRegimeRivers(self, streamLayerInput, streamLayerFeatures, points):
        for river in streamLayerFeatures:
            if not river['regime']==1:
                continue
            for geometry in river.geometry().constGet():
                ptFin = QgsGeometry.fromPointXY(QgsPointXY(geometry[-1]))
                lineTouched = self.linesTouched(streamLayerInput, river, ptFin)
            if len(lineTouched) == 0:
                continue 
            for line in lineTouched:
                for geometry in line.geometry().constGet():
                    ptIni = QgsGeometry.fromPointXY(QgsPointXY(geometry[0]))
                if not ptIni.intersects(ptFin):
                    continue
                if not line['regime'] ==1:
                    points.append([ptIni, 2])
        return False
    def verifyHydroElements(self, hydroElemPointFeatures, hydroElemLineFeatures, hydroElemPolygonFeatures, streamLayerFeatures, waterBodyFeatures, outputPoints, outputLines, outputPolygons):
        bancoDeAreia = [14, 15, 16, 17]
        
        for hydroPoint in hydroElemPointFeatures:
            intersectsOutsideRiver = False
            if hydroPoint['tipo'] ==12:
                for river in streamLayerFeatures:
                    if hydroPoint.geometry().intersects(river.geometry()):
                        if river['situacao_em_poligono']==1:
                            intersectsOutsideRiver = True
                            break
                if not intersectsOutsideRiver:
                    outputPoints.append([hydroPoint.geometry(), 26])
        for hydroLine in hydroElemLineFeatures:
            insideWaterbody = False
            crossesWaterbody = False
            withinOutsideRiver = False
            if hydroLine['tipo'] ==12:
                for waterBody in waterBodyFeatures:
                    if hydroLine.geometry().crosses(waterBody.geometry()):
                        crossesWaterbody = True
                        break
                    if hydroLine.geometry().within(waterBody.geometry()):
                        insideWaterbody = True
                if crossesWaterbody:
                    outputLines.append([hydroLine.geometry(), 21])
                    continue
                if not insideWaterbody:
                    for river in streamLayerFeatures:
                        if river['situacao_em_poligono']==1:
                            if hydroLine.geometry().within(river.geometry()):
                                withinOutsideRiver = True
                                break
                    if not withinOutsideRiver:
                        outputLines.append([hydroLine.geometry(), 22])
                        continue
                else:
                    intersectsPrimaryRiver = 0
                    for river in streamLayerFeatures:
                        inters = hydroLine.geometry().intersection(river.geometry())
                        if inters.isNull():
                            continue
                        if (not inters.type()==0) or inters.isMultipart():
                            outputLines.append([hydroLine.geometry(), 23])
                            continue
                        if not (river['situacao_em_poligono']==2 or river['situacao_em_poligono']==3):
                            outputLines.append([hydroLine.geometry(), 24])
                            continue
                        if river['situacao_em_poligono']==2:
                            intersectsPrimaryRiver +=1
                    if intersectsPrimaryRiver >1:
                        outputLines.append([hydroLine.geometry(), 25])        
        for hydroPolygon in hydroElemPolygonFeatures:
            insideWaterbody = False
            if hydroPolygon['tipo'] in bancoDeAreia or hydroPolygon['tipo']==12:
                for waterBody in waterBodyFeatures:
                    if hydroPolygon.geometry().within(waterBody.geometry()):
                        insideWaterbody = True
                        break
                if not insideWaterbody:
                    if hydroPolygon['tipo'] in bancoDeAreia:
                        outputPolygons.append([hydroPolygon.geometry(), 20])
                    if hydroPolygon['tipo']==12:
                        outputPolygons.append([hydroPolygon.geometry(), 27])


    def deleteEqualPoints(self, points):
        for point in points:
            count = 0
            for point2 in points:
                if point[0].intersects(point2[0]):
                    count+=1
            if count>1:
                points.remove(point)
        return False
    def verifyFrameFlags(self, points, outputLines, frameLayer):
        pointsToAdd = []
        pointsToRemove = []
        linesToRemove = []
        allFramesFeature = next(self.dissolveFrame(frameLayer).getFeatures())
        allFramesGeom = allFramesFeature.geometry()
        if not allFramesGeom.isMultipart():
            framegeom = allFramesGeom.asPolygon()
            for i in range(len(framegeom)):
                for pt in framegeom[i]:
                    pointsToAdd.append(pt)
        else:
            framegeom = allFramesGeom.asMultiPolygon()[0][0]
            for i in range(len(framegeom)):
                pointsToAdd.append(framegeom[i])
        pointsInFrame=QgsGeometry().fromMultiPointXY(pointsToAdd)
        for pt in points:
            if pt[0].intersects(pointsInFrame):
                pointsToRemove.append(pt)
                continue
            if not pt[0].intersects(allFramesGeom):
                pointsToRemove.append(pt)
        for pointR in pointsToRemove:
            points.remove(pointR)
        '''
        for line in outputLines:
            for geometry in line[0].constGet():
                    ptIni = QgsGeometry.fromPointXY(QgsPointXY(geometry[0]))
            if ptIni.intersects(pointsInFrame):
                linesToRemove.append(line)
                continue
        for lineR in linesToRemove:
            outputLines.remove(lineR)
        '''
        return False
    def shouldBeIgnored(self, outputLines, outputPolygons, frameLayer):
        pointsToAdd = []
        polyToRemove = []
        lineToRemove = []
        toBeVerified = [7, 8, 10, 29, 30]
        allFramesFeature = next(self.dissolveFrame(frameLayer).getFeatures())
        allFramesGeom = allFramesFeature.geometry()
        if not allFramesGeom.isMultipart():
            framegeom = allFramesGeom.asPolygon()
            for i in range(len(framegeom)):
                for pt in framegeom[i]:
                    pointsToAdd.append(pt)
        else:
            framegeom = allFramesGeom.asMultiPolygon()[0][0]
            for i in range(len(framegeom)):
                pointsToAdd.append(framegeom[i])
        pointsInFrame=QgsGeometry().fromMultiPointXY(pointsToAdd)
        for line in outputLines:
            if line[0].intersects(pointsInFrame) and line[1] in toBeVerified:
                lineToRemove.append(line)
        for poly in outputPolygons:
            if poly[0].intersects(pointsInFrame) and poly[1] in toBeVerified:
                polyToRemove.append(poly)
        for polyR in polyToRemove:
            outputPolygons.remove(polyR)
        for lineR in lineToRemove:
            outputLines.remove(lineR)
        return False
    def dissolveFrame(self, layer):
        r = processing.run(
            'native:dissolve',
            {   'FIELD' : [], 
                'INPUT' : QgsProcessingFeatureSourceDefinition(
                    layer.source()
                ), 
                'OUTPUT' : 'TEMPORARY_OUTPUT'
            }
        )
        return r['OUTPUT']            
    def linesTouched(self, layer, feature, point):
        lines = []
        AreaOfInterest = feature.geometry().boundingBox()
        request = QgsFeatureRequest().setFilterRect(AreaOfInterest)
        for feat in layer.getFeatures(request):
            if feat.geometry().intersects(point):
                if str(feature.geometry())==str(feat.geometry()):
                    continue
                lines.append(feat)
        return lines
    def outLayer(self, parameters, context, geometry, streamLayer, geomType):
        newField = QgsFields()
        newField.append(QgsField('id', QVariant.Int))
        newField.append(QgsField('erro', QVariant.String))

        (sink, newLayer) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            newField,
            geomType, #1point 2line 3polygon
            streamLayer.sourceCrs()
        )
        
        idcounter = 1
        dicterro = {
            1:'tipo incorreto',
            2:'regime incorreto',
            3:'vertedouro/sumidouro incorreto',
            4:'rio cruzou massa d\'água',
            5:'rio está fora de polígono, mas atributo não é fora de polígono',
            6:'massa d\'água sem fluxo contém trecho de drenagem',
            7:'massa d\'água com fluxo não contém nenhum trecho de drenagem',
            8:'massa d\'água com fluxo não contém trecho de drenagem principal',
            9:'massa d\'água sem fluxo intersecta ponto inicial e final de drenagem',
            10:'massa d\'água com fluxo não intersecta ponto inicial e final de drenagem',
            11:'rio intersecta barragem, mas não (somente) no ponto inicial ou final',
            12:'rio compartilhado (entrando) não inicia em rio fora de polígono',
            13:'rio compartilhado (entrando) não termina em rios principais ou rios secundários',
            14:'rio principal não termina em rio fora de polígono ou em rio principal',
            15:'rio principal termina em massa d\'água com fluxo mas não toca trecho compartilhado ou principal',
            16:'rio principal termina em massa d\'água sem fluxo e em outra drenagem',
            17:'rio principal não inicia em rio fora de polígono ou em rio principal',
            18:'rio fora de polígono termina em massa d\'água com fluxo mas não toca trecho compartilhado ou principal',
            19:'rio principal ou secundário com nome diferente da massa d\'água',
            20:'banco de areia fora de massa d\'água',
            21:'corredeira cruza massa d\'água',
            22:'corredeira fora de massa d\'água não coincide com trecho de drenagem fora de polígono',
            23:'corredeira dentro de massa d\'água não intersecta um trecho em apenas um ponto',
            24:'corredeira não intersecta rio principal ou secundário',
            25:'corredeira intersecta mais de um rio principal',
            26:'corredeira não intersecta trecho de drenagem fora de polígono',
            27:'corredeira não é interna a massa d\'água',
            28:'barragem não intersecta massa d\'água do tipo represa/açude ou rio',
            29:'relacionamento incorreto entre barragem (poligono) e massa d\'água',
            30:'relacionamento incorreto entre barragem (linha) e massa d\'água',
            31:'rio compartilhado (saindo) não inicia em rio primário ou secundário',
            32:'rio compartilhado (saindo) não termina em rio principais, secundários ou fora de polígono',
            33:'rio compartilhado deve iniciar e terminar em massa d\'água com fluxo',
            34:'rio compartilhado entre 2 massas d\'água não inicia em rio principal nem secundário',
            35:'rio começa em massa d\'água, mas não é do tipo Rio, Canal nem Canal encoberto',
            36:'rio começa em vertedouro, mas não é tipo Rio',
            37:'rio não intersecta outro rio, nem massa d\'água, nem vertedouro, mas não é pluvial',
            38:'rio pluvial toca em outro rio que não é pluvial'
        }
        for geom in geometry:
            newFeat = QgsFeature()
            newFeat.setGeometry(geom[0])
            newFeat.setFields(newField)
            newFeat['id'] = idcounter
            newFeat['erro'] = dicterro[geom[1]]
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
            idcounter +=1
        return newLayer
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return VerifyHydrography()

    def name(self):
        return 'verifyhydrography'

    def displayName(self):
        return self.tr('Verifica Hidrografia')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo verifica a consistência lógica de regimes e tipos de rios")
    
