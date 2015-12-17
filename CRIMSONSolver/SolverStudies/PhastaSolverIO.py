import numpy
import parse
import sys
import operator


class PhastaIO:
    ByteOrderMagicNumber = 362436


def _checkFileOpenInBinaryMode(file, mode):
    try:
        file.mode
    except:
        return

    for c in mode:
        if file.mode.find(mode) == -1:
            raise IOError('The file for phasta io should be read/write binary. Received {0}.'.format(file.mode))

class PhastaRawFileReader(object):
    class DataBlockDescriptor(object):
        def __init__(self):
            self.posInFile = 0
            self.totalBytes = 0
            self.headerElements = []
            self.rawData = None

    def __init__(self, file):
        _checkFileOpenInBinaryMode(file, 'rb')
        self.file = file
        self.blockDescriptors = {}
        self.byteOrderCode = '='
        self.parseHeaders()
        self.detectEndiannes()

    def parseHeaders(self):
        headerParser = parse.compile("{name} : < {totalBytes} > {tail}")
        while True:
            l = self.file.readline()
            if not l:
                break

            if l.startswith('#') or l.startswith('\n'):
                continue

            parseResult = headerParser.parse(l)
            if parseResult is None:
                raise IOError('Failed to parse string {0}'.format(l))

            dataBlockDescriptor = PhastaRawFileReader.DataBlockDescriptor()
            dataBlockDescriptor.posInFile = self.file.tell()
            dataBlockDescriptor.totalBytes = int(parseResult.named['totalBytes']) - 1
            dataBlockDescriptor.headerElements = [int(x) for x in parseResult.named['tail'].split()]

            self.blockDescriptors[parseResult.named['name'].strip()] = dataBlockDescriptor
            self.file.seek(dataBlockDescriptor.totalBytes + 1, 1)

    def detectEndiannes(self):
        byteOrderArrayName = 'byteorder magic number'
        byteOrderExpectedValue = PhastaIO.ByteOrderMagicNumber

        if byteOrderArrayName not in self.blockDescriptors:
            return

        magicNumber = self.getDataBlock(byteOrderArrayName, numpy.int32)
        if magicNumber[0] != byteOrderExpectedValue:
            sys_is_le = sys.byteorder == 'little'
            self.byteOrderCode = sys_is_le and '>' or '<'
            magicNumber = self.getDataBlock(byteOrderArrayName, numpy.int32)
            if magicNumber[0] != byteOrderExpectedValue:
                raise RuntimeError('Failed to detect endianness')

    def getBlockDescriptor(self, dataBlockName):
        return self.blockDescriptors[dataBlockName]

    def getRawData(self, dataBlockName):
        '''
        Get raw data for the data block.
        :param dataBlockName: name of the data block
        :return: 1d numpy.ndarray of numpy.byte
        '''
        blockDescriptor = self.blockDescriptors[dataBlockName]

        if blockDescriptor.rawData is not None:
            return blockDescriptor.rawData

        if blockDescriptor.totalBytes == -1:
            raise KeyError('Block {0} has no data'.format(dataBlockName))

        self.file.seek(blockDescriptor.posInFile)
        blockDescriptor.rawData = numpy.fromfile(self.file, dtype=numpy.byte, count=blockDescriptor.totalBytes)

        return blockDescriptor.rawData

    def getDataBlock(self, dataBlockName, dtype):
        '''
        Reinterpret the raw data for 'dataBlockName' as an array of particular type.
        :param dataBlockName: name of the data block
        :param dtype: they numpy data type (e.g. 'i4' or numpy.float64)
        :return: 2d numpy.ndarray. The arrays's first dimension is component, i.e. arrayData[1,:] means 'quantity's component 1 for all nodes'

        Raises KeyError if data block named 'dataBlockName' does not exist or it's header-only block (i.e. totalBytes == -1)
        '''

        rawData = self.getRawData(dataBlockName)

        blockDescriptor = self.blockDescriptors[dataBlockName]

        element_dtype = numpy.dtype(dtype).newbyteorder(self.byteOrderCode)

        # Number of arrayelements is expected to be the first element in the header
        numberOfElements = blockDescriptor.headerElements[0]

        bytesPerComponent = element_dtype.itemsize * numberOfElements
        if blockDescriptor.totalBytes % bytesPerComponent != 0:
            raise RuntimeError(
                'Data block \'{0}\' cannot be interpreted as an array of components, '
                'each with number of elements {1} of type {2}'.format(
                    dataBlockName, numberOfElements, dtype))

        numberOfComponents = blockDescriptor.totalBytes / bytesPerComponent

        if numberOfComponents > 1:
            if len(blockDescriptor.headerElements) < 2 or numberOfComponents != blockDescriptor.headerElements[1]:
                raise RuntimeError(
                    'Computed number of components ({0}) is inconsistent '
                    'with expected number of components saved in header ({1}) for data block \'{2}\''.format(
                        numberOfComponents, blockDescriptor.headerElements[1], dataBlockName))

        # Each component is stored in a contiguous array
        array_dtype = numpy.dtype('{0}{1}'.format(numberOfElements, element_dtype.str))

        return numpy.frombuffer(rawData, dtype=array_dtype, count=numberOfComponents)

