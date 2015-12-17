import PythonQtMock as PythonQt

import sys
sys.modules["PythonQt"] = PythonQt

import CRIMSONSolver
import CRIMSONCore
import os
import numpy

print(CRIMSONSolver.getSolverSetupManager())
#t = CRIMSONSolver.Common.FaceIdentifier.FaceIdentifier(1, "")

from CRIMSONSolver.SolverStudies import PhastaSolverIO, PhastaConfig

#fName = r'd:\kcl\Data\Mesh-Adaption-CRIMSON\restart.2520.0'
#fName = r'd:\111\restart.0.1'
#fName = r'd:\kcl\Data\kev_adapt\restart.4000.0'
#fName = r'g:\kcl\Data\adapt_test_2\Solver_output\restart.1300.0'
#fName = r'g:\kcl\Data\adapt_test_2\Solver_output\ybar.1300.0'

#config = PhastaConfig.restartConfig
#config = PhastaConfig.ybarConfig

import unittest

class TestPhastaIO(unittest.TestCase):
    fName = r'g:\kcl\Data\adapt_test_2\Solver_output\restart.1300.0'
    config = PhastaConfig.restartConfig

    def test_read_write(self):
        reader1 = PhastaSolverIO.PhastaFileReader(TestPhastaIO.fName, TestPhastaIO.config)
        writer = PhastaSolverIO.PhastaFileWriter('temp', TestPhastaIO.config, reader1.solutionStorage)
        reader2 = PhastaSolverIO.PhastaFileReader('temp', TestPhastaIO.config)

        self.assertEqual(reader1.solutionStorage.getNArrays(), reader2.solutionStorage.getNArrays())
        for i in xrange(reader1.solutionStorage.getNArrays()):
            self.assertEqual(reader1.solutionStorage.getArrayName(i), reader2.solutionStorage.getArrayName(i))
            self.assertEqual(reader1.solutionStorage.getArrayNComponents(i), reader2.solutionStorage.getArrayNComponents(i))
            self.assertEqual(reader1.solutionStorage.getArrayNTuples(i), reader2.solutionStorage.getArrayNTuples(i))
            self.assertEqual(reader1.solutionStorage.getArrayDataType(i), reader2.solutionStorage.getArrayDataType(i))
            self.assertTrue(numpy.allclose(reader1.solutionStorage.getArrayData(i), reader2.solutionStorage.getArrayData(i)))

if __name__ == '__main__':
    unittest.main()
