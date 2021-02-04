from CRIMSONCore.FaceData import FaceData
from PythonQt.CRIMSON import FaceType


class ScalarDirichlet(FaceData):
    unique = False
    humanReadableName = "Scalar Dirichlet Boundary Condition"
    applicableFaceTypes = [FaceType.ftCapInflow, FaceType.ftCapOutflow]

    def __init__(self):
        FaceData.__init__(self)
        self.properties = [
            {
                "value": 0.0,
                "attributes": 
                {
                    #\u00B3 is Superscript three
                    "suffix": u" mol/mm\u00B3"
                }
            },
        ]
