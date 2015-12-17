import PythonQtMock as PythonQt
import sys

sys.modules['PythonQt'] = PythonQt

import unittest
import tempfile
import numpy
from CRIMSONSolver.SolverStudies.PhastaSolverIO import PhastaRawFileReader, PhastaRawFileWriter, readPhastaFile, \
    writePhastaFile
from CRIMSONSolver.SolverStudies.PhastaConfig import restartConfig, ybarConfig


class TestRawIO(unittest.TestCase):
    @classmethod
    def setUp(cls):
        cls.fileName = r'testData\ybar.1300.0'

    @classmethod
    def tearDown(cls):
        pass

    def test_read(self):
        with open(TestRawIO.fileName, 'rb') as inFile:
            reader = PhastaRawFileReader(inFile)

            byteorderBlockDescriptor = reader.getBlockDescriptor('byteorder magic number')
            self.assertListEqual(byteorderBlockDescriptor.headerElements, [1])
            self.assertEqual(byteorderBlockDescriptor.totalBytes, 4)

            with self.assertRaises(KeyError):
                reader.getBlockDescriptor('UNKNOWN')

            nummodesBlockDescriptor = reader.getBlockDescriptor('number of modes')
            with self.assertRaises(KeyError):
                reader.getDataBlock('number of modes', numpy.float64)

            ybarBlockDescriptor = reader.getBlockDescriptor('ybar')
            expectedNElements = nummodesBlockDescriptor.headerElements[0]
            expectedNComponents = 5
            expectedTimeStep = 1300
            self.assertListEqual(ybarBlockDescriptor.headerElements,
                                 [expectedNElements, expectedNComponents, expectedTimeStep])
            self.assertEqual(ybarBlockDescriptor.totalBytes,
                             expectedNElements * expectedNComponents * 8)  # double is 8 bytes

            with self.assertRaises(KeyError):
                reader.getDataBlock('UNKNOWN', numpy.float64)

            ybarDataBlock = reader.getDataBlock('ybar', numpy.float64)
            self.assertTrue(isinstance(ybarDataBlock, numpy.ndarray))
            self.assertTupleEqual(ybarDataBlock.shape, (expectedNComponents, expectedNElements))
            self.assertEqual(ybarDataBlock.dtype, numpy.dtype(numpy.float64))

    def test_read_write(self):
        with open(self.fileName, 'rb') as inFile:
            rawReader = PhastaRawFileReader(inFile)
            _, tempFName = tempfile.mkstemp()

            with open(tempFName, 'wb') as tempFile:
                rawWriter = PhastaRawFileWriter(tempFile)
                rawWriter.writeFileHeader()

                for blockName, blockDescriptor in rawReader.blockDescriptors.iteritems():
                    if blockDescriptor.totalBytes == -1:  # header only
                        rawWriter.writeHeader(blockName, 0, blockDescriptor.headerElements)
                    elif blockName != 'byteorder magic number':  # header and data
                        rawWriter.writeRawData(blockName, rawReader.getRawData(blockName), blockDescriptor.headerElements)

            with open(tempFName, 'rb') as tempFile:
                rawReader2 = PhastaRawFileReader(tempFile)

                for (blockName, blockDescriptor) in rawReader.blockDescriptors.iteritems():
                    blockDescriptor2 = rawReader2.getBlockDescriptor(blockName)
                    self.assertEqual(blockDescriptor.totalBytes, blockDescriptor2.totalBytes)
                    self.assertListEqual(blockDescriptor.headerElements, blockDescriptor2.headerElements)

                    if blockDescriptor.totalBytes == -1:
                        continue

                    rawData = rawReader.getRawData(blockName)
                    rawData2 = rawReader2.getRawData(blockName)
                    self.assertTrue(numpy.allclose(rawData, rawData2))

    def test_wrong_openmode(self):
        with self.assertRaises(IOError):
            PhastaRawFileReader(open(TestRawIO.fileName, 'rt'))
        with self.assertRaises(IOError):
            PhastaRawFileReader(open(TestRawIO.fileName, 'wb'))
        with self.assertRaises(IOError):
            PhastaRawFileWriter(open(TestRawIO.fileName, 'wt'))
        with self.assertRaises(IOError):
            PhastaRawFileWriter(open(TestRawIO.fileName, 'rb'))


class TestConfigIO(unittest.TestCase):
    @classmethod
    def setUp(cls):
        cls.inFile = open(r'testData\restart.1300.0', 'rb')
        cls.config = restartConfig


    @classmethod
    def tearDown(cls):
        cls.inFile.close()

    def checkField(self, data, phastaField):
        self.assertEqual(data.shape[0], phastaField.nComponents)

    def test_read(self):
        fields = readPhastaFile(PhastaRawFileReader(TestConfigIO.inFile), TestConfigIO.config)

        # Test if all non-optional fields were found
        for arrayDesc in TestConfigIO.config.arrayDescriptors:
            if arrayDesc.optional:
                continue
            for fieldDesc in arrayDesc.fields:
                self.assertTrue(fieldDesc.name in fields)

        # Test consistency of fields that have been read
        elementCount = {}
        for fieldName, fieldArray in fields.iteritems():
            arrayDesc, fieldDesc = TestConfigIO.config.findDescriptorAndField(fieldName)
            self.assertEqual(fieldArray.shape[0], fieldDesc.nComponents)
            self.assertEqual(fieldArray.dtype, numpy.dtype(arrayDesc.dataType))

            # Ensure all fields for the same array have the same element count
            if arrayDesc not in elementCount:
                elementCount[arrayDesc] = fieldArray.shape[1]
            else:
                self.assertEqual(elementCount[arrayDesc], fieldArray.shape[1])

    def test_read_write(self):
        fields1 = readPhastaFile(PhastaRawFileReader(TestConfigIO.inFile), TestConfigIO.config)
        _, tempFName = tempfile.mkstemp()

        with open(tempFName, 'wb') as tempFile:
            writePhastaFile(PhastaRawFileWriter(tempFile), TestConfigIO.config, fields1)

        with open(tempFName, 'rb') as tempFile:
            fields2 = readPhastaFile(PhastaRawFileReader(tempFile), TestConfigIO.config)

        self.assertEqual(len(fields1), len(fields2))

        for (name1, field1), (name2, field2) in zip(fields1.iteritems(), fields2.iteritems()):
            self.assertEqual(name1, name2)
            self.assertEqual(field1.dtype, field2.dtype)
            self.assertEqual(field1.shape, field2.shape)
            self.assertTrue(numpy.allclose(field1, field2))
