from CRIMSONCore.FaceData import FaceData
from PythonQt.CRIMSON import FaceType
from CRIMSONSolver.BoundaryConditions.NetlistEditor import NetlistEditor

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
        self.circuitDescriptionFileRemover = None

    def createCustomEditorWidget(self):
        if not self.editor:
            self.editor = NetlistEditor(self)
        return self.editor.getEditorWidget()

    def addDynamicAdjusterFile(self, fileName, fileContents):
        self.circuitDynamicAdjustmentFiles[fileName] = fileContents

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
        else:
            # error: unknown file. should never reach here.
            fileContents = None

        return fileContents

    def getCircuitDynamicAdjustmentFiles(self):
        return self.circuitDynamicAdjustmentFiles

    def getNetlistCircuitFileName(self):
        return self.netlistSurfacesDatFileName

    def removeFile(self, fileName):
        if self.circuitDynamicAdjustmentFiles.__contains__(fileName):
            del self.circuitDynamicAdjustmentFiles[fileName]
            print "removeFile 1 in Netlist.py: " + fileName
        elif self.netlistSurfacesDatFileName == fileName:
            self.netlistSurfacesDat = ''
            self.netlistSurfacesDatFileName = ''
            print "removeFile 2 in Netlist.py: " + fileName
        else:
            print "No such file to remove: " + fileName

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