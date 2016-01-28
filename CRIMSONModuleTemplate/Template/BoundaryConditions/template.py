from CRIMSONCore.BoundaryCondition import BoundaryCondition
from PythonQt.CRIMSON import FaceType

class {{ClassName}}(BoundaryCondition):
    unique = False
    humanReadableName = "{{ClassName}}"
    applicableFaceTypes = [FaceType.ftWall] # Modify as necessary 

    def __init__(self):
        BoundaryCondition.__init__(self)
        self.properties = [
            # Add properties here
        ]