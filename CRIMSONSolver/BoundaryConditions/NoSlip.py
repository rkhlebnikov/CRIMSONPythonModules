from CRIMSONCore.BoundaryCondition import BoundaryCondition
from PythonQt.CRIMSON import FaceType


class NoSlip(BoundaryCondition):
    unique = False
    humanReadableName = "No slip"
    applicableFaceTypes = [FaceType.ftWall]

    def __init__(self):
        BoundaryCondition.__init__(self)
