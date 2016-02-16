from CRIMSONCore.BoundaryCondition import BoundaryCondition
from PythonQt.CRIMSON import FaceType

from CRIMSONSolver.Materials.MaterialEditor import MaterialEditor

class DeformableWallMaterial(BoundaryCondition):
    unique = False
    humanReadableName = "Deformable wall material"
    applicableFaceTypes = [FaceType.ftWall]

    def __init__(self):
        BoundaryCondition.__init__(self)
        self.properties = [
            {"Stiffness": 1.0},
            {"Thickness": 1.0, "attributes": {"suffix": " mm"}},
            {
                "MultiComponent": [
                    {"A11": 0.0},
                    {"A21": 1.0},
                    {"A22": 0.0}
                ]
            }
        ]

        self.editor = None

    def createCustomEditorWidget(self):
        if not self.editor:
            self.editor = MaterialEditor(self)
        return self.editor.getEditorWidget()

    def __getstate__(self):
        odict = self.__dict__.copy() # copy the dict
        del odict['editor'] # editor shouldn't be pickled
        return odict

    def __setstate__(self, dict):
        self.__dict__.update(dict)
        self.editor = None # Reload classes on un-pickling
        
    def computeMaterialValues(self, output, vesselForestData, solidModelData, meshData, elementMap):
        validFaceIdentifiers = lambda bc: (x for x in bc.faceIdentifiers if
                                           solidModelData.faceIdentifierIndex(x) != -1)
                          
        materialType = self.getProperties()["Material type"]
        for faceId in validFaceIdentifiers(self):
            for info in meshData.getMeshFaceInfoForFace(faceId):
                output[materialType][elementMap[info[1]]] = self.getProperties()["value"]
