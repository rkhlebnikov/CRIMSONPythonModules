from CRIMSONCore.BoundaryCondition import BoundaryCondition
from PythonQt.CRIMSON import FaceType


class InitialPressure(BoundaryCondition):
    unique = True
    humanReadableName = "Initial pressure"
    applicableFaceTypes = []

    def __init__(self):
        BoundaryCondition.__init__(self)
        self.properties = [
            {
                "name": "Initial pressure",
                "value": 13332.0,
                "attributes": {"minimum": 0.0, "suffix": u" g/(mm\u00B7s\u00B2)"}
            },
        ]
