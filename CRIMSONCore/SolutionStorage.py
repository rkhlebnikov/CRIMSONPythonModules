import numpy
from PythonQt.CRIMSON import ArrayDataType

class SolutionStorage(object):
    '''
    SolutionStorage class is used to pass the loaded solution data to the C++ code.
    The arrays data members should be filled with instances of SolutionStorage.ArrayInfo class.
    SolutionStorage.ArrayInfo contains a name of the data array, e.g. 'velocity' or 'pressure',
    as well as the data itself in form of a 2D numpy.ndarray
    Allowed data types for the data are numpy.int32 and numpy.float64
    '''

    class ArrayInfo(object):
        '''
        A convenience class for storing the solution name (string) and data (numpy.ndarray).
        '''
        def __init__(self, name, data):
            assert(isinstance(name, basestring))
            assert(isinstance(data, numpy.ndarray))
            assert(len(data.shape) <= 2)
            assert(data.dtype.type is numpy.float64 or data.dtype.type is numpy.int32)
            self.name = name
            self.data = data

    def __init__(self, arrays=None):
        self.arrays = [] if arrays is None else arrays

    def getNArrays(self):
        return len(self.arrays)

    def getArrayName(self, i):
        return self.arrays[i].name

    def getArrayNComponents(self, i):
        shape = self.arrays[i].data.shape
        return shape[1] if len(shape) > 1 else 1

    def getArrayNTuples(self, i):
        return self.arrays[i].data.shape[0]

    def getArrayDataType(self, i):
        return ArrayDataType.Double if self.arrays[i].data.dtype.type is numpy.float64 else ArrayDataType.Int

    def getArrayData(self, i):
        shape = self.arrays[i].data.shape
        return self.arrays[i].data if len(shape) == 1 else self.arrays[i].data.reshape((shape[0] * shape[1]))

