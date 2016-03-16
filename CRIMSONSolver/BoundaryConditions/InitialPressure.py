from CRIMSONCore.FaceData import FaceData
from PythonQt.CRIMSON import FaceType


class InitialPressure(FaceData):
    unique = True
    humanReadableName = "Initial pressure"
    applicableFaceTypes = []

    def __init__(self):
        FaceData.__init__(self)
        self.properties = [
            {
                "Initial pressure": 13332.0,
                "attributes": {"minimum": 0.0, "suffix": u" g/(mm\u00B7s\u00B2)"}
            },
        ]