class PhastaRawFileWriter(object):
    '''
    Writer for phasta data files
    If 'append' is False (default), the header containing the byte order magic number will be automatically written to the file
    '''

    def __init__(self, file):
        _checkFileOpenInBinaryMode(file, 'wb')
        self.file = file

    def writeFileHeader(self):
        self.file.write('''# PHASTA Input File Version 2.0
# Byte Order Magic Number : {0}
# Output generated by PhastaSolverIO.py:
'''.format(PhastaIO.ByteOrderMagicNumber))
        # Write byteorder magic number
        self.writeDataBlock('byteorder magic number', numpy.array([[PhastaIO.ByteOrderMagicNumber]], numpy.int32))

    def writeHeader(self, name, totalBytes, additionalHeaderData=None):
        '''
        This function writes only a header.
        To write a data block, use writeDataBlock(), which will write the correct header internally.
        '''
        self.file.write('{0} : < {1} >'.format(name, totalBytes))

        if additionalHeaderData is not None:
            for headerItem in additionalHeaderData:
                self.file.write(' ')
                self.file.write(str(headerItem))

        self.file.write('\n')

    def writeRawData(self, name, rawData, additionalHeaderData=None):
        '''
        Write raw data represented as 1d array of numpy.byte to phasta file.
        The header will have the form 'name : < totalBytesInArray > [additionalHeaderData...]'
        :param name: data block name
        :param rawData: 1d numpy.ndarray of numpy.byte
        :param additionalHeaderData: must be a sequence or None
        '''
        self.writeHeader(name, rawData.shape[0] + 1, additionalHeaderData) # + 1 for '\n'

        rawData.tofile(self.file)
        self.file.write('\n')


    def writeDataBlock(self, name, arrayData, additionalHeaderData=None):
        '''
        Write a numpy array to phasta file.
        The header will have the form 'name : < totalBytesInArray > numberOfElements [numberOfComponents] [additionalHeaderData...]'
        :param name: data block name
        :param arrayData: 2d numpy.ndarray. The arrayData's first dimension is component, i.e. arrayData[1,:] means 'quantity's component 1 for all nodes'
        :param additionalHeaderData: must be a sequence or None
        numberOfComponents will be written to header only if it is more than 1
        '''
        assert (isinstance(arrayData, numpy.ndarray) and 0 < len(arrayData.shape) <= 2)

        headerData = [arrayData.shape[1]]
        if arrayData.shape[0] > 1:
            headerData.append(arrayData.shape[0])
        if additionalHeaderData is not None:
            headerData += additionalHeaderData

        # Write data
        rawData = numpy.frombuffer(arrayData, dtype=numpy.byte)
        self.writeRawData(name, rawData, headerData)


