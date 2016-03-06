import numpy
from PythonQt.CRIMSON import ArrayDataType

class SolutionStorage(object):
    '''
    TODO: Update!
    SolutionStorage class is used to pass the loaded solution data to the C++ code.
    The arrays data members should be filled with instances of SolutionStorage.ArrayInfo class.
    SolutionStorage.ArrayInfo contains a name of the data array, e.g. 'velocity' or 'pressure',
    as well as the data itself in form of a 2D numpy.ndarray
    Allowed data types for the data are numpy.int32 and numpy.float64
    '''

    def __init__(self, arrays=None):
        self.arrays = {} if arrays is None else arrays

    def getNArrays(self):
        return len(self.arrays)

    def getArrayName(self, i):
        return self.arrays.items()[i][0]

    def getArrayNComponents(self, i):
        shape = self.arrays.items()[i][1].shape
        return shape[1] if len(shape) > 1 else 1

    def getArrayNTuples(self, i):
        return self.arrays.items()[i][1].shape[0]

    def getArrayDataType(self, i):
        return ArrayDataType.Double if self.arrays.items()[i][1].dtype.type is numpy.float64 else ArrayDataType.Int

    def getArrayData(self, i):
        data =  self.arrays.items()[i][1]
        shape = data.shape
        return data if len(shape) == 1 else data.reshape((shape[0] * shape[1]))

