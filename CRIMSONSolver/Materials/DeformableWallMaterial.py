from PythonQt.CRIMSON import FaceType

from CRIMSONSolver.Materials.MaterialBase import MaterialBase

class DeformableWallMaterial(MaterialBase):
    unique = False
    humanReadableName = "Deformable wall material"
    applicableFaceTypes = [FaceType.ftWall]

    def __init__(self):
        MaterialBase.__init__(self)
        self.properties = [
            {"Young's modulus": 4661000.0, "attributes": {"suffix": u" g/(mm\u00B7s\u00B2)", "minimum": 0.0}},
            {"Thickness": 1.0, "attributes": {"suffix": u" mm", "minimum": 0.0}},
        ]

        self.fillMaterialData()

