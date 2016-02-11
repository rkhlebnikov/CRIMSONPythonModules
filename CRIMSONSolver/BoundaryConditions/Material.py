from CRIMSONCore.BoundaryCondition import BoundaryCondition
from PythonQt.CRIMSON import FaceType

class MaterialType(object):
    enumNames = ["Stiffness", "Wall thickness"]
    Stiffness, WallThickness, count = range(3)

class DeformableMaterial(BoundaryCondition):
    unique = False
    humanReadableName = "Material"
    applicableFaceTypes = [FaceType.ftWall]

    def __init__(self):
        BoundaryCondition.__init__(self)
        self.properties = [
            {
                "name": "Material type",
                "value": MaterialType.Stiffness,
                "attributes": {"enumNames": MaterialType.enumNames}
            },
            {
                "name": "value",
                "value": 0.0
            }
        ]
        
    def computeMaterialValues(self, output, vesselForestData, solidModelData, meshData, elementMap):
        validFaceIdentifiers = lambda bc: (x for x in bc.faceIdentifiers if
                                           solidModelData.faceIdentifierIndex(x) != -1)
                          
        materialType = self.getProperties()["Material type"]
        for faceId in validFaceIdentifiers(self):
            for info in meshData.getMeshFaceInfoForFace(faceId):
                output[materialType][elementMap[info[1]]] = self.getProperties()["value"]
