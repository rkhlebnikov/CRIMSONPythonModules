from CRIMSONCore.FaceData import FaceData
from PythonQt.CRIMSON import FaceType

"""
    This is the "do nothing" boundary condition.
    Testing seemed to show that the ability to mark a face as being deliberately unassigned was helpful.
"""
class ConsistentFlux(FaceData):
    unique = False
    humanReadableName = "Consistent Flux"

    # can be applied to any face
    applicableFaceTypes = [FaceType.ftCapInflow, FaceType.ftCapOutflow, FaceType.ftWall]

    def __init__(self):
        FaceData.__init__(self)