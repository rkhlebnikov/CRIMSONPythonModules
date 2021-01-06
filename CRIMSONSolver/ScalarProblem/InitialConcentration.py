from CRIMSONCore.FaceData import FaceData
from PythonQt.CRIMSON import FaceType

# Note that this boundary condition is uniform throughout the entire solid, there is no need to select faces for this.
class InitialConcentration(FaceData):
    unique = False
    humanReadableName = "Initial Concentration"
    applicableFaceTypes = []

    def __init__(self):
        FaceData.__init__(self)
        self.properties = [
            {
                "concentration": 0.0,
                #"attributes": {
                # TODO: What should the suffix be?
                #"suffix": u" g/(mm\u00B7s\u00B2)"
                #    }
            },
        ]
