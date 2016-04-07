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
        self.netlistSurfacesDat = ''

    def createCustomEditorWidget(self):
        if not self.editor:
            self.editor = NetlistEditor(self)
        return self.editor.getEditorWidget()

    def __getstate__(self):
        odict = self.__dict__.copy()  # copy the dict
        del odict['editor']  # editor shouldn't be pickled
        return odict

    def __setstate__(self, dict):
        self.__dict__.update(dict)
        self.editor = None  # Reload classes on un-pickling