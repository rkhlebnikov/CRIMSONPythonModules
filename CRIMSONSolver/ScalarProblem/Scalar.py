from CRIMSONCore.PropertyStorage import PropertyStorage
from CRIMSONSolver.ScalarProblem.ScalarBC import ScalarBC


class Scalar(PropertyStorage):
    '''
    Base class for all face-attached data classes (e.g. boundary conditions and materials).

    In addition to having the functionality of a :mod:`PropertyStorage <CRIMSONCore.PropertyStorage>`, the face data
    also stores a list of :mod:`face identifiers <CRIMSONCore.FaceIdentifier>` stored in ``FaceData.faceIdentifiers``
    which are filled by the C++ code through user interaction.

    '''
    def __init__(self):
        PropertyStorage.__init__(self)
        self.BCs = {}
        self.properties = [
            {
                "Initial value": 0.0
            },
            {
                "Diffusion coefficient": 0.0
            }
        ]

    def setBC(self, faceIdentifier, scalarBC):  # for use in CPP code
        self.BCs[faceIdentifier] = scalarBC

    def getBC(self, faceIdentifier):  # for use in CPP code
        return self.BCs[faceIdentifier]