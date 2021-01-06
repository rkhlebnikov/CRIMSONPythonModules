import cPickle

"""
    NOTE: The methods in this file are called by
    crimson\Modules\PythonSolverSetupService\src\SolverSetupPythonObjectIO.h
"""

def saveToFile(obj, filename):
    with open(filename, 'wb') as f:
        cPickle.dump(obj, f)

def loadFromFile(filename):
    with open(filename, 'rb') as f:
        return cPickle.load(f)


