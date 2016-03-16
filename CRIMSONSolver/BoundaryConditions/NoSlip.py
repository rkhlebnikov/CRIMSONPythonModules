from CRIMSONCore.FaceData import FaceData
from PythonQt.CRIMSON import FaceType


class NoSlip(FaceData):
    unique = False
    humanReadableName = "No slip"
    applicableFaceTypes = [FaceType.ftWall]

    def __init__(self):
        FaceData.__init__(self)
