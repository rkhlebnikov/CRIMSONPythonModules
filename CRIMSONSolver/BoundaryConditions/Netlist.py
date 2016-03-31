from CRIMSONCore.FaceData import FaceData
from PythonQt.CRIMSON import FaceType

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