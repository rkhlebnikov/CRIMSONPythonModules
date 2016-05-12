import os
import shutil
import subprocess
import tempfile
from collections import OrderedDict
import numpy
import math
import operator
import ntpath
import stat

from PythonQt import QtGui
from PythonQt.CRIMSON import FaceType
from PythonQt.CRIMSON import Utils

from CRIMSONCore.SolutionStorage import SolutionStorage
from CRIMSONSolver.SolverStudies import PresolverExecutableName, PhastaSolverIO, PhastaConfig
from CRIMSONSolver.SolverSetupManagers.FlowProfileGenerator import FlowProfileGenerator
from CRIMSONSolver.SolverStudies.FileList import FileList
from CRIMSONSolver.SolverStudies.SolverInpData import SolverInpData
from CRIMSONSolver.SolverStudies.Timer import Timer
from CRIMSONSolver.BoundaryConditions import NoSlip, InitialPressure, RCR, ZeroPressure, PrescribedVelocities, \
    DeformableWall, Netlist
from CRIMSONSolver.Materials import MaterialData


# A helper class providing lazily-evaluated quantities for material computation
class MaterialFaceInfo(object):
    def __init__(self, vesselForestData, meshData, faceIdentifier, meshFaceInfoData):
        self.vesselForestData = vesselForestData
        self.meshData = meshData
        self.meshFaceInfoData = meshFaceInfoData
        self.faceIdentifier = faceIdentifier

    def getMeshFaceInfo(self):
        return self.meshFaceInfoData

    def getFaceCenter(self):
        if 'center' not in self.__dict__:
            self.center = self.meshData.getNodeCoordinates(self.meshFaceInfoData[2])
            self.center = map(operator.add, self.center, self.meshData.getNodeCoordinates(self.meshFaceInfoData[3]))
            self.center = map(operator.add, self.center, self.meshData.getNodeCoordinates(self.meshFaceInfoData[4]))

            for i in xrange(3):
                self.center[i] /= 3

        return self.center

    #    This version is actually slower than getFaceCenter()
    #    def getFaceCenter2(self, faceInfo, meshData):
    #        center = numpy.array(meshData.getNodeCoordinates(faceInfo[2]))
    #        numpy.add(center, meshData.getNodeCoordinates(faceInfo[3]), center)
    #        numpy.add(center, meshData.getNodeCoordinates(faceInfo[4]), center)
    #
    #        return center / 3

    def getLocalRadius(self):
        if 'localRadius' not in self.__dict__:
            self._computeLocalRadiusAndArcLength()

        return self.localRadius

    def getArcLength(self):
        if 'arcLength' not in self.__dict__:
            self._computeLocalRadiusAndArcLength()

        return self.arcLength

    def getVesselPathCoordinateFrame(self):
        if 'vesselPathCoordinateFrame' not in self.__dict__:
            faceCenter = self.getFaceCenter()
            self.vesselPathCoordinateFrame = \
                self.vesselForestData.getVesselPathCoordinateFrame(self.faceIdentifier, faceCenter[0], faceCenter[1],
                                                                   faceCenter[2]) \
                    if self.vesselForestData is not None else []

        return self.vesselPathCoordinateFrame

    def _computeLocalRadiusAndArcLength(self):
        faceCenter = self.getFaceCenter()
        self.localRadius, self.arcLength = \
            self.vesselForestData.getClosestPoint(self.faceIdentifier, faceCenter[0], faceCenter[1], faceCenter[2]) \
                if self.vesselForestData is not None else (0, 0)


