import BoundaryConditions
import BoundaryConditionSets
import SolverSetups
import SolverStudies
import SolverSetupManagers

__all__ = ['BoundaryConditions', 'BoundaryConditionSets', 'SolverSetups', 'SolverStudies',
           'SolverSetupManagers']

import inspect


def getHumanReadableName(objClass):
    return objClass.humanReadableName if hasattr(objClass, 'humanReadableName') else objClass.__name__

def getSolverSetupManager():
    solverSetupManagerClass = SolverSetupManagers.{{SolverSetupManagerName}}.{{SolverSetupManagerName}}
    return (getHumanReadableName(solverSetupManagerClass), solverSetupManagerClass)

def reloadAll():
    for module_name in __all__:
        exec ('{0} = reload({0})'.format(module_name))
