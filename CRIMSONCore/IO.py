from __future__ import print_function

import cPickle
from CRIMSONCore.VersionedObject import VersionedObject

"""
    NOTE: The methods in this file are called by
    crimson\Modules\PythonSolverSetupService\src\SolverSetupPythonObjectIO.h
"""

def saveToFile(obj, filename):
    with open(filename, 'wb') as f:
        cPickle.dump(obj, f)

def loadFromFile(filename):
    with open(filename, 'rb') as f:
        obj = cPickle.load(f)

    if(obj is None):
        print('Loaded obj from fileName "', filename, '" that contained no data.', sep='')
        return obj
    
    if(isinstance(obj, VersionedObject)):
        obj.upgradeToLatest()
    
    else:
        print('Loaded object of type "', obj.__class__.__name__, ' from filename "', fileName, '" that was not upgradable.', sep='')

    return obj
        


