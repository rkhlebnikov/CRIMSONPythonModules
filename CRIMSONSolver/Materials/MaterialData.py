import numpy

class RepresentationType(object):
    Table, Script, Constant = range(3)


class InputVariableType(object):
    DistanceAlongPath, LocalRadius, x, y, z = range(5)

class TableData(object):
    def __init__(self, data=None, inputVariableType=InputVariableType.DistanceAlongPath):
        self.data = data
        self.inputVariableType = inputVariableType


class MaterialData(object):
    def __init__(self, name='', nComponents=1, componentNames=None, repr=RepresentationType.Constant,
                 tableData = None,
                 scriptData='def computeMaterialValue(info):\n\treturn 0'):
        self.name = name
        self.nComponents = nComponents
        self.componentNames = componentNames
        self.representation = repr
        self.tableData = tableData if tableData is not None else TableData()
        self.scriptData = scriptData