class SolverStudy(object):
    def __init__(self):
        self.meshNodeUID = ""
        self.solverParametersNodeUID = ""
        self.boundaryConditionSetNodeUIDs = []
        self.materialNodeUIDs = []

    def getMeshNodeUID(self):
        return self.meshNodeUID

    def setMeshNodeUID(self, uid):
        self.meshNodeUID = uid

    def getSolverParametersNodeUID(self):
        return self.solverParametersNodeUID

    def setSolverParametersNodeUID(self, uid):
        self.solverParametersNodeUID = uid

    def getBoundaryConditionSetNodeUIDs(self):
        return self.boundaryConditionSetNodeUIDs

    def setBoundaryConditionSetNodeUIDs(self, uids):
        self.boundaryConditionSetNodeUIDs = uids

    def getMaterialNodeUIDs(self):
        if 'materialNodeUIDs' not in self.__dict__:
            self.materialNodeUIDs = []  # Support for old scenes
        return self.materialNodeUIDs

    def setMaterialNodeUIDs(self, uids):
        self.materialNodeUIDs = uids

    def loadSolution(self):
        fullNames = QtGui.QFileDialog.getOpenFileNames(None, "Load solution")

        if not fullNames:
            return

        solutions = SolutionStorage()
        for fullName in fullNames:
            fileName = os.path.basename(fullName)
            if fileName.startswith('restart'):
                config = PhastaConfig.restartConfig
            elif fileName.startswith('ybar'):
                config = PhastaConfig.ybarConfig
            else:
                QtGui.QMessageBox.critical(None, "Solution loading failed",
                                           "File {0} was not recognized as a phasta solution file.\n"
                                           "Only 'restart.*' and 'ybar.*' files are supported.".format(
                                               fullName))
                continue
            try:
                with open(fullName, 'rb') as inFile:
                    fields = PhastaSolverIO.readPhastaFile(PhastaSolverIO.PhastaRawFileReader(inFile), config)

                for fieldName, fieldData in fields.iteritems():
                    solutions.arrays[fieldName] = SolutionStorage.ArrayInfo(fieldData.transpose())

            except Exception as e:
                QtGui.QMessageBox.critical(None, "Solution loading failed",
                                           "Failed to load solution from file {0}:\n{1}.".format(fullName, str(e)))
                continue

        return solutions

    def writeSolverSetup(self, vesselForestData, solidModelData, meshData, solverParameters, boundaryConditions,
                         materials, vesselPathNames, solutionStorage):

        outputDir = QtGui.QFileDialog.getExistingDirectory(None, 'Select output folder')

        if not outputDir:
            return

        if solutionStorage is not None:
            if QtGui.QMessageBox.question(None, 'Write solution to the solver output?',
                                          'Would you like to use the solutions in the solver output?',
                                          QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                          QtGui.QMessageBox.Yes) != QtGui.QMessageBox.Yes:
                solutionStorage = None

        presolverDir = os.path.join(outputDir, 'presolver')
        if not os.path.exists(presolverDir):
            os.makedirs(presolverDir)

        fileList = FileList(outputDir)

        try:
            faceIndicesAndFileNames = self._computeFaceIndicesAndFileNames(solidModelData, vesselPathNames)
            solverInpData = SolverInpData(solverParameters, faceIndicesAndFileNames)

            supreFile = fileList[os.path.join('presolver', 'the.supre')]

            self._writeSupreHeader(meshData, supreFile)
            self._writeSupreSurfaceIDs(faceIndicesAndFileNames, supreFile)

            with Timer('Written nbc and ebc files'):
                faceIndicesInAllExteriorFaces = self._writeNbcEbc(solidModelData, meshData, faceIndicesAndFileNames,
                                                                  fileList)
            with Timer('Written coordinates'):
                self._writeNodeCoordinates(meshData, fileList)
            with Timer('Written connectivity'):
                self._writeConnectivity(meshData, fileList)
            with Timer('Written adjacency'):
                self._writeAdjacency(meshData, fileList)
            with Timer('Written boundary conditions'):
                self._writeBoundaryConditions(vesselForestData, solidModelData, meshData, boundaryConditions,
                                              materials, faceIndicesAndFileNames, solverInpData, fileList,
                                              faceIndicesInAllExteriorFaces)

            self._writeSolverSetup(solverInpData, fileList)

            supreFile.write('write_geombc  geombc.dat.1\n')
            supreFile.write('write_restart  restart.0.1\n')

            fileList['numstart.dat', 'wb'].write('0\n')
            fileList.close()

            with Timer('Ran presolver'):
                self._runPresolver(os.path.join(outputDir, 'presolver', 'the.supre'), outputDir,
                                   ['geombc.dat.1', 'restart.0.1'])

            if solutionStorage is not None:
                with Timer('Appended solutions'):
                    self._appendSolutionsToRestart(outputDir, solutionStorage)

                Utils.logInformation('Done')

        except Exception as e:
            Utils.logError(str(e))
            fileList.close()
            raise

    def _appendSolutionsToRestart(self, outputDir, solutionStorage):
        restartFileName = os.path.join(outputDir, 'restart.0.1')
        with open(restartFileName, 'rb') as restartFile:
            rawReader = PhastaSolverIO.PhastaRawFileReader(restartFile)
            dataBlocksToReplace = ['byteorder magic number']
            newFields = {}
            for name, dataInfo in solutionStorage.arrays.iteritems():
                arrayDesc, fieldDesc = PhastaConfig.restartConfig.findDescriptorAndField(name)
                if arrayDesc is None:
                    Utils.logWarning(
                        'Cannot write solution \'{0}\' to the restart file. Skipping.'.format(name))
                    continue
                Utils.logInformation('Appending solution data \'{0}\'...'.format(name))

                dataBlocksToReplace.append(arrayDesc.phastaDataBlockName)
                newFields[fieldDesc.name] = dataInfo.data.transpose()

            _, tempFileName = tempfile.mkstemp()
            with open(tempFileName, 'wb') as tempFile:
                rawWriter = PhastaSolverIO.PhastaRawFileWriter(tempFile)
                rawWriter.writeFileHeader()

                for blockName, blockDescriptor in rawReader.blockDescriptors.iteritems():
                    if blockDescriptor.totalBytes == -1:  # header only
                        rawWriter.writeHeader(blockName, 0, blockDescriptor.headerElements)
                    elif blockName not in dataBlocksToReplace:  # header and data
                        rawWriter.writeRawData(blockName, rawReader.getRawData(blockName),
                                               blockDescriptor.headerElements)

                PhastaSolverIO.writePhastaFile(rawWriter, PhastaConfig.restartConfig, newFields)

        shutil.copy(tempFileName, restartFileName)

    def _runPresolver(self, supreFile, outputDir, outputFiles):
        presolverExecutable = os.path.normpath(os.path.join(os.path.realpath(__file__), os.pardir,
                                                            PresolverExecutableName.getPresolverExecutableName()))
        Utils.logInformation('Running presolver from ' + presolverExecutable)

        os.chmod(presolverExecutable, os.stat(presolverExecutable).st_mode | stat.S_IEXEC)

        supreDir, supreFileName = os.path.split(supreFile)
        p = subprocess.Popen([presolverExecutable, supreFileName], cwd=supreDir,
                             stderr=subprocess.STDOUT)  # stdout=subprocess.PIPE,

        out, _ = p.communicate()
        # self._logPresolverOutput(out)

        if p.returncode != 0:
            Utils.logError("Presolver run has failed.")
            return

        try:
            Utils.logInformation("Moving output files to output folder")
            for fName in outputFiles:
                fullName = os.path.normpath(os.path.join(supreFile, os.path.pardir, fName))
                shutil.copy(fullName, outputDir)
                os.remove(fullName)
        except Exception as e:
            Utils.logError("Failed to move output files: " + str(e))
            raise

    def _logPresolverOutput(self, out):
        for s in out.splitlines():
            if s.find('ERROR') != -1:
                Utils.logError(s)
            else:
                Utils.logInformation(s)

    def _writeAdjacency(self, meshData, fileList):
        # node and element indices are 0-based for presolver adjacency (!)
        outFileAdjacency = fileList[os.path.join('presolver', 'the.xadj')]

        xadjString = 'xadj: {0}\n'.format(meshData.getNElements() + 1)
        outFileAdjacency.write(xadjString)
        # reserve space in the beginning of file
        outFileAdjacency.write(' ' * 50 + '\n')

        curIndex = 0
        outFileAdjacency.write('0\n')
        for i in xrange(meshData.getNElements()):
            curIndex += len(meshData.getAdjacentElements(i))
            outFileAdjacency.write('{0}\n'.format(curIndex))

        for i in xrange(meshData.getNElements()):
            for adjacentId in meshData.getAdjacentElements(i):
                outFileAdjacency.write('{0}\n'.format(adjacentId))

        outFileAdjacency.seek(len(xadjString) + len(os.linesep) - 1)  # +1 for potential \r
        outFileAdjacency.write('adjncy: {0}'.format(curIndex))

    def _writeConnectivity(self, meshData, fileList):
        outFileConnectivity = fileList[os.path.join('presolver', 'the.connectivity')]

        for i in xrange(meshData.getNElements()):
            # node and element indices are 1-based for presolver
            outFileConnectivity.write(
                '{0} {1[0]} {1[1]} {1[2]} {1[3]}\n'.format(i + 1, [x + 1 for x in meshData.getElementNodeIds(i)]))

    def _writeNodeCoordinates(self, meshData, fileList):
        outFileCoordinates = fileList[os.path.join('presolver', 'the.coordinates')]

        for i in xrange(meshData.getNNodes()):
            # node indices are 1-based for presolver
            outFileCoordinates.write('{0} {1[0]} {1[1]} {1[2]}\n'.format(i + 1, meshData.getNodeCoordinates(i)))

    def _writeNbc(self, meshData, faceIdentifiers, outputFile):
        nodeIndices = set()

        for faceIdentifier in faceIdentifiers:
            nodeIndices.update(meshData.getNodeIdsForFace(faceIdentifier))

        for i in sorted(nodeIndices):
            outputFile.write('{0}\n'.format(i + 1))  # Node indices are 1-based for presolver

    def _writeEbc(self, meshData, faceIdentifiers, outputFile):
        faceIndicesInFile = []
        for faceIdentifier in faceIdentifiers:
            for info in meshData.getMeshFaceInfoForFace(faceIdentifier):
                l = '{0}\n'.format(
                    ' '.join(str(x + 1) for x in info))  # element and node indices are 1-based for presolver
                outputFile.write(l)

                faceIndicesInFile.append(info[1])

        return faceIndicesInFile

    def _writeNbcEbc(self, solidModelData, meshData, faceIndicesAndFileNames, fileList):
        allFaceIdentifiers = [solidModelData.getFaceIdentifier(i) for i in
                              xrange(solidModelData.getNumberOfFaceIdentifiers())]

        # Write wall.nbc
        self._writeNbc(meshData, [id for id in allFaceIdentifiers if id.faceType == FaceType.ftWall],
                       fileList[os.path.join('presolver', 'wall.nbc')])

        # Write per-face-identifier ebc and nbc files
        for i in xrange(solidModelData.getNumberOfFaceIdentifiers()):
            faceIdentifier = solidModelData.getFaceIdentifier(i)

            baseFileName = os.path.join('presolver', faceIndicesAndFileNames[faceIdentifier][1])
            self._writeNbc(meshData, [faceIdentifier], fileList[baseFileName + '.nbc'])
            self._writeEbc(meshData, [faceIdentifier], fileList[baseFileName + '.ebc'])

        # Write all_eterior_faces.ebc
        return self._writeEbc(meshData, allFaceIdentifiers,
                              fileList[os.path.join('presolver', 'all_exterior_faces.ebc')])

    def _writeSolverSetup(self, solverInpData, fileList):
        solverInpFile = fileList['solver.inp', 'wb']

        for category, values in sorted(solverInpData.data.iteritems()):
            solverInpFile.write('\n\n# {0}\n# {{\n'.format(category))
            for kv in values.iteritems():
                solverInpFile.write('    {0[0]} : {0[1]}\n'.format(kv))
            solverInpFile.write('# }\n')

    def _validateBoundaryConditions(self, boundaryConditions):
        if len(boundaryConditions) == 0:
            Utils.logError('Cannot write CRIMSON solver setup without any boundary conditions selected')
            return False

        # Check unique BC's
        bcByType = {}
        for bc in boundaryConditions:
            bcByType.setdefault(bc.__class__.__name__, []).append(bc)

        hadError = False

        for bcType, bcs in bcByType.iteritems():
            if bcs[0].unique and len(bcs) > 1:
                Utils.logError(
                    'Multiple instances of boundary condition {0} are not allowed in a single study'.format(bcType))
                hadError = True

        return not hadError

    def _writeBoundaryConditions(self, vesselForestData, solidModelData, meshData, boundaryConditions, materials,
                                 faceIndicesAndFileNames, solverInpData, fileList, faceIndicesInAllExteriorFaces):
        if not self._validateBoundaryConditions(boundaryConditions):
            raise RuntimeError('Invalid boundary conditions. Aborting.')

        supreFile = fileList[os.path.join('presolver', 'the.supre')]

        class RCRInfo(object):
            def __init__(self):
                self.first = True
                self.faceIds = []

        rcrInfo = RCRInfo()

        class NetlistInfo(object):
            def __init__(self):
                self.faceIds = []

        netlistInfo = NetlistInfo()

        class BCTInfo(object):
            def __init__(self):
                self.first = True
                self.totalPoints = 0
                self.maxNTimeSteps = 0
                self.faceIds = []
                self.period = 1.1  # for RCR

        bctInfo = BCTInfo()

        validFaceIdentifiers = lambda bc: (x for x in bc.faceIdentifiers if
                                           solidModelData.faceIdentifierIndex(x) != -1)

        is_boundary_condition_type = lambda bc, bcclass: bc.__class__.__name__ == bcclass.__name__

        initialPressure = None

        materialStorage = self.computeMaterials(materials, vesselForestData, solidModelData, meshData)

        # Processing priority for a particular BC type defines the order of processing the BCs
        # Default value is assumed to be 1. The higher the priority, the later the BC is processed
        bcProcessingPriorities = {
            RCR.RCR.__name__: 2,  # Process RCR after PrescribedVelocities
            DeformableWall.DeformableWall.__name__: 3  # Process deformable wall last
        }

        bcCompare = lambda l, r: \
            cmp([bcProcessingPriorities.get(l.__class__.__name__, 1), l.__class__.__name__],
                [bcProcessingPriorities.get(r.__class__.__name__, 1), r.__class__.__name__])

        for bc in sorted(boundaryConditions, cmp=bcCompare):
            if is_boundary_condition_type(bc, NoSlip.NoSlip):
                for faceId in validFaceIdentifiers(bc):
                    supreFile.write('noslip {0}.nbc\n'.format(faceIndicesAndFileNames[faceId][1]))
                supreFile.write('\n')

            elif is_boundary_condition_type(bc, InitialPressure.InitialPressure):
                initialPressure = bc.getProperties()['Initial pressure']
                supreFile.write('initial_pressure {0}\n\n'.format(initialPressure))

            elif is_boundary_condition_type(bc, RCR.RCR):
                rcrtFile = fileList['rcrt.dat']
                faceInfoFile = fileList['faceInfo.dat']

                if rcrInfo.first:
                    rcrInfo.first = False
                    rcrtFile.write('2\n')

                for faceId in validFaceIdentifiers(bc):
                    supreFile.write('zero_pressure {0}.ebc\n'.format(faceIndicesAndFileNames[faceId][1]))
                    faceInfoFile.write('RCR {0[0]} {0[1]}\n'.format(faceIndicesAndFileNames[faceId]))

                    rcrInfo.faceIds.append(str(faceIndicesAndFileNames[faceId][0]))

                    rcrtFile.write('2\n'
                                   '{0[Proximal resistance]}\n'
                                   '{0[Capacitance]}\n'
                                   '{0[Distal resistance]}\n'
                                   '0 0.0\n'
                                   '{1} 0.0\n'.format(bc.getProperties(), bctInfo.period))
                supreFile.write('\n')

            elif is_boundary_condition_type(bc, Netlist.Netlist):
                faceInfoFile = fileList['faceInfo.dat']

                for faceId in validFaceIdentifiers(bc):

                    if bc.getProperties()['Heart model']:
                        supreFile.write('prescribed_velocities {0}.nbc\n'.format(faceIndicesAndFileNames[faceId][1]))
                        faceInfoFile.write('Netlist Heart {0[0]} {0[1]}\n'.format(faceIndicesAndFileNames[faceId]))
                    else:
                        faceInfoFile.write('Netlist {0[0]} {0[1]}\n'.format(faceIndicesAndFileNames[faceId]))

                    if not bc.netlistSurfacesDat == '':
                        Utils.logInformation('Writing to file \'{0}\''.format('netlist_surfaces.dat'))
                        fileList['netlist_surfaces.dat', 'wb'].write(bc.netlistSurfacesDat)
                    else:
                        Utils.logWarning('No circuit file was specified for the Netlist at surface  \'{0}\'.'.format(
                            faceIndicesAndFileNames[faceId][0]))

                    dynamicAdjustmentScriptFileNamesAndContents = bc.getCircuitDynamicAdjustmentFiles()
                    for dynamicAdjustmentScriptName in dynamicAdjustmentScriptFileNamesAndContents:
                        fileContentsToWrite = dynamicAdjustmentScriptFileNamesAndContents[dynamicAdjustmentScriptName]
                        nameOfFileToWrite = ntpath.basename(dynamicAdjustmentScriptName)
                        Utils.logInformation('Writing file \'{0}\''.format(nameOfFileToWrite))
                        if fileList.isOpen(nameOfFileToWrite):
                            Utils.logWarning(
                                'File with name \'{0}\' occurs multiple times in solver setup. Overwriting. This is ok if all copies should be identical'.format(
                                    nameOfFileToWrite))
                        fileList[nameOfFileToWrite, 'wb'].write(fileContentsToWrite)

                    additionalDataFileNamesAndContents = bc.getCircuitAdditionalDataFiles()
                    for additionalDataFileName in additionalDataFileNamesAndContents:
                        fileContentsToWrite = additionalDataFileNamesAndContents[additionalDataFileName]
                        nameOfFileToWrite = ntpath.basename(additionalDataFileName)
                        Utils.logInformation('Writing file \'{0}\''.format(nameOfFileToWrite))
                        if fileList.isOpen(nameOfFileToWrite):
                            Utils.logWarning(
                                'File with name \'{0}\' occurs multiple times in solver setup. Overwriting. This is ok if all copies should be identical'.format(
                                    nameOfFileToWrite))
                        fileList[nameOfFileToWrite, 'wb'].write(fileContentsToWrite)

                    supreFile.write('zero_pressure {0}.ebc\n'.format(faceIndicesAndFileNames[faceId][1]))

                    netlistInfo.faceIds.append(str(faceIndicesAndFileNames[faceId][0]))

                supreFile.write('\n')




            elif is_boundary_condition_type(bc, ZeroPressure.ZeroPressure):
                for faceId in validFaceIdentifiers(bc):
                    supreFile.write('zero_pressure {0}.ebc\n'.format(faceIndicesAndFileNames[faceId][1]))
                supreFile.write('\n')

            elif is_boundary_condition_type(bc, PrescribedVelocities.PrescribedVelocities):
                faceInfoFile = fileList['faceInfo.dat']

                bctFile = fileList['bct.dat']
                bctSteadyFile = fileList['bct_steady.dat']

                if bctInfo.first:
                    bctInfo.first = False
                    emptyLine = ' ' * 50 + '\n'
                    bctFile.write(emptyLine)
                    bctSteadyFile.write(emptyLine)
                    bctInfo.period = bc.originalWaveform[-1, 0]  # Last time point
                else:
                    if abs(bc.originalWaveform[-1, 0] - bctInfo.period) > 1e-5:
                        Utils.logWarning(
                            'Periods of waveforms used for prescribed velocities are different. RCR boundary conditions may be inconsistent - the period used is {0}'.format(
                                bctInfo.period))

                waveform = bc.smoothedWaveform
                steadyWaveformValue = numpy.trapz(waveform[:, 1], x=waveform[:, 0]) / (waveform[-1, 0] - waveform[0, 0])

                bctInfo.maxNTimeSteps = max(bctInfo.maxNTimeSteps, waveform.shape[0])

                for faceId in validFaceIdentifiers(bc):
                    supreFile.write('prescribed_velocities {0}.nbc\n'.format(faceIndicesAndFileNames[faceId][1]));
                    faceInfoFile.write('PrescribedVelocities {0[0]} {0[1]}\n'.format(faceIndicesAndFileNames[faceId]))
                    bctInfo.faceIds.append(str(faceIndicesAndFileNames[faceId][0]))

                supreFile.write('\n')

                def writeBctProfile(file, wave):
                    for faceId in validFaceIdentifiers(bc):
                        flowProfileGenerator = FlowProfileGenerator(bc.getProperties()['Profile type'], solidModelData,
                                                                    meshData, faceId)

                        for pointIndex, flowVectorList in flowProfileGenerator.generateProfile(wave[:, 1]):
                            bctInfo.totalPoints += 1
                            file.write('{0[0]} {0[1]} {0[2]} {1}\n'.format(meshData.getNodeCoordinates(pointIndex),
                                                                           wave.shape[0]))
                            for timeStep, flowVector in enumerate(flowVectorList):
                                file.write('{0[0]} {0[1]} {0[2]} {1}\n'.format(flowVector, wave[timeStep, 0]))

                writeBctProfile(bctFile, waveform)
                writeBctProfile(bctSteadyFile,
                                numpy.array([[waveform[0, 0], steadyWaveformValue],
                                             [waveform[-1, 0], steadyWaveformValue]]))

            elif is_boundary_condition_type(bc, DeformableWall.DeformableWall):
                if initialPressure is None:
                    raise RuntimeError('Deformable wall boundary condition requires initial pressure to be defined.\n'
                                       'Please add the "Initial pressure" condition to the boundary condition set.')

                # Write the ebc for deformable wall
                self._writeEbc(meshData, validFaceIdentifiers(bc),
                               fileList[os.path.join('presolver', 'deformable_wall.ebc')])

                shearConstant = 0.8333333

                supreFile.write('deformable_wall deformable_wall.ebc\n')
                supreFile.write('fix_free_edge_nodes deformable_wall.ebc\n')
                supreFile.write('deformable_create_mesh deformable_wall.ebc\n')
                supreFile.write('deformable_write_feap inputdataformatlab.dat\n')
                supreFile.write('deformable_pressure {0}\n'.format(initialPressure))
                supreFile.write('deformable_Evw {0}\n'.format(bc.getProperties()["Young's modulus"]))
                supreFile.write('deformable_nuvw {0}\n'.format(bc.getProperties()["Poisson ratio"]))
                supreFile.write('deformable_thickness {0}\n'.format(bc.getProperties()["Thickness"]))
                supreFile.write('deformable_kcons {0}\n'.format(shearConstant))

                deformableGroup = solverInpData['DEFORMABLE WALL PARAMETERS']
                deformableGroup['Deformable Wall'] = True
                deformableGroup['Density of Vessel Wall'] = bc.getProperties()["Density"]
                deformableGroup['Thickness of Vessel Wall'] = bc.getProperties()["Thickness"]
                deformableGroup['Young Mod of Vessel Wall'] = bc.getProperties()["Young's modulus"]
                deformableGroup['Poisson Ratio of Vessel Wall'] = bc.getProperties()["Poisson ratio"]
                deformableGroup['Shear Constant of Vessel Wall'] = shearConstant

                deformableGroup['Use SWB File'] = False
                deformableGroup['Use TWB File'] = False
                deformableGroup['Use EWB File'] = False
                deformableGroup['Wall External Support Term'] = bc.getProperties()["Enable tissue support term"]
                deformableGroup['Stiffness Coefficient for Tissue Support'] = \
                    bc.getProperties()["Stiffness coefficient"]
                deformableGroup['Wall Damping Term'] = bc.getProperties()["Enable damping term"]
                deformableGroup['Damping Coefficient for Tissue Support'] = bc.getProperties()["Damping coefficient"]
                deformableGroup['Wall State Filter Term'] = False
                deformableGroup['Wall State Filter Coefficient'] = 0

                if "Young's modulus" in materialStorage.arrays and "Young's modulus (anisotropic)" in materialStorage.arrays:
                    raise RuntimeError('Isotropic and anisotropic deformable wall materials cannot be combined')

                useSWB = False
                numberOfWallProps = 10
                readSWBCommand = None

                # Check if external material is present
                if 'Thickness' in materialStorage.arrays:
                    if "Young's modulus" in materialStorage.arrays:
                        # Isotropic material
                        useSWB = True
                        numberOfWallProps = 10
                        swbFileName = 'SWB_ISO.dat'
                        swbFile = fileList[os.path.join('presolver', swbFileName)]
                        readSWBCommand = 'read_SWB_ISO ' + swbFileName
                        self._writeIsotropicMaterial(bc, faceIndicesInAllExteriorFaces, swbFile, materialStorage,
                                                     shearConstant)

                    elif "Young's modulus (anisotropic)" in materialStorage.arrays:
                        # Anisotropic material
                        useSWB = True
                        numberOfWallProps = 21
                        swbFileName = 'SWB_ANISO.dat'
                        swbFile = fileList[os.path.join('presolver', swbFileName)]
                        readSWBCommand = 'read_SWB_ORTHO ' + swbFileName

                        self._writeAnisotropicMaterial(bc, faceIndicesInAllExteriorFaces, swbFile, materialStorage,
                                                       meshData, solidModelData, vesselForestData)

                deformableGroup['Use SWB File'] = useSWB
                deformableGroup['Number of Wall Properties per Node'] = numberOfWallProps
                supreFile.write('number_of_wall_Props {0}\n'.format(numberOfWallProps))
                if readSWBCommand is not None:
                    supreFile.write(readSWBCommand + '\n')
                supreFile.write('deformable_solve\n\n')

        # Finalize
        if len(rcrInfo.faceIds) > 0:
            rcrGroup = solverInpData['CARDIOVASCULAR MODELING PARAMETERS: RCR']

            rcrValuesFromFileKey = 'RCR Values From File'
            numberOfRCRSurfacesKey = 'Number of RCR Surfaces'
            listOfRCRSurfacesKey = 'List of RCR Surfaces'

            if len(netlistInfo.faceIds) > 0:
                rcrValuesFromFileKey = 'experimental RCR Values From File'
                numberOfRCRSurfacesKey = 'Number of experimental RCR Surfaces'
                listOfRCRSurfacesKey = 'List of experimental RCR Surfaces'

            rcrGroup[rcrValuesFromFileKey] = True
            rcrGroup[numberOfRCRSurfacesKey] = len(rcrInfo.faceIds)
            rcrGroup[listOfRCRSurfacesKey] = ' '.join(rcrInfo.faceIds)

        if len(netlistInfo.faceIds) > 0:
            netlistGroup = solverInpData['CARDIOVASCULAR MODELING PARAMETERS: NETLIST LPNs']
            netlistGroup['Number of Netlist LPN Surfaces'] = len(netlistInfo.faceIds)
            netlistGroup['List of Netlist LPN Surfaces'] = ' '.join(netlistInfo.faceIds)

            multidomainFile = fileList['multidomain.dat']
            multidomainFile.write('#\n{0}\n#\n0\n'.format(0 if len(rcrInfo.faceIds) == 0 else 1))

        if not bctInfo.first:
            bctInfo.totalPoints /= 2  # points counted twice for steady and non-steady output

            def writeBctInfo(file, maxNTimesteps):
                file.seek(0)
                file.write('{0} {1}'.format(bctInfo.totalPoints, maxNTimesteps))

            writeBctInfo(bctFile, bctInfo.maxNTimeSteps)
            writeBctInfo(bctSteadyFile, 2)

            presribedVelocititesGroup = solverInpData['CARDIOVASCULAR MODELING PARAMETERS: PRESCRIBED VELOCITIES']
            presribedVelocititesGroup['Time Varying Boundary Conditions From File'] = True
            presribedVelocititesGroup['BCT Time Scale Factor'] = 1.0
            presribedVelocititesGroup['Number of Dirichlet Surfaces Which Output Pressure and Flow'] = \
                len(bctInfo.faceIds)
            presribedVelocititesGroup['List of Dirichlet Surfaces'] = ' '.join(bctInfo.faceIds)

    def _writeIsotropicMaterial(self, bc, faceIndicesInAllExteriorFaces, swbFile, materialStorage, shearConstant):
        thicknessArray = materialStorage.arrays['Thickness'].data
        stiffnessArray = materialStorage.arrays["Young's modulus"].data
        v = bc.getProperties()["Poisson ratio"]
        v2 = math.pow(v, 2)
        Econst = bc.getProperties()["Young's modulus"]
        tConst = bc.getProperties()["Thickness"]
        k = shearConstant
        # SWB file MUST contain information for all exterior faces
        for i, faceId in enumerate(faceIndicesInAllExteriorFaces):
            t = thicknessArray[faceId][0]
            E = stiffnessArray[faceId][0]

            if numpy.isnan(t):
                t = tConst
            if numpy.isnan(E):
                E = Econst

            S11 = S21 = S22 = S31 = S32 = 0.0
            K11 = E / (1 - v2)
            K12 = (E * v) / (1 - v2)
            K33 = (0.5 * E * (1 - v)) / (1 - v2)
            K44 = (0.5 * k * E * (1 - v)) / (1 - v2)

            swbFile.write(
                '{0} {1} {2} {3} {4} {5} {6} {7} {8} {9} {10}\n'.format(i + 1, t, S11, S21, S22, S31, S32,
                                                                        K11, K12, K33, K44))

    def _writeAnisotropicMaterial(self, bc, faceIndicesInAllExteriorFaces, swbFile, materialStorage, meshData,
                                  solidModelData, vesselForestData):
        thicknessArray = materialStorage.arrays['Thickness'].data
        stiffnessArray = materialStorage.arrays["Young's modulus (anisotropic)"].data
        tConst = bc.getProperties()["Thickness"]
        # SWB file MUST contain information for all exterior faces
        for i in xrange(solidModelData.getNumberOfFaceIdentifiers()):
            faceIdentifier = solidModelData.getFaceIdentifier(i)
            for meshFaceInfo in meshData.getMeshFaceInfoForFace(faceIdentifier):
                globalFaceId = meshFaceInfo[1]
                t = thicknessArray[globalFaceId][0]
                E = stiffnessArray[globalFaceId]

                if numpy.isnan(t):
                    t = tConst
                if numpy.isnan(E[0]):
                    E = [0, 0, 0, 0, 0, 0]

                materialFaceInfo = MaterialFaceInfo(vesselForestData, meshData, faceIdentifier,
                                                    meshFaceInfo)
                coordinateFrame = materialFaceInfo.getVesselPathCoordinateFrame()

                x1 = numpy.array(meshData.getNodeCoordinates(meshFaceInfo[2]))
                x2 = numpy.array(meshData.getNodeCoordinates(meshFaceInfo[3]))
                x3 = numpy.array(meshData.getNodeCoordinates(meshFaceInfo[4]))

                # Face coordinate frame
                v1 = x2 - x1
                v1 /= numpy.linalg.norm(v1)

                v2 = x3 - x1
                v3 = numpy.cross(v1, v2)
                v3 /= numpy.linalg.norm(v3)

                v2 = numpy.cross(v3, v1)

                # 'Membrane' coordinate frame
                e3 = numpy.array(materialFaceInfo.getFaceCenter()) - numpy.array(coordinateFrame[0:3])
                e3 /= numpy.linalg.norm(e3)
                e2 = numpy.array(coordinateFrame[3:6])
                e1 = numpy.cross(e2, e3)
                e1 /= numpy.linalg.norm(e1)
                e3 = numpy.cross(e1, e2)

                # Transformation matrix
                Q = numpy.array([[numpy.dot(v1, e1), numpy.dot(v1, e2), numpy.dot(v1, e3)],
                                 [numpy.dot(v2, e1), numpy.dot(v2, e2), numpy.dot(v2, e3)],
                                 [numpy.dot(v3, e1), numpy.dot(v3, e2), numpy.dot(v3, e3)]])

                tempC = numpy.zeros([3, 3, 3, 3])

                tempC[0, 0, 0, 0] = E[0]  # C_qqqq
                tempC[0, 0, 1, 1] = E[1]  # C_qqzz
                tempC[1, 1, 0, 0] = tempC[0, 0, 1, 1]
                tempC[1, 1, 1, 1] = E[2]  # C_zzzz

                tempC[0, 1, 0, 1] = E[3]  # 0.25 * (C_qzqz+C_qzzq+C_zqzq+C_zqqz)

                tempC[0, 1, 1, 0] = tempC[0, 1, 0, 1]
                tempC[1, 0, 1, 0] = tempC[0, 1, 0, 1]
                tempC[1, 0, 0, 1] = tempC[0, 1, 0, 1]

                tempC[2, 0, 2, 0] = E[4]  # C_rqrq

                tempC[2, 1, 2, 1] = E[5]  # C_rzrz

                tempCrot = numpy.zeros([3, 3, 3, 3])

                # Transform the tensor
                for i in range(3):
                    for j in range(3):
                        for k in range(3):
                            for l in range(3):
                                tempCrot[i, j, k, l] = \
                                    Q[i, 0] * Q[j, 0] * Q[k, 0] * Q[l, 0] * tempC[0, 0, 0, 0] + \
                                    Q[i, 1] * Q[j, 1] * Q[k, 1] * Q[l, 1] * tempC[1, 1, 1, 1] + \
                                    Q[i, 0] * Q[j, 0] * Q[k, 1] * Q[l, 1] * tempC[0, 0, 1, 1] + \
                                    Q[i, 1] * Q[j, 1] * Q[k, 0] * Q[l, 0] * tempC[1, 1, 0, 0] + \
                                    Q[i, 0] * Q[j, 1] * Q[k, 0] * Q[l, 1] * tempC[0, 1, 0, 1] + \
                                    Q[i, 1] * Q[j, 0] * Q[k, 1] * Q[l, 0] * tempC[1, 0, 1, 0] + \
                                    Q[i, 1] * Q[j, 0] * Q[k, 0] * Q[l, 1] * tempC[1, 0, 0, 1] + \
                                    Q[i, 0] * Q[j, 1] * Q[k, 1] * Q[l, 0] * tempC[0, 1, 1, 0] + \
                                    Q[i, 0] * Q[j, 1] * Q[k, 0] * Q[l, 0] * tempC[0, 1, 0, 0] + \
                                    Q[i, 0] * Q[j, 0] * Q[k, 0] * Q[l, 1] * tempC[0, 0, 0, 1] + \
                                    Q[i, 1] * Q[j, 0] * Q[k, 1] * Q[l, 1] * tempC[1, 0, 1, 1] + \
                                    Q[i, 1] * Q[j, 1] * Q[k, 1] * Q[l, 0] * tempC[1, 1, 1, 0] + \
                                    Q[i, 1] * Q[j, 2] * Q[k, 1] * Q[l, 2] * tempC[1, 2, 1, 2] + \
                                    Q[i, 2] * Q[j, 1] * Q[k, 2] * Q[l, 1] * tempC[2, 1, 2, 1] + \
                                    Q[i, 2] * Q[j, 0] * Q[k, 2] * Q[l, 0] * tempC[2, 0, 2, 0] + \
                                    Q[i, 0] * Q[j, 2] * Q[k, 0] * Q[l, 2] * tempC[0, 2, 0, 2] + \
                                    tempCrot[i, j, k, l]

                Kmatrix = numpy.zeros([5, 5])

                Kmatrix[0, 0] = tempCrot[0, 0, 0, 0]
                Kmatrix[0, 1] = tempCrot[0, 0, 1, 1]
                Kmatrix[0, 2] = 0.5 * (tempCrot[0, 0, 0, 1] + tempCrot[0, 0, 1, 0])
                Kmatrix[0, 3] = tempCrot[0, 0, 2, 0]
                Kmatrix[0, 4] = tempCrot[0, 0, 2, 1]

                Kmatrix[1, 0] = tempCrot[1, 1, 0, 0]
                Kmatrix[1, 1] = tempCrot[1, 1, 1, 1]
                Kmatrix[1, 2] = 0.5 * (tempCrot[1, 1, 0, 1] + tempCrot[1, 1, 1, 0])
                Kmatrix[1, 3] = tempCrot[1, 1, 2, 0]
                Kmatrix[1, 4] = tempCrot[1, 1, 2, 1]

                Kmatrix[2, 0] = 0.5 * (tempCrot[0, 1, 0, 0] + tempCrot[1, 0, 0, 0])
                Kmatrix[2, 1] = 0.5 * (tempCrot[0, 1, 1, 1] + tempCrot[1, 0, 1, 1])
                Kmatrix[2, 2] = 0.25 * (tempCrot[0, 1, 0, 1] + tempCrot[0, 1, 1, 0] +
                                        tempCrot[1, 0, 1, 0] + tempCrot[1, 0, 0, 1])
                Kmatrix[2, 3] = 0.5 * (tempCrot[0, 1, 2, 0] + tempCrot[1, 0, 2, 0])
                Kmatrix[2, 4] = 0.5 * (tempCrot[0, 1, 2, 1] + tempCrot[1, 0, 2, 1])

                Kmatrix[3, 0] = tempCrot[2, 0, 0, 0]
                Kmatrix[3, 1] = tempCrot[2, 0, 1, 1]
                Kmatrix[3, 2] = 0.5 * (tempCrot[2, 0, 0, 1] + tempCrot[2, 0, 1, 0])
                Kmatrix[3, 3] = tempCrot[2, 0, 2, 0]
                Kmatrix[3, 4] = tempCrot[2, 0, 2, 1]

                Kmatrix[4, 0] = tempCrot[2, 1, 0, 0]
                Kmatrix[4, 1] = tempCrot[2, 1, 1, 1]
                Kmatrix[4, 2] = 0.5 * (tempCrot[2, 1, 0, 1] + tempCrot[2, 1, 1, 0])
                Kmatrix[4, 3] = tempCrot[2, 1, 2, 0]
                Kmatrix[4, 4] = tempCrot[2, 1, 2, 1]

                swbFile.write(
                    '{0} {1} 0 0 0 0 0 '
                    '{2[0][0]} {2[1][0]} {2[1][1]} '
                    '{2[2][0]} {2[2][1]} {2[2][2]} '
                    '{2[3][0]} {2[3][1]} {2[3][2]} '
                    '{2[3][3]} {2[4][0]} {2[4][1]} '
                    '{2[4][2]} {2[4][3]} {2[4][4]}\n'.format(
                        faceIndicesInAllExteriorFaces.index(meshFaceInfo[1]) + 1, t, Kmatrix))

    def _writeSupreSurfaceIDs(self, faceIndicesAndFileNames, supreFile):
        supreFile.write('set_surface_id all_exterior_faces.ebc 1\n')
        for idAndName in sorted(faceIndicesAndFileNames.viewvalues(), key=lambda x: x[0]):
            supreFile.write('set_surface_id {0[1]}.ebc {0[0]}\n'.format(idAndName))
        supreFile.write('\n')

    def _writeSupreHeader(self, meshData, supreFile):
        supreFile.write('number_of_variables 5\n')
        supreFile.write('number_of_nodes {0}\n'.format(meshData.getNNodes()))
        supreFile.write('number_of_elements {0}\n'.format(meshData.getNElements()))
        supreFile.write('number_of_mesh_edges {0}\n'.format(meshData.getNEdges()))
        supreFile.write('number_of_mesh_faces {0}\n'.format(meshData.getNFaces()))
        supreFile.write('\n')
        supreFile.write('phasta_node_order\n')
        supreFile.write('\n')
        supreFile.write('nodes the.coordinates\n')
        supreFile.write('elements the.connectivity\n')
        supreFile.write('boundary_faces all_exterior_faces.ebc\n')
        supreFile.write('adjacency the.xadj\n')
        supreFile.write('\n')

    def _computeFaceIndicesAndFileNames(self, solidModelData, vesselPathNames):
        faceTypePrefixes = {FaceType.ftCapInflow: 'inflow_',
                            FaceType.ftCapOutflow: 'outflow_',
                            FaceType.ftWall: 'wall_'}

        faceIndicesAndFileNames = {}
        for i in xrange(solidModelData.getNumberOfFaceIdentifiers()):
            faceIdentifier = solidModelData.getFaceIdentifier(i)

            faceIndicesAndFileNames[faceIdentifier] = [-1, faceTypePrefixes[faceIdentifier.faceType] + '_'.join(
                (vesselPathNames.get(vesselPathUID, vesselPathUID).replace(' ', '_') for vesselPathUID in
                 faceIdentifier.parentSolidIndices))]

        faceTypePriority = {FaceType.ftCapInflow: 1, FaceType.ftCapOutflow: 2, FaceType.ftWall: 3}

        def compareWithPriority(l, r):
            if l[0].faceType != r[0].faceType:
                return -1 if faceTypePriority[l[0].faceType] < faceTypePriority[r[0].faceType] else 1
            return -1 if l[1] < r[1] else 1

        for i, kv in enumerate(sorted(faceIndicesAndFileNames.iteritems(),
                                      cmp=compareWithPriority)):
            faceIndicesAndFileNames[kv[0]][0] = i + 2  # 1 is reserved for all_exterior_faces

        return OrderedDict(sorted(faceIndicesAndFileNames.items(), key=lambda t: t[1][0]))

    # Compute materials and return them in form of SolutionStorage
    def computeMaterials(self, materials, vesselForestData, solidModelData, meshData):
        with Timer('Compute materials'):
            solutionStorage = SolutionStorage()

            validFaceIdentifiers = lambda bc: (x for x in bc.faceIdentifiers if
                                               solidModelData.faceIdentifierIndex(x) != -1)

            def getMaterialConstantValue(materialData):
                if materialData.nComponents == 1:
                    return m.getProperties()[materialData.name]
                else:
                    return [m.getProperties()[materialData.name][materialData.componentNames[component]] for component
                            in xrange(materialData.nComponents)]

            for m in materials:
                for materialData in m.materialDatas:
                    if materialData.name not in solutionStorage.arrays:
                        newMat = numpy.zeros((meshData.getNFaces(), materialData.nComponents))
                        newMat[:] = numpy.NAN
                        solutionStorage.arrays[materialData.name] = SolutionStorage.ArrayInfo(newMat,
                                                                                              materialData.componentNames)

                    if materialData.representation == MaterialData.RepresentationType.Table:
                        # sort by argument value, see http://stackoverflow.com/questions/2828059/sorting-arrays-in-numpy-by-column
                        tableData = materialData.tableData.data.transpose()
                        tableData = tableData[tableData[:, 0].argsort()].transpose()
                    elif materialData.representation == MaterialData.RepresentationType.Script:
                        exec compile(materialData.scriptData, 'material {0}'.format(materialData.name),
                                     'exec') in globals(), globals()
                    for faceId in validFaceIdentifiers(m):
                        constantValue = getMaterialConstantValue(materialData)
                        for info in meshData.getMeshFaceInfoForFace(faceId):
                            materialFaceInfo = MaterialFaceInfo(vesselForestData, meshData, faceId, info)

                            if materialData.representation == MaterialData.RepresentationType.Constant:
                                value = constantValue
                            elif materialData.representation == MaterialData.RepresentationType.Table:
                                if materialData.tableData.inputVariableType == MaterialData.InputVariableType.DistanceAlongPath:
                                    x = materialFaceInfo.getArcLength()
                                elif materialData.tableData.inputVariableType == MaterialData.InputVariableType.LocalRadius:
                                    x = materialFaceInfo.getLocalRadius()
                                elif materialData.tableData.inputVariableType == MaterialData.InputVariableType.x:
                                    x = materialFaceInfo.getFaceCenter()[0]
                                elif materialData.tableData.inputVariableType == MaterialData.InputVariableType.y:
                                    x = materialFaceInfo.getFaceCenter()[1]
                                elif materialData.tableData.inputVariableType == MaterialData.InputVariableType.z:
                                    x = materialFaceInfo.getFaceCenter()[2]

                                value = [numpy.interp(x, tableData[0], tableData[component])
                                         for component in xrange(1, materialData.nComponents + 1)]
                            elif materialData.representation == MaterialData.RepresentationType.Script:
                                value = computeMaterialValue(materialFaceInfo)

                            solutionStorage.arrays[materialData.name].data[info[1]] = value
                            #
        return solutionStorage
