from CRIMSONCore.FaceData import FaceData
from PythonQt.CRIMSON import FaceType


class ScalarNeumann(FaceData):
    unique = False
    humanReadableName = "Scalar Neumann Boundary Condition"
    applicableFaceTypes = [FaceType.ftCapInflow, FaceType.ftCapOutflow]

    def __init__(self):
        FaceData.__init__(self)
        self.properties = [
            {
                "value": 0.0,
                "attributes": {
                    #superscript four
                    "suffix": u" mol/mm\u2074)"
                }
            },
        ]
