import numpy

from CRIMSONCore.FaceData import FaceData

from PythonQt.CRIMSON import FaceType

class PCMRI(FaceData):
    '''
    This boundary condition is in fact a python object wrapper for a BC object that is entirely C++ based. The true BC object is passed
    to the python BC using the setDataObject method. All of the BC logic and GUI initialization are done in the C++ code.

    '''
    unique = False
    humanReadableName = "PCMRI"
    applicableFaceTypes = [FaceType.ftCapInflow, FaceType.ftCapOutflow]

    def __init__(self):
        FaceData.__init__(self)

        self.originalWaveform = numpy.array([])
        self.smoothedWaveform = numpy.array([])
        self.firstFilteredCoef = 0
        self.numberOfSamples = 100
        self.pcmriNodeUID=None
        self.pcmriData=None

def setDataObject(self, data):  # for use in CPP code
        self.pcmriData = data

def setDataNodeUID(self, uid):  # for use in CPP code
        self.pcmriNodeUID = uid

def getDataNodeUID(self):  # for use in CPP code
        return self.pcmriNodeUID