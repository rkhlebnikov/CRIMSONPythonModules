import BoundaryConditions
import Materials
import BoundaryConditionSets
import SolverParameters
import SolverStudies
import SolverSetupManagers

SolverSetups = SolverParameters # To support loading scenes created before rename

__all__ = ['BoundaryConditions', 'Materials', 'BoundaryConditionSets', 'SolverParameters', 'SolverStudies',
           'SolverSetupManagers']

import inspect


def getHumanReadableName(objClass):
    return objClass.humanReadableName if hasattr(objClass, 'humanReadableName') else objClass.__name__

def getSolverSetupManager():
    solverSetupManagerClass = SolverSetupManagers.CRIMSONSolverSolverSetupManager.CRIMSONSolverSolverSetupManager
    return (getHumanReadableName(solverSetupManagerClass), solverSetupManagerClass)

def reloadAll():
    for module_name in __all__:
        exec ('{0} = reload({0})'.format(module_name))
