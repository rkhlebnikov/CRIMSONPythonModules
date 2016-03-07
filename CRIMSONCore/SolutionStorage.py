import numpy
from PythonQt.CRIMSON import ArrayDataType
from PythonQt.QtCore import QByteArray

class SolutionStorage(object):
    '''
    TODO: Update!
    SolutionStorage class is used to pass the loaded solution data to the C++ code.
    The arrays data member is a dict mapping name of the data array, e.g. 'velocity' or 'pressure',
    to the data itself in form of a 2D numpy.ndarray
    Allowed data types for the data are numpy.int32 and numpy.float64
    '''

    def __init__(self, arrays=None):
        self.arrays = {} if arrays is None else arrays
        self._buffers = {}

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
        name = self.getArrayName(i)
        if name not in self._buffers:
            data =  self.arrays.items()[i][1]
            shape = data.shape
            buf = numpy.getbuffer(data if len(shape) == 1 else data.reshape((shape[0] * shape[1])))
            ba = QByteArray()
            ba.reserve(len(buf))
            ba.append(str(buf), len(buf))
            self._buffers[name] = ba

        return self._buffers[name]

