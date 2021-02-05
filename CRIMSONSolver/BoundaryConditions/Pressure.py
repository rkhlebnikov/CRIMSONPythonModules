from CRIMSONCore.FaceData import FaceData
from PythonQt.CRIMSON import FaceType

"""
    Pressure applied at the inlet/outlet faces
"""
class Pressure(FaceData):
    unique = False
    humanReadableName = "Pressure"
    applicableFaceTypes = [FaceType.ftCapInflow, FaceType.ftCapOutflow]

    def __init__(self):
        FaceData.__init__(self)
        self.properties = [
            {
                "Pressure": 13332.0,
                "attributes": {"minimum": 0.0, "suffix": u" g/(mm\u00B7s\u00B2)"}
            },
        ]