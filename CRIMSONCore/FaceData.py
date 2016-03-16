from CRIMSONCore.PropertyStorage import PropertyStorage


class FaceData(PropertyStorage):
    '''
    Base class for all face-attached data classes (e.g. boundary conditions and materials).

    In addition to having the functionality of a :mod:`PropertyStorage <CRIMSONCore.PropertyStorage>`, the face data
    also stores a list of :mod:`face identifiers <CRIMSONCore.FaceIdentifier>` stored in ``FaceData.faceIdentifiers``
    which are filled by the C++ code through user interaction.

    '''
    def __init__(self):
        PropertyStorage.__init__(self)
        self.faceIdentifiers = []

    def setFaceIdentifiers(self, faceIdentifiers):  # for use in CPP code
        self.faceIdentifiers = faceIdentifiers

    def getFaceIdentifiers(self):  # for use in CPP code
        return self.faceIdentifiers