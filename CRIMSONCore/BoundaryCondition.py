from CRIMSONCore.PropertyStorage import PropertyStorage


class BoundaryCondition(PropertyStorage):
    '''
    Base class for all boundary conditions.

    In addition to having the functionality of a :mod:`PropertyStorage <CRIMSONCore.PropertyStorage>`, the boundary condition
    also stores a list of :mod:`face identifiers <CRIMSONCore.FaceIdentifier>` stored in ``BoundaryCondition.faceIdentifiers``
    which are filled by the C++ code through user interaction.

    '''
    def __init__(self):
        PropertyStorage.__init__(self)
        self.faceIdentifiers = []

    def setFaceIdentifiers(self, faceIdentifiers):  # for use in CPP code
        self.faceIdentifiers = faceIdentifiers

    def getFaceIdentifiers(self):  # for use in CPP code
        return self.faceIdentifiers