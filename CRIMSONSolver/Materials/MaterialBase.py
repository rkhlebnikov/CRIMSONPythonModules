from CRIMSONCore.FaceData import FaceData
from CRIMSONCore.PropertyStorage import PropertyAccessor

from CRIMSONSolver.Materials.MaterialEditor import MaterialEditor
from CRIMSONSolver.Materials.MaterialData import MaterialData

class MaterialBase(FaceData):
    def __init__(self):
        FaceData.__init__(self)

        self.materialDatas = []
        self.editor = None

    # Call this function after filling the properties
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

            self.materialDatas.append(MaterialData(name, nComponents, componentNames))


    def createCustomEditorWidget(self):
        if not self.editor:
            self.editor = MaterialEditor(self.materialDatas)
        return self.editor.getEditorWidget()

    def __getstate__(self):
        odict = self.__dict__.copy() # copy the dict
        del odict['editor'] # editor shouldn't be pickled
        return odict

    def __setstate__(self, dict):
        self.__dict__.update(dict)
        self.editor = None # Reload classes on un-pickling