def _extractFieldFromDataBlock(dataBlock, startIndex, nComponents):
    return dataBlock[startIndex:(startIndex + nComponents), :]

def _embedFieldToDataBlock(dataBlock, fieldData, startIndex, nComponents):
    dataBlock[startIndex:(startIndex + nComponents), :] = fieldData

def readPhastaFile(rawReader, config):
    '''
    Read a phasta file using a configuration which defines conversion from raw data blocks to data fields
    :param rawReader: instance of PhastaRawFileReader
    :param config: configuration (instance of PhastaConfig)
    :return: a dictionary {'field name': numpy.ndarray}.
    The returned 2d arrays' first dimension is (usually node) index
    '''
    result = {}
    for arrayDesc in config.arrayDescriptors:
        try:
            dataBlock = rawReader.getDataBlock(arrayDesc.phastaDataBlockName, arrayDesc.dataType)
        except KeyError:
            if not arrayDesc.optional:
                raise KeyError(
                    'A non-optional data block {0} not found in phasta file {1}'.format(arrayDesc.phastaDataBlockName,
                                                                                        rawReader.file.name))
            else:
                continue

        for field in (f for f in arrayDesc.fields if f.name is not None):
            result[field.name] = _extractFieldFromDataBlock(dataBlock, field.startIndex, field.nComponents)

    return result


def writePhastaFile(rawWriter, config, fields):
    '''
    Write a phasta file using a configuration which defines conversion from raw data blocks to data fields
    :param rawWriter: instance of PhastaRawFileWriter
    :param config: configuration (instance of PhastaConfig). If no fields for a particular data block are provided, the data block will be skipped
    :param fields: a dictionary {'field name': numpy.ndarray}.
    '''

    descriptorToFieldsMap = {}

    for fieldName, fieldData in fields.iteritems():
        arrayDesc, fieldDesc = config.findDescriptorAndField(fieldName)
        if arrayDesc is None:
            raise KeyError('Array descriptor for field {0} was not found'.format(fieldName))

        descriptorToFieldsMap.setdefault(arrayDesc, {})[fieldDesc] = fieldData

    for arrayDesc in (x for x in config.arrayDescriptors if x in descriptorToFieldsMap):
        # Compose the full data back from fields
        totalNComponents = reduce(max, [f.startIndex + f.nComponents for f in arrayDesc.fields], 0)

        fieldsForThisArray = descriptorToFieldsMap[arrayDesc]

        firstFieldData = fieldsForThisArray.itervalues().next()
        numElements = firstFieldData.shape[1]

        # Allocate storage for all fields
        dataBlockShape = [totalNComponents, numElements]
        dataBlock = numpy.zeros(dataBlockShape, arrayDesc.dataType)

        for fieldDesc, fieldData in fieldsForThisArray.iteritems():
            # Sanity checks
            if fieldData.dtype != arrayDesc.dataType:
                raise IndexError(
                    'Field {0} for data block {1} has incorrect dtype'.format(fieldDesc.name,
                                                                              arrayDesc.phastaArrayName))
            if fieldData.shape[0] != fieldDesc.nComponents:
                raise IndexError(
                    'Field with name {0} has a different number of components ({1}) '
                    'than expected by configuration ({2})'.format(fieldDesc.name, fieldData.shape[0],
                                                                  fieldDesc.nComponents))

            if fieldData.shape[1] != dataBlockShape[1]:
                raise IndexError(
                    'Fields for data block {0} have different number of elements'.format(arrayDesc.phastaArrayName))

            _embedFieldToDataBlock(dataBlock, fieldData, fieldDesc.startIndex, fieldDesc.nComponents)

        # Write data to file
        timeStep = 0 # TODO: time step handling
        rawWriter.writeDataBlock(arrayDesc.phastaDataBlockName, dataBlock, additionalHeaderData=[timeStep])
