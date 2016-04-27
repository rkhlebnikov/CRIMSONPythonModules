from CRIMSONCore.FaceData import FaceData
from PythonQt.CRIMSON import FaceType
from CRIMSONSolver.BoundaryConditions.NetlistEditor import NetlistEditor
from PythonQt.CRIMSON import Utils

class Netlist(FaceData):
    unique = False
    humanReadableName = "Netlist"
    applicableFaceTypes = [FaceType.ftCapInflow, FaceType.ftCapOutflow]

    def __init__(self):
        FaceData.__init__(self)
        self.properties = [
            # Add properties here
            {
                "Heart model": False,
            }
        ]

        self.editor = None
        self.netlistSurfacesDatFileName = ''
        self.netlistSurfacesDat = ''
        self.circuitDynamicAdjustmentFiles = {}
        self.circuitAdditionalDataFiles = {}
        self.circuitDescriptionFileRemover = None

    def createCustomEditorWidget(self):
        if not self.editor:
            self.editor = NetlistEditor(self)
        return self.editor.getEditorWidget()

    def addDynamicAdjusterFile(self, fileName, fileContents):
        fileNameWasAlreadyKnown = self.circuitDynamicAdjustmentFiles.__contains__(fileName)
        self.circuitDynamicAdjustmentFiles[fileName] = fileContents
        return fileNameWasAlreadyKnown

    def addAdditionalDataFile(self, fileName, fileContents):
        fileNameWasAlreadyKnown = self.circuitAdditionalDataFiles.__contains__(fileName)
        self.circuitAdditionalDataFiles[fileName] = fileContents
        return fileNameWasAlreadyKnown

    def addCircuitFile(self, fileName, fileContents):
        if self.circuitDescriptionFileRemover:
            self.circuitDescriptionFileRemover()
        self.netlistSurfacesDatFileName = fileName
        self.netlistSurfacesDat = fileContents

    def getFile(self, fileName):
        if self.circuitDynamicAdjustmentFiles.__contains__(fileName):
            fileContents = self.circuitDynamicAdjustmentFiles[fileName]
        elif self.netlistSurfacesDatFileName == fileName:
            fileContents = self.netlistSurfacesDat
        elif self.circuitAdditionalDataFiles. __contains__(fileName):
            fileContents = self.circuitAdditionalDataFiles[fileName]
        else:
            # error: unknown file. should never reach here.
            Utils.logWarning('Attempted to process unknown file \'{0}\'. Skipping.'.format(fileName))
            fileContents = None

        return fileContents

    def getCircuitDynamicAdjustmentFiles(self):
        return self.circuitDynamicAdjustmentFiles

    def getCircuitAdditionalDataFiles(self):
        return self.circuitAdditionalDataFiles

    def getNetlistCircuitFileName(self):
        return self.netlistSurfacesDatFileName

    def removeFile(self, fileName):
        if fileName in self.circuitDynamicAdjustmentFiles:
            del self.circuitDynamicAdjustmentFiles[fileName]
        elif self.netlistSurfacesDatFileName == fileName:
            self.netlistSurfacesDat = ''
            self.netlistSurfacesDatFileName = ''
        elif fileName in self.circuitAdditionalDataFiles:
            del self.circuitAdditionalDataFiles[fileName]
        else:
            # error: unknown file. should never reach here.
            Utils.logWarning('Attempted to remove unknown file \'{0}\'. Skipping.'.format(fileName))

    def setCircuitDescriptionFileRemover(self, fileRemover):
        self.circuitDescriptionFileRemover = fileRemover

    def __getstate__(self):
        odict = self.__dict__.copy()  # copy the dict
        del odict['editor']  # editor shouldn't be pickled
        del odict['circuitDescriptionFileRemover']
        return odict

    def __setstate__(self, dict):
        self.__dict__.update(dict)
        self.editor = None  # Reload classes on un-pickling
        self.circuitDescriptionFileRemover = None