from CRIMSONCore.BoundaryCondition import BoundaryCondition
from PythonQt.CRIMSON import FaceType


class ZeroPressure(BoundaryCondition):
    unique = False
    humanReadableName = "Zero pressure"
    applicableFaceTypes = [FaceType.ftCapInflow, FaceType.ftCapOutflow]

    def __init__(self):
        BoundaryCondition.__init__(self)
