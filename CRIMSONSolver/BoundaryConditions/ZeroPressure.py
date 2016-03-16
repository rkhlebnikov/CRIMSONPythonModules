from CRIMSONCore.FaceData import FaceData
from PythonQt.CRIMSON import FaceType


class ZeroPressure(FaceData):
    unique = False
    humanReadableName = "Zero pressure"
    applicableFaceTypes = [FaceType.ftCapInflow, FaceType.ftCapOutflow]

    def __init__(self):
        FaceData.__init__(self)
