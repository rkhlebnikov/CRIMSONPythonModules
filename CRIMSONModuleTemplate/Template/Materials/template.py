from CRIMSONCore.FaceData import FaceData
from PythonQt.CRIMSON import FaceType

class {{ClassName}}(FaceData):
    unique = False
    humanReadableName = "{{ClassName}}"
    applicableFaceTypes = [FaceType.ftWall] # Modify as necessary 

    def __init__(self):
        FaceData.__init__(self)
        self.properties = [
            # Add properties here
        ]