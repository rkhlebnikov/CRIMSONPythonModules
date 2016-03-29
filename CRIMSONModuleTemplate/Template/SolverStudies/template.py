from PythonQt import QtGui
from PythonQt.CRIMSON import FaceType
from PythonQt.CRIMSON import Utils

from CRIMSONCore.SolutionStorage import SolutionStorage
from {{ModuleName}}.BoundaryConditions import ({{#BoundaryConditionNames}}{{name}}, {{/BoundaryConditionNames}})

class {{ClassName}}(object):
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
        return self.materialNodeUIDs

    def setMaterialNodeUIDs(self, uids):
        self.materialNodeUIDs = uids

    def loadSolution(self):
        # Implement if needed - see documentation
        pass

    def writeSolverSetup(self, vesselForestData, solidModelData, meshData, solverParameters, boundaryConditions,
                         materials, vesselPathNames, solutionStorage):
        # Get the output folder 
        outputDir = QtGui.QFileDialog.getExistingDirectory(None, 'Select output folder')

        if not outputDir:
            return

        # Write the files for your solver. See documentation for details
        raise NotImplementedError()