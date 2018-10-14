from CRIMSONCore.FaceData import FaceData

from PythonQt.CRIMSON import FaceType

class BCType(object):
    enumNames = ["Do Nothing", "Dirichlet", "Neumann", "Robin"]
    DoNothing, Dirichlet, Neumann, Robin = range(4)

class ScalarBC(FaceData):
    unique = False
    humanReadableName = "Scalar Boundary Condition"
    applicableFaceTypes = [FaceType.ftCapInflow, FaceType.ftCapOutflow]

    def __init__(self):
        FaceData.__init__(self)
        #self.type = BCType.DoNothing;
        self.type = "Do Nothing";
        self.value = 0.0;
        self.properties = [
            {
                "Boundary condition type": BCType.DoNothing,
                "attributes": {"enumNames": BCType.enumNames}
            },
            {
                "Value": 0.0
            }
        ]

    def setType(self, type):  # for use in CPP code
        self.type = type

    def getType(self):  # for use in CPP code
        return self.type

    def setValue(self, value):  # for use in CPP code
        self.value = value

    def getValue(self):  # for use in CPP code
        return self.value
