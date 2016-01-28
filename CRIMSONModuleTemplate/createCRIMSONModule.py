import pystache
import shutil
import os

def processAndCopy(moduleName, subdir, fileName, outFileName, mustacheData):
    with open(os.path.join('Template', subdir, fileName), 'rt') as inFile, open(os.path.join(moduleName, subdir, outFileName), 'wt') as outFile:
        outFile.write(pystache.render(inFile.read(), mustacheData))
    
    
def createFilesPerClass(moduleName, subDirName, mustacheData, classNames):
    os.mkdir(os.path.join(moduleName, subDirName))
    processAndCopy(moduleName, subDirName, '__init__.py', '__init__.py', mustacheData)
    for className in classNames:
        mustacheData['ClassName'] = className
        processAndCopy(moduleName, subDirName, 'template.py', className + '.py', mustacheData)
    

def createCRIMSONModule(moduleName, solverSetupManagerName, bcNames, solverSetupNames, solverStudyNames, bcSetNames = ['BoundaryConditionSet']):
    if os.path.exists(moduleName):
        shutil.rmtree(moduleName)
    os.mkdir(moduleName)
    
    mustacheData = {
        'ModuleName': moduleName,
        'SolverSetupManagerName': solverSetupManagerName,
        'BoundaryConditionSetNames': [{'name': x} for x in bcSetNames],
        'BoundaryConditionNames': [{'name': x} for x in bcNames],
        'SolverSetupNames': [{'name': x} for x in solverSetupNames],
        'SolverStudyNames': [{'name': x} for x in solverStudyNames]
    }
    
    processAndCopy(moduleName, '', '__init__.py', '__init__.py', mustacheData)
    
    os.mkdir(os.path.join(moduleName, 'SolverSetupManagers'))
    processAndCopy(moduleName, 'SolverSetupManagers', '__init__.py', '__init__.py', mustacheData)
    processAndCopy(moduleName, 'SolverSetupManagers', 'SolverSetupManager.py', solverSetupManagerName + '.py', mustacheData)

    createFilesPerClass(moduleName, 'BoundaryConditionSets', mustacheData, bcSetNames)
    createFilesPerClass(moduleName, 'BoundaryConditions', mustacheData, bcNames)
    createFilesPerClass(moduleName, 'SolverSetups', mustacheData, solverSetupNames)
    createFilesPerClass(moduleName, 'SolverStudies', mustacheData, solverStudyNames)
        
    
createCRIMSONModule('MySolver', 'MySolverSetupManager', ['MyBC1', 'MyBC2'], ['MySolverSetup1', 'MySolverSetup2'], ['MyStudy1', 'MyStudy2'])
    
    


