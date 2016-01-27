import os
import shutil
import subprocess
import tempfile
from collections import OrderedDict

import numpy

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
    DeformableWall


class SolverStudy(object):
    def __init__(self):
        self.meshNodeUID = ""
        self.solverSetupNodeUID = ""
        self.boundaryConditionSetNodeUIDs = []

    def getMeshNodeUID(self):
        return self.meshNodeUID

    def setMeshNodeUID(self, uid):
        self.meshNodeUID = uid

    def getSolverSetupNodeUID(self):
        return self.solverSetupNodeUID

    def setSolverSetupNodeUID(self, uid):
        self.solverSetupNodeUID = uid

    def getBoundaryConditionSetNodeUIDs(self):
        return self.boundaryConditionSetNodeUIDs

    def setBoundaryConditionSetNodeUIDs(self, uids):
        self.boundaryConditionSetNodeUIDs = uids

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
                    solutions.arrays.append(SolutionStorage.ArrayInfo(fieldName, fieldData.transpose()))

            except Exception as e:
                QtGui.QMessageBox.critical(None, "Solution loading failed",
                                           "Failed to load solution from file {0}:\n{1}.".format(fullName, str(e)))
                continue

        return solutions

    def writeSolverSetup(self, vesselForestData, solidModelData, meshData, solverSetup, boundaryConditions,
                         vesselPathNames, solutionStorage):

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
            solverInpData = SolverInpData(solverSetup, faceIndicesAndFileNames)

            supreFile = fileList[os.path.join('presolver', 'the.supre')]

            self._writeSupreHeader(meshData, supreFile)
            self._writeSupreSurfaceIDs(faceIndicesAndFileNames, supreFile)

            with Timer('Written nbc and ebc files'):
                self._writeNbcEbc(solidModelData, meshData, faceIndicesAndFileNames, fileList)
            with Timer('Written coordinates'):
                self._writeNodeCoordinates(meshData, fileList)
            with Timer('Written connectivity'):
                self._writeConnectivity(meshData, fileList)
            with Timer('Written adjacency'):
                self._writeAdjacency(meshData, fileList)
            with Timer('Written boundary conditions'):
                self._writeBoundaryConditions(solidModelData, meshData, boundaryConditions, faceIndicesAndFileNames,
                                              solverInpData, fileList)

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
            for solution in solutionStorage.arrays:
                arrayDesc, fieldDesc = PhastaConfig.restartConfig.findDescriptorAndField(solution.name)
                if arrayDesc is None:
                    Utils.logWarning(
                        'Cannot write solution \'{0}\' to the restart file. Skipping.'.format(solution.name))
                    continue
                Utils.logInformation('Appending solution data \'{0}\'...'.format(solution.name))

                dataBlocksToReplace.append(arrayDesc.phastaDataBlockName)
                newFields[fieldDesc.name] = solution.data.transpose()

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
        presolverExecutable = os.path.join(os.path.realpath(__file__), os.pardir,
                                           PresolverExecutableName.getPresolverExecutableName())
        Utils.logInformation('Running presolver from ' + presolverExecutable)

        supreDir, supreFileName = os.path.split(supreFile)
        p = subprocess.Popen([presolverExecutable, supreFileName], cwd=supreDir,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        out, _ = p.communicate()
        self._logPresolverOutput(out)

        if p.returncode != 0:
            Utils.logError("Presolver run has failed.")
            return

        try:
            Utils.logInformation("Moving output files to output folder")
            for fName in outputFiles:
                fullName = os.path.join(supreFile, os.path.pardir, fName)
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

        outFileAdjacency.seek(len(xadjString) + 1)  # +1 for potential \r
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
        for faceIdentifier in faceIdentifiers:
            for info in meshData.getMeshFaceInfoForFace(faceIdentifier):
                l = '{0}\n'.format(
                    ' '.join(str(x + 1) for x in info))  # element and node indices are 1-based for presolver
                outputFile.write(l)

    def _writeNbcEbc(self, solidModelData, meshData, faceIndicesAndFileNames, fileList):
        allFaceIdentifiers = [solidModelData.getFaceIdentifier(i) for i in
                              xrange(solidModelData.getNumberOfFaceIdentifiers())]

        # Write wall.nbc
        self._writeNbc(meshData, [id for id in allFaceIdentifiers if id.faceType == FaceType.ftWall],
                       fileList[os.path.join('presolver', 'wall.nbc')])

        # Write all_eterior_faces.ebc
        self._writeEbc(meshData, allFaceIdentifiers, fileList[os.path.join('presolver', 'all_exterior_faces.ebc')])

        # Write per-face-identifier ebc and nbc files
        for i in xrange(solidModelData.getNumberOfFaceIdentifiers()):
            faceIdentifier = solidModelData.getFaceIdentifier(i)

            baseFileName = os.path.join('presolver', faceIndicesAndFileNames[faceIdentifier][1])
            self._writeNbc(meshData, [faceIdentifier], fileList[baseFileName + '.nbc'])
            self._writeEbc(meshData, [faceIdentifier], fileList[baseFileName + '.ebc'])

    def _writeSolverSetup(self, solverInpData, fileList):
        solverInpFile = fileList['solver.inp', 'wb']

        for category, values in sorted(solverInpData.data.iteritems()):
            solverInpFile.write('\n\n# {0}\n# {{\n'.format(category))
            for kv in values.iteritems():
                solverInpFile.write('    {0[0]} : {0[1]}\n'.format(kv))
            solverInpFile.write('# }\n')

    def _validateBoundaryConditions(self, boundaryConditions):
        # Check unique BC's
        bcByType = {}
        for bc in boundaryConditions:
            bcByType.setdefault(bc.__class__.__name__, []).append(bc)

        hadError = False

        for bcType, bcs in bcByType.iteritems():
            if bcs[0].unique and len(bcs) > 1:
                Utils.logError(
                    'Multiple instances of foundary condition {0} are not allowed in a single study'.format(bcType))
                hadError = True

        return not hadError

    def _writeBoundaryConditions(self, solidModelData, meshData, boundaryConditions, faceIndicesAndFileNames,
                                 solverInpData, fileList):
        if not self._validateBoundaryConditions(boundaryConditions):
            raise RuntimeError('Invalid boundary conditions. Aborting.')

        supreFile = fileList[os.path.join('presolver', 'the.supre')]

        class RCRInfo(object):
            def __init__(self):
                self.first = True
                self.faceIds = []

        rcrInfo = RCRInfo()

        class BCTInfo(object):
            def __init__(self):
                self.first = True
                self.totalPoints = 0
                self.maxNTimeSteps = 0
                self.faceIds = []

        bctInfo = BCTInfo()

        validFaceIdentifiers = lambda bc: (x for x in bc.faceIdentifiers if
                                           solidModelData.faceIdentifierIndex(x) != -1)

        is_boundary_condition_type = lambda bc, bcclass: bc.__class__.__name__ == bcclass.__name__

        initialPressure = 13332

        # Processing priority for a particular BC type defines the order of processing the BCs
        # Default value is assumed to be 1. The higher the priority, the later the BC is processed
        bcProcessingPriorities = {DeformableWall.DeformableWall.__name__: 2}
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
                                   '1.1 0.0\n'.format(bc.getProperties()))
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
                # Write the ebc for deformable wall
                self._writeEbc(meshData, validFaceIdentifiers(bc),
                               fileList[os.path.join('presolver', 'deformable_wall.ebc')])

                shearConstant = 0.8333333

                supreFile.write('deformable_wall deformable_wall.ebc\n')
                supreFile.write('fix_free_edge_nodes deformable_wall.ebc\n')
                supreFile.write('number_of_wall_Props 10\n')
                supreFile.write('deformable_create_mesh deformable_wall.ebc\n')
                supreFile.write('deformable_write_feap inputdataformatlab.dat\n')
                supreFile.write('deformable_pressure {0}\n'.format(initialPressure))
                supreFile.write('deformable_Evw {0}\n'.format(bc.getProperties()["Young's modulus"]))
                supreFile.write('deformable_nuvw {0}\n'.format(bc.getProperties()["Poisson ratio"]))
                supreFile.write('deformable_thickness {0}\n'.format(bc.getProperties()["Thickness"]))
                supreFile.write('deformable_kcons {0}\n'.format(shearConstant))
                supreFile.write('deformable_solve\n\n')

                deformableGroup = solverInpData['DEFORMABLE WALL PARAMETERS']
                deformableGroup['Deformable Wall'] = True
                deformableGroup['Density of Vessel Wall'] = bc.getProperties()["Density"]
                deformableGroup['Thickness of Vessel Wall'] = bc.getProperties()["Thickness"]
                deformableGroup['Young Mod of Vessel Wall'] = bc.getProperties()["Young's modulus"]
                deformableGroup['Poisson Ratio of Vessel Wall'] = bc.getProperties()["Poisson ratio"]
                deformableGroup['Shear Constant of Vessel Wall'] = shearConstant
                deformableGroup['Number of Wall Properties per Node'] = 10

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

        # Finalize
        if not rcrInfo.first:
            rcrGroup = solverInpData['CARDIOVASCULAR MODELING PARAMETERS: RCR']
            rcrGroup['RCR Values From File'] = True
            rcrGroup['Number of RCR Surfaces'] = len(rcrInfo.faceIds)
            rcrGroup['List of RCR Surfaces'] = ' '.join(rcrInfo.faceIds)

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

        faceTypePriority = {FaceType.ftWall: 1, FaceType.ftCapInflow: 2, FaceType.ftCapOutflow: 3}

        def compareWithPriority(l, r):
            if l[0].faceType != r[0].faceType:
                return -1 if faceTypePriority[l[0].faceType] < faceTypePriority[r[0].faceType] else 1
            return -1 if l[1] < r[1] else 1

        for i, kv in enumerate(sorted(faceIndicesAndFileNames.iteritems(),
                                      cmp=compareWithPriority)):
            faceIndicesAndFileNames[kv[0]][0] = i + 2  # 1 is reserved for all_exterior_faces

        return OrderedDict(sorted(faceIndicesAndFileNames.items(), key=lambda t: t[1][0]))
