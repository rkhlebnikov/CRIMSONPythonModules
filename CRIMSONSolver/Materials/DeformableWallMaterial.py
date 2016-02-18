from CRIMSONCore.BoundaryCondition import BoundaryCondition
from CRIMSONCore.PropertyStorage import PropertyAccessor

from PythonQt.CRIMSON import FaceType

from CRIMSONSolver.Materials.MaterialEditor import MaterialEditor
from CRIMSONSolver.Materials.MaterialData import MaterialData

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

        self.materialData = []
        self.fillMaterialData()
        self.editor = None

    def fillMaterialData(self):
        for property in self.properties:
            name, valueKey = PropertyAccessor.getNameAndValueKey(property)
            value = property[valueKey]
            componentNames = []
            nComponents = 0
            if type(value) is list:
                for componentProperty in value:
                    componentName, _ = PropertyAccessor.getNameAndValueKey(componentProperty)
                    componentNames.append(componentName)
                    nComponents += 1

            nComponents = max(1, nComponents)

            self.materialData.append(MaterialData(name, nComponents, componentNames))


    def createCustomEditorWidget(self):
        if not self.editor:
            self.editor = MaterialEditor(self.materialData)
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
