from CRIMSONCore.BoundaryCondition import BoundaryCondition
from PythonQt.CRIMSON import FaceType

class RCR(BoundaryCondition):
    unique = False
    humanReadableName = "RCR"
    applicableFaceTypes = [FaceType.ftCapInflow, FaceType.ftCapOutflow]

    def __init__(self):
        BoundaryCondition.__init__(self)
        resistancePropertyAttributes = {"suffix": u" g/(mm\u2074\u00B7s)", "minimum": 0.0}
        capacitancePropertyAttributes = {"suffix": u" mm\u2074\u00B7s\u00B2/g", "minimum": 0.0}
        self.properties = [
            {
                "Proximal resistance": 100.0,
                "attributes": resistancePropertyAttributes
            },
            {
                "Capacitance": 1e-5,
                "attributes": capacitancePropertyAttributes
            },
            {
                "Distal resistance": 1000.0,
                "attributes": resistancePropertyAttributes
            }
        ]