from CRIMSONCore.FaceData import FaceData
from PythonQt.CRIMSON import FaceType

# Scalar no flux boundary condition (equivalent of No Slip but for scalar)
class NoFlux(FaceData):
    unique = False
    humanReadableName = "No flux"
    applicableFaceTypes = [FaceType.ftWall]

    def __init__(self):
        FaceData.__init__(self)
